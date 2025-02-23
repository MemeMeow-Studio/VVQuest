import streamlit as st
import random
import yaml
from services.image_search import ImageSearch
from config.settings import Config

# 页面配置
st.set_page_config(
    page_title="VVQuest",
    page_icon="🌐",
    layout="wide",
    initial_sidebar_state="expanded"
)

def save_config_yaml(api_key: str, base_url: str) -> None:
    """保存API key到config.yaml"""
    config_path = 'config/config.yaml'
    try:
        # 更新API key
        with Config() as config_data:
            config_data.api.embedding_models.api_key = api_key
            config_data.api.embedding_models.base_url = base_url
        # 更新EmbeddingService的API key
        if st.session_state.search_engine:
            st.session_state.search_engine.embedding_service.embedding_api_key = api_key
            st.session_state.search_engine.embedding_service.base_url = base_url
    except Exception as e:
        st.error(f"保存配置失败: {str(e)}")

# 搜索框提示语列表
SEARCH_PLACEHOLDERS = [
    "如何看待Deepseek？",
    "如何看待六代机？",
    "如何看待VVQuest？",
    "如何看待张维为？",
    "如何看待...？",
]

st.title("VVQuest")

# 初始化session state
if 'placeholder' not in st.session_state:
    st.session_state.placeholder = random.choice(SEARCH_PLACEHOLDERS)
if 'search_query' not in st.session_state:
    st.session_state.search_query = ""
if 'n_results' not in st.session_state:
    st.session_state.n_results = 5
if 'api_key' not in st.session_state:
    st.session_state.embedding_api_key = Config().api.embedding_models.api_key
    if st.session_state.embedding_api_key is None:
        st.session_state.embedding_api_key = ''
if 'base_url' not in st.session_state:
    st.session_state.base_url = Config().api.embedding_models.base_url
    if st.session_state.base_url is None:
        st.session_state.base_url = ''
if 'mode' not in st.session_state:
    st.session_state.mode = 'api'
if 'model_name' not in st.session_state:
    st.session_state.model_name = Config().models.default_model
if 'search_engine' not in st.session_state:
    st.session_state.search_engine = ImageSearch(
        mode=st.session_state.mode,
        model_name=st.session_state.model_name
    )
if 'has_cache' not in st.session_state:
    st.session_state.has_cache = st.session_state.search_engine.has_cache()

# 搜索函数
def search():
    if not st.session_state.search_query:
        st.session_state.results = []
        return []
        
    try:
        with st.spinner('Searching'):
            results = st.session_state.search_engine.search(
                st.session_state.search_query, 
                st.session_state.n_results,
                st.session_state.embedding_api_key if st.session_state.mode == 'api' else None
            )
            st.session_state.results = results if results else []
            return st.session_state.results
    except Exception as e:
        st.sidebar.error(f"搜索失败: {e}")
        st.session_state.results = []
        return []

# 回调函数
def on_input_change():
    st.session_state.results = []
    st.session_state.search_query = st.session_state.user_input
    if st.session_state.search_query:
        st.session_state.results = search()

def on_slider_change():
    st.session_state.n_results = st.session_state.n_results_widget
    if st.session_state.search_query:
        st.session_state.results = search()

def on_api_key_change():
    new_key = st.session_state.api_key_input
    if new_key != st.session_state.embedding_api_key:
        st.session_state.embedding_api_key = new_key
        # 保存到配置文件
        save_config_yaml(new_key, st.session_state.base_url)
        
def on_base_url_change():
    new_base_url = st.session_state.base_url_input
    if new_base_url != st.session_state.base_url:
        st.session_state.base_url = new_base_url
        # 保存到配置文件
        save_config_yaml(st.session_state.embedding_api_key, new_base_url)

def on_mode_change():
    new_mode = st.session_state.mode_widget
    if new_mode != st.session_state.mode:
        st.session_state.mode = new_mode
        try:
            if new_mode == 'local':
                st.session_state.search_engine.set_mode(new_mode, st.session_state.model_name)
            else:
                st.session_state.search_engine.set_mode(new_mode)
            if st.session_state.search_query:
                st.session_state.results = search()
        except Exception as e:
            st.error(f"模式切换失败: {str(e)}")

def on_model_change():
    # 从选项中提取模型ID
    new_model = st.session_state.model_widget.split()[0]
    if new_model != st.session_state.model_name:
        st.session_state.model_name = new_model
        if st.session_state.mode == 'local':
            try:
                st.session_state.search_engine.set_mode('local', new_model)
                if st.session_state.search_query:
                    st.session_state.results = search()
            except Exception as e:
                st.error(f"模型切换失败: {str(e)}")

def on_download_model():
    """下载模型回调"""
    with st.spinner('正在下载模型...'):
        st.session_state.search_engine.download_model()
    st.success('模型下载完成！')

def on_generate_cache():
    """生成缓存回调"""
    with st.spinner('正在生成表情包缓存...'):
        progress_bar = st.progress(0)
        st.session_state.search_engine.generate_cache(progress_bar)
        progress_bar.empty()
        # 强制重新检查缓存状态
        st.session_state.has_cache = st.session_state.search_engine.has_cache()
    st.success('缓存生成完成！')

