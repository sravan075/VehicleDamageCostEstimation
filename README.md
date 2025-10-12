# 🚗 Vehicle Damage Cost Estimation - Backend

AI-powered vehicle damage detection and repair cost estimation system using YOLO deep learning models.

---

## 📋 What This Project Does

This Flask API provides:
- **Damage Detection**: Identifies damaged vehicle parts using YOLO
- **Severity Classification**: Determines damage severity level
- **Cost Estimation**: Calculates repair costs based on car model and damage
- **PDF Invoice Generation**: Creates professional repair estimates with images

---

## 🛠️ Tech Stack

- **Framework**: Flask 3.1.0
- **AI/ML**: 
  - Ultralytics YOLO (8.3.50)
  - PyTorch 2.5.1
  - TorchVision 0.20.1
  - OpenCV 4.10.0
- **PDF Generation**: ReportLab
- **Data Processing**: 
  - Pandas 2.2.3
  - NumPy 2.2.0
- **API**: Flask-CORS for frontend communication
- **Python Version**: 3.11+

---

## 🚀 Local Setup

### Prerequisites
- Python 3.11 or higher
- pip (Python package manager)
- Virtual environment (recommended)

### Installation Steps

1. **Clone the repository**
   ```bash
   git clone https://github.com/sravan075/VehicleDamageCostEstimation.git
   cd VehicleDamageCostEstimation
   ```

2. **Create and activate virtual environment**
   
   **Windows:**
   ```bash
   python -m venv costenv
   .\costenv\Scripts\activate
   ```
   
   **Linux/Mac:**
   ```bash
   python -m venv costenv
   source costenv/bin/activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Verify model files exist**
   - Ensure `model/damage.pt` exists
   - Ensure `model/severity.pt` exists
   - Ensure `price.csv` exists

5. **Run the application**
   ```bash
   python main.py
   ```

6. **Server will start at**: `http://localhost:5000`

---

## 📁 Project Structure

```
backend/
├── main.py                  # Main application (current)
├── app_organized.py         # Organized version (alternative)
├── config/                  # Configuration
│   └── settings.py          # Constants and settings
├── routes/                  # API routes
│   └── api_routes.py        # Endpoint definitions
├── services/                # Business logic
│   ├── damage_detection.py  # YOLO inference
│   ├── cost_estimation.py   # Cost calculations
│   └── pdf_generator.py     # PDF generation
├── utils/                   # Utilities
│   └── image_processing.py  # Image helpers
├── model/                   # YOLO models
│   ├── damage.pt
│   └── severity.pt
├── price.csv               # Parts pricing data
└── requirements.txt        # Dependencies
```

---

## 🔌 API Endpoints

### 1. Get Car Models
```http
GET /car-models
```
Returns list of supported car models.

**Response:**
```json
["Swift", "Baleno", "Brezza", ...]
```

---

### 2. Upload Images for Analysis
```http
POST /upload
Content-Type: multipart/form-data
```

**Parameters:**
- `images`: File[] (up to 4 images)
- `carModel`: string (selected car model)

**Response:**
```json
[
  {
    "damage": "Front-Bumper",
    "severity": "moderate-dent",
    "cost_estimate": {
      "Painting Cost": 3000,
      "Labour Cost": 5000,
      "Part Price": 0,
      "Component Price": 0,
      "Internal Damage Cost": 0,
      "Total Repair Cost": 8000
    },
    "labeled_image": "base64_encoded_image"
  }
]
```

---

### 3. Generate PDF Bill
```http
POST /generate_bill
Content-Type: application/json
```

**Body:**
```json
{
  "bill_data": "JSON string or array of results",
  "car_model": "Swift"
}
```

**Response:** PDF file download

---

## 💰 Cost Calculation

The system calculates costs based on:

1. **Painting Costs**: Per vehicle part
2. **Labour Costs**: Based on severity level
3. **Part Replacement**: For severe damage
4. **Component Costs**: Related parts affected
5. **Internal Damage**: Hidden structural damage

### Severity Levels
- Minor Scratch
- Moderate Scratch
- Severe Scratch
- Minor Dent
- Moderate Dent
- Severe Dent
- Moderate Broken
- Severe Broken

---

## 📊 Supported Car Models

The system supports multiple Maruti Suzuki models including:
- Swift, Swift Dzire
- Baleno
- Brezza
- Alto (800, K10)
- WagonR
- Ertiga
- And more...

*(Full list in `price.csv`)*

---

## 🔧 Configuration

### Model Paths
Update in `config/settings.py`:
```python
DAMAGE_MODEL_PATH = "model/damage.pt"
SEVERITY_MODEL_PATH = "model/severity.pt"
CSV_PATH = "price.csv"
```

### Cost Customization
Edit cost dictionaries in `config/settings.py`:
- `PAINTING_COSTS`
- `LABOUR_COSTS`
- `INTERNAL_DAMAGE_COSTS`

---

## 🧪 Testing

**Test the API:**
```bash
# Get car models
curl http://localhost:5000/car-models

# Upload image (PowerShell)
Invoke-WebRequest -Uri http://localhost:5000/upload -Method POST -Form @{carModel="Swift"; images=Get-Item "image.jpg"}
```

---

## 📝 Development

### Adding New Features

1. **New endpoint**: Add to `routes/api_routes.py`
2. **New business logic**: Add to `services/`
3. **New utilities**: Add to `utils/`
4. **New constants**: Add to `config/settings.py`

### Code Organization

- ✅ Modular structure for scalability
- ✅ Separation of concerns
- ✅ Easy to test individual modules
- ✅ Clean imports

---

## 🐛 Troubleshooting

**Port already in use:**
```bash
# Change port in main.py
app.run(debug=True, port=5001)
```

**Module not found:**
```bash
pip install -r requirements.txt
```

**Model not found:**
- Ensure `.pt` files are in `model/` directory

---

## 📄 License

[Add your license here]

---

## 👨‍💻 Author

**Sravan**  
GitHub: [@sravan075](https://github.com/sravan075)

---

## 🔗 Related

**Frontend Repository**: [VehicleDamageCostEstimation-Frontend](https://github.com/sravan075/VehicleDamageCostEstimation-Frontend)

---

## 📞 Support

For issues and questions, please open an issue on GitHub.
