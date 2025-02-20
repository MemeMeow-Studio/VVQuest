import hashlib
import os
import sys
import requests
import pickle
from typing import List, Optional, Union
import numpy as np

def verify_folder(root):
    if '.' in os.path.basename(root):
        root = os.path.dirname(root)
    if not os.path.exists(root):
        verify_folder(os.path.join(root, "../"))
        os.mkdir(root)
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
