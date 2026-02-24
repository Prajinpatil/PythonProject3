import cv2
import numpy as np
import torch


def rgb_p(frame):

    # 1. Early Exit: If the frame is bad, stop immediately.
    if frame is None:
        print("Error: Empty frame passed.")
        return None

    # print("success, frame captured")

    # 2. Center Cropping
    h, w, _ = frame.shape
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
    # Tip: Added dtype=np.float32 to dst to perfectly match the cv2.CV_32F output
    dst = np.zeros(blurredFrame.shape, dtype=np.float32)
    normalizedFrame = cv2.normalize(blurredFrame, dst, alpha=0, beta=1, norm_type=cv2.NORM_MINMAX, dtype=cv2.CV_32F)

    # 5. Channel Expansion
    dims = frame.ndim
    if dims == 3:
        finalFrame = normalizedFrame
    elif dims == 2:
        finalFrame = np.expand_dims(normalizedFrame, axis=-1)
    ChannellingFrame = np.transpose(finalFrame, (2, 0, 1))
    # 6. Conversion to CNN tensor
    # cnn_input = np.expand_dims(ChannellingFrame, axis=0)

    # Send the tensor back to the main loop!
    return ChannellingFrame