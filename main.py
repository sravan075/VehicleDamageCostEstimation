# Updated main.py
import os
import cv2
import numpy as np
import base64
import pandas as pd
import json
from flask import Flask, request, jsonify, send_file
from flask_cors import CORS
from ultralytics import YOLO
from io import BytesIO
from reportlab.lib.pagesizes import A4
from reportlab.platypus import (
    SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
)
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from datetime import datetime

app = Flask(__name__)
CORS(app)

# Paths to models and data
BASE_DIR = r"Z:\\Projects\\Main Project\\Project\\backend"
csv_path = os.path.join(BASE_DIR, "price.csv")
damage_model_path = os.path.join(BASE_DIR, "model", "damage.pt")
severity_model_path = os.path.join(BASE_DIR, "model", "severity.pt")

# Load data and models
df = pd.read_csv(csv_path)
car_models = df['carmodel'].unique().tolist()
damage_model = YOLO(damage_model_path)
severity_model = YOLO(severity_model_path)

# Cost dictionaries
painting_costs = {
    'Door': 4000, 'Front-Bumper': 3000, 'Front-fender': 1500, 'Rear-Bumper': 3000,
    'Rear-Fender': 1500, 'Rear-Trunk': 2000, 'bonnet-damage': 2000, 'doorouter-damage': 4000,
    'fender-damage': 1500, 'front-bumper-damage': 3000, 'rear-bumper-damage': 3000
}

labour_costs = {
    "minor-scratch": 2500, "moderate-scratch": 3000, "severe-scratch": 4000,
    "minor-dent": 4000, "moderate-dent": 5000, "severe-dent": 6000,
    "moderate-broken": 7000, "severe-broken": 8000
}

internal_damage_costs = {
    'Door': 2000, 'Front-Bumper': 6000, 'Rear-Bumper': 4000, 'Rear-Fender': 5000, 
    'Rear-Trunk': 3000, 'doorouter-damage': 2000, 'fender-damage': 5000, 
    'front-bumper-damage': 6000, 'rear-bumper-damage': 4000, 'bonnet-damage': 6000
}

class_to_components = {
    'Door': ['Door', 'Door Handle', 'Door Handle Bracket', 'Door Hinge', 'Door Latch',
             'Door Lock', 'Door Seal', 'Door Trim Cap', 'Door Lock Cylinder', 'Door Lock Link',
             'Door Check Arm', 'Door Membrane'],
    'Front-Bumper': ['Front Bumper', 'Bumper Brackets', 'Bumper Trim'],
    'Rear-Bumper': ['Rear Bumper', 'Bumper Brackets', 'Bumper Trim'],
    # Add more mappings as needed
}

# Cost estimation function
def estimate_damage_cost(car_model, damaged_part, severity):
    if damaged_part == "fender-damage":
        damaged_part = "Front-fender"
    if damaged_part == "doorouter-damage":
        damaged_part = "Door"

    paint_cost = painting_costs.get(damaged_part, 0)
    labour_cost = labour_costs.get(severity, 0)

    primary_part_price = 0
    component_price = 0
    part_list = []
    component_list = []

    related_components = class_to_components.get(damaged_part, [])
    if related_components:
        component_df = df[(df["carmodel"] == car_model) & (df["component"].isin(related_components))]

        if not component_df.empty:
            max_price_row = component_df.loc[component_df["price"].idxmax()]
            primary_part_price = max_price_row["price"]
            main_part_name = max_price_row["component"]

            filtered_component_df = component_df[component_df["component"] != main_part_name]

            part_list = [{"title": max_price_row["title"], "price": primary_part_price}]
            if severity in ["moderate-broken", "severe-broken"]:
                component_price = filtered_component_df["price"].sum()
                component_list = filtered_component_df[["title", "price"]].to_dict(orient="records")

    if severity not in ["moderate-broken", "severe-dent", "severe-broken"]:
        primary_part_price = 0
        part_list = []
        component_price = 0
        component_list = []

    additional_cost = 0
    if severity == "minor-scratch":
        additional_cost += paint_cost
    if severity == "moderate-scratch":
        additional_cost += paint_cost
    if severity == "severe-scratch":
        additional_cost += paint_cost
    if severity == "minor-dent":
        additional_cost += 0
    if severity == "moderate-dent":
        additional_cost += paint_cost
    if severity == "severe-dent":
        additional_cost += primary_part_price + paint_cost
    if severity == "moderate-broken":
        additional_cost += paint_cost + primary_part_price + component_price
    if severity == "severe-broken":
        additional_cost += primary_part_price + component_price + paint_cost + internal_damage_costs.get(damaged_part, 0)

    total_cost = labour_cost + additional_cost

    return {
        "Painting Cost": paint_cost,
        "Labour Cost": labour_cost,
        "Part Price": primary_part_price,
        "Parts": part_list,
        "Component Price": component_price,
        "Components": component_list,
        "Internal Damage Cost": internal_damage_costs.get(damaged_part, 0) if severity == "severe-broken" else 0,
        "Total Repair Cost": total_cost,
    }

