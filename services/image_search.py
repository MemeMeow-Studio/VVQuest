import os
import threading
import time

import numpy as np
import pickle
import re
from typing import Optional, List, Dict

from config.settings import Config

from services.embedding_service import EmbeddingService
from services.resource_pack_manager import ResourcePackManager
from services.utils import *


class ImageSearch:
    def __init__(self, mode: str = 'api', model_name: Optional[str] = None):
        self.embedding_service = EmbeddingService()
        self.embedding_service.set_mode(mode, model_name)
        self.resource_pack_manager = ResourcePackManager()
        self.image_data = None
        self._try_load_cache()

    def __reload_class_cache(self):
        self.embedding_service = EmbeddingService()

    def _try_load_cache(self) -> None:
        self.__reload_class_cache()
        """尝试加载缓存"""
        # 获取所有启用的资源包的缓存文件
        cache_files = self.resource_pack_manager.get_cache_files()
        
        if not cache_files:
            self.image_data = None
            return
            
        # 合并所有缓存文件的数据
        all_embeddings = []
        
        for pack_id, cache_file in cache_files.items():
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
                            # 使用资源包的路径
                            pack_info = self.resource_pack_manager.get_enabled_packs().get(pack_id)
                            if not pack_info:
                                continue
                                
                            pack_path = pack_info["path"]
                            if not os.path.isabs(pack_path):
                                pack_path = os.path.join(Config().base_dir, pack_path)
                                
                            full_path = os.path.join(pack_path, item['filename'])
                            # 添加filepath字段
                            item['filepath'] = full_path

                        if os.path.exists(full_path):
                            # 添加资源包ID
                            item['pack_id'] = pack_id
                            valid_embeddings.append(item)

                    if valid_embeddings:
                        all_embeddings.extend(valid_embeddings)
                        # 更新缓存文件
                        if len(valid_embeddings) != len(cached_data):
                            with open(cache_file, 'wb') as f:
                                pickle.dump(valid_embeddings, f)
                except (pickle.UnpicklingError, EOFError) as e:
                    print(f"加载缓存文件 {cache_file} 失败: {str(e)}")
        
        if all_embeddings:
            self.image_data = all_embeddings
        else:
            self.image_data = None

    def _get_cache_file(self, pack_id: str = "default_pack") -> str:
        """获取指定资源包的缓存文件路径"""
        # 使用ResourcePackManager的方法获取缓存文件路径，传递当前模型名称
        cache_file = self.resource_pack_manager.get_pack_cache_file(pack_id, self.embedding_service.selected_model)
        if cache_file:
            return cache_file
            
        # 如果ResourcePackManager没有返回路径，使用旧的逻辑作为后备
        pack_info = self.resource_pack_manager.get_available_packs().get(pack_id)
        if not pack_info:
            # 使用默认缓存文件
            if self.embedding_service.selected_model:
                return Config().get_abs_cache_file().replace('.pkl', f'_{self.embedding_service.selected_model}.pkl')
            return Config().get_abs_cache_file()
            
        cache_file = pack_info["cache_file"]
        if not os.path.isabs(cache_file):
            cache_file = os.path.join(Config().base_dir, cache_file)
            
        # 添加模型名称
        if self.embedding_service.selected_model:
            cache_file = cache_file.replace('.pkl', f'_{self.embedding_service.selected_model}.pkl')
            
        return cache_file

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
        self.__reload_class_cache()
        """生成缓存"""
        if self.embedding_service.mode == 'local':
            # 确保模型已加载
            if not self.embedding_service.current_model:
                self.load_model()
                if not self.embedding_service.current_model:
                    raise RuntimeError("无法加载模型，请检查模型是否已下载")

        # 获取所有启用的资源包
        enabled_packs = self.resource_pack_manager.get_enabled_packs()
        if not enabled_packs:
            raise RuntimeError("没有启用的资源包")
            
        # 为每个资源包生成缓存
        total_packs = len(enabled_packs)
        success_count = 0
        failed_packs = []
        
        for i, (pack_id, pack_info) in enumerate(enabled_packs.items()):
            progress_bar.progress(i / total_packs, text=f"处理资源包 {i+1}/{total_packs}: {pack_info['name']}")
            try:
                self._generate_pack_cache(pack_id, pack_info, progress_bar)
                success_count += 1
            except Exception as e:
                print(f"生成资源包 {pack_info['name']} 的缓存失败: {str(e)}")
                failed_packs.append(f"{pack_info['name']}: {str(e)}")
            
        # 重新加载所有缓存
        progress_bar.progress(1.0, text="重新加载缓存...")
        self._try_load_cache()
        
        # 如果有失败的资源包，报告错误
        if failed_packs:
            error_message = f"成功生成 {success_count}/{total_packs} 个资源包的缓存。\n以下资源包生成失败:\n" + "\n".join(failed_packs)
            raise RuntimeError(error_message)

    def _generate_pack_cache(self, pack_id: str, pack_info: Dict, progress_bar) -> None:
        self.__reload_class_cache()
        """为指定的资源包生成缓存"""
        img_dir = pack_info["path"]
        if not os.path.isabs(img_dir):
            img_dir = os.path.join(Config().base_dir, img_dir)
            
        if not os.path.exists(img_dir):
            os.makedirs(img_dir, exist_ok=True)
            
        cache_file = self._get_cache_file(pack_id)
        
        # 确保缓存目录存在
        os.makedirs(os.path.dirname(cache_file), exist_ok=True)
        
        # 尝试加载现有缓存
        existing_embeddings = []
        if os.path.exists(cache_file):
            try:
                with open(cache_file, 'rb') as f:
                    loaded_data = pickle.load(f)
                    
                # 验证加载的数据格式
                if isinstance(loaded_data, list):
                    # 过滤掉不是字典或缺少必要键的元素
                    valid_embeddings = []
                    for item in loaded_data:
                        if isinstance(item, dict) and 'filename' in item and 'embedding' in item:
                            valid_embeddings.append(item)
                        else:
                            print(f"警告: 缓存文件中发现无效的数据项: {type(item)}")
                    existing_embeddings = valid_embeddings
                else:
                    print(f"警告: 缓存文件格式不正确，期望列表但得到 {type(loaded_data)}")
            except (pickle.UnpicklingError, EOFError) as e:
                print(f"加载缓存文件 {cache_file} 失败: {str(e)}")
                existing_embeddings = []
                
        # 确保所有缓存数据都有filepath字段
        generated_files = []
        for item in existing_embeddings:
            if 'filepath' not in item:
                item['filepath'] = os.path.join(img_dir, item['filename'])
            generated_files.append(item['filepath'])

        # 获取所有图片文件路径
        def get_all_file_paths(folder_path):
            file_paths = []
            for root, _, files in os.walk(folder_path):
                for filename in files:
                    file_path = os.path.join(root, filename)
                    file_paths.append(file_path)
            return file_paths

        all_files = get_all_file_paths(img_dir)
        image_files = [
            f for f in all_files
            if f.lower().endswith(('.png', '.jpg', '.jpeg', '.gif'))
        ]
        
        # 过滤掉已经生成过嵌入的文件
        new_image_files = [f for f in image_files if f not in generated_files]
        
        if not new_image_files and existing_embeddings:
            # 如果没有新文件且已有缓存，直接返回
            return
            
        # 获取资源包类型
        image_type = pack_info.get("type", "vv")
        
        # 获取替换规则
        replace_patterns_regex = None
        if "regex" in pack_info:
            replace_patterns_regex = {pack_info["regex"]["pattern"]: pack_info["regex"]["replacement"]}
            
        # 生成新文件的嵌入
        embeddings = existing_embeddings.copy()
        errors = []
        
        # 创建线程列表和线程锁
        threads = []
        embedding_lock = threading.Lock()
        
        total_files = len(new_image_files)
        for index, filepath in enumerate(new_image_files):
            try:
                if not os.path.isabs(filepath):
                    filepath = os.path.join(Config().base_dir, filepath)
                    
                filename = os.path.splitext(os.path.basename(filepath))[0]
                full_filename = None
                
                for ext in ['.png', '.jpg', '.jpeg', '.gif']:
                    if os.path.exists(os.path.join(os.path.dirname(filepath), filename + ext)):
                        full_filename = filename + ext
                        break
                        
                if full_filename:
                    raw_embedding_name = filename
                    if replace_patterns_regex is not None:
                        for pattern, replacement in replace_patterns_regex.items():
                            raw_embedding_name = re.sub(pattern, replacement, raw_embedding_name)
                            
                    embedding_names = raw_embedding_name.split('-')
                    for embedding_name in embedding_names:
                        if embedding_name == '':
                            continue
                            
                        def add_embedding_thread(embedding_service: EmbeddingService, store_embedding_list: List,
                                               filename_: str, filepath_: str, embedding_name_: str,
                                               image_type_: str, pack_id_: str, lock: threading.Lock, errors_list: List):
                            try:
                                embedding = embedding_service.get_embedding(embedding_name_)
                                with lock:
                                    store_embedding_list.append({
                                        "filename": filename_,
                                        "filepath": filepath_,
                                        "embedding": embedding,
                                        "embedding_name": embedding_name_,
                                        "type": image_type_ if image_type_ is not None else 'Normal',
                                        "pack_id": pack_id_
                                    })
                            except Exception as e:
                                error_msg = f"生成嵌入失败 [{filepath_}]: {str(e)}"
                                print(error_msg)
                                with lock:
                                    errors_list.append(f"[{filepath_}] {str(e)}")
                                
                        while self.embedding_service.is_rpm_overload():
                            print(f"RPM过载，等待1秒...")
                            time.sleep(1)
                            
                        # 创建并启动线程
                        thread = threading.Thread(
                            target=add_embedding_thread, 
                            args=(self.embedding_service, embeddings, filename, filepath, 
                                  embedding_name, image_type, pack_id, embedding_lock, errors)
                        )
                        thread.start()
                        threads.append(thread)
                        
                progress_bar.progress((index + 1) / total_files, text=f"处理 {pack_info['name']} 图片 {index + 1}/{total_files}")
                
                # 每处理150个文件，等待所有线程完成并保存一次缓存
                if index % 150 == 0 and index > 0:
                    # 等待所有线程完成
                    for t in threads:
                        t.join()
                    threads = []  # 清空线程列表
                    
                    # 保存中间缓存
                    if embeddings:
                        with embedding_lock:
                            os.makedirs(os.path.dirname(cache_file), exist_ok=True)
                            with open(cache_file, 'wb') as f:
                                pickle.dump(embeddings, f)
                            
                            self.embedding_service.cache_lock.acquire()
                            self.embedding_service.save_embedding_cache()
                            self.embedding_service.cache_lock.release()
                        
            except Exception as e:
                print(f"生成嵌入失败 [{filepath}]: {str(e)}")
                errors.append(f"[{filepath}] {str(e)}")
        
        # 等待所有剩余线程完成
        for t in threads:
            t.join()
                
        # 保存最终缓存
        if embeddings:
            with embedding_lock:
                os.makedirs(os.path.dirname(cache_file), exist_ok=True)
                with open(cache_file, 'wb') as f:
                    pickle.dump(embeddings, f)
                
                self.embedding_service.cache_lock.acquire()
                self.embedding_service.save_embedding_cache()
                self.embedding_service.cache_lock.release()
            
        # 提出错误
        if errors:
            error_summary = "\n".join(errors)
            print(error_summary)
            raise RuntimeError(error_summary)

    def _cosine_similarity(self, a: np.ndarray, b: np.ndarray) -> float:
        """余弦相似度计算"""
        return np.dot(a, b)

    def search(self, query: str, top_k: int = 5, api_key: Optional[str] = None) -> List[str]:
        self.__reload_class_cache()
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
                # 使用资源包的路径
                pack_id = img.get('pack_id', 'default_pack')
                pack_info = self.resource_pack_manager.get_enabled_packs().get(pack_id)
                if not pack_info:
                    continue
                    
                pack_path = pack_info["path"]
                if not os.path.isabs(pack_path):
                    pack_path = os.path.join(Config().base_dir, pack_path)
                    
                img['filepath'] = os.path.join(pack_path, img["filename"])
                
            if os.path.exists(img['filepath']):
                exists_imgs_path.append(img['filepath'])
                similarity = self._cosine_similarity(query_embedding, img['embedding'])
                similarities.append((similarity, img['filepath']))

        # 按相似度排序
        similarities.sort(reverse=True)
        
        # 返回前top_k个结果
        return [item[1] for item in similarities[:top_k]]
        
    def reload_resource_packs(self) -> None:
        """重新加载资源包"""
        self.resource_pack_manager = ResourcePackManager()
        self._try_load_cache()
        
    def enable_resource_pack(self, pack_id: str) -> bool:
        """启用资源包"""
        result = self.resource_pack_manager.enable_pack(pack_id)
        if result:
            self._try_load_cache()
        return result
        
    def disable_resource_pack(self, pack_id: str) -> bool:
        """禁用资源包"""
        result = self.resource_pack_manager.disable_pack(pack_id)
        if result:
            self._try_load_cache()
        return result
        
    def get_resource_packs(self) -> Dict[str, Dict]:
        """获取所有资源包"""
        return self.resource_pack_manager.get_available_packs()
        
    def get_enabled_resource_packs(self) -> Dict[str, Dict]:
        """获取所有启用的资源包"""
        return self.resource_pack_manager.get_enabled_packs()
        
    def get_resource_pack_cover(self, pack_id: str) -> Optional[str]:
        """获取资源包封面"""
        return self.resource_pack_manager.get_pack_cover(pack_id)


def pop_similar_images(input_image_list, threshold=0.9):
    return_images = []
    image_list = []
    for index, i in enumerate(input_image_list):
        c = i.copy()
        c['image'] = load_image(i['path'])
        image_list.append(c)
    for index, img in enumerate(image_list):

        max_similar = 0
        print(index)
        for j in image_list[index+1:]:
            max_similar = max(max_similar, calculate_image_similarity(img['image'], j['image']))
        if max_similar < threshold:
            return_images.append(img)

    return return_images