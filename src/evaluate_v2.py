import os
import json
import argparse
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import torch
from tqdm import tqdm
from torch.amp import autocast
from sklearn.metrics import classification_report, confusion_matrix, accuracy_score, f1_score

from src.config import CLASSES, DEVICE, USE_AMP, NUM_CLASSES
from src.dataset_v2 import get_dataloaders_v2, SPLITS_V2_DIR, OUTPUTS_V2_DIR
from src.model import build_model

CHECKPOINTS_V2_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "checkpoints", "v2")


def plot_confusion_matrix(cm, class_names, save_path, title="Normalized Confusion Matrix - VisionIQ Surveillance (v2)"):
    cm_normalized = cm.astype('float') / (cm.sum(axis=1)[:, np.newaxis] + 1e-7)
    
    fig, ax = plt.subplots(figsize=(9, 8))
    im = ax.imshow(cm_normalized, interpolation='nearest', cmap=plt.cm.Blues)
    ax.figure.colorbar(im, ax=ax, fraction=0.046, pad=0.04)
    
    ax.set(
        xticks=np.arange(cm.shape[1]),
        yticks=np.arange(cm.shape[0]),
        xticklabels=class_names,
        yticklabels=class_names,
        title=title,
        ylabel="True Activity Label",
        xlabel="Predicted Activity Label"
    )
    plt.setp(ax.get_xticklabels(), rotation=45, ha="right", rotation_mode="anchor")
    
    thresh = cm_normalized.max() / 2.0
    for i in range(cm.shape[0]):
        for j in range(cm.shape[1]):
            val_pct = cm_normalized[i, j] * 100
            raw_cnt = cm[i, j]
            ax.text(j, i, f"{raw_cnt}\n({val_pct:.1f}%)",
                    ha="center", va="center",
                    color="white" if cm_normalized[i, j] > thresh else "black",
                    fontsize=8)
            
    fig.tight_layout()
    plt.savefig(save_path, dpi=250)
    plt.close()


def generate_comparison_report(v2_report, v2_acc, v2_macro_f1, v2_weighted_f1, save_path):
    v1_report_path = os.path.join(os.path.dirname(OUTPUTS_V2_DIR), "evaluation_report.json")
    v1_data = None
    if os.path.exists(v1_report_path):
        try:
            with open(v1_report_path, "r") as f:
                v1_data = json.load(f)
        except Exception:
            pass

    comparison = {
        "overall_metrics": {
            "v1": {
                "accuracy": v1_data.get("accuracy", 0.3814) if v1_data else 0.3814,
                "macro_f1": v1_data.get("macro avg", {}).get("f1-score", 0.2696) if v1_data else 0.2696,
                "weighted_f1": v1_data.get("weighted avg", {}).get("f1-score", 0.3568) if v1_data else 0.3568,
                "test_clips": v1_data.get("macro avg", {}).get("support", 797) if v1_data else 797
            },
            "v2": {
                "accuracy": v2_acc,
                "macro_f1": v2_macro_f1,
                "weighted_f1": v2_weighted_f1,
                "test_clips": int(v2_report.get("macro avg", {}).get("support", 0))
            },
            "delta": {
                "accuracy_change": round(v2_acc - (v1_data.get("accuracy", 0.3814) if v1_data else 0.3814), 4),
                "macro_f1_change": round(v2_macro_f1 - (v1_data.get("macro avg", {}).get("f1-score", 0.2696) if v1_data else 0.2696), 4)
            }
        },
        "per_class_comparison": {}
    }

    for c in CLASSES:
        v1_c = v1_data.get(c, {}) if v1_data else {}
        v2_c = v2_report.get(c, {})
        comparison["per_class_comparison"][c] = {
            "v1_precision": v1_c.get("precision", 0.0),
            "v1_recall": v1_c.get("recall", 0.0),
            "v1_f1": v1_c.get("f1-score", 0.0),
            "v1_support": v1_c.get("support", 0),
            "v2_precision": v2_c.get("precision", 0.0),
            "v2_recall": v2_c.get("recall", 0.0),
            "v2_f1": v2_c.get("f1-score", 0.0),
            "v2_support": v2_c.get("support", 0),
            "f1_improvement": round(v2_c.get("f1-score", 0.0) - v1_c.get("f1-score", 0.0), 4)
        }

    with open(save_path, "w") as f:
        json.dump(comparison, f, indent=4)
    print(f"Saved side-by-side comparison report to: {save_path}")
    return comparison


