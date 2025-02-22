import os
import shutil
import time
import re

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
from services.resource_pack import ResourcePackService



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
if 'resource_pack_service' not in st.session_state:
    st.session_state.resource_pack_service = ResourcePackService()

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
            return True
        except Exception as e:
            print(f'pregenerate_label failed: {str(e)}')
            time.sleep(1)


with st.sidebar:
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

    st.divider()
    st.subheader("资源包导出")
    
    # 资源包信息输入
    pack_name = st.text_input("资源包名称", value="我的资源包", help="资源包的名称,不能为空")
    pack_version = st.text_input("版本号", value="1.0.0", help="版本号,格式如: 1.0.0")
    pack_author = st.text_input("作者", value="", help="资源包作者,不能为空")
    pack_description = st.text_input("描述", value="", help="资源包的简要描述")
    pack_tags = st.text_input("标签", value="", help="用英文逗号分隔多个标签")
            
    export_disabled = not (pack_name and pack_version and pack_author)
    export_help = "请填写必要信息" if export_disabled else "创建并下载资源包"
    
    if st.button("导出资源包", disabled=export_disabled, help=export_help):
        try:
            if not st.session_state.all_images_path:
                st.error("没有可打包的图片文件")
                st.stop()
                
            with st.spinner("正在创建资源包..."):
                tags = [tag.strip() for tag in pack_tags.split(",") if tag.strip()]
                
                # 创建资源包
                pack_dir = st.session_state.resource_pack_service.create_resource_pack(
                    name=pack_name,
                    version=pack_version,
                    author=pack_author,
                    description=pack_description,
                    image_paths=st.session_state.all_images_path,
                    tags=tags
                )
                    
                st.success("资源包创建成功!")
                
                try:
                    shutil.rmtree(pack_dir)
                except Exception as e:
                    print(f"清理临时文件失败: {str(e)}")
                
        except Exception as e:
            st.error(f"创建资源包失败: {str(e)}")
            st.stop()

if os.path.exists(st.session_state.image_folder_name):
    st.write(st.session_state.image_folder_name)
    img_path = st.session_state.all_images_path[st.session_state.image_index]
    # st.write(img_path)
    # with Image.open(img_path) as img:
    #     img_obj = img.copy()
    # img_obj = np.array(img_obj)
    # img_obj = resize_image(img_obj, 256)
    st.image(img_path, width=256)

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
            colB1, colB2, colB3, colB4 = st.columns([1, 1, 1, 1])
            for index, i in enumerate([colB1, colB2, colB3, colB4]):
                with i:
                    def create_onc(inner_index):
                        def onc():
                            st.session_state.new_file_name += name_list[inner_index]
                        return onc
                    if not name_list[index] == '':
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

    st.divider()
    st.subheader("文件列表")
    search_term = st.text_input("搜索文件", help="输入文件名关键词进行搜索")
    
    filtered_files = []
    for idx, img_path in enumerate(st.session_state.all_images_path):
        filename = os.path.basename(img_path)
        if not search_term or search_term.lower() in filename.lower():
            filtered_files.append((idx, img_path))
    
    ITEMS_PER_PAGE = 6  # 每页显示的文件数
    total_pages = max(1, (len(filtered_files) + ITEMS_PER_PAGE - 1) // ITEMS_PER_PAGE)
    
    if 'current_page' not in st.session_state:
        st.session_state.current_page = 1
        
    # 确保页码在有效范围内
    st.session_state.current_page = max(1, min(st.session_state.current_page, total_pages))
    
    page_cols = st.columns([1, 2, 1, 1])
    
    with page_cols[0]:
        if st.button("上一页", disabled=st.session_state.current_page <= 1):
            st.session_state.current_page -= 1
            st.rerun()  # 强制重新运行以更新页面
            
    with page_cols[1]:
        current_page = st.number_input(
            "页码", 
            min_value=1, 
            max_value=total_pages,
            value=st.session_state.current_page,
            key=f"page_input_{st.session_state.current_page}"  # 使用动态key确保更新
        )
        if current_page != st.session_state.current_page:
            st.session_state.current_page = current_page
            st.rerun()  # 强制重新运行以更新页面
            
    with page_cols[2]:
        st.write(f"共 {total_pages} 页")
        
    with page_cols[3]:
        if st.button("下一页", disabled=st.session_state.current_page >= total_pages):
            st.session_state.current_page += 1
            st.rerun()  # 强制重新运行以更新页面
    
    start_idx = (st.session_state.current_page - 1) * ITEMS_PER_PAGE
    end_idx = min(start_idx + ITEMS_PER_PAGE, len(filtered_files))
    
    if search_term:
        st.info(f"找到 {len(filtered_files)} 个匹配的文件")
    
    cols = st.columns([5, 1])
    with cols[0]:
        st.write("文件名")
    with cols[1]:
        st.write("操作")
        
    for i in range(start_idx, end_idx):
        original_idx, img_path = filtered_files[i]
        with st.container():
            col1, col2 = st.columns([5, 1])
            
            with col1:
                filename = os.path.basename(img_path)
                if original_idx == st.session_state.image_index:
                    st.markdown(f"**→ {filename}**")
                else:
                    if search_term:
                        pattern = re.compile(f'({re.escape(search_term)})', re.IGNORECASE)
                        highlighted = pattern.sub(r'**\1**', filename)
                        st.markdown(highlighted)
                    else:
                        st.write(filename)
                    
            with col2:
                def create_jump_callback(target_idx):
                    def jump():
                        st.session_state.image_index = target_idx
                        st.session_state.can_add_vlm_result_to_filename = False
                        st.session_state.new_file_name = ''
                    return jump
                    
                st.button("跳转", key=f"jump_{original_idx}", on_click=create_jump_callback(original_idx))

    if st.session_state.auto_generate_labels:
        pass