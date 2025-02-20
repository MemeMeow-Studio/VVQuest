import os
import sys
import requests
import pickle
from typing import List, Optional, Union
import numpy as np

def verify_folder(root):
    if os.path.isfile(root):
        root = os.path.dirname(root)
    if not os.path.exists(root):
        verify_folder(os.path.join(root, "../"))
        os.mkdir(root)
        print(f"dir {root} has been created")
