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

IMAGE_DIRS_PATH = 'data/image_dirs'
if not os.path.exists(IMAGE_DIRS_PATH):
    os.makedirs(IMAGE_DIRS_PATH)

# 获取image_dirs下的所有文件夹
def get_image_dirs():
    dirs = ['data/images']  # 默认包含原始图片目录
    if os.path.exists(IMAGE_DIRS_PATH):
        for item in os.listdir(IMAGE_DIRS_PATH):
            item_path = os.path.join(IMAGE_DIRS_PATH, item)
            if os.path.isdir(item_path):
                dirs.append(item_path)
    return dirs

st.set_page_config(
    page_title="LabelImages",
    page_icon="🌐",
    layout="wide",
    initial_sidebar_state="expanded"
)

if 'image_folder_name' not in st.session_state:
    st.session_state.image_folder_name = 'data/images'  # 默认使用原始图片目录
if 'image_index' not in st.session_state:
    st.session_state.image_index = 0
if 'all_images_path' not in st.session_state:
    st.session_state.all_images_path = get_all_file_paths('data/images')  # 初始化图片列表
if 'label_meme_obj' not in st.session_state:
    st.session_state.label_meme_obj = LabelMemes()
if 'new_file_name' not in st.session_state:
    st.session_state.new_file_name = ''
if 'can_add_vlm_result_to_filename' not in st.session_state:
    st.session_state.can_add_vlm_result_to_filename = False
if 'auto_generate_labels' not in st.session_state:  
    st.session_state.auto_generate_labels = False
if 'result_folder_name' not in st.session_state:
    st.session_state.result_folder_name = ''
if st.session_state.result_folder_name == '' and 'image_folder_name' in st.session_state:
    st.session_state.result_folder_name = st.session_state.image_folder_name
if st.session_state.result_folder_name == '' and 'image_folder_name' in st.session_state:
    st.session_state.result_folder_name = st.session_state.image_folder_name
if 'pre_generate_result' not in st.session_state:
    st.session_state.pre_generate_result = {}

def onchange_folder_name():
    st.session_state.image_index = 0
    st.session_state.all_images_path = get_all_file_paths(st.session_state.image_folder_name)


def onclick_start_stop_auto_generate():
    st.session_state.auto_generate_labels = not st.session_state.auto_generate_labels
    if st.session_state.auto_generate_labels:
        st.success('自动生成已启动')
    else:
        st.success('自动生成已停止')

def onclick_use_vlm_generate():
    try:
        img_path = st.session_state.all_images_path[st.session_state.image_index]
        st.session_state.img_analyse_result = st.session_state.label_meme_obj.label_image(img_path)
        st.session_state.can_add_vlm_result_to_filename = True
        return True
    except Exception as e:
        st.error(f"VLM 生成描述失败: {str(e)}")
        return False

def pregenerate_label(img_path, label_obj:LabelMemes, result_dict):
    print(f'pregenerate_label: {img_path}')
    for i in range(5):
        try:
            result_dict[img_path] = list(label_obj.label_image(img_path))
        except Exception as e:
            print(f'pregenerate_label failed: {str(e)}')


with st.sidebar:
    # 使用selectbox替代text_input
    st.selectbox(
        '选择图片文件夹',
        options=get_image_dirs(),
        on_change=onchange_folder_name,
        key='image_folder_name',
        help='可以在data/image_dirs下创建新的文件夹来保存图片。'
    )
    st.checkbox('AI预生成',
                key='ai_pre_generate',
                help='预生成接下来2张图片的描述，加速操作')

    st.checkbox('点击下一张图片时自动重命名',
                key='rename_when_click_next',
                value=True)
    # st.text_input('生成结果文件夹', key='result_folder_name')

    # """暂未实现，预生成的性能足够用，不太需要"""
    # st.button('开始/启动自动生成',on_click=onclick_start_stop_auto_generate)




if os.path.exists(st.session_state.image_folder_name):

    st.write(st.session_state.image_folder_name)
    img_path = st.session_state.all_images_path[st.session_state.image_index]
    st.write(img_path)
    with Image.open(img_path) as img:
        img_obj = img.copy()
    img_obj = np.array(img_obj)
    img_obj = resize_image(img_obj, 256)
    st.image(img_obj)

    col3, col4, col5 = st.columns([1, 1, 1])


    with col3:
        st.button('使用VLM生成描述', on_click = onclick_use_vlm_generate)

    """缓存处理"""
    if st.session_state.ai_pre_generate:
        for i in range(1,3):
            if st.session_state.image_index+i <= len(st.session_state.all_images_path)-1:
                cache_img_path = st.session_state.all_images_path[st.session_state.image_index+i]
                if cache_img_path not in st.session_state.pre_generate_result:
                    st.session_state.pre_generate_result[cache_img_path] = [] # 先占着位置
                    threading.Thread(target=pregenerate_label, args=(cache_img_path, st.session_state.label_meme_obj, st.session_state.pre_generate_result)).start()

        if not st.session_state.can_add_vlm_result_to_filename:
            if img_path in st.session_state.pre_generate_result:
                st.session_state.img_analyse_result = st.session_state.pre_generate_result[img_path]
                st.session_state.can_add_vlm_result_to_filename = True

    def use_vlm_result_to_generate_buttons():
        try:
            name_list = st.session_state.img_analyse_result
            colB1, colB2, colB3 = st.columns([1, 1, 1])
            for index, i in enumerate([colB1, colB2, colB3]):
                with i:
                    def create_onc(inner_index):
                        def onc():
                            st.session_state.new_file_name += name_list[inner_index]
                        return onc

                    st.button(f"添加 \"{name_list[index]}\" 到文件名", on_click=create_onc(index),key=f'generate_clicked_{index}')

                    # auto mode
                    if st.session_state.auto_generate_labels:
                        if index in [0,1]:
                            st.session_state.new_file_name += name_list[index]
        except Exception as e:
            st.error(f"VLM 生成描述失败: {str(e)}")


    st.text_input('New file name', key='new_file_name')

    if st.session_state.can_add_vlm_result_to_filename:
        img_path = st.session_state.all_images_path[st.session_state.image_index]
        use_vlm_result_to_generate_buttons()


    def onclick_rename_file():
        original_path = st.session_state.all_images_path[st.session_state.image_index]
        # new_path = os.path.join(st.session_state.result_folder_name, st.session_state.new_file_name+os.path.splitext(os.path.basename(original_path))[1])
        new_path = original_path.replace(os.path.splitext(os.path.basename(original_path))[0], st.session_state.new_file_name)
        try:
            os.rename(original_path, new_path)
        except Exception as e:
            st.error(f"重命名文件失败: {str(e)}")
            return False
        st.session_state.all_images_path[st.session_state.all_images_path.index(original_path)] = new_path
        st.success(f"文件已重命名为: {new_path}")
        return True
    st.button('重命名文件', on_click=onclick_rename_file)

    col1, _, col2 = st.columns([1,2,1])
    def onc1():
        st.session_state.image_index -= 1
        st.session_state.can_add_vlm_result_to_filename = False
        st.session_state.new_file_name = ''
    def onc2():
        if st.session_state.rename_when_click_next:
            if os.path.exists(st.session_state.all_images_path[st.session_state.image_index]) and \
                st.session_state.new_file_name != '':
                onclick_rename_file()
        st.session_state.image_index += 1
        st.session_state.can_add_vlm_result_to_filename = False
        st.session_state.new_file_name = ''
    with col1:
        st.button('上一张', on_click=onc1)

    with col2:
        st.button('下一张', on_click=onc2)

    if st.session_state.auto_generate_labels:
        pass