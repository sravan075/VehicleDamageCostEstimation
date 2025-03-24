from flask import Flask, request, render_template
from ultralytics import YOLO
import cv2
import numpy as np
import base64
import pandas as pd

app = Flask(__name__)

# Path to the CSV file
csv_path = "Z:\\Projects\\Main Project\\Project\\YoloV8\\price-dataset\\cleaned_cars.csv"
df = pd.read_csv(csv_path)
car_models = df['carmodel'].unique().tolist()

# Paths to YOLO models
damage_model_path = r"Z:\\Projects\\Main Project\\Project\\YoloV8\\trained-weights\\damage-classification-weights-v1\\runs\\detect\\train\\weights\\best.pt"
severity_model_path = r"Z:\\Projects\\Main Project\\Project\\YoloV8\\trained-weights\\severity-classification-weights\\content\\runs\\detect\\train\\weights\\best.pt"
damage_model = YOLO(damage_model_path)
severity_model = YOLO(severity_model_path)

# Define painting costs
painting_costs = {
    'Door': 4000, 'Front-Bumper': 3000, 'Front-fender': 1500, 'Rear-Bumper': 3000,
    'Rear-Fender': 1500, 'Rear-Trunk': 2000, 'bonnet-damage': 2000, 'doorouter-damage': 4000,
    'fender-damage': 1500, 'front-bumper-damage': 3000, 'rear-bumper-damage': 3000
}

# Define severity-based labor costs and required procedures
severity_costs = {
    "minor-scratch": {
        "labour": 2500, 
        "additions": ["paint", "spot_putty"],
        "description": "Spot putty application, sanding, and paint job"
    },
    "moderate-scratch": {
        "labour": 3000, 
        "additions": ["paint", "spot_putty", "primer", "tinner"],
        "description": "Deeper scratch repair with putty, primer, tinner and paint"
    },
    "severe-scratch": {
        "labour": 4000, 
        "additions": ["paint", "spot_putty", "primer", "tinner"],
        "description": "Extensive scratch repair with advanced putty work, primer, tinner and paint"
    },
    "minor-dent": {
        "labour": 4000, 
        "additions": ["PDR"],
        "description": "Paintless Dent Repair (PDR) technique"
    },
    "moderate-dent": {
        "labour": 5000, 
        "additions": ["paint", "spot_putty", "PDR"],
        "description": "Dent repair with putty application and paint"
    },
    "severe-dent": {
        "labour": 6000, 
        "additions": ["paint", "part_price"],
        "description": "Component replacement due to severe dent damage"
    },
    "moderate-broken": {
        "labour": 7000, 
        "additions": ["paint", "part_price", "component_price"],
        "description": "Part and related component replacement with paint job"
    },
    "severe-broken": {
        "labour": 8000, 
        "additions": ["paint", "part_price", "component_price", "internal_damage"],
        "description": "Complete part replacement, possible interior/structural damage repair"
    }
}

# Miscellaneous costs
misc_costs = {
    "spot_putty": 500,
    "primer": 500,
    "tinner": 300,
    "PDR": 1000,
    "internal_damage": 5000  # Estimate for potential interior/structural damage
}

# Mapping class names to primary parts
primary_parts_map = {
    'Door': 'Door',
    'Front-Bumper': 'Front Bumper',
    'Front-fender': 'Fender',
    'Front-lamp-Damage': 'Headlight',
    'Light': 'Headlight',
    'Rear-Bumper': 'Rear Bumper',
    'Rear-Fender': 'Rear Fender',
    'Rear-Trunk': 'Boot',
    'Rear-Windshield': 'Rear Windshield',
    'Rear-lamp-Damage': 'Rear Lamp',
    'Side-Screen': 'Window',
    'Sidemirror-Damage': 'Outside Mirror',
    'Windscreen-Damage': 'Front Windshield',
    'bonnet-damage': 'Bonnet',
    'doorouter-damage': 'Door',
    'fender-damage': 'Fender',
    'front-bumper-damage': 'Front Bumper',
    'quarterpanel-damage': 'Quarter Panel',
    'rear-bumper-damage': 'Rear Bumper'
}

