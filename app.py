import streamlit as st
import random
import yaml
from services.image_search import ImageSearch
from config.settings import config, reload_config

pg = st.navigation([st.Page("streamlit_app.py"), st.Page("pages/label_images.py")])
pg.run()