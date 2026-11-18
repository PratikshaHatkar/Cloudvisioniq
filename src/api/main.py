import os
import uuid
from datetime import datetime, timezone
from typing import List, Optional, Dict, Any
from contextlib import asynccontextmanager

from fastapi import FastAPI, UploadFile, File, HTTPException, Depends, Query, BackgroundTasks, status, Response
from fastapi.responses import FileResponse, RedirectResponse
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session

from src.config import (
    ALLOWED_EXTENSIONS, VIDEOS_DIR, EVIDENCE_DIR,
    DEFAULT_CONFIDENCE_THRESHOLD, DEFAULT_WINDOW_SEC, DEFAULT_STRIDE_SEC
)
from src.api.database import get_db
from src.api.storage import get_storage
from src.api.schemas import (
    HealthResponse, VideoUploadResponse, VideoProcessResponse,
    VideoStatusResponse, VideosListResponse, EventResponse, EventsListResponse,
    ChatQueryRequest, ChatQueryResponse, ChatEventRecord,
    UserRegisterRequest, UserLoginRequest, UserProfileResponse, AuthResponse
)
from src.api.auth import (
    get_current_user, get_optional_current_user,
    hash_password, verify_password, create_access_token,
    validate_email, validate_password
)
from src.api.service import (
    ModelManager, probe_video_file, process_video_background
)
from src.api.nlp.service import execute_chat_query
from src.api.live.router import live_router
from src.api.live.storage import get_live_storage
from src.api.live.stream_manager import get_stream_manager
from src.api.live.inference_service import get_live_inference_service

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: Initialize storage (SQLite tables & MongoDB indexes) and preload model
    storage = get_storage()
    storage.initialize()
    try:
        get_live_storage().initialize()
    except Exception as e:
        print(f"[Lifespan Warning] Could not initialize live storage: {e}")

    try:
        ModelManager.get_instance().load_model()
    except Exception as e:
        print(f"[Lifespan Warning] Could not preload model at startup: {e}")
    yield
    # Shutdown logic: clean up live camera worker threads and inference loop
    try:
        get_stream_manager().shutdown_all()
        get_live_inference_service().stop()
    except Exception as e:
        print(f"[Lifespan Shutdown Error]: {e}")

app = FastAPI(
    title="VisionIQ Surveillance API",
    description="AI-Powered Event Processing Backend with MongoDB Persistence for CCTV Suspicious Activity Recognition",
    version="1.0.0",
    lifespan=lifespan
)

# Enable CORS for frontend integration (supporting cookies and credentials)
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:3000",
        "http://127.0.0.1:3000"
    ],
    allow_origin_regex=r"https?://(localhost|127\.0\.0\.1)(:[0-9]+)?",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# -------------------------------------------------------------
# Root Endpoint (Friendly greeting + docs link)
# -------------------------------------------------------------
@app.get("/", include_in_schema=False)
def root():
    """
    Root endpoint redirecting or displaying API overview.
    """
    return {
        "name": "VisionIQ Surveillance API",
        "version": "1.0.0",
        "status": "operational",
        "documentation": "/docs",
        "health": "/health"
    }

# -------------------------------------------------------------
# 1. Health Endpoint
# -------------------------------------------------------------
@app.get("/health", response_model=HealthResponse, tags=["Health"])
def health_check():
    """
    Returns API health, model loading status, and database connectivity.
    Reports MongoDB status, engine type, and fallback availability.
    """
    model_mgr = ModelManager.get_instance()
    storage = get_storage()
    db_info = storage.get_status()

    return HealthResponse(
        status="healthy",
        api="VisionIQ Surveillance API",
        version="1.0.0",
        model=model_mgr.get_info(),
        database=db_info["status"],
        database_engine=db_info["engine"],
        database_details=db_info["details"],
        mongodb={
            "connected": db_info["engine"] == "mongodb",
            "details": db_info["details"],
            "database": db_info["database"]
        }
    )

