import cv2
import numpy as np
import base64
from fastapi import FastAPI, File, UploadFile, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from ultralytics import YOLO
import os
from typing import List
import asyncio

app = FastAPI()

# 允许前端跨域请求
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# 加载模型（使用相对路径）
model_path = os.path.join(os.path.dirname(__file__), "models", "best.pt")
model = YOLO(model_path)

# 置信度阈值（只有大于此值的缺陷才计入统计）
CONFIDENCE_THRESHOLD = 0.3


def detect_single_image(image_bytes):
    """单张图片检测，返回缺陷信息和标注图base64"""
    nparr = np.frombuffer(image_bytes, np.uint8)
    img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
    results = model(img)

    boxes = results[0].boxes
    all_defects = []
    high_conf_defects = []

    if boxes is not None:
        for box in boxes:
            conf = float(box.conf[0])
            defect = {
                "class": results[0].names[int(box.cls[0])],
                "confidence": round(conf, 3),
                "bbox": [int(x) for x in box.xyxy[0].tolist()]
            }
            all_defects.append(defect)
            # 只统计高置信度的缺陷
            if conf > CONFIDENCE_THRESHOLD:
                high_conf_defects.append(defect)

    # 标注图：画所有检测框（包括低置信度）
    annotated = results[0].plot()
    _, buffer = cv2.imencode(".jpg", annotated)
    img_base64 = base64.b64encode(buffer).decode()

    return high_conf_defects, f"data:image/jpeg;base64,{img_base64}"


@app.post("/detect")
async def detect(file: UploadFile = File(...)):
    """单张图片检测接口"""
    contents = await file.read()
    defects, result_img = detect_single_image(contents)
    return {
        "defect_count": len(defects),
        "defects": defects,
        "result_image": result_img
    }


@app.post("/detect_batch")
async def detect_batch(files: List[UploadFile] = File(...)):
    """批量检测接口"""
    results = []
    for file in files:
        contents = await file.read()
        defects, result_img = detect_single_image(contents)
        results.append({
            "filename": file.filename,
            "defect_count": len(defects),
            "defects": defects,
            "result_image": result_img
        })
    return {"results": results}


@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket 摄像头检测（实时流）"""
    await websocket.accept()
    print("✅ WebSocket 连接成功")

    cap = None
    try:
        cap = cv2.VideoCapture(0)
        if not cap.isOpened():
            await websocket.send_json({"error": "无法打开摄像头"})
            await websocket.close()
            return

        print("📷 摄像头已开启")

        while True:
            ret, frame = cap.read()
            if not ret:
                break

            results = model(frame)
            annotated = results[0].plot()
            _, buffer = cv2.imencode('.jpg', annotated)
            img_base64 = base64.b64encode(buffer).decode()

            boxes = results[0].boxes
            high_conf_defects = []
            if boxes is not None:
                for box in boxes:
                    conf = float(box.conf[0])
                    if conf > CONFIDENCE_THRESHOLD:
                        high_conf_defects.append({
                            "class": results[0].names[int(box.cls[0])],
                            "confidence": round(conf, 3)
                        })

            await websocket.send_json({
                "image": f"data:image/jpeg;base64,{img_base64}",
                "defect_count": len(high_conf_defects),
                "defects": high_conf_defects
            })

            await asyncio.sleep(0.05)

    except WebSocketDisconnect:
        print("🔌 WebSocket 断开连接")
    except Exception as e:
        print(f"❌ 发生错误: {e}")
    finally:
        if cap is not None:
            cap.release()
            print("📷 摄像头已释放")


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)