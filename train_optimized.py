from ultralytics import YOLO

# 使用更大的模型（yolov8s比nano精度更高）
model = YOLO('yolov8s.pt')  # 如果没下载，会自动下载；但你有网的话可以现在下载

model.train(
    data='pcb_yolo_dataset/data.yaml',
    epochs=100,              # 增加到100轮
    imgsz=640,
    batch=8,
    device='cpu',
    workers=0,
    patience=20,             # 20轮不提升就停止
    # 增强数据增强
    mosaic=1.0,
    mixup=0.2,
    project='pcb_training',
    name='exp2'              # 新的实验名称
)