# -------------------------------------------------------------
# 2. Authentication Endpoints
# -------------------------------------------------------------
@app.post("/api/auth/register", response_model=AuthResponse, status_code=status.HTTP_201_CREATED, tags=["Authentication"])
async def register(payload: UserRegisterRequest, response: Response):
    """
    Registers a new user account with hashed password and generates an authenticated JWT session.
    """
    name = payload.name.strip()
    email = payload.email.strip().lower()

    if not validate_email(email):
        raise HTTPException(status_code=400, detail="Invalid email address format.")

    is_valid_pw, pw_err = validate_password(payload.password)
    if not is_valid_pw:
        raise HTTPException(status_code=400, detail=pw_err)

    storage = get_storage()
    existing_user = storage.get_user_by_email(email)
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="An account with this email address already exists. Please log in."
        )

    user_id = str(uuid.uuid4())
    pw_hash = hash_password(payload.password)

    new_user = storage.create_user({
        "id": user_id,
        "name": name,
        "email": email,
        "password_hash": pw_hash,
        "created_at": datetime.now(timezone.utc)
    })

    token = create_access_token({"sub": user_id, "email": email})

    # Set secure HttpOnly cookie for session persistence across page refreshes
    response.set_cookie(
        key="access_token",
        value=token,
        httponly=True,
        samesite="lax",
        max_age=60 * 60 * 24 * 7,
        path="/"
    )

    return AuthResponse(
        status="success",
        message="Account registered successfully.",
        access_token=token,
        token_type="bearer",
        user=UserProfileResponse(
            id=new_user["id"],
            name=new_user["name"],
            email=new_user["email"],
            created_at=new_user.get("created_at")
        )
    )

@app.post("/api/auth/login", response_model=AuthResponse, tags=["Authentication"])
async def login(payload: UserLoginRequest, response: Response):
    """
    Authenticates user credentials against the database and establishes a secure session.
    """
    email = payload.email.strip().lower()
    storage = get_storage()
    user = storage.get_user_by_email(email)

    if not user or not verify_password(payload.password, user.get("password_hash", "")):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password."
        )

    user_id = user.get("id") or user.get("user_id")
    token = create_access_token({"sub": user_id, "email": email})

    # Set secure HttpOnly cookie
    response.set_cookie(
        key="access_token",
        value=token,
        httponly=True,
        samesite="lax",
        max_age=60 * 60 * 24 * 7,
        path="/"
    )

    return AuthResponse(
        status="success",
        message="Login successful.",
        access_token=token,
        token_type="bearer",
        user=UserProfileResponse(
            id=user_id,
            name=user.get("name", "User"),
            email=user.get("email"),
            created_at=user.get("created_at")
        )
    )

@app.post("/api/auth/logout", tags=["Authentication"])
async def logout(response: Response):
    """
    Logs out the current user and clears the authentication session cookie.
    """
    response.delete_cookie(key="access_token", path="/")
    return {"status": "success", "message": "Successfully logged out."}

@app.get("/api/auth/me", response_model=UserProfileResponse, tags=["Authentication"])
async def get_current_user_profile(current_user: Dict[str, Any] = Depends(get_current_user)):
    """
    Returns the authenticated user's profile information.
    """
    return UserProfileResponse(
        id=current_user["id"],
        name=current_user["name"],
        email=current_user["email"],
        created_at=current_user.get("created_at")
    )

