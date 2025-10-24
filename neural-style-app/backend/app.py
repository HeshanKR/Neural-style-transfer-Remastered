from flask import Flask, request, jsonify
from flask_cors import CORS
import tensorflow_hub as hub
import tensorflow as tf
from matplotlib import pyplot as plt
import numpy as np
import cv2
from PIL import Image
import io
import base64
import os

app = Flask(__name__)
CORS(app)  # Enable CORS for all routes

# Load the model
model = hub.load('https://tfhub.dev/google/magenta/arbitrary-image-stylization-v1-256/2')

def validate_image(file):
    """Validate if the uploaded file is a valid image."""
    try:
        img = Image.open(file)
        img.verify()  # Verify it's a valid image
        file.seek(0)  # Reset file pointer
        return True
    except Exception:
        return False

def resize_image(img_bytes, max_size=512):
    """Resize image to max_size while maintaining aspect ratio."""
    img = Image.open(io.BytesIO(img_bytes))
    img.thumbnail((max_size, max_size), Image.Resampling.LANCZOS)
    output = io.BytesIO()
    img.save(output, format='JPEG')
    output.seek(0)
    return output.getvalue()

def load_image(img_bytes):
    img = tf.image.decode_image(img_bytes, channels=3)
    img = tf.image.convert_image_dtype(img, tf.float32)
    img = img[tf.newaxis, :]
    return img

@app.route('/')
def hello_world():
    return 'Hello, World!'

@app.route('/stylize', methods=['POST'])
def stylize():
    try:
        if 'content' not in request.files or 'style' not in request.files:
            return jsonify({'error': 'Both content and style images are required'}), 400

        content_file = request.files['content']
        style_file = request.files['style']

        if content_file.filename == '' or style_file.filename == '':
            return jsonify({'error': 'No selected file'}), 400

        # Validate images
        if not validate_image(content_file):
            return jsonify({'error': 'Invalid content image'}), 400
        if not validate_image(style_file):
            return jsonify({'error': 'Invalid style image'}), 400

        content_bytes = content_file.read()
        style_bytes = style_file.read()

        # Resize images for faster processing
        content_bytes = resize_image(content_bytes)
        style_bytes = resize_image(style_bytes)

        content_image = load_image(content_bytes)
        style_image = load_image(style_bytes)

        stylized_image = model(tf.constant(content_image), tf.constant(style_image))[0]

        # Convert to PIL Image
        stylized_np = np.squeeze(stylized_image) * 255
        stylized_np = stylized_np.astype(np.uint8)
        pil_image = Image.fromarray(stylized_np)

        # Save to bytes
        img_byte_arr = io.BytesIO()
        pil_image.save(img_byte_arr, format='JPEG')
        img_byte_arr = img_byte_arr.getvalue()

        # Encode to base64
        encoded_img = base64.b64encode(img_byte_arr).decode('utf-8')

        return jsonify({'stylized_image': encoded_img})

    except Exception as e:
        return jsonify({'error': f'An error occurred: {str(e)}'}), 500

if __name__ == '__main__':
    app.run(debug=True)