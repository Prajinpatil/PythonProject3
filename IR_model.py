import torch
import torch.nn as nn
import torch.nn.functional as F


class IRCNN(nn.Module):

    def __init__(self):

        super(IRCNN, self).__init__()

        # Input: (1, 224, 224)

        self.conv1 = nn.Conv2d(1, 32, kernel_size=3, padding=1)
        self.pool = nn.MaxPool2d(2, 2)

        self.conv2 = nn.Conv2d(32, 64, kernel_size=3, padding=1)

        self.conv3 = nn.Conv2d(64, 128, kernel_size=3, padding=1)

        # after 3 pool layers: 224 → 112 → 56 → 28
        self.fc1 = nn.Linear(128 * 28 * 28, 128)

        self.fc2 = nn.Linear(128, 2)


    def forward(self, x):

        x = self.pool(F.relu(self.conv1(x)))

        x = self.pool(F.relu(self.conv2(x)))

        x = self.pool(F.relu(self.conv3(x)))

        x = x.view(x.size(0), -1)

        x = F.relu(self.fc1(x))

        output = self.fc2(x)

        return output