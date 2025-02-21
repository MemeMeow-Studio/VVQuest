import streamlit as st
import random
import yaml
from services.image_search import ImageSearch
from config.settings import config, reload_config

pg = st.navigation([st.Page("pages/VVQuest.py"), st.Page("pages/label_images.py"), st.Page("pages/images_manager.py")])
pg.run()