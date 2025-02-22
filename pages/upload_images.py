import datetime
import os
import shutil
import time

import numpy as np
import streamlit as st
import random
import yaml
from PIL import Image
import threading

from services.image_search import ImageSearch
from config.settings import config, reload_config
from pages.utils import *
from services.label_memes import LabelMemes
from services.utils import verify_folder

if 'label_meme_obj' not in st.session_state:
    st.session_state.label_meme_obj = LabelMemes()
if 'image_folder_name' not in st.session_state:
    st.session_state.image_folder_name = 'data/images'  # 默认使用原始图片目录

with st.sidebar:
    st.selectbox(
        '选择图片文件夹',
        options=get_image_dirs(),
        key='image_folder_name',
        help='选择导入后的图片文件夹'
    )

    st.checkbox(
        '使用VLM自动生成文件名',
        key='auto_generate_labels',
        value=True
    )

    uploaded_images = st.file_uploader(label='添加表情包', accept_multiple_files=True, type=['png', 'jpg', 'jpeg', 'gif'])

CACHE_PATH = os.path.join(config.base_dir, 'cache')
verify_folder(CACHE_PATH)

def label_image(image_path, show_result_area):
    for i in range(15):
        try:
            l = st.session_state.label_meme_obj.label_image(image_path)
            return f'{l[0]}-{l[1]}-{l[2]}-{l[3]}'
        except Exception as e:
            show_result_area.error(f'第{i + 1}次尝试生成描述失败, 错误信息: {e}')
            time.sleep(1)
    show_result_area.error('生成描述失败')
    return False

if uploaded_images:
    show_image_area = st.empty()
    show_result_area= st.empty()
    for uploaded_image in uploaded_images:
        try:
            img_name = uploaded_image.name
        except Exception as e:
            img_name = f'{datetime.datetime.now()}.gif'
        # 使用 PIL 打开图片并显示
        img = Image.open(uploaded_image)
        show_image_area.image(img, caption=uploaded_image.name, width=200)
        cache_path = os.path.join(CACHE_PATH, img_name)
        if img.mode == 'P':
            img = img.convert('RGB')
        img.save(os.path.join(cache_path))
        # 生成图片描述
        if st.session_state.auto_generate_labels:
            res = label_image(cache_path, show_result_area)
            if res:
                img_name = res + os.path.splitext(img_name)[1]

        # 保存上传的图片到指定文件夹
        save_image_path = os.path.join(st.session_state.image_folder_name,img_name )
        if os.path.exists(save_image_path):
            show_result_area.error(f'图片 {save_image_path} 已存在')
        else:
            if img.mode == 'P':
                img = img.convert('RGB')
            img.save(save_image_path)
            show_result_area.success(f'图片 {save_image_path} 已保存')
    uploaded_images = []