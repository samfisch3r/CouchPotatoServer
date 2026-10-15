import os
import sys

base_path = os.path.dirname(os.path.abspath(__file__))
libs_path = os.path.join(base_path, 'libs')
if libs_path not in sys.path:
    sys.path.append(libs_path)
