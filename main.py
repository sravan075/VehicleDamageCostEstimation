from flask import Flask, request, jsonify
from flask_cors import CORS
from ultralytics import YOLO
import cv2
import numpy as np
import base64
import pandas as pd
import os

# Import the existing functions from app.py
from app import (
    estimate_damage_cost, 
    painting_costs, 
    primary_parts_map, 
    severity_costs, 
    class_to_components
)

app = Flask(__name__)
CORS(app)  # Enable CORS for all routes

# Paths to models and data
BASE_DIR = r"Z:\Projects\Main Project\Project\backend"
csv_path = os.path.join(BASE_DIR, "price.csv")
damage_model_path = os.path.join(BASE_DIR, "model", "damage.pt")
severity_model_path = os.path.join(BASE_DIR, "model", "severity.pt")

# Load data and models
df = pd.read_csv(csv_path)
car_models = df['carmodel'].unique().tolist()
damage_model = YOLO(damage_model_path)
severity_model = YOLO(severity_model_path)

@app.route('/upload', methods=['POST'])
def upload_image():
    if 'image' not in request.files:
        return jsonify({"error": "No image uploaded"}), 400
    
    file = request.files['image']
    car_model = request.form.get('carModel')
    
    if not file or not car_model:
        return jsonify({"error": "Please select both a car model and an image"}), 400

    # Read and process the image
    npimg = np.frombuffer(file.read(), np.uint8)
    image = cv2.imdecode(npimg, cv2.IMREAD_COLOR)
    
    try:
        # Process image with YOLO models
        damage_results = damage_model.predict(source=image, imgsz=640, conf=0.5, save=False)
        severity_results = severity_model.predict(source=image, imgsz=640, conf=0.5, save=False)
        
        # Check if we have detection results
        if len(damage_results[0].boxes.cls) > 0 and len(severity_results[0].boxes.cls) > 0:
            detected_damage = damage_model.names[int(damage_results[0].boxes.cls[0])]
            detected_severity = severity_model.names[int(severity_results[0].boxes.cls[0])]
            
            # Calculate cost estimate
            cost_estimate = estimate_damage_cost(car_model, detected_damage, detected_severity)
            
            # Draw bounding boxes for damage
            damage_image = image.copy()
            for result in damage_results:
                for box in result.boxes.xyxy:
                    x1, y1, x2, y2 = map(int, box)
                    cv2.rectangle(damage_image, (x1, y1), (x2, y2), (255, 0, 0), 2)
                    cv2.putText(damage_image, f"{detected_damage}", (x1, y1-10), 
                               cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 0, 0), 2)
            
            # Draw bounding boxes for severity
            severity_image = image.copy()
            for result in severity_results:
                for box in result.boxes.xyxy:
                    x1, y1, x2, y2 = map(int, box)
                    cv2.rectangle(severity_image, (x1, y1), (x2, y2), (0, 0, 255), 2)
                    cv2.putText(severity_image, f"{detected_severity}", (x1, y1-10), 
                               cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 255), 2)
            
            # Convert labeled images to base64
            _, damage_buffer = cv2.imencode('.jpg', damage_image)
            damage_encoded = base64.b64encode(damage_buffer).decode('utf-8')
            
            _, severity_buffer = cv2.imencode('.jpg', severity_image)
            severity_encoded = base64.b64encode(severity_buffer).decode('utf-8')
            
            return jsonify({
                "damage_classes": [detected_damage],
                "severity_classes": {"0": detected_severity},
                "cost_estimate": cost_estimate,
                "processed_images": {
                    "damage": damage_encoded,
                    "severity": severity_encoded
                }
            })
        else:
            return jsonify({"error": "No damage or severity detected in the image"}), 400
    
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/car-models', methods=['GET'])
def get_car_models():
    return jsonify(car_models)

if __name__ == '__main__':
    app.run(debug=True, port=5000)