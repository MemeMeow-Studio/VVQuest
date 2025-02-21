import os

import cv2


def get_all_file_paths(folder_path):
    # 用于存储所有文件的绝对路径
    file_paths = []
    # 使用os.walk()遍历文件夹及其子文件夹
    for root, directories, files in os.walk(folder_path):
        for filename in files:
            # 构建文件的绝对路径
            file_path = os.path.join(root, filename)
            # 将绝对路径添加到列表中
            file_paths.append(file_path)
    return file_paths

def resize_image(img, max_size=1024):
    """尺寸调整"""
    h, w = img.shape[:2]

    if max(h, w) > max_size:
        scale = max_size / max(h, w)
        new_w = int(w * scale)
        new_h = int(h * scale)
        return cv2.resize(img, (new_w, new_h), interpolation=cv2.INTER_AREA)
    return img