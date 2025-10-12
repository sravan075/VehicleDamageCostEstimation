from flask import Flask, request, render_template, send_file
from ultralytics import YOLO
import cv2
import numpy as np
import base64
import pandas as pd
from io import BytesIO
from reportlab.lib.pagesizes import A4
from reportlab.platypus import (
    SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, 
    Image, PageBreak
)
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.lib.enums import TA_CENTER, TA_RIGHT
from datetime import datetime
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.enums import TA_CENTER


app = Flask(__name__)

# Path to the CSV file
csv_path = r"Z:\\Projects\\Main Project\\Project\\backend\\price.csv"
df = pd.read_csv(csv_path)
car_models = df['carmodel'].unique().tolist()

# Paths to YOLO models
damage_model_path = r"Z:\\Projects\\Main Project\\Project\\backend\\model\\damage.pt"
severity_model_path = r"Z:\\Projects\\Main Project\\Project\\backend\\model\\severity.pt"
damage_model = YOLO(damage_model_path)
severity_model = YOLO(severity_model_path)
# Define painting costs
painting_costs = {
    'Door': 4000, 'Front-Bumper': 3000, 'Front-fender': 1500, 'Rear-Bumper': 3000,
    'Rear-Fender': 1500, 'Rear-Trunk': 2000, 'bonnet-damage': 2000, 'doorouter-damage': 4000,
    'fender-damage': 1500, 'front-bumper-damage': 3000, 'rear-bumper-damage': 3000
}

# Define severity-based labor costs
labour_costs = {
    "minor-scratch": 2500, "moderate-scratch": 3000, "severe-scratch": 4000,
    "minor-dent": 4000, "moderate-dent": 5000, "severe-dent": 6000,
    "moderate-broken": 7000, "severe-broken": 8000
}

# Define additional repair material costs
repair_materials = {
    "paint": 0, "putty": 700, "primer": 500, "tinner": 300, "PDR": 1000
}

# Define internal damage costs
internal_damage_costs = {
    'Door': 2000, 'Front-Bumper': 6000, 'Rear-Bumper': 4000, 'Rear-Fender': 5000, 'Rear-Trunk': 3000,
    'doorouter-damage': 2000, 'fender-damage': 5000, 'front-bumper-damage': 6000, 'rear-bumper-damage': 4000, 'bonnet-damage': 6000
}

# Define component mappings
class_to_components = {
    'Door': ['Door', 'Door Handle', 'Door Handle Bracket', 'Door Hinge', 'Door Latch',
             'Door Lock', 'Door Seal', 'Door Trim Cap', 'Door Lock Cylinder', 'Door Lock Link',
             'Door Check Arm', 'Door Membrane'],
    'Front-Bumper': ['Front Bumper', 'Bumper Brackets', 'Bumper Trim'],
    'Front-fender': ['Fender', 'Fender Trim', 'Fender Bracket'],
    'Front-lamp-Damage': ['Headlight', 'Headlight Parts'],
    'Light': ['Headlight', 'Rear Lamp', 'Rear Light Parts'],
    'Rear-Bumper': ['Rear Bumper', 'Bumper Brackets', 'Bumper Trim'],
    'Rear-Fender': ['Rear Fender', 'Fender Trim', 'Fender Bracket'],
    'Rear-Trunk': ['Boot'],
    'Rear-Windshield': ['Rear Windshield', 'Windshield Seal'],
    'Rear-lamp-Damage': ['Rear Lamp', 'Rear Light Parts'],
    'Side-Screen': ['Window', 'Window Seal'],
    'Sidemirror-Damage': ['Outside Mirror', 'Mirror Glass', 'Mirror Sash', 'Cover Outside Mirror'],
    'Windscreen-Damage': ['Front Windshield', 'Windshield Seal'],
    'bonnet-damage': ['Bonnet', 'Bonnet Lid', 'Bonnet Hinge', 'Bonnet Lock', 'Bonnet Seal',
                      'Bonnet Silencing Material', 'Bonnet Stay Rod Holder', 'Bonnet Strut',
                      'Bonnet Support Bracket', 'Bonnet Trim', 'Bonnet Hinge Cover'],
    'doorouter-damage': ['Door', 'Door Handle', 'Door Handle Bracket', 'Door Handle Cap',
                         'Door Hinge', 'Door Latch', 'Door Lock', 'Door Seal', 'Door Trim Cap',
                         'Door Lock Cylinder', 'Door Lock Link', 'Door Check Arm', 'Door Membrane'],
    'fender-damage': ['Fender', 'Fender Trim', 'Fender Bracket'],
    'front-bumper-damage': ['Front Bumper', 'Bumper Brackets', 'Bumper Trim'],
    'quarterpanel-damage': ['Quarter Panel'],
    'rear-bumper-damage': ['Rear Bumper', 'Bumper Brackets', 'Bumper Trim']
}

