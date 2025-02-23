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
from config.settings import Config
from pages.utils import *
from services.label_memes import LabelMemes
from services.utils import verify_folder

if 'label_meme_obj' not in st.session_state:
    st.session_state.label_meme_obj = LabelMemes()
if 'image_folder_name' not in st.session_state:
    st.session_state.image_folder_name = 'data/images'  # 默认使用原始图片目录
# api
if 'api_key' not in st.session_state:
    st.session_state.vlm_api_key = Config().api.vlm_models.api_key
    if st.session_state.vlm_api_key is None:
        st.session_state.vlm_api_key = ''
if 'base_url' not in st.session_state:
    st.session_state.base_url = Config().api.vlm_models.base_url
    if st.session_state.base_url is None:
        st.session_state.base_url = ''


def on_api_key_change():
    new_key = st.session_state.api_key_input
    if new_key != st.session_state.vlm_api_key:
        st.session_state.vlm_api_key = new_key
        # 保存到配置文件
        with Config() as config:
            config.api.vlm_models.api_key = st.session_state.vlm_api_key


def on_base_url_change():
    new_base_url = st.session_state.base_url_input
    if new_base_url != st.session_state.base_url:
        st.session_state.base_url = new_base_url
        # 保存到配置文件
        with Config() as config:
            config.api.vlm_models.base_url = st.session_state.base_url

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
    api_key = st.text_input(
        "请输入API Key",
        value=st.session_state.vlm_api_key,
        type="password",
        key="api_key_input",
        on_change=on_api_key_change
    )
    base_url = st.text_input(
        "请输入Base URL",
        value=st.session_state.base_url,
        key="base_url_input",
        on_change=on_base_url_change
    )
    uploaded_images = st.file_uploader(label='添加表情包', accept_multiple_files=True, type=['png', 'jpg', 'jpeg', 'gif'])



CACHE_PATH = os.path.join(Config().base_dir, 'cache')
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
        if img.mode == 'P': #TODO: 检查这行代码是否不需要
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
    uploaded_images = [] # 这行代码没用，那个组件仍然会保存已上传的文件