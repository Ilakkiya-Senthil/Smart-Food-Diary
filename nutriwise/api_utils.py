import os
import requests
import logging

API_URL = "https://vision.foodvisor.io/api/1.0/en/analysis/"
API_KEY = 'TNWFnlBB.fgffWC7CvExZQrUvL7HiZfbfN3DrK3FM'
HEADERS = {"Authorization": f"Api-Key {API_KEY}"}

logger = logging.getLogger(__name__)

def analyze_food_image(image_path):
    """
    Sends an image to the Foodvisor API and retrieves the analysis data.
    """
    if not os.path.exists(image_path):
        return {"error": "Image file does not exist."}

    try:
        with open(image_path, "rb") as image:
            response = requests.post(API_URL, headers=HEADERS, files={"image": image})
            response.raise_for_status()
            return response.json()
    except requests.exceptions.RequestException as e:
        logger.error(f"API request failed: {e}")
        return {"error": f"Request failed with error: {str(e)}"}

def parse_analysis(data):
    """
    Parses the API response for food analysis.
    """
    if "error" in data:
        return None, data["error"]

    analysis = {
        "analysis_id": data.get("analysis_id", "N/A"),
        "items": []
    }

    for item in data.get("items", []):
        item_details = []
        for food in item.get("food", []):
            food_info = food.get("food_info", {})
            item_details.append({
                "name": food_info.get("display_name", "N/A"),
                "confidence": food.get("confidence", "N/A"),
                "grade": food_info.get("fv_grade", "N/A"),
                "quantity": food_info.get("quantity", "N/A"),
                "nutrition": food_info.get("nutrition", {}),
                "ingredients": [
                    {
                        "name": ing.get("food_info", {}).get("display_name", "N/A"),
                        "grade": ing.get("food_info", {}).get("fv_grade", "N/A"),
                        "quantity": ing.get("quantity", "N/A")
                    }
                    for ing in food.get("ingredients", [])
                ]
            })
        analysis["items"].append(item_details)

    return analysis, None

def print_analysis(data):
    """
    Prints a detailed analysis of the food items from the API response.
    """
    analysis, error = parse_analysis(data)
    if error:
        print(f"Error: {error}")
        return

    print("Analysis ID:", analysis["analysis_id"])
    print("\nDetected Food Items:\n")
    for item in analysis["items"]:
        for food in item:
            print("-" * 40)
            print(f"Food Name: {food['name']}")
            print(f"Confidence: {food['confidence']}")
            print(f"Nutrition Grade: {food['grade']}")
            print(f"Quantity (g): {food['quantity']}")
            print("\nNutrition Details (per 100g):")
            for key, value in food["nutrition"].items():
                print(f"  {key}: {value}")
            print("\nIngredients:")
            for ingredient in food["ingredients"]:
                print(f"  - {ingredient['name']} ({ingredient['grade']})")
                print(f"    Quantity: {ingredient['quantity']}g")
            print("-" * 40)
from .models import FoodAnalysis

def save_analysis_to_db(data, user):
    """
    Save the parsed analysis data into the database under the given user.
    """
    analysis, error = parse_analysis(data)
    if error:
        return {"error": error}

    for item in analysis["items"]:
        for food in item:
            FoodAnalysis.objects.create(
                user=user,
                analysis_id=analysis["analysis_id"],
                food_name=food["name"],
                confidence=food["confidence"],
                nutrition_grade=food["grade"],
                quantity=food["quantity"],
                nutrition_details=food["nutrition"],
                ingredients=food["ingredients"],
            )
    return {"success": "Analysis data saved to database."}

def handle_food_analysis(image_path, user):
    """
    Orchestrates the food analysis and saving to the database.
    """
    data = analyze_food_image(image_path)
    return save_analysis_to_db(data, user)
