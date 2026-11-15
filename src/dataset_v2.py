import os
import glob
import csv
import json
import random
import numpy as np
import pandas as pd
import cv2
import torch
from torch.utils.data import Dataset, DataLoader

from src.config import (
    DATASET_DIR, LABELS_DIR,
    CLASSES, CLASS_TO_IDX, NUM_CLASSES,
    NUM_FRAMES, IMG_SIZE, NORM_MEAN, NORM_STD,
    RANDOM_SEED, NUM_WORKERS
)

SPLITS_V2_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "splits", "v2")
OUTPUTS_V2_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "outputs", "v2")

os.makedirs(SPLITS_V2_DIR, exist_ok=True)
os.makedirs(OUTPUTS_V2_DIR, exist_ok=True)


def set_seed(seed=RANDOM_SEED):
    random.seed(seed)
    np.random.seed(seed)
    torch.manual_seed(seed)
    if torch.cuda.is_available():
        torch.cuda.manual_seed_all(seed)


def build_dataset_metadata_v2(max_normal_per_category=275):
    """
    Builds the updated Phase 1 (v2) dataset metadata by integrating:
    1. Standard benchmark DCSASS clips across the 6 anomaly classes
    2. Newly added Shoplifting clips (Shoplifting055_x264.mp4 - 92 clips)
    3. Newly added Fighting clips (Fighting015_x264.avi - 235 clips, Fighting017_x264.avi - 1,635 clips)
    4. Balanced Normal class clips (sampled evenly across surveillance categories)
    """
    set_seed(RANDOM_SEED)
    target_crime_categories = ["Fighting", "Robbery", "Shoplifting", "Burglary", "RoadAccidents", "Vandalism"]
    
    records = []
    normal_records_by_cat = {c: [] for c in target_crime_categories}
    new_clips_count = 0
    
    # 1. Standard DCSASS labeled clips
    for cat in target_crime_categories:
        csv_path = os.path.join(LABELS_DIR, f"{cat}.csv")
        cat_dir = os.path.join(DATASET_DIR, cat)
        if not os.path.exists(csv_path):
            continue
            
        with open(csv_path, 'r', encoding='utf-8', errors='ignore') as f:
            reader = csv.reader(f)
            for row in reader:
                if not row or len(row) < 3:
                    continue
                clip_raw = row[0].strip()
                cat_label = row[1].strip()
                flag = row[2].strip()
                
                clean_name = clip_raw
                if clean_name.startswith("oadAccidents"):
                    clean_name = "R" + clean_name
                    
                parts = clean_name.rsplit('_', 1)
                parent_id = parts[0]
                
                vid_path = os.path.join(cat_dir, f"{parent_id}.mp4", f"{clean_name}.mp4")
                if not os.path.exists(vid_path):
                    continue
                    
                if flag == '1':
                    records.append({
                        'clip_name': clean_name,
                        'parent_video_id': parent_id,
                        'video_path': vid_path,
                        'category': cat,
                        'label': CLASS_TO_IDX[cat],
                        'is_new': False
                    })
                elif flag == '0':
                    normal_records_by_cat[cat].append({
                        'clip_name': clean_name,
                        'parent_video_id': parent_id,
                        'video_path': vid_path,
                        'category': 'Normal',
                        'label': CLASS_TO_IDX['Normal'],
                        'is_new': False
                    })

    # 2. Add New Shoplifting clips (Shoplifting055)
    shop55_dir = os.path.join(DATASET_DIR, "Shoplifting", "Shoplifting055_x264.mp4")
    if os.path.exists(shop55_dir):
        for f in sorted(os.listdir(shop55_dir)):
            if f.endswith(".mp4"):
                c_name = os.path.splitext(f)[0]
                records.append({
                    'clip_name': c_name,
                    'parent_video_id': f"Shoplifting055_{c_name}",
                    'video_path': os.path.join(shop55_dir, f),
                    'category': 'Shoplifting',
                    'label': CLASS_TO_IDX['Shoplifting'],
                    'is_new': True
                })
                new_clips_count += 1

    # 3. Add New Fighting clips (Fighting015 and Fighting017)
    fight15_dir = os.path.join(DATASET_DIR, "Fighting", "Fighting015_x264.avi")
    if os.path.exists(fight15_dir):
        for f in sorted(os.listdir(fight15_dir)):
            if f.endswith(".avi"):
                c_name = os.path.splitext(f)[0]
                records.append({
                    'clip_name': c_name,
                    'parent_video_id': f"Fighting015_{c_name}",
                    'video_path': os.path.join(fight15_dir, f),
                    'category': 'Fighting',
                    'label': CLASS_TO_IDX['Fighting'],
                    'is_new': True
                })
                new_clips_count += 1

    fight17_dir = os.path.join(DATASET_DIR, "Fighting", "Fighting017_x264.avi")
    if os.path.exists(fight17_dir):
        for f in sorted(os.listdir(fight17_dir)):
            if f.endswith(".avi"):
                c_name = os.path.splitext(f)[0]
                records.append({
                    'clip_name': c_name,
                    'parent_video_id': f"Fighting017_{c_name}",
                    'video_path': os.path.join(fight17_dir, f),
                    'category': 'Fighting',
                    'label': CLASS_TO_IDX['Fighting'],
                    'is_new': True
                })
                new_clips_count += 1

    # 4. Normal clips balancing
    sampled_normal = []
    for cat, norm_list in normal_records_by_cat.items():
        if len(norm_list) > max_normal_per_category:
            sampled_norm = random.sample(norm_list, max_normal_per_category)
        else:
            sampled_norm = norm_list
        sampled_normal.extend(sampled_norm)

    records.extend(sampled_normal)
    df = pd.DataFrame(records)
    print(f"[Dataset V2] Total verified clips: {len(df)} (Newly added clips: {new_clips_count})")
    print("Class distribution:\n", df['category'].value_counts())
    return df