# -------------------------------------------------------------
# 3. Video Upload Endpoint (User Scoped)
# -------------------------------------------------------------
@app.post("/api/videos/upload", response_model=VideoUploadResponse, status_code=status.HTTP_201_CREATED, tags=["Videos"])
async def upload_video(
    file: UploadFile = File(...),
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """
    Validates and stores an uploaded CCTV video file, returns metadata and unique video_id.
    Persists video document to MongoDB and mirrors to SQLite, associating with authenticated user.
    """
    if not file.filename:
        raise HTTPException(status_code=400, detail="No file uploaded.")

    # Validate file extension
    ext = os.path.splitext(file.filename)[1].lower()
    if ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid file format '{ext}'. Allowed formats: {sorted(list(ALLOWED_EXTENSIONS))}"
        )

    video_id = str(uuid.uuid4())
    safe_filename = f"{video_id}_{os.path.basename(file.filename)}"
    destination_path = os.path.join(VIDEOS_DIR, safe_filename)

    # Stream write to disk
    bytes_written = 0
    try:
        with open(destination_path, "wb") as buffer:
            while chunk := await file.read(1024 * 1024):  # 1MB chunks
                buffer.write(chunk)
                bytes_written += len(chunk)
    except Exception as e:
        if os.path.exists(destination_path):
            os.remove(destination_path)
        raise HTTPException(status_code=500, detail=f"Failed to save video: {str(e)}")

    if bytes_written == 0:
        if os.path.exists(destination_path):
            os.remove(destination_path)
        raise HTTPException(status_code=400, detail="Uploaded file is empty (0 bytes).")

    # Probe video metadata using OpenCV
    try:
        meta = probe_video_file(destination_path)
    except Exception as e:
        if os.path.exists(destination_path):
            os.remove(destination_path)
        raise HTTPException(status_code=400, detail=f"Invalid or corrupted video: {str(e)}")

    # Store in database via StorageRepository with authenticated user ownership
    storage = get_storage()
    video_record = storage.create_video({
        "video_id": video_id,
        "user_id": current_user["id"],
        "filename": file.filename,
        "file_path": destination_path,
        "file_size": bytes_written,
        "status": "uploaded",
        "duration": meta.get("duration"),
        "fps": meta.get("fps"),
        "total_frames": meta.get("total_frames"),
        "width": meta.get("width"),
        "height": meta.get("height"),
        "resolution": meta.get("resolution"),
        "created_at": datetime.now(timezone.utc)
    }, user_id=current_user["id"])

    return VideoUploadResponse(
        video_id=video_record["video_id"],
        filename=video_record["filename"],
        status=video_record["status"],
        file_size=video_record["file_size"],
        duration=video_record.get("duration"),
        fps=video_record.get("fps"),
        resolution=video_record.get("resolution") or (f"{video_record['width']}x{video_record['height']}" if video_record.get("width") and video_record.get("height") else None),
        created_at=video_record["created_at"]
    )

