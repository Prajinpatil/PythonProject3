import torch
import torch.nn as nn
import torchvision.transforms as transforms
from torch.utils.data import DataLoader
from ir_model_multiclass import IRCNN, CLASSES, NUM_CLASSES
from ir_dataset_loader_multiclass import IRDataset
from PIL import Image
import os

def test_folder(model,loader,device):
    """Tests entire folder and prints results."""
    model.eval()
    correct=0
    total=0

    class_correct={cls: 0 for cls in CLASSES}
    class_total={cls: 0 for cls in CLASSES}
    wrong_preds=[]

    with torch.no_grad():
        for ir,labels in loader:
            ir= ir.to(device)
            labels=labels.to(device)

            outputs= model(ir)
            probs=torch.softmax(outputs, dim=1)
            _, predicted=torch.max(outputs, 1)

            correct+=(predicted == labels).sum().item()
            total+= labels.size(0)

            for i in range(len(labels)):
                true_cls=CLASSES[labels[i].item()]
                pred_cls=CLASSES[predicted[i].item()]
                conf=probs[i][predicted[i]].item() * 100

                class_total[true_cls]+= 1
                if predicted[i]==labels[i]:
                    class_correct[true_cls] += 1
                else:
                    wrong_preds.append((true_cls, pred_cls, conf))

    accuracy=100*correct/total

    print(f"\n{'='*45}")
    print(f"  Test Accuracy: {accuracy:.2f}%")
    print(f"  Correct: {correct}/{total}")
    print(f"{'='*45}")

    print(f"\nPer-Class Accuracy:")
    print(f"{'-'*40}")
    for cls in CLASSES:
        if class_total[cls] > 0:
            cls_acc=100*class_correct[cls] / class_total[cls]
            print(f"{cls:<25} {cls_acc:.2f}%  ({class_correct[cls]}/{class_total[cls]})")

    print(f"\nWrong Predictions (sample):")
    print(f"{'-'*40}")
    for true_cls, pred_cls, conf in wrong_preds[:10]:   # show first 10 mistakes
        print(f"True: {true_cls:<22} Predicted: {pred_cls:<22} Conf: {conf:.1f}%")

    print(f"{'='*45}\n")
    return accuracy


def test_single_image(model, image_path, device):
    """Tests a single image and prints prediction."""
    transform = transforms.Compose([
        transforms.Grayscale(num_output_channels=1),
        transforms.Resize((224, 224)),
        transforms.ToTensor(),
        transforms.Normalize(mean=[0.5], std=[0.5])
    ])

    image=Image.open(image_path).convert("L")
    image=transform(image).unsqueeze(0).to(device)

    model.eval()
    with torch.no_grad():
        outputs=model(image)
        probs=torch.softmax(outputs, dim=1)
        conf,predicted = torch.max(probs, 1)
    label=CLASSES[predicted.item()]
    score=conf.item() * 100
    print(f"\n  Image: {os.path.basename(image_path)}")
    print(f"Prediction: {label}")
    print(f"Confidence: {score:.2f}%")
    print(f"\n  All class probabilities:")
    for cls, prob in zip(CLASSES, probs[0]):
        bar = '█' * int(prob.item() * 30)
        print(f"  {cls:<25} {prob.item()*100:5.2f}%  {bar}")
    return label, score
def main():
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    print(f"Using device: {device}")

    model=IRCNN(num_classes=NUM_CLASSES).to(device)
    checkpoint=torch.load("models/train4/ir_model_best4.pth", map_location=device)
    model.load_state_dict(checkpoint["model_state_dict"])
    print(f"Loaded model from epoch {checkpoint['epoch']}")

    test_dataset=IRDataset("ir_dataset_test2_test")     # ← your test folder
    test_loader=DataLoader(test_dataset, batch_size=16, shuffle=False, num_workers=2)
    test_folder(model, test_loader, device)

    # test_single_image(model, r"C:\Users\DELL\PycharmProjects\PythonProject3\dataset_collection\sample1.jpg", device)
if __name__=="__main__":
    main()