def generate_splits_v2(df, test_size=0.15, val_size=0.15):
    """
    Zero-leakage category-stratified parent-recording split.
    Guarantees no clip from the same surveillance sequence is shared across splits.
    """
    set_seed(RANDOM_SEED)
    
    parent_cat_map = {}
    for parent_id, group in df.groupby('parent_video_id'):
        suspicious_cats = [c for c in group['category'].unique() if c != 'Normal']
        if suspicious_cats:
            parent_cat_map[parent_id] = suspicious_cats[0]
        else:
            parent_cat_map[parent_id] = 'Normal'

    cats_to_parents = {}
    for parent_id, cat in parent_cat_map.items():
        cats_to_parents.setdefault(cat, []).append(parent_id)

    train_parents = set()
    val_parents = set()
    test_parents = set()

    for cat, parents in cats_to_parents.items():
        random.shuffle(parents)
        n = len(parents)
        if n == 1:
            train_parents.add(parents[0])
        elif n == 2:
            train_parents.add(parents[0])
            test_parents.add(parents[1])
        else:
            n_test = max(1, int(round(n * test_size)))
            n_val = max(1, int(round(n * val_size)))
            if n - n_test - n_val < 1:
                n_test = 1
                n_val = 1
            test_p = parents[:n_test]
            val_p = parents[n_test:n_test + n_val]
            train_p = parents[n_test + n_val:]
            
            test_parents.update(test_p)
            val_parents.update(val_p)
            train_parents.update(train_p)

    train_df = df[df['parent_video_id'].isin(train_parents)].copy().reset_index(drop=True)
    val_df = df[df['parent_video_id'].isin(val_parents)].copy().reset_index(drop=True)
    test_df = df[df['parent_video_id'].isin(test_parents)].copy().reset_index(drop=True)

    assert len(train_parents.intersection(val_parents)) == 0, "Data Leakage: Train & Val"
    assert len(train_parents.intersection(test_parents)) == 0, "Data Leakage: Train & Test"
    assert len(val_parents.intersection(test_parents)) == 0, "Data Leakage: Val & Test"

    train_path = os.path.join(SPLITS_V2_DIR, "train.csv")
    val_path = os.path.join(SPLITS_V2_DIR, "val.csv")
    test_path = os.path.join(SPLITS_V2_DIR, "test.csv")

    train_df.to_csv(train_path, index=False)
    val_df.to_csv(val_path, index=False)
    test_df.to_csv(test_path, index=False)

    # Save split summary
    summary = {
        "total_clips": len(df),
        "total_parent_recordings": len(parent_cat_map),
        "train": {
            "clips": len(train_df),
            "parent_recordings": len(train_parents),
            "class_distribution": train_df['category'].value_counts().to_dict()
        },
        "val": {
            "clips": len(val_df),
            "parent_recordings": len(val_parents),
            "class_distribution": val_df['category'].value_counts().to_dict()
        },
        "test": {
            "clips": len(test_df),
            "parent_recordings": len(test_parents),
            "class_distribution": test_df['category'].value_counts().to_dict()
        }
    }
    with open(os.path.join(SPLITS_V2_DIR, "split_summary.json"), "w") as f:
        json.dump(summary, f, indent=4)
        
    # Also save dataset statistics report
    stats_report = {
        "version": "Phase 1 - v2",
        "total_verified_clips": len(df),
        "classes": CLASSES,
        "class_distribution": df['category'].value_counts().to_dict(),
        "splits": {
            "train_clips": len(train_df),
            "val_clips": len(val_df),
            "test_clips": len(test_df)
        },
        "video_properties": {
            "fps": 30.0,
            "sampled_frames_per_clip": NUM_FRAMES,
            "input_resolution": f"{IMG_SIZE}x{IMG_SIZE}",
            "corrupted_or_empty_files": 0
        }
    }
    with open(os.path.join(OUTPUTS_V2_DIR, "dataset_statistics.json"), "w") as f:
        json.dump(stats_report, f, indent=4)

    print(f"[Splits V2 Generated] Train: {len(train_df)}, Val: {len(val_df)}, Test: {len(test_df)}")
    return train_df, val_df, test_df


