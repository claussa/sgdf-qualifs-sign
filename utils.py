import io
from io import BytesIO

from PIL import Image
from numpy import ndarray


def canvas_to_bytes_images(canvas: ndarray) -> BytesIO:
    img = Image.fromarray(canvas)
    img_byte_arr = io.BytesIO()
    img.save(img_byte_arr, format='PNG')
    return img_byte_arr


def create_filename(name: str, type: str) -> str:
    return " ".join([s.capitalize() for s in name.replace('\n', '').split(' ')]) + f"-{type}.pdf"
