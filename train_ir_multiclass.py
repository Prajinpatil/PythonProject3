import torch
import torch.nn as nn
import torch.optim as optim
from ir_model_multiclass import IRCNN, CLASSES, NUM_CLASSES
from torch.utils.data import DataLoader, random_split
from ir_dataset_loader_multiclass import IRDataset
import os

def evaluate(model,loader,criterion,device):
    """Runs model on validation set, returns avg loss and accuracy."""
    model.eval()
    total_loss= 0
    correct=0
    total=0

    with torch.no_grad():
        for ir,labels in loader:
            ir=ir.to(device)
            labels=labels.to(device)

            outputs=model(ir)
            loss=criterion(outputs,labels)
            total_loss+=loss.item()

            _, predicted=torch.max(outputs, 1)
            correct+=(predicted == labels).sum().item()
            total+=labels.size(0)

    avg_loss=total_loss/len(loader)
    accuracy=100*correct/total
    return avg_loss,accuracy


def main():
    print(f"Training{NUM_CLASSES}-class model: {CLASSES}\n")


    full_dataset=IRDataset("ir_dataset_test2")
    # 80% train, 20% validation split
    val_size=int(0.2 * len(full_dataset))
    train_size=len(full_dataset) - val_size
    train_dataset,val_dataset=random_split(full_dataset,[train_size,val_size])

    train_loader=DataLoader(
        train_dataset,
        batch_size=16,
        shuffle=True,
        num_workers=2,
        pin_memory=True
    )
    val_loader=DataLoader(
        val_dataset,
        batch_size=16,
        shuffle=False,
        num_workers=2,
        pin_memory=True
    )


    device=torch.device("cuda" if torch.cuda.is_available() else "cpu")
    print(f"Using device:{device}")

    model=IRCNN(num_classes=NUM_CLASSES).to(device)

    # ── Loss, Optimizer
    # weight balancing
    criterion=nn.CrossEntropyLoss()
    optimizer=optim.Adam(model.parameters(), lr=0.001)
    scheduler=torch.optim.lr_scheduler.ReduceLROnPlateau(optimizer, patience=2)

    #Training
    epochs = 20    # more epochs for 7 classes vs 2
    best_val_loss=float("inf")
    os.makedirs("models",exist_ok=True)

    for epoch in range(epochs):
        model.train()
        epoch_loss=0

        for ir, labels in train_loader:
            ir=ir.to(device)
            labels=labels.to(device)

            optimizer.zero_grad()
            outputs=model(ir)
            loss=criterion(outputs, labels)
            loss.backward()
            optimizer.step()

            epoch_loss+=loss.item()

        avg_train_loss=epoch_loss / len(train_loader)

        # Validation
        val_loss,val_accuracy=evaluate(model, val_loader, criterion, device)

        current_lr=optimizer.param_groups[0]['lr']
        print(f"Epoch{epoch+1}/{epochs} | "
              f"Train Loss:{avg_train_loss:.4f} | "
              f"Val Loss:{val_loss:.4f} | "
              f"Val Acc:{val_accuracy:.2f}% | "
              f"LR:{current_lr:.6f}")

        scheduler.step(val_loss)   # scheduler watches val loss, not train loss

        # Save best model based on validation loss
        if val_loss<best_val_loss:
            best_val_loss=val_loss
            torch.save({
                "epoch":epoch+ 1,
                "model_state_dict": model.state_dict(),
                "optimizer_state_dict": optimizer.state_dict(),
                "val_loss": best_val_loss,
                "val_accuracy": val_accuracy,
                "classes": CLASSES
            }, "models/train4/ir_model_best4.pth")
            print(f"  → Best model saved (val loss: {best_val_loss:.4f}, acc: {val_accuracy:.2f}%)")

    # Save final model
    torch.save({
        "epoch": epochs,
        "model_state_dict": model.state_dict(),
        "optimizer_state_dict": optimizer.state_dict(),
        "val_loss": val_loss,
        "classes": CLASSES
    }, "models/train4/ir_model_final4.pth")
    print("\nTraining complete. Final model saved.")


if __name__ == "__main__":
    main()