# Mapping class names to related components
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
    # Get repair procedure based on severity
    repair_info = severity_costs.get(severity, {"labour": 0, "additions": [], "description": "Basic repair"})
    
    # Initialize cost breakdown dictionary
    cost_breakdown = {
        "Repair Description": repair_info["description"],
        "Labour Cost": repair_info["labour"],
        "Painting Cost": 0,
        "Miscellaneous Costs": [],
        "Part Price": 0,
        "Parts": [],
        "Component Price": 0,
        "Components": [],
        "Total Repair Cost": repair_info["labour"]  # Start with labour cost
    }
    
    # Add painting cost if required
    if "paint" in repair_info["additions"]:
        cost_breakdown["Painting Cost"] = painting_costs.get(damaged_part, 0)
        cost_breakdown["Total Repair Cost"] += cost_breakdown["Painting Cost"]
    
    # Add miscellaneous costs
    misc_total = 0
    for addition in repair_info["additions"]:
        if addition in misc_costs:
            misc_item = {"title": addition.replace("_", " ").title(), "price": misc_costs[addition]}
            cost_breakdown["Miscellaneous Costs"].append(misc_item)
            misc_total += misc_costs[addition]
            cost_breakdown["Total Repair Cost"] += misc_costs[addition]
    
    # Get primary part name
    primary_part = primary_parts_map.get(damaged_part, damaged_part)
    
    # Look up part in database
    part_df = df[(df["carmodel"] == car_model) & (df["component"] == primary_part)]
    
    # If no exact match, try partial match
    if part_df.empty:
        main_part_name = damaged_part.split('-')[0]  # Extract main part name
        part_df = df[(df["carmodel"] == car_model) & 
                     (df["component"].str.contains(main_part_name, case=False, na=False))]
    
    # Calculate Part Price and extract titles if needed
    if "part_price" in repair_info["additions"] or severity in ["severe-dent", "moderate-broken", "severe-broken"]:
        cost_breakdown["Part Price"] = part_df["price"].sum()
        cost_breakdown["Parts"] = part_df[["title", "price"]].to_dict(orient="records")
        cost_breakdown["Total Repair Cost"] += cost_breakdown["Part Price"]
    
    # Calculate Component Price if needed
    if "component_price" in repair_info["additions"] or severity in ["moderate-broken", "severe-broken"]:
        # Find related components
        component_df = df[(df["carmodel"] == car_model) & 
                         (df["component"].str.contains(damaged_part.split('-')[0], case=False, na=False)) & 
                         (~df["component"].isin(part_df["component"]))]
        
        cost_breakdown["Component Price"] = component_df["price"].sum()
        cost_breakdown["Components"] = component_df[["title", "price"]].to_dict(orient="records")
        cost_breakdown["Total Repair Cost"] += cost_breakdown["Component Price"]
    
    return cost_breakdown

@app.route('/', methods=['GET', 'POST'])
def home():
    if request.method == 'POST':
        file = request.files.get('image')
        selected_car_model = request.form.get('carModel')
        
        # Debug prints
        print(f"Selected car model: {selected_car_model}")
        print(f"File received: {file.filename if file else 'None'}")
        
        if not file or not selected_car_model:
            return render_template('index.html', car_models=car_models, error="Please select both a car model and an image")

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
                
                print(f"Detected damage: {detected_damage}")
                print(f"Detected severity: {detected_severity}")
                
                # Get highest confidence detections
                damage_confidence = float(damage_results[0].boxes.conf[0])
                severity_confidence = float(severity_results[0].boxes.conf[0])
                
                # Calculate cost estimate
                cost_estimate = estimate_damage_cost(selected_car_model, detected_damage, detected_severity)
                
                # Add detection confidence to the cost estimate
                cost_estimate["Detection Confidence"] = {
                    "Damage": f"{damage_confidence:.2%}",
                    "Severity": f"{severity_confidence:.2%}"
                }
                
                # Draw bounding boxes for damage
                damage_image = image.copy()
                for result in damage_results:
                    for box, conf in zip(result.boxes.xyxy, result.boxes.conf):
                        x1, y1, x2, y2 = map(int, box)
                        cv2.rectangle(damage_image, (x1, y1), (x2, y2), (255, 0, 0), 2)
                        cv2.putText(damage_image, f"{detected_damage} ({conf:.2f})", (x1, y1-10), 
                                   cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 0, 0), 2)
                
                # Draw bounding boxes for severity
                severity_image = image.copy()
                for result in severity_results:
                    for box, conf in zip(result.boxes.xyxy, result.boxes.conf):
                        x1, y1, x2, y2 = map(int, box)
                        cv2.rectangle(severity_image, (x1, y1), (x2, y2), (0, 0, 255), 2)
                        cv2.putText(severity_image, f"{detected_severity} ({conf:.2f})", (x1, y1-10), 
                                   cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 255), 2)
                
                # Convert labeled images to base64
                _, damage_buffer = cv2.imencode('.jpg', damage_image)
                damage_encoded = base64.b64encode(damage_buffer).decode('utf-8')
                
                _, severity_buffer = cv2.imencode('.jpg', severity_image)
                severity_encoded = base64.b64encode(severity_buffer).decode('utf-8')
                
                # Create variables that match your template
                processed_images = {
                    'damage': damage_encoded,
                    'severity': severity_encoded
                }
                
                # Create class names that match your template expectations
                damage_classes = [detected_damage]
                damage_colors = {detected_damage: "(255,0,0)"}
                
                severity_classes = {0: detected_severity}
                severity_colors = {0: "(0,0,255)"}
                
                return render_template(
                    'index.html', car_models=car_models,
                    detected_damage=detected_damage, detected_severity=detected_severity,
                    cost_estimate=cost_estimate, labeled_image=damage_encoded,
                    processed_images=processed_images,
                    damage_classes=damage_classes, damage_colors=damage_colors,
                    severity_classes=severity_classes, severity_colors=severity_colors
                )
            else:
                return render_template('index.html', car_models=car_models, 
                                      error="No damage or severity detected in the image. Please try another image.")
        except Exception as e:
            print(f"Error during processing: {e}")
            return render_template('index.html', car_models=car_models, 
                                  error=f"Error processing image: {str(e)}")
    
    return render_template('index.html', car_models=car_models)

if __name__ == '__main__':
    app.run(debug=True)