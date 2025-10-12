"""
Image processing utilities
"""
import cv2
import numpy as np
import base64

def decode_image(file):
    """
    Decode uploaded file to image array
    
    Args:
        file: uploaded file object
        
    Returns:
        numpy array: decoded image
    """
    npimg = np.frombuffer(file.read(), np.uint8)
    image = cv2.imdecode(npimg, cv2.IMREAD_COLOR)
    return image

def encode_image(image):
    """
    Encode image array to base64 string
    
    Args:
        image: numpy array
        
    Returns:
        str: base64 encoded image
    """
    _, buffer = cv2.imencode('.jpg', image)
    encoded_image = base64.b64encode(buffer).decode('utf-8')
    return encoded_image

