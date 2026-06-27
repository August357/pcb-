import ultralytics
import cv2
import torch
import PyQt5

print("✅ ultralytics 版本:", ultralytics.__version__)
print("✅ OpenCV 版本:", cv2.__version__)
print("✅ PyTorch 版本:", torch.__version__)
print("✅ PyQt5 安装成功")

# 测试YOLO能否加载
from ultralytics import YOLO
model = YOLO('yolov8n.pt')  # 会自动下载预训练模型
print("✅ YOLOv8 模型加载成功")