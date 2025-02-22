import os, sys, shutil
from typing import Dict, List, Optional
from confz import BaseConfig, ConfigSource, FileSource
from pydantic import Field

CONFIG_DIR = os.path.dirname(os.path.abspath(__file__))
CONFIG_FILE = os.path.join(CONFIG_DIR, 'config.yaml')
CONFIG_EXAMPLE_FILE = os.path.join(CONFIG_DIR, 'config.example.yaml')

# 如果配置文件不存在,从示例文件复制
if not os.path.exists(CONFIG_FILE):
    shutil.copyfile(CONFIG_EXAMPLE_FILE, CONFIG_FILE)

class EmbeddingModelConfig(BaseConfig):
    name: str
    performance: str

class VlmModelConfig(BaseConfig):
    name: str
    performance: str

class ModelsConfig(BaseConfig):
    embedding_models: Dict[str, EmbeddingModelConfig]
    vlm_models: Dict[str, VlmModelConfig]
    default_model: str

class PathsConfig(BaseConfig):
    image_dirs: Dict
    cache_file: str
    models_dir: str
    api_embeddings_cache_file: str
    label_images_cache_file: str

class OpenaiConfig(BaseConfig):
    base_url: str
    api_key: Optional[str] = None

class ApiConfig(BaseConfig):
    embedding_models: OpenaiConfig
    vlm_models: OpenaiConfig

class MiscConfig(BaseConfig):
    adapt_for_old_version: bool

class Config(BaseConfig):
    api: ApiConfig
    models: ModelsConfig
    paths: PathsConfig
    misc: MiscConfig

    CONFIG_SOURCES = [
        FileSource(
            file=CONFIG_FILE
        ),
    ]

    @property
    def base_dir(self) -> str:
        """获取项目根目录"""
        return os.path.dirname(os.path.dirname(__file__))

    def get_model_path(self, model_name: str) -> str:
        """获取模型保存路径"""
        return os.path.join(self.base_dir, self.paths.models_dir, model_name.replace('/', '_'))

    def get_absolute_image_dirs(self) -> List[str]:
        """获取图片目录的绝对路径"""
        r = []
        for v in self.paths.image_dirs.values():
            if not os.path.isabs(v['path']):
                r.append(os.path.join(self.base_dir, v['path']))
            else:
                r.append(v['path'])

        return r

    def get_absolute_cache_file(self) -> str:
        """获取缓存文件的绝对路径"""
        return os.path.join(self.base_dir, self.paths.cache_file)

    def get_abs_api_cache_file(self) -> str:
        """获取缓存文件的绝对路径"""
        return os.path.join(self.base_dir, self.paths.api_embeddings_cache_file)

    def get_label_images_cache_file(self) -> str:
        """获取缓存文件的绝对路径"""
        return os.path.join(self.base_dir,self.paths.label_images_cache_file)

    def reload(self) -> None:
        """重新加载配置文件"""
        new_config = Config()
        self.api = new_config.api
        self.models = new_config.models
        self.paths = new_config.paths
        self.misc = new_config.misc

# 创建全局配置实例
config = Config()

def reload_config() -> None:
    """重新加载配置文件"""
    global config
    config = Config()