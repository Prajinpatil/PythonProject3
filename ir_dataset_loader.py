import os
import cv2
import torch
from torch.utils.data import Dataset
from IR import ir_p


class IRDataset(Dataset):

    def __init__(self, root_dir):

        self.samples = []
        self.labels = []

        intruder_dir = os.path.join(root_dir, "intruder")
        non_dir = os.path.join(root_dir, "non_intruder")

        for img in os.listdir(intruder_dir):
            self.samples.append(os.path.join(intruder_dir, img))
            self.labels.append(1)

        for img in os.listdir(non_dir):
            self.samples.append(os.path.join(non_dir, img))
            self.labels.append(0)

    def __len__(self):
        return len(self.samples)

    def __getitem__(self, idx):

        img_path = self.samples[idx]

        frame = cv2.imread(img_path)

        tensor = ir_p(frame)

        #tensor = torch.from_numpy(tensor).float()
        tensor = torch.tensor(tensor, dtype=torch.float32)

        # simple augmentation
        # if torch.rand(1) < 0.5:
        #     tensor = torch.flip(tensor, [2])

        label = torch.tensor(self.labels[idx])

        return tensor, label