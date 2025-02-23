import os
import sys

import requests
import openai
from openai import OpenAI
import pickle
from config.settings import Config
from typing import List, Optional, Union
import numpy as np
from FlagEmbedding import BGEM3FlagModel
from huggingface_hub import snapshot_download
from tqdm import tqdm
from services.utils import verify_folder

class EmbeddingService:
    def __init__(self):
        self.api_key = Config().api.embedding_models.api_key
        self.base_url = Config().api.embedding_models.base_url
        self.local_models = {}
        self.current_model = None
        self.mode = 'api'  # 'api' or 'local'
        self.selected_model = None
        self.embedding_cache = {}
        self._get_embedding_cache()

    def _get_embedding_cache(self):
        """获取嵌入缓存"""
        if self.mode == 'api':
            cache_file = Config().get_abs_api_cache_file()
            verify_folder(cache_file)
        else:
            if not self.selected_model:
                return
            cache_file = Config().get_absolute_cache_file().replace('.pkl', f'_{self.selected_model}.pkl')
            verify_folder(cache_file)
            
        if os.path.exists(cache_file):
            with open(cache_file, 'rb') as f:
                self.embedding_cache = pickle.load(f)

    def save_embedding_cache(self):
        """保存嵌入缓存"""
        if self.mode == 'api':
            cache_file = Config().get_abs_api_cache_file()
        else:
            if not self.selected_model:
                return
            cache_file = Config().get_absolute_cache_file().replace('.pkl', f'_{self.selected_model}.pkl')
            
        if sys.gettrace() is not None:
            print(f'saving cache: {sum(len(i) for i in self.embedding_cache.values())}')
        with open(cache_file, 'wb') as f:
            pickle.dump(self.embedding_cache, f)

    def _download_model(self, model_name: str) -> None:
        """下载模型到本地"""
        model_info = Config().models.embedding_models.get(model_name)
        if not model_info:
            raise ValueError(f"未知的模型: {model_name}")
            
        model_path = Config().get_model_path(model_name)
        if not os.path.exists(model_path):
            os.makedirs(model_path, exist_ok=True)
            print(f"正在下载模型 {model_name}...")
            snapshot_download(
                repo_id=model_info.name,
                local_dir=model_path,
                local_dir_use_symlinks=False
            )
            
    def _load_local_model(self, model_name: str) -> None:
        """加载本地模型"""
        try:
            if model_name not in self.local_models:
                model_path = Config().get_model_path(model_name)
                if not os.path.exists(model_path):
                    raise RuntimeError(f"模型 {model_name} 尚未下载")
                print(f"正在加载模型 {model_name}...")
                self.local_models[model_name] = BGEM3FlagModel(
                    model_path,
                    use_fp16=True
                )
            self.current_model = self.local_models[model_name]
        except Exception as e:
            print(f"模型加载失败: {str(e)}")
            self.current_model = None
            # 如果加载失败，从缓存中移除
            if model_name in self.local_models:
                del self.local_models[model_name]
            # 删除可能损坏的模型文件
            model_path = Config().get_model_path(model_name)
            if os.path.exists(model_path):
                import shutil
                shutil.rmtree(model_path)
            raise RuntimeError(f"模型加载失败，请重新下载模型。错误信息: {str(e)}")
            
    def set_mode(self, mode: str, model_name: Optional[str] = None) -> None:
        """设置服务模式(api/local)和选择模型"""
        if mode not in ['api', 'local']:
            raise ValueError("模式必须是 'api' 或 'local'")
            
        self.mode = mode
        if mode == 'local':
            if model_name is None:
                model_name = Config().models.default_model
            self.selected_model = model_name
            # 如果模型已下载，尝试加载
            if self.is_model_downloaded(model_name):
                try:
                    self._load_local_model(model_name)
                except Exception as e:
                    print(f"模型加载失败: {str(e)}")
                    self.current_model = None
            else:
                self.current_model = None
        else:
            self.current_model = None
            self.selected_model = None
            
    def download_selected_model(self) -> None:
        """下载已选择的模型"""
        if self.mode != 'local' or not self.selected_model:
            raise RuntimeError("请先选择本地模式和模型")
        self._download_model(self.selected_model)
        # 下载后自动加载
        self._load_local_model(self.selected_model)
            
    def load_selected_model(self) -> None:
        """加载已选择的模型"""
        if self.mode != 'local' or not self.selected_model:
            raise RuntimeError("请先选择本地模式和模型")
        self._load_local_model(self.selected_model)
            
    def is_model_downloaded(self, model_name: str) -> bool:
        """检查模型是否已下载"""
        model_path = Config().get_model_path(model_name)
        return os.path.exists(model_path)
            
    @staticmethod
    def normalize_embedding(embedding: Union[List[float], np.ndarray]) -> np.ndarray:
        """归一化嵌入向量"""
        if isinstance(embedding, list):
            embedding = np.array(embedding)
        return embedding / np.linalg.norm(embedding)
    
    def get_embedding(self, text: str, key: str = None) -> np.ndarray:
        """获取文本嵌入并归一化"""
        if self.mode == 'api':
            # API 模式
            model_name = Config().models.embedding_models['bge-m3'].name
            payload = {
                "input": text,
                "model": model_name,
                "encoding_format": "float"  # 指定返回格式
            }
            try:
                if model_name in self.embedding_cache.keys() and text in self.embedding_cache[model_name].keys():
                    if sys.gettrace() is not None:
                        print(f'using cache: {model_name} {text}')
                    embedding = self.embedding_cache[model_name][text]
                else:
                    # 检查是否指定新的api key，如果指定则更新api key
                    if key is not None and key != self.api_key:
                        self.api_key = key
                    client = OpenAI(api_key=self.api_key, base_url=self.base_url)
                    response = client.embeddings.create(**payload)
                    embedding = response.data[0].embedding
                    
                    if model_name not in self.embedding_cache.keys():
                        self.embedding_cache[model_name] = {}
                    self.embedding_cache[model_name][text] = embedding
            except openai.OpenAIError as e:
                raise RuntimeError(f"API请求失败: {str(e)}\n请求参数: {payload}")
        else:
            # 本地模式
            if self.current_model is None:
                # 如果模型未加载但已下载，尝试加载
                if self.selected_model and self.is_model_downloaded(self.selected_model):
                    self._load_local_model(self.selected_model)
                else:
                    raise RuntimeError("未加载本地模型")
            # 每次都重新计算嵌入向量
            output = self.current_model.encode(
                text, 
                return_dense=True, 
                return_sparse=False, 
                return_colbert_vecs=False
            )
            embedding = output['dense_vecs']
                
        # 确保返回新的归一化向量
        return self.normalize_embedding(embedding.copy() if isinstance(embedding, np.ndarray) else embedding)