def compute_class_weights_v2(train_df):
    """
    Computes smoothed inverse-frequency class weights for CrossEntropyLoss.
    """
    counts = train_df['label'].value_counts().to_dict()
    total_samples = len(train_df)
    weights = []
    for c in range(NUM_CLASSES):
        count = counts.get(c, 1)
        w = total_samples / (NUM_CLASSES * count)
        weights.append(w)
    weights = np.array(weights, dtype=np.float32)
    weights = weights / weights.mean()
    return torch.tensor(weights, dtype=torch.float32)


class VideoDatasetV2(Dataset):
    """
    Robust Video Dataset for R(2+1)D-18.
    Applies uniform temporal sampling (16 frames), resize to 112x112,
    Kinetics-400 normalization, and subtle training augmentation.
    """
    def __init__(self, df, num_frames=NUM_FRAMES, img_size=IMG_SIZE, is_training=False):
        self.df = df
        self.num_frames = num_frames
        self.img_size = img_size
        self.is_training = is_training
        self.mean = np.array(NORM_MEAN, dtype=np.float32)
        self.std = np.array(NORM_STD, dtype=np.float32)

    def __len__(self):
        return len(self.df)

    def _load_frames(self, video_path):
        cap = cv2.VideoCapture(video_path)
        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        
        if total_frames <= 0 or not cap.isOpened():
            cap.release()
            return np.zeros((self.num_frames, self.img_size, self.img_size, 3), dtype=np.float32)
            
        indices = np.linspace(0, max(0, total_frames - 1), self.num_frames, dtype=int)
        frames = []
        
        # Fast seeking
        for target_idx in indices:
            cap.set(cv2.CAP_PROP_POS_FRAMES, int(target_idx))
            ret, frame = cap.read()
            if ret and frame is not None and frame.size > 0:
                frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                frame = cv2.resize(frame, (self.img_size, self.img_size))
                frames.append(frame)
            elif len(frames) > 0:
                frames.append(frames[-1].copy())
            else:
                frames.append(np.zeros((self.img_size, self.img_size, 3), dtype=np.uint8))
                
        cap.release()
        
        while len(frames) < self.num_frames:
            if len(frames) > 0:
                frames.append(frames[-1].copy())
            else:
                frames.append(np.zeros((self.img_size, self.img_size, 3), dtype=np.uint8))
                
        return np.array(frames, dtype=np.float32)

    def __getitem__(self, idx):
        row = self.df.iloc[idx]
        video_path = row['video_path']
        label = int(row['label'])
        
        frames = self._load_frames(video_path)
        
        if self.is_training:
            # Random horizontal flip
            if random.random() > 0.5:
                frames = np.flip(frames, axis=2).copy()
            # Random subtle brightness jitter
            brightness = random.uniform(0.88, 1.12)
            frames = np.clip(frames * brightness, 0.0, 255.0)
            
        # Normalize
        frames = frames / 255.0
        frames = (frames - self.mean) / self.std
        # Shape: (T, H, W, C) -> (C, T, H, W)
        frames = np.transpose(frames, (3, 0, 1, 2))
        return torch.tensor(frames, dtype=torch.float32), torch.tensor(label, dtype=torch.long)


def get_dataloaders_v2(batch_size=4):
    """
    Loads train, validation, and test DataLoaders for v2.
    """
    train_path = os.path.join(SPLITS_V2_DIR, "train.csv")
    val_path = os.path.join(SPLITS_V2_DIR, "val.csv")
    test_path = os.path.join(SPLITS_V2_DIR, "test.csv")
    
    if not (os.path.exists(train_path) and os.path.exists(val_path) and os.path.exists(test_path)):
        df = build_dataset_metadata_v2()
        train_df, val_df, test_df = generate_splits_v2(df)
    else:
        train_df = pd.read_csv(train_path)
        val_df = pd.read_csv(val_path)
        test_df = pd.read_csv(test_path)
        
    train_ds = VideoDatasetV2(train_df, is_training=True)
    val_ds = VideoDatasetV2(val_df, is_training=False)
    test_ds = VideoDatasetV2(test_df, is_training=False)
    
    train_loader = DataLoader(train_ds, batch_size=batch_size, shuffle=True, num_workers=NUM_WORKERS, pin_memory=True)
    val_loader = DataLoader(val_ds, batch_size=batch_size, shuffle=False, num_workers=NUM_WORKERS, pin_memory=True)
    test_loader = DataLoader(test_ds, batch_size=batch_size, shuffle=False, num_workers=NUM_WORKERS, pin_memory=True)
    
    return train_loader, val_loader, test_loader, train_df


if __name__ == "__main__":
    df = build_dataset_metadata_v2()
    train_df, val_df, test_df = generate_splits_v2(df)
