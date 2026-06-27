# PCB 缺陷检测系统

基于 **YOLOv8** 的 PCB（印刷电路板）表面缺陷自动检测系统，支持 6 类典型缺陷的实时定位与分类，并提供命令行、桌面 GUI 与 Web 端多种使用方式。

## 功能特性

- **多类缺陷识别**：支持缺孔、鼠咬、开路、短路、毛刺、多余铜箔 6 种缺陷
- **多种检测方式**：单张检测、批量检测、摄像头实时检测
- **完整 Web 系统**：Vue3 前端 + FastAPI 后端，含登录、历史记录、对比分析、管理后台
- **桌面 GUI**：提供 PyQt5 与 Tkinter 两种轻量界面
- **训练流水线**：VOC 数据集自动转换、YOLO 格式划分、模型训练与优化

## 缺陷类别

| 类别 | 英文标识 | 说明 |
|------|----------|------|
| 缺孔 | `missing_hole` | 应存在但未钻孔的焊盘 |
| 鼠咬 | `mouse_bite` | 铜箔边缘不规则缺口 |
| 开路 | `open_circuit` | 导线断裂 |
| 短路 | `short` | 不应连接的导体间短接 |
| 毛刺 | `spur` | 多余铜箔突起 |
| 多余铜箔 | `spurious_copper` | 非设计区域的铜残留 |

## 项目结构

```
.
├── pcb_inspection_system/       # Web 检测系统
│   ├── backend/                 # FastAPI 后端
│   │   ├── main.py              # API 与 WebSocket 服务
│   │   ├── requirements.txt
│   │   └── models/              # 放置 best.pt（需自行训练）
│   └── frontend/                # Vue3 + Element Plus 前端
│       └── src/views/           # 单张/批量/摄像头/历史/对比等页面
├── pcb_yolo_dataset/            # YOLO 数据集（需自行准备）
│   └── data.yaml                # 数据集配置文件
├── prepare_dataset.py           # VOC → YOLO 格式转换与划分
├── convert_voc_to_yolo.py       # VOC 标注转换工具
├── train.py                     # 基础训练（YOLOv8n）
├── train_optimized.py           # 优化训练（YOLOv8s + 数据增强）
├── test_detection.py            # 批量检测脚本
├── gui.py                       # PyQt5 桌面 GUI
├── simple_gui.py                # Tkinter 桌面 GUI
└── test_env.py                  # 环境依赖检测
```

## 技术栈

| 模块 | 技术 |
|------|------|
| 目标检测 | YOLOv8（Ultralytics） |
| 图像处理 | OpenCV |
| Web 后端 | FastAPI + Uvicorn |
| Web 前端 | Vue 3 + Vite + Element Plus + ECharts |
| 桌面 GUI | PyQt5 / Tkinter |
| 数据集 | 北京大学 PCB 缺陷数据集（VOC 格式） |

## 环境要求

- Python 3.8+
- Node.js 20+（Web 前端）
- 可选：CUDA GPU（加速训练与推理）

### Python 依赖

**训练与检测：**

```bash
pip install ultralytics opencv-python torch scikit-learn
```

**Web 后端：**

```bash
pip install -r pcb_inspection_system/backend/requirements.txt
```

**桌面 GUI（可选）：**

```bash
pip install PyQt5 pillow
```

验证环境：

```bash
python test_env.py
```

## 快速开始

### 1. 准备数据集

下载 [北京大学 PCB 缺陷数据集](https://github.com/Charmve/Surface-Defect-Detection) 并解压至 `PCB_DATASET_VOC/`，然后运行：

```bash
python prepare_dataset.py
```

脚本会将 VOC 格式转换为 YOLO 格式，并按 8:2 划分训练集与验证集，输出至 `pcb_yolo_dataset/`。

### 2. 训练模型

**基础训练（速度快，适合快速验证）：**

```bash
python train.py
```

**优化训练（精度更高，推荐）：**

```bash
python train_optimized.py
```

训练完成后，最佳权重位于 `pcb_training/exp*/weights/best.pt`。

### 3. 部署模型

将训练好的 `best.pt` 复制到 Web 后端模型目录：

```bash
cp pcb_training/exp2/weights/best.pt pcb_inspection_system/backend/models/best.pt
```

> 本仓库不含模型权重文件，需自行训练或放置已训练模型。

### 4. 启动 Web 系统

**后端：**

```bash
cd pcb_inspection_system/backend
python main.py
```

服务默认运行在 `http://localhost:8000`。

**前端：**

```bash
cd pcb_inspection_system/frontend
npm install
npm run dev
```

浏览器访问前端开发地址（默认 `http://localhost:5173`）。

### 5. 桌面 GUI（可选）

```bash
# PyQt5 版本
python gui.py

# Tkinter 版本（更轻量）
python simple_gui.py
```

> 使用前请修改 GUI 脚本中的模型路径，指向你的 `best.pt`。

## API 接口

| 方法 | 路径 | 说明 |
|------|------|------|
| POST | `/detect` | 单张图片检测，返回缺陷列表与标注图 |
| POST | `/detect_batch` | 批量图片检测 |
| WS | `/ws` | WebSocket 摄像头实时检测 |

**单张检测示例：**

```bash
curl -X POST http://localhost:8000/detect \
  -F "file=@your_pcb_image.jpg"
```

**响应字段：**

- `defect_count`：高置信度缺陷数量（阈值 0.3）
- `defects`：缺陷详情（类别、置信度、边界框）
- `result_image`：标注结果图（Base64）

## Web 前端页面

| 路由 | 功能 |
|------|------|
| `/` | 单张图片上传检测 |
| `/batch` | 批量图片检测 |
| `/camera` | 摄像头实时检测 |
| `/history` | 检测历史记录 |
| `/compare` | 检测结果对比 |
| `/admin` | 管理后台 |
| `/login` | 用户登录 |

## 批量检测（命令行）

```bash
python test_detection.py
```

检测结果保存至 `runs/detect/predict/`。

## 注意事项

- Windows 下训练建议设置 `workers=0`，避免多进程报错
- CPU 训练时 `batch` 建议设为 8；GPU 可适当增大
- 摄像头实时检测需连接可用摄像头设备
- 数据集与模型文件体积较大，未纳入版本控制，请按上述步骤自行准备

## 作者

[August357](https://github.com/August357)
