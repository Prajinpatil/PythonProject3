import torch
from IR_model import IRCNN

model = IRCNN()

ir = torch.randn(1, 1, 224, 224)

output = model(ir)

print(output.shape)