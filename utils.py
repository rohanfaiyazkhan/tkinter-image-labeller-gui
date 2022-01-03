from PIL import Image, ImageTk
import numpy as np
import matplotlib.pyplot as plt
from pathlib import Path
import cv2
import os

IMAGE_FILE_EXTENSIONS = ('.png', '.jpg', '.jpeg', '.tiff', '.bmp', '.gif')

def is_image_path_valid(path: Path):
    "Check if path is a path to a file and if the extension is that of an image"
    return path.is_file() and path.suffix in IMAGE_FILE_EXTENSIONS

def verify_image(fn):
    "Confirm that `fn` can be opened"
    try:
        im = Image.open(fn)
        im.draft(im.mode, (32,32))
        im.load()
        resized = resize_with_padding(im)
        ImageTk.PhotoImage(resized)
        return True
    except: return False

def resize_with_padding(image, desired_size=450):
    old_size = image.size # old_size[0] is in (width, height) format

    ratio = float(desired_size) / max(old_size)
    new_size = tuple([int(x * ratio) for x in old_size])
    
    image = np.array(image)
    image = cv2.resize(image, (new_size[0], new_size[1])) 

    delta_w = desired_size - new_size[0]
    delta_h = desired_size - new_size[1]
    top, bottom = delta_h//2, delta_h-(delta_h//2)
    left, right = delta_w//2, delta_w-(delta_w//2)

    color = [0, 0, 0]
    new_im = cv2.copyMakeBorder(image, top, bottom, left, right, cv2.BORDER_CONSTANT,
        value=color)

    return Image.fromarray(new_im)

def load_images_recursively(root_dir: Path):
    "Returns list of all images in root directory"
    ls = os.listdir
    
    images_path = []
    label2image = []
    
    def append_if_image(root: Path, filename: str):
        path = root / filename
        
        if is_image_path_valid(path):
            images_path.append(path)
            label2image.append(root.stem)
        
    for filename in ls(root_dir):
        file_path = root_dir / filename
            
        if file_path.is_dir():
            for nested_filename in ls(file_path):
                append_if_image(file_path, nested_filename)
        else:
            append_if_image(root_dir, filename)
            
    return images_path, label2image