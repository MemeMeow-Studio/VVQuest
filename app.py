import sys
import types

import streamlit as st
import random
import os
import yaml
from services.image_search import ImageSearch
from config.settings import Config
from base import *
from loguru import logger

logger.remove(handler_id=None)
logger.add(os.path.join(Config().base_dir, os.path.join(Config().base_dir, 'Logs', "{time:YYYY-MM-DD}/{time:YYYY-MM-DD}.log")), level="TRACE", backtrace=True)
if TRACE_MODE:
    logger.add(sys.stdout, level="TRACE", backtrace=True)
elif DEBUG_MODE:
    logger.add(sys.stdout, level="DEBUG", backtrace=True)
else:
    logger.add(sys.stdout, level="INFO", backtrace=True)

def delete_all_files_in_folder(folder_path):
    try:
        # 遍历文件夹中的所有文件和子文件夹
        for root, dirs, files in os.walk(folder_path, topdown=False):
            # 删除所有文件
            for file in files:
                file_path = os.path.join(root, file)
                os.remove(file_path)
            # 删除所有空文件夹
            for dir in dirs:
                dir_path = os.path.join(root, dir)
                os.rmdir(dir_path)
    except Exception as e:
        print(f"删除过程中出现错误: {e}")

verify_folder(os.path.join(Config().temp_dir))
delete_all_files_in_folder(os.path.join(Config().temp_dir))
pg = st.navigation([st.Page("pages/Mememeow.py"), st.Page("pages/label_images.py"), st.Page("pages/upload_images.py")])
pg.run()