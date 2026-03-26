import os
import cv2
import torch
from torch.utils.data import Dataset
from IR import ir_p


class IRDataset(Dataset):
    def __init__(self, root_dir, augment=True):
        self.root_dir = root_dir
        self.augment  = augment

        # Reads folder names as class labels
        self.classes      = sorted(os.listdir(root_dir))
        self.class_to_idx = {cls: idx for idx, cls in enumerate(self.classes)}

        # Build list of (image_path, label) pairs
        self.samples = []
        for cls in self.classes:
            cls_folder = os.path.join(root_dir, cls)
            if not os.path.isdir(cls_folder):
                continue
            for img_file in os.listdir(cls_folder):
                if img_file.lower().endswith((".png", ".jpg", ".jpeg")):
                    self.samples.append((
                        os.path.join(cls_folder, img_file),
                        self.class_to_idx[cls]
                    ))

        print(f"Dataset loaded: {len(self.samples)} images across {len(self.classes)} classes")
        print(f"Classes: {self.classes}")

    def __len__(self):
        return len(self.samples)

    def __getitem__(self, idx):
        img_path, label = self.samples[idx]

        # Read image and pass to your IR.py preprocessor
        frame     = cv2.imread(img_path)
        processed = ir_p(frame)

        # If image is corrupt/unreadable, return blank tensor
        if processed is None:
            tensor = torch.zeros(1, 224, 224)
        else:
            tensor = torch.from_numpy(processed).float()

        return tensor, label