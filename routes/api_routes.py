"""
API routes for the application
"""
from flask import Blueprint, request, jsonify, send_file
import json
from services.damage_detection import detect_damage
from services.cost_estimation import estimate_damage_cost, get_car_models
from services.pdf_generator import generate_detailed_bill
from utils.image_processing import decode_image, encode_image

api = Blueprint('api', __name__)

@api.route('/car-models', methods=['GET'])
def car_models():
    """Get list of available car models"""
    return jsonify(get_car_models())

@api.route('/upload', methods=['POST'])
def upload_images():
    """Process uploaded images and detect damage"""
    if 'images' not in request.files:
        return jsonify({"error": "No images uploaded"}), 400

    files = request.files.getlist('images')
    car_model = request.form.get('carModel')

    if not files or not car_model:
        return jsonify({"error": "Please select a car model and upload images"}), 400

    results = []
    try:
        for file in files[:4]:  # Limit to 4 images
            image = decode_image(file)
            
            detected_damage, detected_severity, labeled_image = detect_damage(image)
            
            if detected_damage and detected_severity:
                cost_estimate = estimate_damage_cost(car_model, detected_damage, detected_severity)
                encoded_image = encode_image(labeled_image)

                results.append({
                    "damage": detected_damage,
                    "severity": detected_severity,
                    "cost_estimate": cost_estimate,
                    "labeled_image": encoded_image
                })
            else:
                results.append({"error": "No damage or severity detected in the image."})

        return jsonify(results)

    except Exception as e:
        return jsonify({"error": str(e)}), 500

@api.route('/generate_bill', methods=['POST'])
def generate_bill():
    """Generate and download PDF bill"""
    try:
        # Handle JSON data from frontend
        data = request.get_json()
        bill_data = data.get('bill_data')
        car_model = data.get('car_model')
        
        # Parse the bill data if it's a string
        if isinstance(bill_data, str):
            results = json.loads(bill_data)
        else:
            results = bill_data
            
        buffer = generate_detailed_bill(results, car_model)
        return send_file(buffer, as_attachment=True, download_name="repair_estimate_bill.pdf", mimetype="application/pdf")
    except Exception as e:
        return jsonify({"error": str(e)}), 500

