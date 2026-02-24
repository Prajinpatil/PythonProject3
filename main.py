
import cv2
import numpy as np

from RGB import rgb_p
from IR import ir_p
#trial
camera=cv2.VideoCapture(0)
if camera.isOpened():
    print("camera is opened")
    ret, frame = camera.read()

else:
    print("camera is not opened")
    exit(0)

if  ret and frame is not None:
    finalFrame=rgb_p(frame)

    # print("success, frame captured")
    # #resizing the frame to 640*640
    # h, w, _ = frame.shape
    # minDim = min(h, w)
    # start_x = (w - minDim) // 2
    # start_y = (h - minDim) // 2
    # croppedFrame = frame[start_y:start_y + minDim, start_x:start_x + minDim]
    #
    # #gaussian blurring
    # k_size = (5,5)
    # sigma = 0
    # resizedFrame = cv2.resize(croppedFrame, (640, 640))
    # blurredFrame = cv2.GaussianBlur(resizedFrame, k_size, sigmaX=sigma)
    #
    # # Normalize to a range of 0.0 to 1.0
    # dst = np.zeros(blurredFrame.shape)
    # normalizedFrame = cv2.normalize( blurredFrame, dst, alpha=0, beta=1, norm_type=cv2.NORM_MINMAX, dtype=cv2.CV_32F)
    #
    # print("original resolution:", frame.shape[0],"*",frame.shape[1])
    # print("modified resolution:",normalizedFrame.shape[0], "*",normalizedFrame.shape[1])
    #
    # #dim expansion
    # dims = frame.ndim
    # if dims==3:
    #    finalFrame=normalizedFrame
    # elif dims==2:
    #    finalFrame = np.expand_dims(normalizedFrame, axis=-1)



else:
    print("failed to capture frame")
    exit(0)

#Conversion to CNN tensor
# cnn_input = np.expand_dims(finalFrame, axis=0)
# print("Final Tensor Shape for CNN:", cnn_input.shape)

camera.release()
cv2.imshow('frame',finalFrame)
# # Assuming 'normalized_frame' is your result
# min_val = normalizedFrame.min()
# max_val = normalizedFrame.max()
#
# print(f"--- Normalization Check ---")
# print(f"Minimum Value: {min_val}")
# print(f"Maximum Value: {max_val}")

# cv2.imshow('frame',frame)
cv2.waitKey(0)

cv2.destroyAllWindows()




