from ultralytics import YOLO

# 加载预训练模型
model = YOLO('yolov8n.pt')  # nano版本，速度快；想更准可以用 yolov8s.pt

# 开始训练
model.train(
    data='pcb_yolo_dataset/data.yaml',  # 数据集配置
    epochs=50,                           # 训练50轮
    imgsz=640,                           # 输入图片尺寸
    batch=8,                             # 批次大小（CPU用8，GPU可以16）
    device='cpu',                        # 用CPU训练（你的torch是CPU版）
    workers=0,                           # Windows下多线程容易报错，设为0
    patience=10,                         # 10轮精度不提升就早停
    save=True,                           # 保存训练好的模型
    project='pcb_training',              # 训练结果保存文件夹
    name='exp1'                          # 本次实验名称
)

print("✅ 训练完成！模型保存在 pcb_training/exp1/weights/best.pt")