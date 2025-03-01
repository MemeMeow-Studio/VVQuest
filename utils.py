import os
def verify_folder(root):
    if '.' in os.path.basename(root):
        root = os.path.dirname(root)
    if not os.path.exists(root):
        parent = os.path.dirname(root)
        if parent != root:  # 防止在根目录时无限递归
            verify_folder(parent)
        os.makedirs(root, exist_ok=True)
        print(f"dir {root} has been created")