# 侧边栏搜索区域
with st.sidebar:
    st.title("🔍 VV智能回应")
    
    # 模式选择
    st.selectbox(
        "选择搜索模式",
        options=['api', 'local'],
        index=0 if st.session_state.mode == 'api' else 1,
        key='mode_widget',
        on_change=on_mode_change,
        help="API模式需要网络连接和API密钥，本地模式需要下载模型"
    )
    
    # 本地模型选择和下载
    if st.session_state.mode == 'local':
        # 生成模型选项和显示名称的映射
        model_options = []
        model_display_names = {}
        for model_id, info in Config().models.embedding_models.items():
            downloaded = st.session_state.search_engine.embedding_service.is_model_downloaded(model_id)
            status = "✅" if downloaded else "⬇️"
            display_name = f"{model_id} [{info.performance}] {status}"
            model_options.append(display_name)
            model_display_names[model_id] = display_name
        
        # 找到当前模型的显示名称
        current_display_name = model_display_names[st.session_state.model_name]
        
        selected_model = st.selectbox(
            "选择嵌入模型",
            options=model_options,
            index=model_options.index(current_display_name),
            key='model_widget',
            on_change=on_model_change,
            help="选择合适的模型以平衡性能和资源消耗"
        )
        
        # 模型下载和重新下载按钮
        if not st.session_state.search_engine.embedding_service.is_model_downloaded(st.session_state.model_name):
            st.info("⚠️ 当前选中的模型尚未下载")
            st.button(
                "下载选中的模型",
                on_click=on_download_model,
                help="下载选中的模型到本地",
                key="download_model_btn",
                use_container_width=True
            )
        elif not st.session_state.search_engine.embedding_service.current_model:
            st.error("⚠️ 模型加载失败！请重新下载")
            st.button(
                "重新下载模型",
                on_click=on_download_model,
                help="模型加载失败时使用此功能重新下载",
                key="reload_model_btn",
                use_container_width=True
            )
            st.warning("提示：如果重新下载后仍然无法加载，请尝试重启应用")
    
    # API密钥输入(仅API模式)
    if st.session_state.mode == 'api':
        api_key = st.text_input(
            "请输入API Key", 
            value=st.session_state.embedding_api_key,
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
    
    # 生成缓存按钮
    has_cache = st.session_state.search_engine.has_cache()
    can_generate_cache = (
        st.session_state.mode == 'api' or 
        (st.session_state.mode == 'local' and 
         st.session_state.search_engine.embedding_service.is_model_downloaded(st.session_state.model_name) and
         st.session_state.search_engine.embedding_service.current_model is not None)  # 确保模型已加载
    )
    
    if not has_cache:
        st.warning("⚠️ 尚未生成表情包缓存")
    
    # 显示缓存生成按钮
    if can_generate_cache:
        button_text = "重新生成缓存" if has_cache else "生成表情包缓存"
        help_text = "更新表情包缓存" if has_cache else "首次使用需要生成表情包缓存"
        
        if st.button(
            button_text,
            help=help_text,
            key="generate_cache_btn",
            use_container_width=True
        ):
            on_generate_cache()
    elif st.session_state.mode == 'local':
        if not st.session_state.search_engine.embedding_service.is_model_downloaded(st.session_state.model_name):
            st.error("请先在上方下载选中的模型")
        elif st.session_state.search_engine.embedding_service.current_model is None:
            st.error("请先在上方重新下载模型并确保加载成功")
    
    # 检查是否可以进行搜索
    can_search = has_cache and (
        st.session_state.mode == 'api' or 
        (st.session_state.mode == 'local' and 
         st.session_state.search_engine.embedding_service.current_model is not None)
    )
    
    if not can_search and st.session_state.mode == 'local':
        if not st.session_state.search_engine.embedding_service.current_model:
            st.error("⚠️ 模型未正确加载，请先解决模型问题")
    
    user_input = st.text_input(
        "请输入搜索关键词", 
        value=st.session_state.search_query,
        placeholder=st.session_state.placeholder,
        key="user_input",
        on_change=on_input_change,
        disabled=not can_search
    )
    
    n_results = st.slider(
        "选择展示的结果数量", 
        1, 30, 
        value=st.session_state.n_results,
        key="n_results_widget",
        on_change=on_slider_change
    )

# 主区域显示搜索结果
if 'results' in st.session_state and st.session_state.results:
    # 计算每行显示的图片数量
    cols = st.columns(3)
    for idx, img_path in enumerate(st.session_state.results):
        with cols[idx % 3]:
            st.image(img_path)
elif st.session_state.search_query:
    st.info("未找到匹配的表情包")

# 添加页脚
st.markdown("---")
st.markdown(
    """
    <div style='text-align: center'>
    
    🌟 关注我 | Follow Me 🌟
    
    👨‍💻 [GitHub](https://github.com/DanielZhangyc) · 
    📺 [哔哩哔哩](https://space.bilibili.com/165404794) · 
    📝 [博客](https://www.xy0v0.top/)
    </div>
    """, 
    unsafe_allow_html=True
) 