# Cost estimation function
def estimate_damage_cost(car_model, damaged_part, severity):
    # Handle mapping for fender and door components
    if damaged_part == "fender-damage":
        damaged_part = "Front-fender"
    if damaged_part == "doorouter-damage":
        damaged_part = "Door"

    # Painting and labor costs
    paint_cost = painting_costs.get(damaged_part, 0)
    labour_cost = labour_costs.get(severity, 0)

    primary_part_price = 0
    component_price = 0
    part_list = []
    component_list = []

    # Get related components based on damaged part
    related_components = class_to_components.get(damaged_part, [])

    if related_components:
        # Filter data for matching car model and related components
        component_df = df[(df["carmodel"] == car_model) & (df["component"].isin(related_components))]

        if not component_df.empty:
            # Get the most expensive part as primary part
            max_price_row = component_df.loc[component_df["price"].idxmax()]
            primary_part_price = max_price_row["price"]
            main_part_name = max_price_row["component"]

            # Exclude main part to calculate component price
            filtered_component_df = component_df[component_df["component"] != main_part_name]

            # Prepare part list
            part_list = [{"title": max_price_row["title"], "price": primary_part_price}]

            # For more severe damages, calculate component prices
            if severity in ["moderate-broken", "severe-dent", "severe-broken"]:
                component_price = filtered_component_df["price"].sum()
                component_list = filtered_component_df[["title", "price"]].to_dict(orient="records")

    # Reset prices for less severe damages
    if severity not in ["moderate-broken", "severe-dent", "severe-broken"]:
        primary_part_price = 0
        part_list = []
        component_price = 0
        component_list = []

    # Calculate additional cost based on severity
    additional_cost = 0
    if severity == "minor-scratch":
        additional_cost += paint_cost
    elif severity == "moderate-scratch":
        additional_cost += paint_cost
    elif severity == "severe-scratch":
        additional_cost += paint_cost
    elif severity == "minor-dent":
        additional_cost += 0
    elif severity == "moderate-dent":
        additional_cost += paint_cost
    elif severity == "severe-dent":
        additional_cost += primary_part_price + paint_cost
    elif severity == "moderate-broken":
        additional_cost += paint_cost + primary_part_price + component_price
    elif severity == "severe-broken":
        additional_cost += (
            primary_part_price + component_price + paint_cost + 
            internal_damage_costs.get(damaged_part, 0)
        )

    # Total cost calculation
    total_cost = labour_cost + additional_cost

    # Detailed cost breakdown
    return {
        "Painting Cost": paint_cost,
        "Labour Cost": labour_cost,
        "Part Price": primary_part_price if severity in ["moderate-broken", "severe-dent", "severe-broken"] else 0,
        "Parts": part_list if severity in ["moderate-broken", "severe-dent", "severe-broken"] else [],
        "Component Price": component_price if severity in ["moderate-broken", "severe-broken"] else 0,
        "Components": component_list if severity in ["moderate-broken", "severe-broken"] else [],
        "Internal Damage Cost": internal_damage_costs.get(damaged_part, 0) if severity == "severe-broken" else 0,
        "Total Repair Cost": total_cost,
    }



def generate_detailed_bill(results, car_model):
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4)
    styles = getSampleStyleSheet()

    # Custom styles
    title_style = ParagraphStyle(
        'Title',
        parent=styles['Title'],
        fontSize=16,
        textColor=colors.HexColor('#2C3E50'),
        alignment=TA_CENTER
    )
    subtitle_style = ParagraphStyle(
        'Subtitle',
        parent=styles['Normal'],
        fontSize=12,
        textColor=colors.HexColor('#34495E'),
        alignment=TA_CENTER
    )

    # Prepare content
    content = []

    # Title and Header
    content.append(Paragraph("Vehicle Damage Repair Estimate", title_style))
    content.append(Paragraph(f"Car Model: {car_model}", subtitle_style))
    content.append(Paragraph(f"Date: {datetime.now().strftime('%d %B %Y')}", subtitle_style))
    content.append(Spacer(1, 12))

    # Aggregators for total costs
    total_parts_price = 0
    total_labour_cost = 0
    total_painting_cost = 0
    total_component_price = 0
    total_internal_damage_cost = 0

    # Parts data table
    parts_data = [['Title', 'Component', 'Price (₹)']]

    for result in results:
        if 'cost_estimate' not in result:
            continue

        cost_estimate = result['cost_estimate']
        
        # Add parts
        if cost_estimate.get('Parts'):
            for part in cost_estimate['Parts']:
                parts_data.append([
                    part['title'], 
                    'Primary Part',
                    part['price']
                ])
                total_parts_price += part['price']

        # Add components
        if cost_estimate.get('Components'):
            for component in cost_estimate['Components']:
                parts_data.append([
                    component['title'], 
                    'Additional Component',
                    component['price']
                ])
                total_component_price += component['price']

        # Accumulate other costs
        total_labour_cost += cost_estimate.get('Labour Cost', 0)
        total_painting_cost += cost_estimate.get('Painting Cost', 0)
        total_internal_damage_cost += cost_estimate.get('Internal Damage Cost', 0)

    # Create parts table
    parts_table = Table(parts_data, colWidths=[250, 150, 100])
    parts_table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#3498DB')),
        ('TEXTCOLOR', (0,0), (-1,0), colors.whitesmoke),
        ('ALIGN', (0,0), (-1,-1), 'CENTER'),
        ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
        ('FONTSIZE', (0,0), (-1,0), 10),
        ('BOTTOMPADDING', (0,0), (-1,0), 8),
        ('GRID', (0,0), (-1,-1), 1, colors.black)
    ]))

    content.append(parts_table)
    content.append(Spacer(1, 12))

    # Final Cost Summary
    summary_data = [
        ['Cost Category', 'Amount (₹)'],
        ['Total Parts Price', total_parts_price],
        ['Total Component Price', total_component_price],
        ['Total Labour Cost', total_labour_cost],
        ['Total Painting Cost', total_painting_cost],
        ['Total Internal Damage Cost', total_internal_damage_cost],
        ['Grand Total', total_parts_price + total_component_price + total_labour_cost + 
                        total_painting_cost + total_internal_damage_cost]
    ]

    summary_table = Table(summary_data, colWidths=[300, 200])
    summary_table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#3498DB')),
        ('TEXTCOLOR', (0,0), (-1,0), colors.whitesmoke),
        ('ALIGN', (0,0), (-1,-1), 'CENTER'),
        ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
        ('FONTSIZE', (0,0), (-1,0), 10),
        ('BOTTOMPADDING', (0,0), (-1,0), 8),
        ('BACKGROUND', (0,-1), (-1,-1), colors.HexColor('#3498DB')),
        ('GRID', (0,0), (-1,-1), 1, colors.black)
    ]))

    content.append(Paragraph("Cost Summary", subtitle_style))
    content.append(Spacer(1, 12))
    content.append(summary_table)

    # Build PDF
    doc.build(content)
    buffer.seek(0)
    return buffer