def evaluate(checkpoint_path=None, batch_size=4):
    if checkpoint_path is None:
        checkpoint_path = os.path.join(CHECKPOINTS_V2_DIR, "best_model.pth")
        
    if not os.path.exists(checkpoint_path):
        raise FileNotFoundError(f"Checkpoint not found at: {checkpoint_path}")
        
    print(f"Loading checkpoint from: {checkpoint_path}")
    checkpoint = torch.load(checkpoint_path, map_location=DEVICE, weights_only=False)
    model_name = checkpoint.get('model_name', 'r2plus1d_18')
    
    model = build_model(model_name=model_name, num_classes=NUM_CLASSES, pretrained=False)
    model.load_state_dict(checkpoint['model_state_dict'])
    model = model.to(DEVICE)
    model.eval()
    
    print("Loading test split DataLoader (v2)...")
    _, _, test_loader, _ = get_dataloaders_v2(batch_size=batch_size)
    
    all_preds = []
    all_targets = []
    all_probs = []
    
    print(f"Running evaluation on {len(test_loader.dataset)} independent test clips...")
    with torch.no_grad():
        for inputs, targets in tqdm(test_loader, desc="[Evaluating Test Set]"):
            inputs = inputs.to(DEVICE)
            with autocast('cuda', enabled=USE_AMP and DEVICE.type == 'cuda'):
                outputs = model(inputs)
                probs = torch.softmax(outputs, dim=1)
                
            preds = torch.argmax(probs, dim=1).cpu().numpy()
            all_preds.extend(preds)
            all_targets.extend(targets.numpy())
            all_probs.extend(probs.cpu().numpy())
            
    all_preds = np.array(all_preds)
    all_targets = np.array(all_targets)
    
    acc = accuracy_score(all_targets, all_preds)
    macro_f1 = f1_score(all_targets, all_preds, average='macro', zero_division=0)
    weighted_f1 = f1_score(all_targets, all_preds, average='weighted', zero_division=0)
    
    print("\n" + "="*55)
    print("        UPDATED TEST SET EVALUATION RESULTS (v2)        ")
    print("="*55)
    print(f"Overall Accuracy : {acc*100:.2f}%")
    print(f"Macro F1-Score   : {macro_f1:.4f}")
    print(f"Weighted F1-Score: {weighted_f1:.4f}")
    print("="*55)
    
    report_dict = classification_report(
        all_targets, all_preds,
        target_names=CLASSES,
        output_dict=True,
        zero_division=0
    )
    report_str = classification_report(
        all_targets, all_preds,
        target_names=CLASSES,
        zero_division=0
    )
    print(report_str)
    
    # Save Report to JSON
    report_path = os.path.join(OUTPUTS_V2_DIR, "evaluation_report.json")
    with open(report_path, 'w') as f:
        json.dump(report_dict, f, indent=4)
    print(f"Saved classification metrics report to: {report_path}")
    
    # Confusion Matrix
    cm = confusion_matrix(all_targets, all_preds, labels=range(NUM_CLASSES))
    cm_plot_path = os.path.join(OUTPUTS_V2_DIR, "confusion_matrix.png")
    plot_confusion_matrix(cm, CLASSES, cm_plot_path)
    print(f"Saved confusion matrix plot to: {cm_plot_path}")
    
    # Save Comparison Report
    comp_path = os.path.join(OUTPUTS_V2_DIR, "model_comparison.json")
    generate_comparison_report(report_dict, acc, macro_f1, weighted_f1, comp_path)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Evaluate Trained Model on Test Split (v2)")
    parser.add_argument("--checkpoint", type=str, default=os.path.join(CHECKPOINTS_V2_DIR, "best_model.pth"))
    parser.add_argument("--batch_size", type=int, default=4)
    args = parser.parse_args()
    evaluate(args.checkpoint, args.batch_size)
