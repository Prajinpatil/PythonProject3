import torch
from model import DualStreamCNN

model = DualStreamCNN()

rgb = torch.randn(1, 3, 224, 224)

ir = torch.randn(1, 1, 224, 224)

output = model(rgb, ir)

print(output.shape)