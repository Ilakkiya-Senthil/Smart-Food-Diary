
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .models import UserProfile, FoodDiaryEntry
from .forms import FoodDiaryEntryForm
from .forms import UserProfileForm
from .api_utils import analyze_food_image
from django.http import HttpResponse
import requests
import json
from django.http import HttpResponse
import logging 
from nutriwise.models import FoodDiaryEntry,FoodAnalysis


API_URL = "https://vision.foodvisor.io/api/1.0/en/analysis/"
API_KEY = 'TNWFnlBB.fgffWC7CvExZQrUvL7HiZfbfN3DrK3FM'
HEADERS = {"Authorization": f"Api-Key {API_KEY}"}


@login_required
def dashboard(request):
    """
    Render the main dashboard.
    The user must be logged in to access.
    """
    user_profile = UserProfile.objects.filter(user=request.user).first()
    uploaded_images = FoodDiaryEntry.objects.filter(user=request.user)
    context = {
        'user': request.user,
        'user_profile': user_profile,
        'uploaded_images': uploaded_images,  
    }
    return render(request, 'nutriwise/dashboard.html', context)

@login_required
def dashboard2(request):
    """
    A separate dashboard view for specific use cases.
    """
    # Get the user's profile or None if it doesn't exist
    user_profile = UserProfile.objects.filter(user=request.user).first()

    # Pass the profile and user data to the template
    context = {
        'user': request.user,
        'user_profile': user_profile,  # Pass profile data to the template
    }

    return render(request, 'nutriwise/dashboard2.html', {'user': request.user})


from django.shortcuts import render, HttpResponse
from .models import FoodDiaryEntry, FoodAnalysis
import requests

@login_required
def analyze_food(request):
    food_details = None  # This will store the food analysis details to be displayed on the same page

    if request.method == 'POST':
        form = FoodDiaryEntryForm(request.POST, request.FILES)
        if form.is_valid():
            uploaded_image = request.FILES['image']
            entry = form.save(commit=False)
            entry.user = request.user
            entry.save()  # Save the uploaded image

            # Set up API details
            url = "https://vision.foodvisor.io/api/1.0/en/analysis/"
            headers = {"Authorization": "Api-Key rLCchLLj.4rH9fCFxYTuPFiUkZAVyX48wlST1EbQs"}

            try:
                # Send the image to the API
                response = requests.post(url, headers=headers, files={"image": uploaded_image})
                response.raise_for_status()  # Raise an error for bad responses

                # Parse the API response into JSON format
                data = response.json()  # This will automatically parse the JSON response

                # Optionally, you can log the response for debugging purposes
                logging.debug("API Response Data: %s", data)

                # Save the JSON response into the entry
                entry.api_response = json.dumps(data)  # Store the JSON as a string
                entry.save()

                messages.success(request, "Image uploaded and analyzed successfully!")

                # Extract relevant food details from the API response
                food_details = []
                for item in data['items']:
                    for food in item['food']:
                        food_info = food['food_info']['nutrition']
                        food_details.append({
                            'name': food['food_info']['display_name'],
                            'quantity': food['quantity'],
                            'calories': food_info.get('calories_100g', 'Not available'),
                            'carbs': food_info.get('carbs_100g', 'Not available'),
                            'fats': food_info.get('fat_100g', 'Not available'),
                            'fiber': food_info.get('fibers_100g', 'Not available'),
                            'sugar': food_info.get('sugars_100g', 'Not available'),
                        })

            except requests.exceptions.RequestException as e:
                messages.error(request, f"An error occurred: {e}")
                entry.delete()  # Optionally delete the entry if analysis fails
        else:
            messages.error(request, "Invalid form submission.")
    else:
        form = FoodDiaryEntryForm()

    return render(request, 'nutriwise/upload_image.html', {
        'form': form,
        'food_details': food_details  # Pass the food details to the template
    })

