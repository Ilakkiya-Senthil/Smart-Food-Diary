import requests

API_URL = "https://vision.foodvisor.io/api/1.0/en/analysis/"
API_KEY = "rLCchLLj.4rH9fCFxYTuPFiUkZAVyX48wlST1EbQs"
HEADERS = {"Authorization": f"Api-Key {API_KEY}"}


def analyze_food_image(image_path):
    """
    Sends an image to the Foodvisor API and retrieves the analysis data.

    Args:
        image_path (str): The path to the image file to analyze.

    Returns:
        dict: The parsed JSON response from the API or an error message.
    """
    try:
        with open(image_path, "rb") as image:
            response = requests.post(API_URL, headers=HEADERS, files={"image": image})
            response.raise_for_status()
            return response.json()
    except requests.exceptions.RequestException as e:
        return {"error": str(e)}


def print_analysis(data):
    """
    Prints a detailed analysis of the food items from the API response.

    Args:
        data (dict): The JSON response from the Foodvisor API.
    """
    if "error" in data:
        print(f"Error: {data['error']}")
        return

    print("Analysis ID:", data.get("analysis_id", "N/A"))
    print("\nDetected Food Items:\n")
    for item in data.get("items", []):
        for food in item.get("food", []):
            print("-" * 40)
            food_info = food.get("food_info", {})
            print(f"Food Name: {food_info.get('display_name', 'N/A')}")
            print(f"Confidence: {food.get('confidence', 'N/A')}")
            print(f"Nutrition Grade: {food_info.get('fv_grade', 'N/A')}")
            print(f"Quantity (g): {food_info.get('quantity', 'N/A')}")
            print("\nNutrition Details (per 100g):")
            nutrition = food_info.get("nutrition", {})
            for key, value in nutrition.items():
                if value is not None:
                    print(f"  {key}: {value}")
            print("\nIngredients:")
            for ingredient in food.get("ingredients", []):
                ing_info = ingredient.get("food_info", {})
                print(f"  - {ing_info.get('display_name', 'N/A')} ({ing_info.get('fv_grade', 'N/A')})")
                print(f"    Quantity: {ingredient.get('quantity', 'N/A')}g")
            print("-" * 40)
