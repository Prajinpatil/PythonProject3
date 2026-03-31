**AI-Based Border Intrusion Detection System**

A real-time computer vision system for detecting intrusions using thermal (IR) imagery and deep learning.

Overview  
This project focuses on detecting intrusions using thermal images.  
A custom CNN model is trained to classify input frames into 7 classes:

1] Animal  
2] Bird  
3] Car  
4] Drone  
5] Human with weapon  
6] Human without weapon  
7] non intruder  

The system is designed to work in low-light and night conditions, where thermal imaging is more effective than RGB.  
The model is designed for real-time surveillance and can be integrated with web-based monitoring systems.

**Architecture:-**

IR Image  
   ↓  
Preprocessing (resize, normalize)  
   ↓  
CNN Model (PyTorch)  
   ↓  
Prediction (Intruder / Non-Intruder)

**Features:-**

* Custom CNN model for thermal image classification  
* Image preprocessing using OpenCV  
* Dataset preparation using FLIR thermal dataset  
* GPU-accelerated training using PyTorch  
* Modular inference pipeline for integration  

**Project Structure:-**

ir_model_multiclass.py  
ir_dataset_loader_multiclass.py  
train_ir_multiclass.py  
test_ir_multiclass.py  
validate_ir_multiclass.py  
IR.py  

**Installation:-**

pip install -r requirements.txt  

**Model Details:-**

* Input size: **224 × 224**  
* Output: prediction of the above mentioned class name with confidence percentage  
* Framework: PyTorch  

**Tech Stack:-**

* Python  
* PyTorch  
* OpenCV  
* NumPy  

Author:-  
Prajin Patil