@login_required
def upload_image(request):
    form = FoodDiaryEntryForm(request.POST or None, request.FILES or None)
    food_details = {
        'name': 'Unknown',
        'confidence': 'Not available',
        'quantity': 'Not available',
        'carbs': 'Not available',
        'fats': 'Not available',
        'fiber': 'Not available',
        'sugar': 'Not available',
    }
    api_response = None

    if form.is_valid():
        image_file = request.FILES['image']  # Get the uploaded file
        try:
            # Prepare the file for the API request
            files = {'image': image_file.read()}

            # Make the API request
            response = requests.post(API_URL, headers=HEADERS, files=files)
            response.raise_for_status()  # Raise HTTPError for bad responses (4xx and 5xx)

            # Parse the JSON response
            api_response = response.json()

            try:
                # Extract relevant food details
                items = api_response.get('items', [])
                if items:
                    # Iterate over each item if there are multiple
                    for item in items:
                        position = item.get('position', {})
                        food_list = item.get('food', [])
                        if food_list:
                            for food_item in food_list:
                                food_info = food_item.get('food_info', {})
                                nutrition = food_info.get('nutrition', {})

                                # Add the extracted details to the food_details dictionary
                                food_details.update({
                                    'name': food_info.get('display_name', 'Unknown'),
                                    'confidence': food_item.get('confidence', 'Not available'),
                                    'quantity': food_item.get('quantity', 'Not available'),
                                    'carbs': nutrition.get('carbs_100g', 'Not available'),
                                    'fats': nutrition.get('fat_100g', 'Not available'),
                                    'fiber': nutrition.get('fibers_100g', 'Not available'),
                                    'sugar': nutrition.get('sugars_100g', 'Not available'),
                                    'calories': nutrition.get('calories_100g', 'Not available'),
                                    'proteins': nutrition.get('proteins_100g', 'Not available'),
                                    'sodium': nutrition.get('sodium_100g', 'Not available'),
                                    'vitamin_c': nutrition.get('vitamin_c_100g', 'Not available'),
                                })
                else:
                    food_details['error'] = 'No items found in the response.'

            except requests.exceptions.RequestException as e:
                # Handle exceptions during API call
                food_details = {'error': str(e)}

        except requests.exceptions.RequestException as e:
            # Handle exceptions during the file upload or API call
            messages.error(request, f"Error processing the image: {str(e)}")

    # Prepare context for rendering the template
    context = {
        'form': form,
        'food_details': food_details,
        'api_response': api_response,
    }
    return render(request, 'nutriwise/upload_image.html', context)




def analysis_result(request, entry_id):
    # Fetch the FoodDiaryEntry object by ID
    entry = get_object_or_404(FoodDiaryEntry, id=entry_id)

    # Parse the API response (load it as JSON if it's a string)
    api_response = entry.api_response
    if isinstance(api_response, str):  # Check if it's stored as a string
        try:
            api_response = json.loads(api_response)  # Convert string to JSON
        except json.JSONDecodeError:
            api_response = {}  # If there's an error parsing, set it to an empty dictionary

    # Pass the parsed response to the template
    return render(request, 'nutriwise/entry_detail.html', {
        'entry': entry,
        'api_response': api_response,  # Pass the parsed JSON response to the template
    })


@login_required
def update_profile(request):
    """
    Update the user's profile information.
    """
    # Get or create the user's profile
    user_profile, created = UserProfile.objects.get_or_create(user=request.user)

    if request.method == "POST":
        try:
            # Update profile fields with data from the form
            user_profile.age = int(request.POST.get('age', 0))
            user_profile.gender = request.POST.get('gender', '').capitalize()
            user_profile.height = float(request.POST.get('height', 0.0))
            user_profile.weight = float(request.POST.get('weight', 0.0))
            user_profile.bmi = (
                user_profile.weight / ((user_profile.height / 100) ** 2)
                if user_profile.height > 0 else 0
            )  # Automatically calculate BMI

            # Save the updated profile
            user_profile.save()
            messages.success(request, "Profile updated successfully!")
        except ValueError:
            messages.error(request, "Invalid input. Please check your data.")

        # Redirect to the dashboard or profile view
        return redirect('nutriwise:dashboard2')

    # Render the profile update form
    context = {'user_profile': user_profile}
    return render(request, 'nutriwise/profile_update.html', context)

# nutriwise/views.py

@login_required
def profile(request):
    """
    Render and handle user profile updates.
    """
    # Ensure the user has a UserProfile
    user_profile, created = UserProfile.objects.get_or_create(user=request.user)

    if request.method == 'POST':
        try:
            # Update user profile fields from the POST request
            user_profile.age = request.POST.get('age') or None
            user_profile.gender = request.POST.get('gender') or None
            user_profile.height = request.POST.get('height') or None
            user_profile.weight = request.POST.get('weight') or None
            user_profile.save()

            messages.success(request, "Profile updated successfully!")
        except Exception as e:
            messages.error(request, f"An error occurred: {str(e)}")
        return redirect('nutriwise:profile')  # Redirect to the profile page after saving

    # Render the profile page
    return render(request, 'nutriwise/dashboard2.html', {'profile': user_profile})

def upload_image_view(request):
    # Fetch the latest entry or handle the case where no entry exists
    entry = FoodDiaryEntry.objects.last()
    if entry and entry.api_response:
        api_response = entry.api_response  # JSON data
    else:
        api_response = {}  # Default to an empty dictionary if no entry or response exists
    
    # Debugging: Log the response
    print("API Response:", api_response)
    
    # Pass to the template
    return render(request, 'upload_image.html', {'api_response': api_response})