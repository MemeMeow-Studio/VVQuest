import streamlit as st
import random
import os
import yaml
from services.image_search import ImageSearch
from config.settings import config, reload_config
from services.utils import verify_folder


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

verify_folder(os.path.join(config.base_dir, "cache"))
delete_all_files_in_folder(os.path.join(config.base_dir, "cache"))
pg = st.navigation([st.Page("pages/VVQuest.py"), st.Page("pages/label_images.py"), st.Page("pages/upload_images.py")])
pg.run()