# Bill generation function
def generate_detailed_bill(results, car_model):
    from reportlab.lib.units import inch
    from reportlab.lib.enums import TA_CENTER
    import base64
    from PIL import Image as PILImage
    
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4, topMargin=0.5*inch, bottomMargin=0.5*inch)
    styles = getSampleStyleSheet()
    
    # Custom styles
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Title'],
        fontSize=24,
        textColor=colors.HexColor('#2c3e50'),
        alignment=TA_CENTER,
        spaceAfter=10
    )
    
    subtitle_style = ParagraphStyle(
        'CustomSubtitle',
        parent=styles['Normal'],
        fontSize=12,
        textColor=colors.HexColor('#7f8c8d'),
        alignment=TA_CENTER,
        spaceAfter=20
    )
    
    heading_style = ParagraphStyle(
        'Heading',
        parent=styles['Heading2'],
        fontSize=16,
        textColor=colors.HexColor('#2c3e50'),
        spaceAfter=10,
        spaceBefore=15
    )
    
    elements = []
    
    # Header section
    elements.append(Paragraph("REPAIR ESTIMATE", title_style))
    elements.append(Paragraph("Vehicle Damage Assessment", subtitle_style))
    
    # Metadata
    meta_data = [
        ['Date:', datetime.now().strftime('%d %B %Y')],
        ['Vehicle:', car_model],
        ['Images Analyzed:', str(len(results))]
    ]
    meta_table = Table(meta_data, colWidths=[2*inch, 4*inch])
    meta_table.setStyle(TableStyle([
        ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('TEXTCOLOR', (0, 0), (0, -1), colors.HexColor('#7f8c8d')),
        ('TEXTCOLOR', (1, 0), (1, -1), colors.HexColor('#2c3e50')),
        ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
    ]))
    elements.append(meta_table)
    elements.append(Spacer(1, 20))
    
    # Results section
    elements.append(Paragraph("Detection Results", heading_style))
    
    for i, result in enumerate(results):
        if "cost_estimate" in result:
            # Add result details
            result_data = [
                ['Image:', f"{result.get('imageIndex', i+1)} - {result.get('imageName', 'Unknown')}"],
                ['Damage Type:', result['damage']],
                ['Severity:', result['severity']],
                ['Repair Cost:', f"₹{result['cost_estimate']['Total Repair Cost']:,}"]
            ]
            
            result_table = Table(result_data, colWidths=[2*inch, 4*inch])
            result_table.setStyle(TableStyle([
                ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
                ('FONTSIZE', (0, 0), (-1, -1), 10),
                ('TEXTCOLOR', (0, 0), (0, -1), colors.HexColor('#7f8c8d')),
                ('TEXTCOLOR', (1, 0), (1, -1), colors.HexColor('#2c3e50')),
                ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
                ('BACKGROUND', (0, -1), (-1, -1), colors.HexColor('#e8f5e9')),
                ('FONTNAME', (0, -1), (-1, -1), 'Helvetica-Bold'),
                ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
                ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#ecf0f1')),
            ]))
            elements.append(result_table)
            
            # Try to add image if available
            try:
                if 'labeled_image' in result:
                    img_data = base64.b64decode(result['labeled_image'])
                    img_buffer = BytesIO(img_data)
                    pil_img = PILImage.open(img_buffer)
                    
                    # Save to temp buffer for reportlab
                    temp_img_buffer = BytesIO()
                    pil_img.save(temp_img_buffer, format='JPEG')
                    temp_img_buffer.seek(0)
                    
                    # Add image with limited size
                    img = PILImage.open(temp_img_buffer)
                    aspect = img.height / float(img.width)
                    img_width = 4.5*inch
                    img_height = img_width * aspect
                    
                    if img_height > 3*inch:
                        img_height = 3*inch
                        img_width = img_height / aspect
                    
                    from reportlab.platypus import Image as RLImage
                    rl_image = RLImage(temp_img_buffer, width=img_width, height=img_height)
                    elements.append(Spacer(1, 10))
                    elements.append(rl_image)
            except:
                pass
            
            elements.append(Spacer(1, 20))
    
    # Invoice section
    elements.append(Paragraph("Cost Breakdown & Invoice", heading_style))
    elements.append(Spacer(1, 10))
    
    # Calculate totals
    total_painting = sum(r['cost_estimate']['Painting Cost'] for r in results if 'cost_estimate' in r)
    total_labour = sum(r['cost_estimate']['Labour Cost'] for r in results if 'cost_estimate' in r)
    total_parts = sum(r['cost_estimate']['Part Price'] for r in results if 'cost_estimate' in r)
    total_components = sum(r['cost_estimate']['Component Price'] for r in results if 'cost_estimate' in r)
    total_internal = sum(r['cost_estimate']['Internal Damage Cost'] for r in results if 'cost_estimate' in r)
    subtotal = sum(r['cost_estimate']['Total Repair Cost'] for r in results if 'cost_estimate' in r)
    gst = subtotal * 0.18
    grand_total = subtotal + gst
    
    # Invoice table
    invoice_data = [
        ['Description', 'Qty', 'Amount (₹)'],
        ['Painting Cost', str(len(results)), f'{total_painting:,}'],
        ['Labour Cost', str(len(results)), f'{total_labour:,}'],
        ['Part Replacement', str(sum(1 for r in results if r['cost_estimate']['Part Price'] > 0)), f'{total_parts:,}'],
        ['Component Replacement', str(sum(1 for r in results if r['cost_estimate']['Component Price'] > 0)), f'{total_components:,}'],
        ['Internal Damage Repair', str(sum(1 for r in results if r['cost_estimate']['Internal Damage Cost'] > 0)), f'{total_internal:,}'],
        ['', 'Subtotal', f'₹{subtotal:,}'],
        ['', 'GST (18%)', f'₹{gst:,.2f}'],
        ['', 'TOTAL AMOUNT', f'₹{grand_total:,.2f}'],
    ]
    
    invoice_table = Table(invoice_data, colWidths=[3.5*inch, 1*inch, 1.5*inch])
    invoice_table.setStyle(TableStyle([
        # Header
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#2c3e50')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 11),
        ('ALIGN', (0, 0), (0, -1), 'LEFT'),
        ('ALIGN', (1, 0), (1, -1), 'CENTER'),
        ('ALIGN', (2, 0), (2, -1), 'RIGHT'),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 10),
        ('TOPPADDING', (0, 0), (-1, 0), 10),
        
        # Body
        ('FONTNAME', (0, 1), (-1, 5), 'Helvetica'),
        ('FONTSIZE', (0, 1), (-1, 5), 10),
        ('TEXTCOLOR', (0, 1), (-1, 5), colors.HexColor('#2c3e50')),
        ('GRID', (0, 0), (-1, 5), 0.5, colors.HexColor('#ecf0f1')),
        ('ROWBACKGROUNDS', (0, 1), (-1, 5), [colors.white, colors.HexColor('#f8f9fa')]),
        ('TOPPADDING', (0, 1), (-1, 5), 8),
        ('BOTTOMPADDING', (0, 1), (-1, 5), 8),
        
        # Subtotal
        ('FONTNAME', (0, 6), (-1, 6), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 6), (-1, 6), 10),
        ('BACKGROUND', (0, 6), (-1, 6), colors.HexColor('#f5f5f5')),
        ('TOPPADDING', (0, 6), (-1, 6), 8),
        ('BOTTOMPADDING', (0, 6), (-1, 6), 8),
        ('LINEABOVE', (0, 6), (-1, 6), 1, colors.HexColor('#bdc3c7')),
        
        # GST
        ('FONTNAME', (0, 7), (-1, 7), 'Helvetica'),
        ('FONTSIZE', (0, 7), (-1, 7), 10),
        ('BACKGROUND', (0, 7), (-1, 7), colors.HexColor('#f5f5f5')),
        ('TOPPADDING', (0, 7), (-1, 7), 8),
        ('BOTTOMPADDING', (0, 7), (-1, 7), 8),
        
        # Total
        ('BACKGROUND', (0, 8), (-1, 8), colors.HexColor('#4CAF50')),
        ('TEXTCOLOR', (0, 8), (-1, 8), colors.whitesmoke),
        ('FONTNAME', (0, 8), (-1, 8), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 8), (-1, 8), 12),
        ('TOPPADDING', (0, 8), (-1, 8), 12),
        ('BOTTOMPADDING', (0, 8), (-1, 8), 12),
    ]))
    
    elements.append(invoice_table)
    elements.append(Spacer(1, 20))
    
    # Footer note
    note_style = ParagraphStyle(
        'Note',
        parent=styles['Normal'],
        fontSize=9,
        textColor=colors.HexColor('#7f8c8d'),
        alignment=TA_CENTER
    )
    elements.append(Paragraph("<strong>Note:</strong> This is an estimated cost. Final charges may vary based on actual repair requirements.", note_style))
    
    doc.build(elements)
    buffer.seek(0)
    return buffer

