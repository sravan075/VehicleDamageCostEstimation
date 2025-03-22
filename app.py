from flask import Flask, request, render_template
from ultralytics import YOLO
import cv2
import numpy as np
import base64

# Initialize Flask app
app = Flask(__name__)

# Paths to the trained YOLO models
damage_model_path = r"Z:\Projects\Main Project\Project\Final Version\model\damage.pt"
severity_model_path = r"Z:\Projects\Main Project\Project\Final Version\model\severity.pt"

# Load both YOLO models
print("Loading YOLO models...")
damage_model = YOLO(damage_model_path)
severity_model = YOLO(severity_model_path)

# Updated damage colors based on actual model classes
damage_colors = {
    'Door': (255, 0, 0),                 # Blue
    'Front-Bumper': (0, 255, 0),         # Green
    'Front-fender': (0, 0, 255),         # Red
    'Front-lamp-Damage': (255, 255, 0),  # Yellow
    'Light': (255, 0, 255),              # Magenta
    'Rear-Bumper': (0, 255, 255),        # Cyan
    'Rear-Fender': (128, 0, 0),          # Maroon
    'Rear-Trunk': (0, 128, 0),           # Dark Green
    'Rear-Windshield': (0, 0, 128),      # Navy
    'Rear-lamp-Damage': (255, 165, 0),   # Orange
    'Side-Screen': (255, 105, 180),      # Hot Pink
    'Sidemirror-Damage': (0, 255, 127),  # Spring Green
    'Windscreen-Damage': (75, 0, 130),   # Indigo
    'bonnet-damage': (34, 139, 34),      # Forest Green
    'doorouter-damage': (70, 130, 180),  # Steel Blue
    'fender-damage': (255, 165, 0),      # Orange
    'front-bumper-damage': (255, 69, 0), # Red-Orange
    'quarterpanel-damage': (255, 20, 147),  # Deep Pink
    'rear-bumper-damage': (138, 43, 226),  # Blue Violet
}

# Define fixed colors for severity classes
severity_colors = {
    0: (255, 102, 102),  # Light Red - Minor-Dent
    1: (255, 178, 102),  # Light Orange - Minor-Scratch
    2: (255, 255, 102),  # Light Yellow - Moderate-Broken
    3: (178, 255, 102),  # Light Green - Moderate-Dent
    4: (102, 255, 102),  # Lime Green - Moderate-Scratch
    5: (102, 255, 178),  # Turquoise - Severe-Broken
    6: (102, 255, 255),  # Light Blue - Severe-Dent
    7: (102, 178, 255),  # Sky Blue - Severe-Scratch
    8: (200, 200, 200),  # Gray - Background
}

@app.route('/', methods=['GET', 'POST'])
def home():
    """Handle both GET and POST requests for the home page"""
    if request.method == 'POST':
        if 'image' not in request.files:
            return render_template('index.html')
        
        file = request.files['image']
        if file.filename == '':
            return render_template('index.html')
        
        # Read the image
        npimg = np.frombuffer(file.read(), np.uint8)
        image = cv2.imdecode(npimg, cv2.IMREAD_COLOR)
        
        # Create copies for both models
        damage_image = image.copy()
        severity_image = image.copy()
        
        # Process with damage model
        damage_results = damage_model.predict(source=damage_image, imgsz=640, conf=0.5, save=False)
        detected_damage_classes = set()
        
        for result in damage_results:
            for box, cls, conf in zip(result.boxes.xyxy, result.boxes.cls, result.boxes.conf):
                x1, y1, x2, y2 = map(int, box)
                class_name = damage_model.names[int(cls)]
                if class_name in damage_colors:
                    detected_damage_classes.add(class_name)
                    color = damage_colors[class_name]
                    label = f"{class_name}: {conf:.2f}"
                    cv2.rectangle(damage_image, (x1, y1), (x2, y2), color, 2)
                    cv2.putText(damage_image, label, (x1, y1 - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 2)

        # Process with severity model
        severity_results = severity_model.predict(source=severity_image, imgsz=640, conf=0.5, save=False)
        
        for result in severity_results:
            for box, cls, conf in zip(result.boxes.xyxy, result.boxes.cls, result.boxes.conf):
                x1, y1, x2, y2 = map(int, box)
                class_id = int(cls)
                if class_id in severity_colors:
                    color = severity_colors[class_id]
                    label = f"{severity_model.names[class_id]}: {conf:.2f}"
                    cv2.rectangle(severity_image, (x1, y1), (x2, y2), color, 2)
                    cv2.putText(severity_image, label, (x1, y1 - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 2)

        # Encode both images to base64
        _, damage_buffer = cv2.imencode('.jpg', damage_image)
        _, severity_buffer = cv2.imencode('.jpg', severity_image)
        
        processed_images = {
            'damage': base64.b64encode(damage_buffer).decode('utf-8'),
            'severity': base64.b64encode(severity_buffer).decode('utf-8')
        }

        # Create a dictionary mapping class names to colors for display
        damage_classes = {name: name for name in damage_colors.keys()}
        
        return render_template(
            'index.html',
            processed_images=processed_images,
            damage_classes=damage_classes,
            severity_classes=severity_model.names,
            damage_colors=damage_colors,
            severity_colors=severity_colors
        )

    return render_template(
        'index.html',
        processed_images=None,
        damage_classes=None,
        severity_classes=None,
        damage_colors=damage_colors,
        severity_colors=severity_colors
    )

if __name__ == '__main__':
    print("\nDamage Model Classes:")
    for name in damage_colors.keys():
        print(f"Class: {name}")
    
    print("\nSeverity Model Classes:")
    for idx, name in severity_model.names.items():
        print(f"{idx}: {name}")
        
    app.run(debug=True)