@app.route('/', methods=['GET', 'POST'])
def home():
    if request.method == 'POST':
        selected_car_model = request.form.get('carModel')
        files = request.files.getlist('images')

        if not files or not selected_car_model:
            return render_template('index.html', car_models=car_models, error="Please select a car model and upload at least one image.")

        total_cost = 0
        results = []

        for file in files:
            try:
                npimg = np.frombuffer(file.read(), np.uint8)
                image = cv2.imdecode(npimg, cv2.IMREAD_COLOR)

                damage_results = damage_model.predict(source=image, imgsz=640, conf=0.5, save=False)
                severity_results = severity_model.predict(source=image, imgsz=640, conf=0.5, save=False)

                if len(damage_results[0].boxes.cls) > 0 and len(severity_results[0].boxes.cls) > 0:
                    detected_damage = damage_model.names[int(damage_results[0].boxes.cls[0])]
                    detected_severity = severity_model.names[int(severity_results[0].boxes.cls[0])]

                    cost_estimate = estimate_damage_cost(selected_car_model, detected_damage, detected_severity)
                    total_repair_cost = cost_estimate["Total Repair Cost"]
                    total_cost += cost_estimate["Total Repair Cost"]

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
                    results.append({"error": "Oops! No damage detected. Try uploading a clearer image!"})

            except Exception as e:
                results.append({"error": f"Error processing image: {str(e)}"})

        return render_template('index.html', car_models=car_models, results=results if results else [], total_cost=total_cost)


    return render_template('index.html', car_models=car_models)

@app.route('/generate_bill', methods=['POST'])
@app.route('/generate_bill', methods=['POST'])
def generate_bill():
    bill_data = request.form.get('bill_data')
    car_model = request.form.get('car_model')
    import json
    
    # Parse the bill data
    try:
        results = json.loads(bill_data)
        
        # Sanitize results to remove non-serializable elements
        sanitized_results = []
        for result in results:
            sanitized_result = result.copy()
            
            # Remove any non-serializable cost estimate components
            if 'cost_estimate' in sanitized_result:
                sanitized_estimate = sanitized_result['cost_estimate'].copy()
                
                # Convert Parts and Components to basic dictionaries
                if 'Parts' in sanitized_estimate:
                    sanitized_estimate['Parts'] = [
                        {k: v for k, v in part.items() if isinstance(v, (str, int, float))}
                        for part in sanitized_estimate['Parts']
                    ]
                
                if 'Components' in sanitized_estimate:
                    sanitized_estimate['Components'] = [
                        {k: v for k, v in component.items() if isinstance(v, (str, int, float))}
                        for component in sanitized_estimate['Components']
                    ]
                
                sanitized_result['cost_estimate'] = sanitized_estimate
            
            sanitized_results.append(sanitized_result)
        
        # Generate the bill
        bill_buffer = generate_detailed_bill(sanitized_results, car_model)
        
        # Send the PDF as a file
        return send_file(
            bill_buffer, 
            as_attachment=True, 
            download_name='repair_estimate_bill.pdf', 
            mimetype='application/pdf'
        )
    
    except json.JSONDecodeError as e:
        return f"JSON Decode Error: {str(e)}", 400
    except Exception as e:
        return f"Error generating bill: {str(e)}", 500

if __name__ == '__main__':
    app.run(debug=True)