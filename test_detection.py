from ultralytics import YOLO

# 加载训练好的最佳模型
model = YOLO('runs/detect/pcb_training/exp1-2/weights/best.pt')

# 检测整个文件夹
results = model('PCB_DATASET_VOC/VOCdevkit/VOC2007/JPEGImages/', save=True)

print("✅ 批量检测完成！")
print("结果保存在: runs/detect/predict/")