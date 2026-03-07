import torch
import torch.nn as nn
import torch.optim as optim
from IR_model import IRCNN
from torch.utils.data import DataLoader
from ir_dataset_loader import IRDataset
dataset = IRDataset("ir_dataset")

loader = DataLoader(dataset, batch_size=8, shuffle=True)
# loader = DataLoader(
#     dataset,
#     batch_size=16,
#     shuffle=True,
#     num_workers=4,
#     pin_memory=True
# )


device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

model = IRCNN().to(device)

criterion = nn.CrossEntropyLoss()

optimizer = optim.Adam(model.parameters(), lr=0.001)

epochs = 10

for epoch in range(epochs):

    for ir, labels in loader:

        ir = ir.to(device)
        labels = labels.to(device)

        outputs = model(ir)

        loss = criterion(outputs, labels)

        optimizer.zero_grad()
        loss.backward()
        optimizer.step()

    print(f"Epoch {epoch+1}, Loss: {loss.item():.4f}")


torch.save(model.state_dict(), "models/ir_model.pth")

print("IR model saved.")