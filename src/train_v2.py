import os
import argparse
import time
import json
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import torch
import torch.nn as nn
from tqdm import tqdm
from torch.amp import autocast, GradScaler
from sklearn.metrics import accuracy_score, f1_score

from src.config import (
    CLASSES, NUM_CLASSES,
    BATCH_SIZE, GRAD_ACCUM_STEPS, LEARNING_RATE,
    WEIGHT_DECAY, NUM_EPOCHS, PATIENCE,
    DEVICE, USE_AMP, RANDOM_SEED
)
from src.dataset_v2 import set_seed, get_dataloaders_v2, compute_class_weights_v2, SPLITS_V2_DIR
from src.model import build_model

CHECKPOINTS_V2_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "checkpoints", "v2")
os.makedirs(CHECKPOINTS_V2_DIR, exist_ok=True)


def train_one_epoch(model, dataloader, criterion, optimizer, scaler, device, epoch_idx=1, total_epochs=1, grad_accum_steps=GRAD_ACCUM_STEPS, debug=False):
    model.train()
    running_loss = 0.0
    all_preds = []
    all_targets = []
    
    optimizer.zero_grad()
    pbar = tqdm(dataloader, desc=f"Epoch {epoch_idx:02d}/{total_epochs:02d} [Train]", unit="batch", leave=False)
    
    for step, (inputs, targets) in enumerate(pbar):
        inputs = inputs.to(device)
        targets = targets.to(device)
        
        with autocast('cuda', enabled=USE_AMP and device.type == 'cuda'):
            outputs = model(inputs)
            loss = criterion(outputs, targets)
            loss_scaled = loss / grad_accum_steps
            
        if scaler and device.type == 'cuda':
            scaler.scale(loss_scaled).backward()
            if (step + 1) % grad_accum_steps == 0 or (step + 1) == len(dataloader):
                scaler.unscale_(optimizer)
                torch.nn.utils.clip_grad_norm_(model.parameters(), max_norm=1.0)
                scaler.step(optimizer)
                scaler.update()
                optimizer.zero_grad()
        else:
            loss_scaled.backward()
            if (step + 1) % grad_accum_steps == 0 or (step + 1) == len(dataloader):
                torch.nn.utils.clip_grad_norm_(model.parameters(), max_norm=1.0)
                optimizer.step()
                optimizer.zero_grad()
                
        running_loss += loss.item() * inputs.size(0)
        preds = torch.argmax(outputs, dim=1).detach().cpu().numpy()
        all_preds.extend(preds)
        all_targets.extend(targets.cpu().numpy())
        
        current_loss = running_loss / len(all_targets)
        current_acc = accuracy_score(all_targets, all_preds)
        pbar.set_postfix({
            'loss': f"{current_loss:.3f}",
            'acc': f"{current_acc:.3f}"
        })
        
        if debug and step >= 3:
            break
            
    total_samples = len(all_targets)
    epoch_loss = running_loss / total_samples
    epoch_acc = accuracy_score(all_targets, all_preds)
    epoch_f1 = f1_score(all_targets, all_preds, average='macro', zero_division=0)
    
    return epoch_loss, epoch_acc, epoch_f1


def validate(model, dataloader, criterion, device, epoch_idx=1, total_epochs=1, debug=False):
    model.eval()
    running_loss = 0.0
    all_preds = []
    all_targets = []
    
    pbar = tqdm(dataloader, desc=f"Epoch {epoch_idx:02d}/{total_epochs:02d} [Val]  ", unit="batch", leave=False)
    
    with torch.no_grad():
        for step, (inputs, targets) in enumerate(pbar):
            inputs = inputs.to(device)
            targets = targets.to(device)
            
            with autocast('cuda', enabled=USE_AMP and device.type == 'cuda'):
                outputs = model(inputs)
                loss = criterion(outputs, targets)
                
            running_loss += loss.item() * inputs.size(0)
            preds = torch.argmax(outputs, dim=1).cpu().numpy()
            all_preds.extend(preds)
            all_targets.extend(targets.cpu().numpy())
            
            current_loss = running_loss / len(all_targets)
            current_acc = accuracy_score(all_targets, all_preds)
            pbar.set_postfix({
                'loss': f"{current_loss:.3f}",
                'acc': f"{current_acc:.3f}"
            })
            
            if debug and step >= 3:
                break
                
    total_samples = len(all_targets)
    val_loss = running_loss / total_samples
    val_acc = accuracy_score(all_targets, all_preds)
    val_f1 = f1_score(all_targets, all_preds, average='macro', zero_division=0)
    
    return val_loss, val_acc, val_f1


