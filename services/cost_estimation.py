"""
Cost estimation service
"""
import pandas as pd
from config.settings import CSV_PATH, PAINTING_COSTS, LABOUR_COSTS, INTERNAL_DAMAGE_COSTS, CLASS_TO_COMPONENTS

# Load data
df = pd.read_csv(CSV_PATH)

def estimate_damage_cost(car_model, damaged_part, severity):
    """
    Estimate the cost of damage repair
    
    Args:
        car_model: str, the car model
        damaged_part: str, the damaged part
        severity: str, the severity level
        
    Returns:
        dict: cost breakdown
    """
    # Handle mapping for fender and door components
    if damaged_part == "fender-damage":
        damaged_part = "Front-fender"
    if damaged_part == "doorouter-damage":
        damaged_part = "Door"

    paint_cost = PAINTING_COSTS.get(damaged_part, 0)
    labour_cost = LABOUR_COSTS.get(severity, 0)

    primary_part_price = 0
    component_price = 0
    part_list = []
    component_list = []

    related_components = CLASS_TO_COMPONENTS.get(damaged_part, [])
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
        additional_cost += primary_part_price + component_price + paint_cost + INTERNAL_DAMAGE_COSTS.get(damaged_part, 0)

    total_cost = labour_cost + additional_cost

    return {
        "Painting Cost": paint_cost,
        "Labour Cost": labour_cost,
        "Part Price": primary_part_price,
        "Parts": part_list,
        "Component Price": component_price,
        "Components": component_list,
        "Internal Damage Cost": INTERNAL_DAMAGE_COSTS.get(damaged_part, 0) if severity == "severe-broken" else 0,
        "Total Repair Cost": total_cost,
    }

def get_car_models():
    """Get list of unique car models"""
    return df['carmodel'].unique().tolist()

