import sys
import os
from PyQt5.QtWidgets import (QApplication, QMainWindow, QPushButton, QLabel,
                             QFileDialog, QVBoxLayout, QHBoxLayout, QWidget,
                             QProgressBar, QMessageBox)
from PyQt5.QtGui import QPixmap, QFont
from PyQt5.QtCore import Qt, QThread, pyqtSignal
from ultralytics import YOLO


class DetectionThread(QThread):
    """检测线程，避免界面卡顿"""
    finished = pyqtSignal(str)  # 检测完成信号
    progress = pyqtSignal(int)  # 进度信号

    def __init__(self, model_path, image_path):
        super().__init__()
        self.model_path = model_path
        self.image_path = image_path

    def run(self):
        model = YOLO(self.model_path)
        results = model(self.image_path, save=True)
        # 结果保存在 runs/detect/predict/
        self.finished.emit("runs/detect/predict/" + os.path.basename(self.image_path))


class PCBSDetectorGUI(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("PCB电路板缺陷检测系统")
        self.setGeometry(100, 100, 900, 700)

        # 加载模型
        self.model = YOLO('runs/detect/pcb_training/exp1-2/weights/best.pt')

        # 设置界面
        self.setup_ui()

    def setup_ui(self):
        # 中央部件
        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        # 主布局
        main_layout = QVBoxLayout(central_widget)

        # 标题
        title = QLabel("PCB电路板表面缺陷视觉检测系统")
        title.setFont(QFont("微软雅黑", 20, QFont.Bold))
        title.setAlignment(Qt.AlignCenter)
        main_layout.addWidget(title)

        # 按钮布局
        btn_layout = QHBoxLayout()

        # 选择图片按钮
        self.btn_select = QPushButton("📁 选择图片")
        self.btn_select.clicked.connect(self.select_image)
        btn_layout.addWidget(self.btn_select)

        # 开始检测按钮
        self.btn_detect = QPushButton("🔍 开始检测")
        self.btn_detect.clicked.connect(self.detect_image)
        self.btn_detect.setEnabled(False)
        btn_layout.addWidget(self.btn_detect)

        main_layout.addLayout(btn_layout)

        # 进度条
        self.progress = QProgressBar()
        self.progress.setVisible(False)
        main_layout.addWidget(self.progress)

        # 图片显示区域
        self.image_label = QLabel()
        self.image_label.setAlignment(Qt.AlignCenter)
        self.image_label.setStyleSheet("border: 2px solid gray; background-color: #f0f0f0;")
        self.image_label.setMinimumHeight(400)
        self.image_label.setText("请选择要检测的PCB图片")
        main_layout.addWidget(self.image_label)

        # 结果标签
        self.result_label = QLabel("检测结果将显示在这里")
        self.result_label.setAlignment(Qt.AlignCenter)
        self.result_label.setStyleSheet("font-size: 14px; color: green;")
        main_layout.addWidget(self.result_label)

        # 状态栏
        self.statusBar().showMessage("就绪 | 模型已加载")

        # 当前图片路径
        self.current_image_path = None

    def select_image(self):
        """选择图片文件"""
        file_path, _ = QFileDialog.getOpenFileName(
            self, "选择PCB图片", "",
            "图片文件 (*.png *.jpg *.jpeg *.bmp);;所有文件 (*)"
        )
        if file_path:
            self.current_image_path = file_path
            # 显示原图
            pixmap = QPixmap(file_path)
            scaled_pixmap = pixmap.scaled(
                self.image_label.width(), 400,
                Qt.KeepAspectRatio, Qt.SmoothTransformation
            )
            self.image_label.setPixmap(scaled_pixmap)
            self.btn_detect.setEnabled(True)
            self.result_label.setText("已选择图片，点击「开始检测」")
            self.statusBar().showMessage(f"已加载: {os.path.basename(file_path)}")

    def detect_image(self):
        """执行检测"""
        if not self.current_image_path:
            return

        # 禁用按钮，显示进度
        self.btn_select.setEnabled(False)
        self.btn_detect.setEnabled(False)
        self.progress.setVisible(True)
        self.progress.setRange(0, 0)  # 不确定进度
        self.result_label.setText("🔄 检测中，请稍候...")
        self.statusBar().showMessage("正在检测缺陷...")

        # 执行检测
        try:
            results = self.model(self.current_image_path)

            # 保存结果
            for r in results:
                result_path = f"temp_result_{os.path.basename(self.current_image_path)}"
                r.save(result_path)

                # 显示结果
                pixmap = QPixmap(result_path)
                scaled_pixmap = pixmap.scaled(
                    self.image_label.width(), 400,
                    Qt.KeepAspectRatio, Qt.SmoothTransformation
                )
                self.image_label.setPixmap(scaled_pixmap)

            # 统计检测结果
            boxes = results[0].boxes
            if boxes is not None:
                num_defects = len(boxes)
                # 统计各类缺陷
                defect_counts = {}
                for box in boxes:
                    cls_id = int(box.cls[0])
                    cls_name = results[0].names[cls_id]
                    defect_counts[cls_name] = defect_counts.get(cls_name, 0) + 1

                result_text = f"✅ 检测完成！共发现 {num_defects} 处缺陷\n"
                for name, count in defect_counts.items():
                    result_text += f"  • {name}: {count}处\n"
                self.result_label.setText(result_text)
                self.statusBar().showMessage(f"检测完成，发现 {num_defects} 处缺陷")
            else:
                self.result_label.setText("✅ 检测完成！未发现缺陷")
                self.statusBar().showMessage("检测完成，未发现缺陷")

        except Exception as e:
            QMessageBox.critical(self, "错误", f"检测失败：{str(e)}")
            self.result_label.setText("❌ 检测失败，请重试")
            self.statusBar().showMessage("检测失败")

        # 恢复按钮
        self.btn_select.setEnabled(True)
        self.btn_detect.setEnabled(True)
        self.progress.setVisible(False)


def main():
    app = QApplication(sys.argv)
    window = PCBSDetectorGUI()
    window.show()
    sys.exit(app.exec_())


if __name__ == '__main__':
    main()