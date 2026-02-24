import torch
import torch.nn as nn
import torch.nn.functional as F


class RGBBranch(nn.Module):
    def __init__(self):
        super(RGBBranch, self).__init__()

        self.conv1 = nn.Conv2d(3, 32, kernel_size=3, padding=1)
        self.pool = nn.MaxPool2d(2, 2)

        self.conv2 = nn.Conv2d(32, 64, kernel_size=3, padding=1)

        self.conv3 = nn.Conv2d(64, 128, kernel_size=3, padding=1)

        self.fc = nn.Linear(128 * 28 * 28, 128)

    def forward(self, x):

        x = self.pool(F.relu(self.conv1(x)))   # 224 → 112

        x = self.pool(F.relu(self.conv2(x)))   # 112 → 56

        x = self.pool(F.relu(self.conv3(x)))   # 56 → 28

        x = x.view(x.size(0), -1)

        x = F.relu(self.fc(x))

        return x


class IRBranch(nn.Module):
    def __init__(self):
        super(IRBranch, self).__init__()

        self.conv1 = nn.Conv2d(1, 32, kernel_size=3, padding=1)

        self.pool = nn.MaxPool2d(2, 2)

        self.conv2 = nn.Conv2d(32, 64, kernel_size=3, padding=1)

        self.conv3 = nn.Conv2d(64, 128, kernel_size=3, padding=1)

        self.fc = nn.Linear(128 * 28 * 28, 128)

    def forward(self, x):

        x = self.pool(F.relu(self.conv1(x)))

        x = self.pool(F.relu(self.conv2(x)))

        x = self.pool(F.relu(self.conv3(x)))

        x = x.view(x.size(0), -1)

        x = F.relu(self.fc(x))

        return x


class DualStreamCNN(nn.Module):

    def __init__(self):

        super(DualStreamCNN, self).__init__()

        self.rgb_branch = RGBBranch()

        self.ir_branch = IRBranch()

        self.fc1 = nn.Linear(256, 64)

        self.fc2 = nn.Linear(64, 2)


    def forward(self, rgb, ir):

        rgb_features = self.rgb_branch(rgb)

        ir_features = self.ir_branch(ir)

        combined = torch.cat((rgb_features, ir_features), dim=1)

        x = F.relu(self.fc1(combined))

        output = self.fc2(x)

        return output