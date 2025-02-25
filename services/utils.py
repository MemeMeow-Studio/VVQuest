import hashlib
import os
import sys
import requests
import pickle
from typing import List, Optional, Union
import numpy as np
import cv2

def verify_folder(root):
    if '.' in os.path.basename(root):
        root = os.path.dirname(root)
    if not os.path.exists(root):
        parent = os.path.dirname(root)
        if parent != root:  # 防止在根目录时无限递归
            verify_folder(parent)
        os.makedirs(root, exist_ok=True)
        print(f"dir {root} has been created")



def get_file_hash(file_path, algorithm='sha256'):
    """
    该函数用于计算文件的哈希值
    :param file_path: 文件的路径
    :param algorithm: 哈希算法，默认为 sha256
    :return: 文件的哈希值
    """
    # 根据指定的算法创建哈希对象
    hash_object = hashlib.new(algorithm)
    try:
        # 以二进制模式打开文件
        with open(file_path, 'rb') as file:
            # 分块读取文件内容，避免大文件占用过多内存
            for chunk in iter(lambda: file.read(4096), b""):
                # 更新哈希对象的内容
                hash_object.update(chunk)
        # 获取最终的哈希值
        return hash_object.hexdigest()
    except FileNotFoundError:
        print(f"文件 {file_path} 未找到。")
        return None

from PIL import Image
import base64
from io import BytesIO
def image_to_base64_jpg(image_path):
    try:
        # 打开图像文件
        with Image.open(image_path) as img:
            img = img.convert('RGB')
            # 创建一个内存缓冲区
            buffer = BytesIO()
            # 将图像保存为JPEG格式到缓冲区
            img.save(buffer, format="JPEG")
            # 获取缓冲区中的二进制数据
            img_bytes = buffer.getvalue()
            # 将二进制数据编码为Base64字符串
            base64_encoded = base64.b64encode(img_bytes).decode('utf-8')
            img.close()
        return base64_encoded
    except Exception as e:
        raise (f"处理图像时出现错误: {e}")

def load_image(image_path) -> np.ndarray:
    # opencv不能打开含有中文路径的图片和gif图，一定要用PIL
    try:
        # 打开图像文件
        with Image.open(image_path) as img:
            img = img.convert('RGB')
            npimg = np.array(img)
            img.close()
            npimg = cv2.cvtColor(npimg, cv2.COLOR_RGB2BGR)
        return npimg
    except Exception as e:
        raise (f"处理图像时出现错误: {e}")

def calculate_image_similarity(img1, img2):
    """
    该函数用于计算两张图片的相似度
    :param image_path1: 第一张图片的路径
    :param image_path2: 第二张图片的路径
    :return: 两张图片的相似度值
    """

    # 确保图片尺寸相同
    img2 = cv2.resize(img2, (img1.shape[1], img1.shape[0]))

    # # 计算直方图
    # hist1 = cv2.calcHist([img1], [0, 1, 2], None, [8, 8, 8], [0, 256, 0, 256, 0, 256])
    # hist2 = cv2.calcHist([img2], [0, 1, 2], None, [8, 8, 8], [0, 256, 0, 256, 0, 256])
    #
    # # 归一化直方图
    # hist1 = cv2.normalize(hist1, hist1).flatten()
    # hist2 = cv2.normalize(hist2, hist2).flatten()
    #
    # # 计算相似度
    # similarity = cv2.compareHist(hist1, hist2, cv2.HISTCMP_CORREL)

    result = cv2.matchTemplate(img1, img2, cv2.TM_CCORR_NORMED)  # TM_CCOEFF_NORMED

    min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(result)
    similarity = max_val

    if sys.gettrace() is not None:
        print(similarity)
    return similarity