def plot_training_history(history, save_path):
    epochs = range(1, len(history['train_loss']) + 1)
    
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 5))
    
    # Loss plot
    ax1.plot(epochs, history['train_loss'], 'b-o', label='Train Loss')
    ax1.plot(epochs, history['val_loss'], 'r-s', label='Val Loss')
    ax1.set_title('Cross-Entropy Loss (v2)')
    ax1.set_xlabel('Epoch')
    ax1.set_ylabel('Loss')
    ax1.legend()
    ax1.grid(True, linestyle='--', alpha=0.6)
    
    # Metrics plot
    ax2.plot(epochs, history['val_acc'], 'g-^', label='Val Accuracy')
    ax2.plot(epochs, history['val_f1'], 'm-d', label='Val Macro F1')
    ax2.set_title('Validation Performance (v2)')
    ax2.set_xlabel('Epoch')
    ax2.set_ylabel('Score')
    ax2.legend()
    ax2.grid(True, linestyle='--', alpha=0.6)
    
    plt.tight_layout()
    plt.savefig(save_path, dpi=200)
    plt.close()


def train(args):
    set_seed(RANDOM_SEED)
    print("=" * 65)
    print("      VisionIQ Phase 1 (v2) - Retraining R(2+1)D-18 Pipeline     ")
    print("=" * 65)
    print(f"Device: {DEVICE}")
    if DEVICE.type == 'cuda':
        print(f"GPU: {torch.cuda.get_device_name(0)}")
        print(f"Initial VRAM Allocated: {torch.cuda.memory_allocated(0)/(1024**2):.1f} MB")
        
    print(f"Loading v2 data with batch size {args.batch_size}...")
    train_loader, val_loader, _, train_df = get_dataloaders_v2(batch_size=args.batch_size)
    
    # Class weights to address imbalance
    class_weights = compute_class_weights_v2(train_df).to(DEVICE)
    print("Class weights:", {CLASSES[i]: round(class_weights[i].item(), 2) for i in range(NUM_CLASSES)})
    criterion = nn.CrossEntropyLoss(weight=class_weights)
    
    print(f"Initializing model: {args.model} (pretrained=True, freeze_early={args.freeze_early})...")
    model = build_model(model_name=args.model, num_classes=NUM_CLASSES, pretrained=True, freeze_early_layers=args.freeze_early)
    model = model.to(DEVICE)
    
    optimizer = torch.optim.AdamW(model.parameters(), lr=args.lr, weight_decay=WEIGHT_DECAY)
    scheduler = torch.optim.lr_scheduler.CosineAnnealingLR(optimizer, T_max=args.epochs, eta_min=1e-6)
    scaler = GradScaler('cuda', enabled=USE_AMP and DEVICE.type == 'cuda')
    
    best_val_f1 = -1.0
    patience_counter = 0
    history = {'train_loss': [], 'val_loss': [], 'val_acc': [], 'val_f1': []}
    
    log_csv_path = os.path.join(CHECKPOINTS_V2_DIR, "training_log.csv")
    log_rows = []
    
    start_time = time.time()
    print(f"Starting training for {args.epochs} epochs (Early stopping patience: {args.patience})...\n")
    
    for epoch in range(1, args.epochs + 1):
        epoch_start = time.time()
        
        train_loss, train_acc, train_f1 = train_one_epoch(
            model, train_loader, criterion, optimizer, scaler, DEVICE,
            epoch_idx=epoch, total_epochs=args.epochs, grad_accum_steps=args.grad_accum, debug=args.debug
        )
        
        val_loss, val_acc, val_f1 = validate(
            model, val_loader, criterion, DEVICE,
            epoch_idx=epoch, total_epochs=args.epochs, debug=args.debug
        )
        
        scheduler.step()
        current_lr = optimizer.param_groups[0]['lr']
        epoch_time = time.time() - epoch_start
        
        history['train_loss'].append(train_loss)
        history['val_loss'].append(val_loss)
        history['val_acc'].append(val_acc)
        history['val_f1'].append(val_f1)
        
        log_rows.append({
            'epoch': epoch,
            'train_loss': train_loss,
            'train_acc': train_acc,
            'train_f1': train_f1,
            'val_loss': val_loss,
            'val_acc': val_acc,
            'val_f1': val_f1,
            'lr': current_lr
        })
        pd.DataFrame(log_rows).to_csv(log_csv_path, index=False)
        plot_training_history(history, os.path.join(CHECKPOINTS_V2_DIR, "loss_curve.png"))
        
        is_best = val_f1 > best_val_f1
        if is_best:
            best_val_f1 = val_f1
            patience_counter = 0
            best_ckpt_path = os.path.join(CHECKPOINTS_V2_DIR, "best_model.pth")
            torch.save({
                'epoch': epoch,
                'model_name': args.model,
                'model_state_dict': model.state_dict(),
                'optimizer_state_dict': optimizer.state_dict(),
                'val_f1': val_f1,
                'val_acc': val_acc,
                'classes': CLASSES,
                'num_classes': NUM_CLASSES
            }, best_ckpt_path)
            status_tag = f"[BEST SAVED: F1={val_f1:.4f}]"
        else:
            patience_counter += 1
            status_tag = f"[Patience: {patience_counter}/{args.patience}]"
            
        print(f"Epoch {epoch:02d}/{args.epochs:02d} ({epoch_time:.1f}s) | "
              f"Train Loss: {train_loss:.4f}, Acc: {train_acc*100:.1f}%, F1: {train_f1:.3f} | "
              f"Val Loss: {val_loss:.4f}, Acc: {val_acc*100:.1f}%, F1: {val_f1:.3f} | {status_tag}")
              
        # Always save last checkpoint
        torch.save({
            'epoch': epoch,
            'model_name': args.model,
            'model_state_dict': model.state_dict(),
            'val_f1': val_f1,
            'val_acc': val_acc
        }, os.path.join(CHECKPOINTS_V2_DIR, "last_model.pth"))
        
        if patience_counter >= args.patience:
            print(f"\nEarly stopping triggered after {epoch} epochs (Best Val Macro F1: {best_val_f1:.4f})")
            break
            
    total_time = time.time() - start_time
    print(f"\nTraining completed in {total_time/60:.1f} minutes.")
    print(f"Best checkpoint saved at: {os.path.join(CHECKPOINTS_V2_DIR, 'best_model.pth')} (Best Val F1: {best_val_f1:.4f})")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Retrain R(2+1)D-18 Model on Updated DCSASS Dataset (v2)")
    parser.add_argument("--model", type=str, default="r2plus1d_18")
    parser.add_argument("--epochs", type=int, default=10)
    parser.add_argument("--batch_size", type=int, default=4)
    parser.add_argument("--grad_accum", type=int, default=2)
    parser.add_argument("--lr", type=float, default=1e-4)
    parser.add_argument("--patience", type=int, default=4)
    parser.add_argument("--freeze_early", action="store_true", help="Freeze stem and early layers of backbone")
    parser.add_argument("--debug", action="store_true", help="Run 3 batches per epoch for sanity checking")
    
    args = parser.parse_args()
    train(args)