# -------------------------------------------------------------
# 4. Video Processing Endpoint (User Scoped)
# -------------------------------------------------------------
@app.post("/api/videos/{video_id}/process", response_model=VideoProcessResponse, tags=["Videos"])
def process_video(
    video_id: str,
    background_tasks: BackgroundTasks,
    confidence_threshold: float = Query(DEFAULT_CONFIDENCE_THRESHOLD, ge=0.0, le=1.0),
    window_sec: float = Query(DEFAULT_WINDOW_SEC, gt=0.0),
    stride_sec: float = Query(DEFAULT_STRIDE_SEC, gt=0.0),
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """
    Initiates asynchronous action recognition processing for a user's uploaded video.
    Prevents IDOR by verifying user ownership.
    """
    storage = get_storage()
    video = storage.get_video(video_id, user_id=current_user["id"])
    if not video:
        raise HTTPException(status_code=404, detail=f"Video '{video_id}' not found.")

    if video["status"] == "processing":
        raise HTTPException(status_code=409, detail="Video is already being processed.")

    if not os.path.exists(video["file_path"]):
        raise HTTPException(status_code=404, detail="Underlying video file is missing from disk.")

    # Mark as processing in storage
    storage.update_video_status(video_id, status="processing")

    # Launch background task
    background_tasks.add_task(
        process_video_background,
        video_id=video_id,
        threshold=confidence_threshold,
        window_sec=window_sec,
        stride_sec=stride_sec
    )

    return VideoProcessResponse(
        video_id=video["video_id"],
        status="processing",
        message="Video processing started in background."
    )

# -------------------------------------------------------------
# 5. List All User Videos Endpoint (User Scoped)
# -------------------------------------------------------------
@app.get("/api/videos", response_model=VideosListResponse, tags=["Videos"])
def list_videos(
    limit: int = Query(50, ge=1, le=500),
    offset: int = Query(0, ge=0),
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """
    Retrieves uploaded videos belonging exclusively to the authenticated user.
    """
    storage = get_storage()
    total, videos = storage.list_videos(limit=limit, offset=offset, user_id=current_user["id"])

    return VideosListResponse(
        total=total,
        videos=[
            VideoStatusResponse(
                video_id=v["video_id"],
                filename=v["filename"],
                status=v["status"],
                events_count=storage.get_video_events_count(v["video_id"], user_id=current_user["id"]),
                duration=v.get("duration"),
                fps=v.get("fps"),
                error_message=v.get("error_message"),
                created_at=v["created_at"],
                updated_at=v.get("updated_at") or v["created_at"]
            )
            for v in videos
        ]
    )

# -------------------------------------------------------------
# 6. Video Status Endpoint (User Scoped)
# -------------------------------------------------------------
@app.get("/api/videos/{video_id}/status", response_model=VideoStatusResponse, tags=["Videos"])
def get_video_status(
    video_id: str,
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """
    Reports current status and event count for a user's video.
    Prevents IDOR by verifying user ownership.
    """
    storage = get_storage()
    video = storage.get_video(video_id, user_id=current_user["id"])
    if not video:
        raise HTTPException(status_code=404, detail=f"Video '{video_id}' not found.")

    events_count = storage.get_video_events_count(video_id, user_id=current_user["id"])

    return VideoStatusResponse(
        video_id=video["video_id"],
        filename=video["filename"],
        status=video["status"],
        events_count=events_count,
        duration=video.get("duration"),
        fps=video.get("fps"),
        error_message=video.get("error_message"),
        created_at=video["created_at"],
        updated_at=video.get("updated_at") or video["created_at"]
    )

@app.delete("/api/videos/{video_id}", tags=["Videos"])
def delete_video(
    video_id: str,
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """
    Deletes an uploaded video, its physical file from disk, and all associated detected events.
    Enforces user ownership to prevent IDOR attacks.
    """
    storage = get_storage()
    deleted = storage.delete_video(video_id, user_id=current_user["id"])
    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Video with ID '{video_id}' not found."
        )
    return {
        "status": "success",
        "message": f"Video '{video_id}' deleted successfully.",
        "video_id": video_id
    }

@app.get("/api/videos/{video_id}/download", tags=["Videos"])
def download_video(
    video_id: str,
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """
    Downloads the underlying video file.
    Enforces user ownership to prevent unauthorized access.
    """
    storage = get_storage()
    video = storage.get_video(video_id, user_id=current_user["id"])
    if not video:
        raise HTTPException(status_code=404, detail=f"Video '{video_id}' not found.")
    file_path = video.get("file_path")
    if not file_path or not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="Video file not found on disk.")
    return FileResponse(file_path, filename=video.get("filename", f"{video_id}.mp4"))

# -------------------------------------------------------------
# 7. Video Events Endpoint (User Scoped)
# -------------------------------------------------------------
@app.get("/api/videos/{video_id}/events", response_model=List[EventResponse], tags=["Events"])
def get_video_events(
    video_id: str,
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """
    Returns detected suspicious activity events for a specific user video.
    Prevents IDOR by verifying user ownership.
    """
    storage = get_storage()
    video = storage.get_video(video_id, user_id=current_user["id"])
    if not video:
        raise HTTPException(status_code=404, detail=f"Video '{video_id}' not found.")

    events = storage.get_video_events(video_id, user_id=current_user["id"])
    return [
        EventResponse(
            event_id=ev["event_id"],
            video_id=ev["video_id"],
            activity_label=ev["activity_label"],
            confidence=ev["confidence"],
            start_timestamp=ev["start_timestamp"],
            end_timestamp=ev["end_timestamp"],
            start_time_formatted=ev["start_time_formatted"],
            end_time_formatted=ev["end_time_formatted"],
            evidence_snapshot=ev.get("evidence_snapshot"),
            evidence_clip=ev.get("evidence_clip"),
            processing_status=ev.get("processing_status", "completed"),
            created_at=ev.get("created_at") or datetime.now(timezone.utc)
        )
        for ev in events
    ]

# -------------------------------------------------------------
# 8. Cross-Video Events Query & Filter Endpoint (User Scoped)
# -------------------------------------------------------------
@app.get("/api/events", response_model=EventsListResponse, tags=["Events"])
def list_events(
    activity: Optional[str] = Query(None, description="Filter by activity category (e.g. Fighting, Robbery)"),
    video_id: Optional[str] = Query(None, description="Filter by specific video ID"),
    min_confidence: Optional[float] = Query(None, ge=0.0, le=1.0, description="Minimum confidence threshold"),
    limit: int = Query(50, ge=1, le=500),
    offset: int = Query(0, ge=0),
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """
    Retrieves events across all videos belonging exclusively to the authenticated user.
    """
    storage = get_storage()
    total, events = storage.list_events(
        activity=activity,
        video_id=video_id,
        min_confidence=min_confidence,
        limit=limit,
        offset=offset,
        user_id=current_user["id"]
    )

    return EventsListResponse(
        total=total,
        events=[
            EventResponse(
                event_id=ev["event_id"],
                video_id=ev["video_id"],
                activity_label=ev["activity_label"],
                confidence=ev["confidence"],
                start_timestamp=ev["start_timestamp"],
                end_timestamp=ev["end_timestamp"],
                start_time_formatted=ev["start_time_formatted"],
                end_time_formatted=ev["end_time_formatted"],
                evidence_snapshot=ev.get("evidence_snapshot"),
                evidence_clip=ev.get("evidence_clip"),
                processing_status=ev.get("processing_status", "completed"),
                created_at=ev.get("created_at") or datetime.now(timezone.utc)
            )
            for ev in events
        ]
    )

@app.delete("/api/events", tags=["Events"])
def clear_all_events(current_user: Dict[str, Any] = Depends(get_current_user)):
    """
    Deletes all detected suspicious events history belonging exclusively to the authenticated user.
    Resets the detected event counter to zero for this user.
    """
    storage = get_storage()
    deleted_count = storage.delete_all_events(user_id=current_user["id"])
    return {
        "status": "success",
        "message": f"Successfully cleared {deleted_count} suspicious events.",
        "deleted_count": deleted_count
    }

@app.delete("/api/events/{event_id}", tags=["Events"])
def delete_single_event(
    event_id: str,
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """
    Deletes a single suspicious event belonging to the authenticated user.
    Prevents IDOR by verifying user ownership.
    """
    storage = get_storage()
    deleted = storage.delete_event(event_id, user_id=current_user["id"])
    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Event with ID '{event_id}' not found."
        )
    return {
        "status": "success",
        "message": f"Event '{event_id}' deleted successfully.",
        "event_id": event_id
    }

# -------------------------------------------------------------
# 9. Evidence Snapshot Serving Endpoint (User Scoped)
# -------------------------------------------------------------
@app.get("/api/evidence/{filename}", tags=["Evidence"])
def get_evidence_snapshot(
    filename: str,
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """
    Safely serves an evidence snapshot image from disk.
    Enforces user ownership validation to prevent unauthorized access or IDOR.
    """
    clean_filename = os.path.basename(filename)
    file_path = os.path.join(EVIDENCE_DIR, clean_filename)

    if not os.path.isfile(file_path):
        raise HTTPException(status_code=404, detail="Evidence snapshot not found.")

    storage = get_storage()
    if not storage.is_evidence_owned_by_user(clean_filename, current_user["id"]):
        raise HTTPException(status_code=404, detail="Evidence snapshot not found.")

    return FileResponse(file_path, media_type="image/jpeg")

# -------------------------------------------------------------
# 10. Semantic Search & Grounded AI Chatbot Endpoint (User Scoped)
# -------------------------------------------------------------
@app.post("/api/chat/query", response_model=ChatQueryResponse, tags=["AI Chatbot"])
def chat_query(
    request: ChatQueryRequest,
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """
    Executes hybrid semantic search and grounded AI question answering strictly over
    the authenticated user's CCTV events. Prevents cross-user data exposure.
    """
    res = execute_chat_query(
        query=request.query,
        video_id=request.video_id,
        activity=request.activity,
        min_confidence=request.min_confidence,
        limit=request.limit,
        user_id=current_user["id"]
    )

    return ChatQueryResponse(
        query=res["query"],
        answer=res["answer"],
        applied_filters=res["applied_filters"],
        events=[
            ChatEventRecord(
                event_id=ev["event_id"],
                video_id=ev["video_id"],
                activity_label=ev["activity_label"],
                confidence=ev["confidence"],
                start_timestamp=ev["start_timestamp"],
                end_timestamp=ev["end_timestamp"],
                start_time_formatted=ev["start_time_formatted"],
                end_time_formatted=ev["end_time_formatted"],
                evidence_snapshot=ev.get("evidence_snapshot"),
                filename=ev.get("filename"),
                relevance_score=ev.get("relevance_score")
            )
            for ev in res["events"]
        ],
        total=res["total"],
        retrieval_method=res["retrieval_method"],
        limitations=res["limitations"]
    )

# -------------------------------------------------------------
# 11. Live CCTV Surveillance Router
# -------------------------------------------------------------
app.include_router(live_router, prefix="/api/live", tags=["Live Surveillance"])
