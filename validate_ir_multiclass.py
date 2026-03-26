import torch
import torch.nn as nn
from torch.utils.data import DataLoader
from ir_model_multiclass import IRCNN, CLASSES, NUM_CLASSES
from ir_dataset_loader_multiclass import IRDataset


def validate(model, loader, criterion, device):
    model.eval()
    total_loss=0
    correct=0
    total=0

    # Per class tracking
    class_correct={cls: 0 for cls in CLASSES}
    class_total={cls: 0 for cls in CLASSES}

    with torch.no_grad():
        for ir,labels in loader:
            ir=ir.to(device)
            labels=labels.to(device)

            outputs=model(ir)
            loss=criterion(outputs, labels)
            total_loss+=loss.item()

            _, predicted=torch.max(outputs, 1)
            correct+=(predicted==labels).sum().item()
            total+=labels.size(0)

            # Per class accuracy
            for i in range(len(labels)):
                true_label=CLASSES[labels[i].item()]
                class_total[true_label]+= 1
                if predicted[i]==labels[i]:
                    class_correct[true_label]+=1

    avg_loss=total_loss/len(loader)
    accuracy=100 * correct/total

    print(f"\n{'='*45}")
    print(f"Validation Loss: {avg_loss:.4f}")
    print(f"Overall Accuracy: {accuracy:.2f}%")
    print(f"{'='*45}")
    print(f"\nPer-Class Accuracy:")
    print(f"{'-'*40}")
    for cls in CLASSES:
        if class_total[cls] > 0:
            cls_acc=100* class_correct[cls] / class_total[cls]
            print(f"{cls:<25} {cls_acc:.2f}%  ({class_correct[cls]}/{class_total[cls]})")
    print(f"{'='*45}\n")

    return avg_loss,accuracy


def main():
    device=torch.device("cuda" if torch.cuda.is_available() else "cpu")
    print(f"Using device:{device}")

    # ── Load model ────────────────────────────────────────────────
    model      = IRCNN(num_classes=NUM_CLASSES).to(device)
    checkpoint = torch.load("models/train4/ir_model_best4.pth", map_location=device)
    model.load_state_dict(checkpoint["model_state_dict"])
    print(f"Loaded model from epoch {checkpoint['epoch']}")

    # ── Validation dataset ────────────────────────────────────────
    val_dataset = IRDataset("ir_dataset_test2_validate")       # ← your validation folder
    val_loader  = DataLoader(val_dataset, batch_size=16, shuffle=False, num_workers=2)

    criterion = nn.CrossEntropyLoss()
    validate(model, val_loader, criterion, device)


if __name__ == "__main__":
    main()