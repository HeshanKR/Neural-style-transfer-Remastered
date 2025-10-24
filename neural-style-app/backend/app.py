from flask import Flask, request, jsonify
import tensorflow_hub as hub
import tensorflow as tf
from matplotlib import pyplot as plt
import numpy as np
import cv2
from PIL import Image
import io
import base64

app = Flask(__name__)

# Load the model
model = hub.load('https://tfhub.dev/google/magenta/arbitrary-image-stylization-v1-256/2')

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
        content_file = request.files['content']
        style_file = request.files['style']

        content_bytes = content_file.read()
        style_bytes = style_file.read()

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
        return jsonify({'error': str(e)}), 400

if __name__ == '__main__':
    app.run(debug=True)