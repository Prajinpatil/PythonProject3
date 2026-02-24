import torch
import torch.nn as nn
import torch.optim as optim
from model import DualStreamCNN

# Step 1: Device configuration
device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

print("Using device:", device)

# Step 2: Initialize model
model = DualStreamCNN().to(device)

# Step 3: Loss function
criterion = nn.CrossEntropyLoss()

# Step 4: Optimizer
optimizer = optim.Adam(model.parameters(), lr=0.001)

# Step 5: Dummy training loop (replace later with real dataset)

epochs = 10

for epoch in range(epochs):

    # Dummy batch for testing pipeline
    rgb = torch.randn(4, 3, 224, 224).to(device)
    ir = torch.randn(4, 1, 224, 224).to(device)
    labels = torch.randint(0, 2, (4,)).to(device)

    # Forward pass
    outputs = model(rgb, ir)

    loss = criterion(outputs, labels)

    # Backward pass
    optimizer.zero_grad()
    loss.backward()
    optimizer.step()

    print(f"Epoch [{epoch+1}/{epochs}], Loss: {loss.item():.4f}")

# Step 6: Save model
torch.save(model.state_dict(), "dual_stream_model.pth")

print("Model saved successfully.")