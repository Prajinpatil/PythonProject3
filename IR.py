import cv2
import numpy as np
import torch

def ir_p(frame):
    # 1. Early Exit
    if frame is None:
        print("Error: Empty frame passed.")
        return None

    if len(frame.shape) == 3:
        frame = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    # 2. Center Cropping (FIXED: Safely get H and W)
    h, w = frame.shape[:2]
    minDim = min(h, w)
    start_x = (w - minDim) // 2
    start_y = (h - minDim) // 2
    croppedFrame = frame[start_y:start_y + minDim, start_x:start_x + minDim]
    # 3. Resize and Gaussian Blurring
    k_size = (5, 5)
    sigma = 0
    resizedFrame = cv2.resize(croppedFrame, (224,224))
    blurredFrame = cv2.GaussianBlur(resizedFrame, k_size, sigmaX=sigma)
    # 4. Normalize to a range of 0.0 to 1.0
    dst = np.zeros(blurredFrame.shape, dtype=np.float32)
    normalizedFrame = cv2.normalize(blurredFrame, dst, alpha=0, beta=1, norm_type=cv2.NORM_MINMAX, dtype=cv2.CV_32F)
    # 5. Channel Expansion
    # Since we guaranteed it's grayscale above, we can just expand the last axis safely
    finalFrame = np.expand_dims(normalizedFrame, axis=-1)
    # 6. Conversion to CNN tensor
    ChannellingFrame = np.transpose(finalFrame, (2, 0, 1))
    # 6. Conversion to CNN tensor
    # cnn_input = np.expand_dims(ChannellingFrame, axis=0)
    # Send the (1, 640, 640, 1) tensor back to the main loop!
    return ChannellingFrame
#final