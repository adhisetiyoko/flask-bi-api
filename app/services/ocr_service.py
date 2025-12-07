import os
from ocr.extractor import KTPOCR

def process_ktp(path_to_image):
    ocr = KTPOCR(path_to_image)
    return ocr.data.__dict__
