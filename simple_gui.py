import cv2
import os
import tkinter as tk
from tkinter import filedialog, Button, Label, Frame, Text
from PIL import Image, ImageTk
from ultralytics import YOLO


class PCBSimpleGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("PCB缺陷检测系统")
        self.root.geometry("900x700")

        # 加载模型
        self.model = YOLO('runs/detect/pcb_training/exp2/weights/best.pt')

        # 界面组件
        self.frame = Frame(root)
        self.frame.pack(pady=10)

        self.btn_load = Button(self.frame, text="📁 选择PCB图片", command=self.load_image,
                               font=("微软雅黑", 12), bg="#4CAF50", fg="white", padx=20, pady=5)
        self.btn_load.pack(side=tk.LEFT, padx=5)

        self.btn_detect = Button(self.frame, text="🔍 检测缺陷", command=self.detect_image,
                                 font=("微软雅黑", 12), bg="#2196F3", fg="white", padx=20, pady=5)
        self.btn_detect.pack(side=tk.LEFT, padx=5)
        self.btn_detect.config(state=tk.DISABLED)

        # 图片显示区域
        self.label = Label(root, text="请选择PCB图片", font=("微软雅黑", 10),
                           bg="#f0f0f0", relief="solid")
        self.label.pack(pady=10, padx=10, expand=True, fill=tk.BOTH)

        # 结果文本框
        self.result_text = Text(root, height=6, font=("微软雅黑", 10))
        self.result_text.pack(pady=5, padx=10, fill=tk.X)

        self.current_image_path = None

    def load_image(self):
        file_path = filedialog.askopenfilename(
            title="选择PCB图片",
            filetypes=[("图片文件", "*.jpg *.jpeg *.png *.bmp"), ("所有文件", "*.*")]
        )
        if file_path:
            self.current_image_path = file_path
            # 显示图片
            img = Image.open(file_path)
            # 调整大小适应窗口
            display_size = (600, 450)
            img.thumbnail(display_size)
            photo = ImageTk.PhotoImage(img)
            self.label.config(image=photo, text="")
            self.label.image = photo
            self.btn_detect.config(state=tk.NORMAL)
            self.result_text.delete(1.0, tk.END)
            self.result_text.insert(1.0, f"✅ 已加载: {os.path.basename(file_path)}\n点击「检测缺陷」开始识别")

    def detect_image(self):
        if not self.current_image_path:
            return

        self.btn_detect.config(state=tk.DISABLED)
        self.btn_load.config(state=tk.DISABLED)
        self.result_text.delete(1.0, tk.END)
        self.result_text.insert(1.0, "🔄 检测中，请稍候...")
        self.root.update()

        try:
            # 执行检测
            results = self.model(self.current_image_path)

            # 读取图片用于画框
            img = cv2.imread(self.current_image_path)
            img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)

            # 统计缺陷
            defect_counts = {}
            boxes = results[0].boxes

            if boxes is not None and len(boxes) > 0:
                for box in boxes:
                    # 获取边界框坐标
                    x1, y1, x2, y2 = box.xyxy[0].tolist()
                    x1, y1, x2, y2 = int(x1), int(y1), int(x2), int(y2)
                    conf = float(box.conf[0])
                    cls_id = int(box.cls[0])
                    cls_name = results[0].names[cls_id]

                    # 统计
                    defect_counts[cls_name] = defect_counts.get(cls_name, 0) + 1

                    # 画框
                    cv2.rectangle(img, (x1, y1), (x2, y2), (0, 255, 0), 2)
                    label = f"{cls_name} {conf:.2f}"
                    cv2.putText(img, label, (x1, y1 - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)

                # 显示结果窗口
                img_bgr = cv2.cvtColor(img, cv2.COLOR_RGB2BGR)
                cv2.imshow("PCB缺陷检测结果 - 按任意键关闭", img_bgr)
                cv2.waitKey(0)
                cv2.destroyAllWindows()

                # 更新文本结果
                result_text = f"✅ 检测完成！共发现 {len(boxes)} 处缺陷\n"
                for name, count in defect_counts.items():
                    result_text += f"  • {name}: {count}处\n"
                self.result_text.delete(1.0, tk.END)
                self.result_text.insert(1.0, result_text)
            else:
                self.result_text.delete(1.0, tk.END)
                self.result_text.insert(1.0, "✅ 检测完成！未发现缺陷")

        except Exception as e:
            self.result_text.delete(1.0, tk.END)
            self.result_text.insert(1.0, f"❌ 检测失败: {str(e)}")

        self.btn_detect.config(state=tk.NORMAL)
        self.btn_load.config(state=tk.NORMAL)


if __name__ == "__main__":
    root = tk.Tk()
    app = PCBSimpleGUI(root)
    root.mainloop()