import os
import xml.etree.ElementTree as ET
from pathlib import Path
import shutil

# ========== 修改这里的路径 ==========
VOC_ROOT = "PCB_DATASET_VOC/VOCdevkit/VOC2007"  # 修正后的路径
OUTPUT_DIR = "pcb_yolo_dataset"  # 输出YOLO格式的文件夹


# ===================================

def convert_voc_to_yolo(xml_path, output_txt_path, class_mapping):
    tree = ET.parse(xml_path)
    root = tree.getroot()

    # 获取图像尺寸
    size = root.find('size')
    img_w = int(size.find('width').text)
    img_h = int(size.find('height').text)

    yolo_boxes = []
    for obj in root.findall('object'):
        class_name = obj.find('name').text
        if class_name not in class_mapping:
            print(f"警告: 未找到类别 {class_name}")
            continue
        class_id = class_mapping[class_name]

        bndbox = obj.find('bndbox')
        xmin = int(bndbox.find('xmin').text)
        ymin = int(bndbox.find('ymin').text)
        xmax = int(bndbox.find('xmax').text)
        ymax = int(bndbox.find('ymax').text)

        # 转换为YOLO格式（归一化坐标）
        center_x = (xmin + xmax) / 2.0 / img_w
        center_y = (ymin + ymax) / 2.0 / img_h
        width = (xmax - xmin) / img_w
        height = (ymax - ymin) / img_h

        yolo_boxes.append(f"{class_id} {center_x:.6f} {center_y:.6f} {width:.6f} {height:.6f}")

    # 写入txt文件
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
        print("请检查VOC_ROOT路径是否正确")
        return

    print(f"找到图片目录: {voc_images}")
    print(f"找到标注目录: {voc_annotations}")

    # 转换所有图片（这里简单处理，全部放入train，你可以自己划分）
    xml_files = list(voc_annotations.glob('*.xml'))
    print(f"找到 {len(xml_files)} 个标注文件")

    for xml_file in xml_files:
        # 获取对应的图片文件名
        img_name = xml_file.stem + '.jpg'
        img_path = voc_images / img_name

        if not img_path.exists():
            print(f"警告: 找不到图片 {img_path}")
            continue

        # 复制图片到输出目录
        shutil.copy(img_path, output_path / 'images' / 'train' / img_name)

        # 转换标注文件
        txt_name = xml_file.stem + '.txt'
        convert_voc_to_yolo(str(xml_file), str(output_path / 'labels' / 'train' / txt_name), class_mapping)

    train_img_count = len(list((output_path / 'images' / 'train').glob('*.jpg')))
    print(f"✅ 转换完成！数据集已保存到 {OUTPUT_DIR}")
    print(f"   图片数量: {train_img_count}")

    # 生成data.yaml配置文件
    yaml_content = f"""
path: {os.path.abspath(OUTPUT_DIR)}
train: images/train
val: images/val

nc: 6
names: ['missing_hole', 'mouse_bite', 'open_circuit', 'short', 'spur', 'spurious_copper']
"""
    with open(OUTPUT_DIR + '/data.yaml', 'w') as f:
        f.write(yaml_content.strip())
    print(f"✅ 已生成配置文件: {OUTPUT_DIR}/data.yaml")


if __name__ == '__main__':
    main()