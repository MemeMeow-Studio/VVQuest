import os
import numpy as np
import pickle
import re
from typing import Optional, List, Dict

from config.settings import Config

from services.embedding_service import EmbeddingService

class ImageSearch:
    def __init__(self, mode: str = 'api', model_name: Optional[str] = None):
        self.embedding_service = EmbeddingService()
        self.embedding_service.set_mode(mode, model_name)
        self.image_data = None
        self._try_load_cache()
        
    def _try_load_cache(self) -> None:
        """尝试加载缓存"""
        cache_file = self._get_cache_file()
        if os.path.exists(cache_file):
            try:
                with open(cache_file, 'rb') as f:
                    cached_data = pickle.load(f)
                valid_embeddings = []
                for item in cached_data:
                    # 获取文件路径
                    if 'filepath' in item:
                        full_path = item['filepath']
                    else:
                        full_path = os.path.join(Config().get_absolute_image_dirs()[0], item['filename'])
                        # 添加filepath字段
                        item['filepath'] = full_path

                    if os.path.exists(full_path):
                        valid_embeddings.append(item)
                    
                if valid_embeddings:
                    self.image_data = valid_embeddings
                    if len(valid_embeddings) != len(cached_data):
                        with open(cache_file, 'wb') as f:
                            pickle.dump(valid_embeddings, f)
                else:
                    self.image_data = None
            except (pickle.UnpicklingError, EOFError):
                self.image_data = None
                
    def _get_cache_file(self) -> str:
        """获取当前模式的缓存文件路径"""
        if self.embedding_service.selected_model:
            return Config().get_absolute_cache_file().replace('.pkl', f'_{self.embedding_service.selected_model}.pkl')
        return Config().get_absolute_cache_file()
        
    def set_mode(self, mode: str, model_name: Optional[str] = None) -> None:
        """切换搜索模式和模型"""
        try:
            self.embedding_service.set_mode(mode, model_name)
            # 清空当前缓存
            self.image_data = None
            # 尝试加载新模式/模型的缓存
            self._try_load_cache()
        except Exception as e:
            print(f"模式切换失败: {str(e)}")
            # 保持错误状态，让UI层处理
            if mode == 'local':
                self.embedding_service.mode = mode
                self.embedding_service.selected_model = model_name
                self.embedding_service.current_model = None
            # 确保清空缓存
            self.image_data = None

    def download_model(self) -> None:
        """下载选中的模型"""
        self.embedding_service.download_selected_model()
        
    def load_model(self) -> None:
        """加载选中的模型"""
        self.embedding_service.load_selected_model()
    
    def has_cache(self) -> bool:
        """检查是否有可用的缓存"""
        return self.image_data is not None
    
    def generate_cache(self, progress_bar) -> None:
        """生成缓存"""
        if self.embedding_service.mode == 'local':
            self.load_model()  # 确保模型已加载
            
        # 获取所有图片目录
        image_dirs = Config().get_absolute_image_dirs()
        for img_dir in image_dirs:
            if not os.path.exists(img_dir):
                os.makedirs(img_dir, exist_ok=True)

        self._try_load_cache()
        generated_files = []
        if self.image_data is not None:
            # 确保所有缓存数据都有filepath字段
            for item in self.image_data:
                if 'filepath' not in item:
                    item['filepath'] = os.path.join(Config().get_absolute_image_dirs()[0], item['filename'])
            generated_files = [i['filepath'] for i in self.image_data]

        # 获取所有路径
        def get_all_file_paths(folder_path):
            # 用于存储所有文件的绝对路径
            file_paths = []
            # 使用os.walk()遍历文件夹及其子文件夹
            for root, directories, files in os.walk(folder_path):
                for filename in files:
                    # 构建文件的绝对路径
                    file_path = os.path.join(root, filename)
                    # 将绝对路径添加到列表中
                    file_paths.append(file_path)
            return file_paths

        embeddings = []
        errors = []  # 收集错误
        # 按照图片文件夹分开循环
        for dirs_k, dirs_v in Config().paths.image_dirs.items():
            all_dir = []

            img_dir = dirs_v['path']
            if not os.path.isabs(img_dir): img_dir = os.path.join(Config().base_dir, img_dir)
            all_dir = get_all_file_paths(img_dir)

            # 构建文件路径列表
            image_files = [
                f
                for f in all_dir
                if f.lower().endswith(('.png', '.jpg', '.jpeg', '.gif'))  # ????????????
            ]
            length = len(image_files)

            # 使用regex替换文件名
            if 'regex' in dirs_v.keys():
                replace_patterns_regex = {dirs_v['regex']['pattern']: dirs_v['regex']['replacement']}
            else:
                replace_patterns_regex = None

            image_type = dirs_v.setdefault('type', 'None')

            for index, filepath in enumerate(image_files):
                try:
                    if not os.path.isabs(filepath): filepath = os.path.join(Config().base_dir, filepath)
                    filename = os.path.splitext(os.path.basename(filepath))[0]

                    full_filename = None
                    for ext in ['.png', '.jpg', '.jpeg', '.gif']:
                        if os.path.exists(os.path.join(os.path.dirname(filepath), filename + ext)):
                            full_filename = filename + ext
                            break

                    if full_filename:
                        # if filepath in generated_files:
                        #     # 使用已经存在的embedding
                        #     embedding = self.image_data[generated_files.index(filepath)]['embedding']
                        #     embedding_name = self.image_data[generated_files.index(filepath)]['embedding_name']
                        # else:

                        # 在service那边已经有缓存了，这边直接开干，同时也是为了适配一个图片多个embedding。
                        raw_embedding_name = filename
                        if replace_patterns_regex is not None:
                            for pattern, replacement in replace_patterns_regex.items():
                                raw_embedding_name = re.sub(pattern, replacement, raw_embedding_name)
                        embedding_names = raw_embedding_name.split('-')
                        for embedding_name in embedding_names:
                            if embedding_name == '':
                                print()
                                continue
                            embedding = self.embedding_service.get_embedding(embedding_name)
                            embeddings.append({
                                "filename": full_filename,
                                "filepath": filepath,
                                "embedding": embedding,
                                "embedding_name": embedding_name,
                                "type": image_type if image_type is not None else 'Normal'
                            })

                    progress_bar.progress((index + 1) / length, text=f"处理图片 {index + 1}/{length}")

                    if index%20==0:
                        self.embedding_service.save_embedding_cache()

                except Exception as e:
                    print(f"生成嵌入失败 [{filepath}]: {str(e)}")
                    errors.append(f"[{filepath}] {str(e)}")
                
        # 保存缓存
        if embeddings:
            cache_file = self._get_cache_file()
            os.makedirs(os.path.dirname(cache_file), exist_ok=True)
            with open(cache_file, 'wb') as f:
                pickle.dump(embeddings, f)
            self.image_data = embeddings

        # 提出错误
        if errors:
            error_summary = "\n".join(errors)
            print(error_summary)
            raise RuntimeError(error_summary)
    
    def _cosine_similarity(self, a: np.ndarray, b: np.ndarray) -> float:
        """余弦相似度计算"""
        return np.dot(a, b)
    
    def search(self, query: str, top_k: int = 5, api_key: Optional[str] = None) -> List[str]:
        """语义搜索最匹配的图片"""
        if not self.has_cache():
            return []
            
        try:
            query_embedding = self.embedding_service.get_embedding(query, api_key)
        except Exception as e:
            print(f"查询嵌入生成失败: {str(e)}")
            return []
        
        similarities = []
        exists_imgs_path = []
        for img in self.image_data:
            if 'filepath' not in img and Config().misc.adapt_for_old_version:
                img['filepath'] = os.path.join(Config().get_absolute_image_dirs()[0], img["filename"])
            if os.path.exists(img['filepath']):
                similarities.append((img['filepath'], self._cosine_similarity(query_embedding, img["embedding"])))
        
        if not similarities:
            return []
            
        # 按相似度降序排序并返回前top_k个结果
        sorted_items = sorted(similarities, key=lambda x: x[1], reverse=True)
        return_list = []
        count = 0
        for i in sorted_items:
            if count >= top_k:
                break
            if i[0] not in exists_imgs_path:
                return_list.append(i[0])
                exists_imgs_path.append(i[0])
                count += 1
        return return_list