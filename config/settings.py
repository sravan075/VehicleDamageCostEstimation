"""
Configuration settings for the application
"""
import os

# Base directory
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# Paths
CSV_PATH = os.path.join(BASE_DIR, "price.csv")
DAMAGE_MODEL_PATH = os.path.join(BASE_DIR, "model", "damage.pt")
SEVERITY_MODEL_PATH = os.path.join(BASE_DIR, "model", "severity.pt")

# Cost dictionaries
PAINTING_COSTS = {
    'Door': 4000, 'Front-Bumper': 3000, 'Front-fender': 1500, 'Rear-Bumper': 3000,
    'Rear-Fender': 1500, 'Rear-Trunk': 2000, 'bonnet-damage': 2000, 'doorouter-damage': 4000,
    'fender-damage': 1500, 'front-bumper-damage': 3000, 'rear-bumper-damage': 3000
}

LABOUR_COSTS = {
    "minor-scratch": 2500, "moderate-scratch": 3000, "severe-scratch": 4000,
    "minor-dent": 4000, "moderate-dent": 5000, "severe-dent": 6000,
    "moderate-broken": 7000, "severe-broken": 8000
}

INTERNAL_DAMAGE_COSTS = {
    'Door': 2000, 'Front-Bumper': 6000, 'Rear-Bumper': 4000, 'Rear-Fender': 5000, 
    'Rear-Trunk': 3000, 'doorouter-damage': 2000, 'fender-damage': 5000, 
    'front-bumper-damage': 6000, 'rear-bumper-damage': 4000, 'bonnet-damage': 6000
}

CLASS_TO_COMPONENTS = {
    'Door': ['Door', 'Door Handle', 'Door Handle Bracket', 'Door Hinge', 'Door Latch',
             'Door Lock', 'Door Seal', 'Door Trim Cap', 'Door Lock Cylinder', 'Door Lock Link',
             'Door Check Arm', 'Door Membrane'],
    'Front-Bumper': ['Front Bumper', 'Bumper Brackets', 'Bumper Trim'],
    'Rear-Bumper': ['Rear Bumper', 'Bumper Brackets', 'Bumper Trim'],
    'Front-fender': ['Fender', 'Fender Trim', 'Fender Bracket'],
    'Rear-Fender': ['Rear Fender', 'Fender Trim', 'Fender Bracket'],
    'bonnet-damage': ['Bonnet', 'Bonnet Lid', 'Bonnet Hinge', 'Bonnet Lock', 'Bonnet Seal'],
    'doorouter-damage': ['Door', 'Door Handle', 'Door Handle Bracket', 'Door Handle Cap'],
    'fender-damage': ['Fender', 'Fender Trim', 'Fender Bracket'],
    'front-bumper-damage': ['Front Bumper', 'Bumper Brackets', 'Bumper Trim'],
    'rear-bumper-damage': ['Rear Bumper', 'Bumper Brackets', 'Bumper Trim']
}

