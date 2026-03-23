import torch
import cv2
from IR_model import IRCNN
from IR import ir_p

# Device
device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

# Load model
model = IRCNN()
# model.load_state_dict(torch.load("models/ir_model.pth"))
model.load_state_dict(torch.load("models/ir_model_best.pth", weights_only=True))
model.to(device)
model.eval()

# Load test image (change path)
# img_path = "ir_dataset/intruder/your_image.jpg"
img_path = "ir_dataset_test1/intruder/000157 (2).jpg"

frame = cv2.imread(img_path)

tensor = ir_p(frame)
tensor = torch.from_numpy(tensor).float()

# Add batch dimension
tensor = tensor.unsqueeze(0).to(device)

# Prediction
with torch.no_grad():
    output = model(tensor)
    pred = torch.argmax(output, dim=1).item()

# Result
if pred == 1:
    print("Intruder detected")
else:
    print("No intruder")