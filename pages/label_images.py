import os
import shutil
import time

import numpy as np
import streamlit as st
import random
import yaml
from PIL import Image

from services.image_search import ImageSearch
from config.settings import config, reload_config
from pages.utils import *
from services.label_memes import LabelMemes



st.set_page_config(
    page_title="LabelImages",
    page_icon="🌐",
    layout="wide",
    initial_sidebar_state="expanded"
)

if 'image_folder_name' not in st.session_state:
    st.session_state.image_folder_name = 'Please Select a Folder'
if 'image_index' not in st.session_state:
    st.session_state.image_index = 0
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

def onchange_folder_name():
    st.session_state.image_index = 0
    st.session_state.all_images_path = get_all_file_paths(st.session_state.image_folder_name)



with st.sidebar:
    st.text_input('原图文件夹', on_change=onchange_folder_name, key='image_folder_name')
    # st.text_input('生成结果文件夹', key='result_folder_name')




if os.path.exists(st.session_state.image_folder_name):

    st.write(st.session_state.image_folder_name)
    img_path = st.session_state.all_images_path[st.session_state.image_index]
    st.write(img_path)
    with Image.open(img_path) as img:
        img_obj = img.copy()
    st.image(img_obj)

    col3, col4, col5 = st.columns([1, 1, 1])

    def onclick_use_vlm_generate():
        try:
            img_path = st.session_state.all_images_path[st.session_state.image_index]
            st.session_state.img_analyse_result = st.session_state.label_meme_obj.label_image(img_path)
            st.session_state.can_add_vlm_result_to_filename = True
            return True
        except Exception as e:
            st.error(f"VLM 生成描述失败: {str(e)}")
            return False
    with col3:
        st.button('使用VLM生成描述', on_click = onclick_use_vlm_generate)

    def get_labals_with_vlm():
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
        get_labals_with_vlm()


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
        return True
    st.button('重命名文件', on_click=onclick_rename_file)

    col1, _, col2 = st.columns([1,2,1])
    def onc1():
        st.session_state.image_index -= 1
        st.session_state.can_add_vlm_result_to_filename = False
        st.session_state.new_file_name = ''
    def onc2():
        st.session_state.image_index += 1
        st.session_state.can_add_vlm_result_to_filename = False
        st.session_state.new_file_name = ''
    with col1:
        st.button('上一张', on_click=onc1)

    with col2:
        st.button('下一张', on_click=onc2)

