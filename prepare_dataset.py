# 创建文件: prepare_dataset.py
import os
import shutil
from pathlib import Path
import xml.etree.ElementTree as ET
from sklearn.model_selection import train_test_split

# ========== 配置 ==========
VOC_ROOT = "PCB_DATASET_VOC/VOCdevkit/VOC2007"
OUTPUT_DIR = "pcb_yolo_dataset"  # 输出根目录
VAL_RATIO = 0.2  # 20% 的数据作为验证集
RANDOM_SEED = 42  # 固定随机种子，确保每次划分一致


# =========================

def convert_voc_to_yolo(xml_path, output_txt_path, class_mapping):
    """将单个VOC格式XML文件转换为YOLO格式TXT文件"""
    tree = ET.parse(xml_path)
    root = tree.getroot()

    size = root.find('size')
    img_w = int(size.find('width').text)
    img_h = int(size.find('height').text)

    yolo_boxes = []
    for obj in root.findall('object'):
        class_name = obj.find('name').text
        if class_name not in class_mapping:
            continue
        class_id = class_mapping[class_name]

        bndbox = obj.find('bndbox')
        xmin = int(bndbox.find('xmin').text)
        ymin = int(bndbox.find('ymin').text)
        xmax = int(bndbox.find('xmax').text)
        ymax = int(bndbox.find('ymax').text)

        # 归一化坐标
        center_x = (xmin + xmax) / 2.0 / img_w
        center_y = (ymin + ymax) / 2.0 / img_h
        width = (xmax - xmin) / img_w
        height = (ymax - ymin) / img_h

        yolo_boxes.append(f"{class_id} {center_x:.6f} {center_y:.6f} {width:.6f} {height:.6f}")

    with open(output_txt_path, 'w') as f:
        f.write('\n'.join(yolo_boxes))


def main():
    # 类别映射（北京大学PCB数据集的6种缺陷）
    class_mapping = {
        'missing_hole': 0,
        'mouse_bite': 1,
        'open_circuit': 2,
        'short': 3,
        'spur': 4,
        'spurious_copper': 5,
    }

    # 创建输出目录
    output_path = Path(OUTPUT_DIR)
    for split in ['train', 'val']:
        (output_path / 'images' / split).mkdir(parents=True, exist_ok=True)
        (output_path / 'labels' / split).mkdir(parents=True, exist_ok=True)

    # VOC数据集路径
    voc_images = Path(VOC_ROOT) / 'JPEGImages'
    voc_annotations = Path(VOC_ROOT) / 'Annotations'

    if not voc_images.exists() or not voc_annotations.exists():
        print(f"错误: 找不到 {voc_images} 或 {voc_annotations}")
        return

    # 获取所有图片文件（.jpg 或 .png）
    image_files = sorted(voc_images.glob('*.jpg'))
    print(f"找到 {len(image_files)} 张图片")

    # 划分训练集和验证集（按文件名）
    image_names = [f.stem for f in image_files]
    train_names, val_names = train_test_split(
        image_names,
        test_size=VAL_RATIO,
        random_state=RANDOM_SEED
    )

    print(f"训练集: {len(train_names)} 张")
    print(f"验证集: {len(val_names)} 张")

    # 处理训练集
    for name in train_names:
        # 复制图片
        src_img = voc_images / f"{name}.jpg"
        dst_img = output_path / 'images' / 'train' / f"{name}.jpg"
        shutil.copy(src_img, dst_img)

        # 转换并保存标注
        src_xml = voc_annotations / f"{name}.xml"
        dst_txt = output_path / 'labels' / 'train' / f"{name}.txt"
        convert_voc_to_yolo(str(src_xml), str(dst_txt), class_mapping)

    # 处理验证集
    for name in val_names:
        src_img = voc_images / f"{name}.jpg"
        dst_img = output_path / 'images' / 'val' / f"{name}.jpg"
        shutil.copy(src_img, dst_img)

        src_xml = voc_annotations / f"{name}.xml"
        dst_txt = output_path / 'labels' / 'val' / f"{name}.txt"
        convert_voc_to_yolo(str(src_xml), str(dst_txt), class_mapping)

    # 生成 data.yaml
    yaml_content = f"""
path: {os.path.abspath(OUTPUT_DIR)}
train: images/train
val: images/val

nc: 6
names: ['missing_hole', 'mouse_bite', 'open_circuit', 'short', 'spur', 'spurious_copper']
"""
    with open(OUTPUT_DIR + '/data.yaml', 'w') as f:
        f.write(yaml_content.strip())

    print(f"✅ 数据集准备完成！保存在 {OUTPUT_DIR}")
    print(f"   训练图片: {len(train_names)}")
    print(f"   验证图片: {len(val_names)}")
    print(f"   配置文件: {OUTPUT_DIR}/data.yaml")


if __name__ == '__main__':
    main()