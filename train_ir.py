import torch
import torch.nn as nn
import torch.optim as optim
from IR_model import IRCNN
from torch.utils.data import DataLoader
from ir_dataset_loader import IRDataset
import os

def main():
    dataset = IRDataset("ir_dataset_test1")
    loader = DataLoader(
        dataset,
        batch_size=16,
        shuffle=True,
        num_workers=2,
        pin_memory=True
    )

    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    model = IRCNN().to(device)
    model.train()

    criterion = nn.CrossEntropyLoss()
    optimizer = optim.Adam(model.parameters(), lr=0.001)
    scheduler = torch.optim.lr_scheduler.ReduceLROnPlateau(optimizer, patience=2, verbose=True)

    epochs = 10
    best_loss = float("inf")
    os.makedirs("models", exist_ok=True)

    for epoch in range(epochs):
        model.train()
        epoch_loss = 0

        for ir, labels in loader:
            ir = ir.to(device)
            labels = labels.to(device)

            optimizer.zero_grad()        # ← fixed: moved before forward pass
            outputs = model(ir)
            loss = criterion(outputs, labels)
            loss.backward()
            optimizer.step()

            epoch_loss += loss.item()

        avg_loss = epoch_loss / len(loader)
        print(f"Epoch {epoch+1}/{epochs}, Loss: {avg_loss:.4f}")

        scheduler.step(avg_loss)

        # Save best model checkpoint
        if avg_loss < best_loss:
            best_loss = avg_loss
            torch.save(model.state_dict(), "models/ir_model_best.pth")
            print(f"  → Best model saved (loss: {best_loss:.4f})")

    # Save final model
    torch.save(model.state_dict(), "models/ir_model_2.pth")
    print("IR model saved.")

if __name__ == "__main__":
    main()