# Route for uploading multiple images
@app.route('/upload', methods=['POST'])
def upload_images():
    if 'images' not in request.files:
        return jsonify({"error": "No images uploaded"}), 400

    files = request.files.getlist('images')
    car_model = request.form.get('carModel')

    if not files or not car_model:
        return jsonify({"error": "Please select a car model and upload images"}), 400

    results = []
    try:
        for file in files[:4]:  # Limit to 4 images
            npimg = np.frombuffer(file.read(), np.uint8)
            image = cv2.imdecode(npimg, cv2.IMREAD_COLOR)

            damage_results = damage_model.predict(source=image, imgsz=640, conf=0.5, save=False)
            severity_results = severity_model.predict(source=image, imgsz=640, conf=0.5, save=False)

            if len(damage_results[0].boxes.cls) > 0 and len(severity_results[0].boxes.cls) > 0:
                detected_damage = damage_model.names[int(damage_results[0].boxes.cls[0])]
                detected_severity = severity_model.names[int(severity_results[0].boxes.cls[0])]

                cost_estimate = estimate_damage_cost(car_model, detected_damage, detected_severity)

                labeled_image = image.copy()
                for box in damage_results[0].boxes.xyxy:
                    x1, y1, x2, y2 = map(int, box)
                    cv2.rectangle(labeled_image, (x1, y1), (x2, y2), (255, 0, 0), 2)
                    cv2.putText(labeled_image, detected_damage, (x1, y1 - 10), 
                                cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 0, 0), 2)

                _, buffer = cv2.imencode('.jpg', labeled_image)
                encoded_image = base64.b64encode(buffer).decode('utf-8')

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

# Route for generating and downloading bill
@app.route('/generate_bill', methods=['POST'])
def generate_bill():
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

# Route for fetching car models
@app.route('/car-models', methods=['GET'])
def get_car_models():
    return jsonify(car_models)

if __name__ == '__main__':
    app.run(debug=True, port=5000)
