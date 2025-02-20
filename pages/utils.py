import os

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