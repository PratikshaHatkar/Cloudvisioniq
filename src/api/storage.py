import os
import re
import uuid
from datetime import datetime, timezone
from typing import List, Dict, Any, Optional, Tuple

from src.config import MONGODB_DATABASE
from src.api.mongo import get_mongo_db, get_mongo_client, check_mongo_connection, init_mongo_indexes
from src.api.database import SessionLocal, init_db as init_sqlite_db
from src.api.models import Video, Event, User
from sqlalchemy import func

def utc_now() -> datetime:
    return datetime.now(timezone.utc)

class StorageRepository:
    """
    Unified storage repository supporting MongoDB as primary store with
    automatic SQLite fallback and dual-sync persistence.
    """

    def __init__(self):
        self._initialized = False

    def initialize(self):
        """
        Initializes both SQLite schemas and MongoDB indexes.
        """
        # 1. Initialize SQLite tables
        try:
            init_sqlite_db()
        except Exception as e:
            print(f"[Storage] SQLite init warning: {e}")

        # 2. Initialize MongoDB indexes if connected
        try:
            db = get_mongo_db()
            if db is not None:
                init_mongo_indexes(db)
                print(f"[Storage] MongoDB indexes verified for database '{MONGODB_DATABASE}'.")
        except Exception as e:
            print(f"[Storage] MongoDB init warning: {e}")

        self._initialized = True

    def get_status(self) -> Dict[str, Any]:
        """
        Checks connectivity to MongoDB and returns status information.
        """
        is_mongo_up, mongo_info = check_mongo_connection()
        if is_mongo_up:
            return {
                "status": "connected",
                "engine": "mongodb",
                "details": mongo_info,
                "database": MONGODB_DATABASE,
                "fallback_available": True
            }
        else:
            return {
                "status": "connected",  # Service is operational via SQLite fallback
                "engine": "sqlite_fallback",
                "details": f"SQLite active ({mongo_info})",
                "database": "sqlite",
                "fallback_available": True
            }

    # -------------------------------------------------------------
    # User Operations & Authentication
    # -------------------------------------------------------------
    def create_user(self, name_or_data: Any, email: Optional[str] = None, password_hash: Optional[str] = None) -> Dict[str, Any]:
        """
        Creates a new user record in MongoDB and mirrors to SQLite.
        Accepts either a dictionary of user fields or (name, email, password_hash).
        """
        if isinstance(name_or_data, dict):
            user_id = name_or_data.get("id") or name_or_data.get("user_id") or str(uuid.uuid4())
            name = name_or_data.get("name", "")
            email = name_or_data.get("email", "")
            password_hash = name_or_data.get("password_hash", "")
            now = name_or_data.get("created_at") or utc_now()
        else:
            user_id = str(uuid.uuid4())
            name = name_or_data or ""
            now = utc_now()

        doc = {
            "user_id": user_id,
            "id": user_id,
            "name": str(name).strip(),
            "email": str(email).strip().lower(),
            "password_hash": password_hash or "",
            "created_at": now,
            "updated_at": now
        }

        # 1. MongoDB
        db = get_mongo_db()
        if db is not None:
            try:
                db["users"].update_one(
                    {"email": doc["email"]},
                    {"$set": doc},
                    upsert=True
                )
            except Exception as e:
                print(f"[Storage Error] Mongo create_user failed: {e}")

        # 2. SQLite
        try:
            with SessionLocal() as sq_db:
                existing = sq_db.query(User).filter(func.lower(User.email) == doc["email"]).first()
                if not existing:
                    u_model = User(
                        id=user_id,
                        name=doc["name"],
                        email=doc["email"],
                        password_hash=doc["password_hash"],
                        created_at=doc["created_at"],
                        updated_at=doc["updated_at"]
                    )
                    sq_db.add(u_model)
                    sq_db.commit()
        except Exception as e:
            print(f"[Storage Error] SQLite create_user failed: {e}")

        return doc

    def get_user_by_email(self, email: str) -> Optional[Dict[str, Any]]:
        """
        Retrieves user record by email (case-insensitive) from MongoDB or SQLite.
        """
        clean_email = email.strip().lower()
        db = get_mongo_db()
        if db is not None:
            try:
                doc = db["users"].find_one({"email": clean_email}, {"_id": 0})
                if doc:
                    return doc
            except Exception as e:
                print(f"[Storage Error] Mongo get_user_by_email failed: {e}")

        try:
            with SessionLocal() as sq_db:
                u = sq_db.query(User).filter(func.lower(User.email) == clean_email).first()
                if u:
                    return {
                        "id": u.id,
                        "user_id": u.id,
                        "name": u.name,
                        "email": u.email,
                        "password_hash": u.password_hash,
                        "created_at": u.created_at,
                        "updated_at": u.updated_at
                    }
        except Exception as e:
            print(f"[Storage Error] SQLite get_user_by_email failed: {e}")

        return None

    def get_user_by_id(self, user_id: str) -> Optional[Dict[str, Any]]:
        """
        Retrieves user record by user_id from MongoDB or SQLite.
        """
        db = get_mongo_db()
        if db is not None:
            try:
                doc = db["users"].find_one({"$or": [{"user_id": user_id}, {"id": user_id}]}, {"_id": 0})
                if doc:
                    return doc
            except Exception as e:
                print(f"[Storage Error] Mongo get_user_by_id failed: {e}")

        try:
            with SessionLocal() as sq_db:
                u = sq_db.query(User).filter(User.id == user_id).first()
                if u:
                    return {
                        "id": u.id,
                        "user_id": u.id,
                        "name": u.name,
                        "email": u.email,
                        "password_hash": u.password_hash,
                        "created_at": u.created_at,
                        "updated_at": u.updated_at
                    }
        except Exception as e:
            print(f"[Storage Error] SQLite get_user_by_id failed: {e}")

        return None

    # -------------------------------------------------------------
    # Video Operations
    # -------------------------------------------------------------
    def create_video(self, video_data: Dict[str, Any], user_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Persists a newly uploaded video metadata record into MongoDB and SQLite.
        Associates the video with the authenticated user_id.
        """
        video_id = video_data.get("video_id") or str(uuid.uuid4())
        owner_id = user_id or video_data.get("user_id")
        now = video_data.get("created_at") or utc_now()
        
        doc = {
            "video_id": video_id,
            "user_id": owner_id,
            "filename": video_data["filename"],
            "file_path": video_data["file_path"],
            "file_size": video_data.get("file_size", 0),
            "status": video_data.get("status", "uploaded"),
            "duration": video_data.get("duration"),
            "fps": video_data.get("fps"),
            "total_frames": video_data.get("total_frames"),
            "width": video_data.get("width"),
            "height": video_data.get("height"),
            "resolution": video_data.get("resolution"),
            "error_message": video_data.get("error_message"),
            "created_at": now,
            "updated_at": now
        }

        # 1. Save to MongoDB
        db = get_mongo_db()
        if db is not None:
            try:
                db["videos"].update_one(
                    {"video_id": video_id},
                    {"$set": doc},
                    upsert=True
                )
            except Exception as e:
                print(f"[Storage Error] Failed to insert video into MongoDB: {e}")

        # 2. Mirror to SQLite
        try:
            with SessionLocal() as sq_db:
                existing = sq_db.query(Video).filter(Video.id == video_id).first()
                if not existing:
                    v_model = Video(
                        id=video_id,
                        user_id=owner_id,
                        filename=doc["filename"],
                        file_path=doc["file_path"],
                        file_size=doc["file_size"],
                        status=doc["status"],
                        duration=doc["duration"],
                        fps=doc["fps"],
                        total_frames=doc["total_frames"],
                        width=doc["width"],
                        height=doc["height"],
                        error_message=doc["error_message"],
                        created_at=doc["created_at"],
                        updated_at=doc["updated_at"]
                    )
                    sq_db.add(v_model)
                    sq_db.commit()
                elif owner_id and not existing.user_id:
                    existing.user_id = owner_id
                    sq_db.commit()
        except Exception as e:
            print(f"[Storage Warning] Mirror to SQLite failed for video {video_id}: {e}")

        return doc

    def get_video(self, video_id: str, user_id: Optional[str] = None) -> Optional[Dict[str, Any]]:
        """
        Retrieves a video record by video_id from MongoDB or SQLite.
        If user_id is provided, enforces that the caller owns the video.
        """
        # Check MongoDB first
        db = get_mongo_db()
        if db is not None:
            try:
                q = {"video_id": video_id}
                if user_id:
                    q["user_id"] = user_id
                doc = db["videos"].find_one(q, {"_id": 0})
                if doc:
                    return doc
            except Exception as e:
                print(f"[Storage Error] Mongo get_video failed: {e}")

        # Fallback to SQLite
        try:
            with SessionLocal() as sq_db:
                query = sq_db.query(Video).filter(Video.id == video_id)
                if user_id:
                    query = query.filter(Video.user_id == user_id)
                v = query.first()
                if v:
                    return {
                        "video_id": v.id,
                        "user_id": v.user_id,
                        "filename": v.filename,
                        "file_path": v.file_path,
                        "file_size": v.file_size,
                        "status": v.status,
                        "duration": v.duration,
                        "fps": v.fps,
                        "total_frames": v.total_frames,
                        "width": v.width,
                        "height": v.height,
                        "resolution": f"{v.width}x{v.height}" if v.width and v.height else None,
                        "error_message": v.error_message,
                        "created_at": v.created_at,
                        "updated_at": v.updated_at
                    }
        except Exception as e:
            print(f"[Storage Error] SQLite get_video failed: {e}")

        return None

    def update_video_status(
        self,
        video_id: str,
        status: str,
        error_message: Optional[str] = None
    ) -> Optional[Dict[str, Any]]:
        """
        Updates the status and optional error_message of a video.
        """
        now = utc_now()
        update_fields = {
            "status": status,
            "error_message": error_message,
            "updated_at": now
        }

        # 1. Update in MongoDB
        db = get_mongo_db()
        if db is not None:
            try:
                db["videos"].update_one(
                    {"video_id": video_id},
                    {"$set": update_fields}
                )
            except Exception as e:
                print(f"[Storage Error] Mongo update_video_status failed: {e}")

        # 2. Update in SQLite
        try:
            with SessionLocal() as sq_db:
                v = sq_db.query(Video).filter(Video.id == video_id).first()
                if v:
                    v.status = status
                    v.error_message = error_message
                    v.updated_at = now
                    sq_db.commit()
        except Exception as e:
            print(f"[Storage Error] SQLite update_video_status failed: {e}")

        return self.get_video(video_id)

    # -------------------------------------------------------------
    # Event Operations
    # -------------------------------------------------------------
    def save_events(self, video_id: str, events_data: List[Dict[str, Any]], user_id: Optional[str] = None) -> int:
        """
        Idempotently persists detected events for a video.
        Associates each event with the owner's user_id.
        """
        if not user_id:
            parent_v = self.get_video(video_id)
            if parent_v:
                user_id = parent_v.get("user_id")

        # 1. MongoDB Save
        db = get_mongo_db()
        if db is not None:
            try:
                db["events"].delete_many({"video_id": video_id})
                if events_data:
                    mongo_docs = []
                    for ev in events_data:
                        edoc = dict(ev)
                        if "_id" in edoc:
                            del edoc["_id"]
                        edoc["user_id"] = user_id
                        mongo_docs.append(edoc)
                    db["events"].insert_many(mongo_docs)
            except Exception as e:
                print(f"[Storage Error] Mongo save_events failed: {e}")

        # 2. Mirror to SQLite
        try:
            with SessionLocal() as sq_db:
                sq_db.query(Event).filter(Event.video_id == video_id).delete()
                for ed in events_data:
                    ev_model = Event(
                        id=ed["event_id"],
                        user_id=user_id,
                        video_id=ed["video_id"],
                        activity_label=ed["activity_label"],
                        confidence=ed["confidence"],
                        start_timestamp=ed["start_timestamp"],
                        end_timestamp=ed["end_timestamp"],
                        start_time_formatted=ed["start_time_formatted"],
                        end_time_formatted=ed["end_time_formatted"],
                        evidence_snapshot=ed.get("evidence_snapshot"),
                        evidence_clip=ed.get("evidence_clip"),
                        processing_status=ed.get("processing_status", "completed"),
                        created_at=ed.get("created_at") or utc_now()
                    )
                    sq_db.add(ev_model)
                sq_db.commit()
        except Exception as e:
            print(f"[Storage Error] SQLite save_events failed: {e}")

        return len(events_data)

    def get_video_events(self, video_id: str, user_id: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Retrieves all detected events for a given video, ordered by start_timestamp.
        If user_id is provided, verifies caller ownership of the parent video.
        """
        if user_id:
            parent_v = self.get_video(video_id, user_id=user_id)
            if not parent_v:
                return []

        # 1. Check MongoDB
        db = get_mongo_db()
        if db is not None:
            try:
                q = {"video_id": video_id}
                if user_id:
                    q["user_id"] = user_id
                docs = list(db["events"].find(q, {"_id": 0}).sort("start_timestamp", 1))
                if docs:
                    return docs
            except Exception as e:
                print(f"[Storage Error] Mongo get_video_events failed: {e}")

        # 2. Check SQLite fallback
        try:
            with SessionLocal() as sq_db:
                q = sq_db.query(Event).filter(Event.video_id == video_id)
                if user_id:
                    q = q.filter(Event.user_id == user_id)
                events = q.order_by(Event.start_timestamp).all()
                if events:
                    return [
                        {
                            "event_id": ev.id,
                            "user_id": ev.user_id,
                            "video_id": ev.video_id,
                            "activity_label": ev.activity_label,
                            "confidence": ev.confidence,
                            "start_timestamp": ev.start_timestamp,
                            "end_timestamp": ev.end_timestamp,
                            "start_time_formatted": ev.start_time_formatted,
                            "end_time_formatted": ev.end_time_formatted,
                            "evidence_snapshot": ev.evidence_snapshot,
                            "evidence_clip": ev.evidence_clip,
                            "processing_status": ev.processing_status,
                            "created_at": ev.created_at
                        }
                        for ev in events
                    ]
        except Exception as e:
            print(f"[Storage Error] SQLite get_video_events failed: {e}")

        return []

    def get_video_events_count(self, video_id: str, user_id: Optional[str] = None) -> int:
        """
        Returns count of events associated with a video.
        """
        if user_id:
            parent_v = self.get_video(video_id, user_id=user_id)
            if not parent_v:
                return 0

        db = get_mongo_db()
        if db is not None:
            try:
                q = {"video_id": video_id}
                if user_id:
                    q["user_id"] = user_id
                count = db["events"].count_documents(q)
                if count > 0:
                    return count
            except Exception as e:
                print(f"[Storage Error] Mongo count failed: {e}")

        try:
            with SessionLocal() as sq_db:
                q = sq_db.query(Event).filter(Event.video_id == video_id)
                if user_id:
                    q = q.filter(Event.user_id == user_id)
                return q.count()
        except Exception:
            return 0

    def list_events(
        self,
        activity: Optional[str] = None,
        video_id: Optional[str] = None,
        min_confidence: Optional[float] = None,
        limit: int = 50,
        offset: int = 0,
        user_id: Optional[str] = None
    ) -> Tuple[int, List[Dict[str, Any]]]:
        """
        Searches and filters events across videos with pagination, scoped to user_id.
        """
        db = get_mongo_db()
        if db is not None:
            try:
                query_filter = {}
                if user_id:
                    query_filter["user_id"] = user_id
                if activity:
                    query_filter["activity_label"] = {"$regex": f"^{activity.strip()}$", "$options": "i"}
                if video_id:
                    query_filter["video_id"] = video_id.strip()
                if min_confidence is not None:
                    query_filter["confidence"] = {"$gte": float(min_confidence)}

                total = db["events"].count_documents(query_filter)
                if total > 0 or not self._has_sqlite_events(activity, video_id, min_confidence, user_id=user_id):
                    cursor = db["events"].find(
                        query_filter,
                        {"_id": 0}
                    ).sort("created_at", -1).skip(offset).limit(limit)
                    return total, list(cursor)
            except Exception as e:
                print(f"[Storage Error] Mongo list_events failed: {e}")

        # SQLite query
        return self._list_events_sqlite(activity, video_id, min_confidence, limit, offset, user_id=user_id)

    def _has_sqlite_events(
        self,
        activity: Optional[str],
        video_id: Optional[str],
        min_confidence: Optional[float],
        user_id: Optional[str] = None
    ) -> bool:
        try:
            with SessionLocal() as sq_db:
                q = sq_db.query(Event)
                if user_id:
                    q = q.filter(Event.user_id == user_id)
                if activity:
                    q = q.filter(Event.activity_label.ilike(activity.strip()))
                if video_id:
                    q = q.filter(Event.video_id == video_id.strip())
                if min_confidence is not None:
                    q = q.filter(Event.confidence >= min_confidence)
                return q.count() > 0
        except Exception:
            return False

    def _list_events_sqlite(
        self,
        activity: Optional[str],
        video_id: Optional[str],
        min_confidence: Optional[float],
        limit: int,
        offset: int,
        user_id: Optional[str] = None
    ) -> Tuple[int, List[Dict[str, Any]]]:
        try:
            with SessionLocal() as sq_db:
                q = sq_db.query(Event)
                if user_id:
                    q = q.filter(Event.user_id == user_id)
                if activity:
                    q = q.filter(Event.activity_label.ilike(activity.strip()))
                if video_id:
                    q = q.filter(Event.video_id == video_id.strip())
                if min_confidence is not None:
                    q = q.filter(Event.confidence >= min_confidence)

                total = q.count()
                events = q.order_by(Event.created_at.desc()).offset(offset).limit(limit).all()

                results = [
                    {
                        "event_id": ev.id,
                        "user_id": ev.user_id,
                        "video_id": ev.video_id,
                        "activity_label": ev.activity_label,
                        "confidence": ev.confidence,
                        "start_timestamp": ev.start_timestamp,
                        "end_timestamp": ev.end_timestamp,
                        "start_time_formatted": ev.start_time_formatted,
                        "end_time_formatted": ev.end_time_formatted,
                        "evidence_snapshot": ev.evidence_snapshot,
                        "evidence_clip": ev.evidence_clip,
                        "processing_status": ev.processing_status,
                        "created_at": ev.created_at
                    }
                    for ev in events
                ]
                return total, results
        except Exception as e:
            print(f"[Storage Error] SQLite _list_events_sqlite failed: {e}")
            return 0, []

    def delete_all_events(self, user_id: Optional[str] = None) -> int:
        """
        Deletes all detected events history from MongoDB and SQLite for the given user.
        Resets the event counter to zero.
        """
        deleted_count = 0
        db = get_mongo_db()
        q = {"user_id": user_id} if user_id else {}
        if db is not None:
            try:
                res = db["events"].delete_many(q)
                deleted_count = max(deleted_count, res.deleted_count)
            except Exception as e:
                print(f"[Storage Error] Mongo delete_all_events failed: {e}")

        try:
            with SessionLocal() as sq_db:
                query = sq_db.query(Event)
                if user_id:
                    query = query.filter(Event.user_id == user_id)
                sq_deleted = query.delete()
                sq_db.commit()
                deleted_count = max(deleted_count, sq_deleted)
        except Exception as e:
            print(f"[Storage Error] SQLite delete_all_events failed: {e}")

        # Also clear live surveillance incidents for this owner if any
        try:
            from src.api.live.storage import get_live_storage
            get_live_storage().clear_all_incidents(owner_id=user_id)
        except Exception:
            pass

        return deleted_count

    def delete_event(self, event_id: str, user_id: Optional[str] = None) -> bool:
        """
        Deletes a single event by event_id from MongoDB and SQLite, validating ownership.
        """
        deleted = False
        db = get_mongo_db()
        q = {"$or": [{"event_id": event_id}, {"id": event_id}]}
        if user_id:
            q["user_id"] = user_id
        if db is not None:
            try:
                res = db["events"].delete_one(q)
                if res.deleted_count > 0:
                    deleted = True
            except Exception as e:
                print(f"[Storage Error] Mongo delete_event failed: {e}")

        try:
            with SessionLocal() as sq_db:
                query = sq_db.query(Event).filter(Event.id == event_id)
                if user_id:
                    query = query.filter(Event.user_id == user_id)
                sq_deleted = query.delete()
                sq_db.commit()
                if sq_deleted > 0:
                    deleted = True
        except Exception as e:
            print(f"[Storage Error] SQLite delete_event failed: {e}")

        return deleted

    def list_videos(self, limit: int = 50, offset: int = 0, user_id: Optional[str] = None) -> Tuple[int, List[Dict[str, Any]]]:
        """
        Retrieves uploaded videos with pagination, scoped to user_id.
        """
        db = get_mongo_db()
        q = {"user_id": user_id} if user_id else {}
        if db is not None:
            try:
                total = db["videos"].count_documents(q)
                cursor = db["videos"].find(q, {"_id": 0}).sort("created_at", -1).skip(offset).limit(limit)
                return total, list(cursor)
            except Exception as e:
                print(f"[Storage Error] Mongo list_videos failed: {e}")

        try:
            with SessionLocal() as sq_db:
                query = sq_db.query(Video)
                if user_id:
                    query = query.filter(Video.user_id == user_id)
                total = query.count()
                videos = query.order_by(Video.created_at.desc()).offset(offset).limit(limit).all()
                results = [
                    {
                        "video_id": v.id,
                        "user_id": v.user_id,
                        "filename": v.filename,
                        "file_path": v.file_path,
                        "file_size": v.file_size,
                        "status": v.status,
                        "duration": v.duration,
                        "fps": v.fps,
                        "total_frames": v.total_frames,
                        "width": v.width,
                        "height": v.height,
                        "resolution": f"{v.width}x{v.height}" if v.width and v.height else None,
                        "error_message": v.error_message,
                        "created_at": v.created_at,
                        "updated_at": v.updated_at
                    }
                    for v in videos
                ]
                return total, results
        except Exception as e:
            print(f"[Storage Error] SQLite list_videos failed: {e}")
            return 0, []

    def delete_video(self, video_id: str, user_id: Optional[str] = None) -> bool:
        """
        Deletes a video, its physical file from disk, and all associated detected events.
        Validates ownership if user_id is provided.
        """
        video = self.get_video(video_id, user_id=user_id)
        if not video:
            return False

        # 1. Delete associated events & video from MongoDB
        db = get_mongo_db()
        if db is not None:
            try:
                db["events"].delete_many({"video_id": video_id})
                db["videos"].delete_one({"$or": [{"video_id": video_id}, {"id": video_id}]})
            except Exception as e:
                print(f"[Storage Error] Mongo delete_video failed: {e}")

        # 2. Delete from SQLite
        try:
            with SessionLocal() as sq_db:
                sq_db.query(Event).filter(Event.video_id == video_id).delete()
                sq_db.query(Video).filter(Video.id == video_id).delete()
                sq_db.commit()
        except Exception as e:
            print(f"[Storage Error] SQLite delete_video failed: {e}")

        # 3. Clean up physical file on disk if it exists
        file_path = video.get("file_path")
        if file_path and os.path.exists(file_path):
            try:
                os.remove(file_path)
            except Exception as e:
                print(f"[Storage Warning] Could not remove video file from disk: {e}")

        return True

    def is_evidence_owned_by_user(self, filename: str, user_id: str) -> bool:
        """
        Validates whether an evidence snapshot image is associated with an event or video owned by user_id.
        """
        clean_fn = os.path.basename(filename)
        db = get_mongo_db()
        if db is not None:
            try:
                ev = db["events"].find_one({
                    "user_id": user_id,
                    "evidence_snapshot": {"$regex": re.escape(clean_fn)}
                })
                if ev:
                    return True
                inc = db["live_incidents"].find_one({
                    "owner_id": user_id,
                    "evidence_snapshot": {"$regex": re.escape(clean_fn)}
                })
                if inc:
                    return True
                ev_any = db["events"].find_one({"evidence_snapshot": {"$regex": re.escape(clean_fn)}})
                if ev_any and ev_any.get("video_id"):
                    v = db["videos"].find_one({"$or": [{"video_id": ev_any["video_id"]}, {"id": ev_any["video_id"]}], "user_id": user_id})
                    if v:
                        return True
            except Exception as e:
                print(f"[Storage Error] Mongo is_evidence_owned_by_user failed: {e}")

        try:
            with SessionLocal() as sq_db:
                ev = sq_db.query(Event).filter(
                    Event.user_id == user_id,
                    Event.evidence_snapshot.like(f"%{clean_fn}%")
                ).first()
                if ev:
                    return True

                from src.api.live.models import LiveIncident
                inc = sq_db.query(LiveIncident).filter(
                    LiveIncident.owner_id == user_id,
                    LiveIncident.evidence_snapshot.like(f"%{clean_fn}%")
                ).first()
                if inc:
                    return True

                ev_any = sq_db.query(Event).filter(Event.evidence_snapshot.like(f"%{clean_fn}%")).first()
                if ev_any and ev_any.video_id:
                    v = sq_db.query(Video).filter(Video.id == ev_any.video_id, Video.user_id == user_id).first()
                    if v:
                        return True
        except Exception as e:
            print(f"[Storage Error] SQLite is_evidence_owned_by_user failed: {e}")

        return False

# Global singleton repository instance
storage = StorageRepository()

def get_storage() -> StorageRepository:
    """
    Dependency or accessor for the unified storage repository.
    """
    return storage
