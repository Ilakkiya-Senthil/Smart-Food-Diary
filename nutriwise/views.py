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
        'user_profile': user_profile,  # Pass profile data to the template
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

from django.shortcuts import render, redirect
from nutriwise.forms import FoodDiaryEntryForm
from .models import FoodDiaryEntry
from .api_utils import analyze_food_image

def analyze_food(request):
    if request.method == 'POST':
        form = FoodDiaryEntryForm(request.POST, request.FILES) 
        if form.is_valid():
            # Get the uploaded image
            uploaded_image = request.FILES['image']
            entry = form.save()
            # Set up API details
            url = "https://vision.foodvisor.io/api/1.0/en/analysis/"
            headers = {"Authorization": "Api-Key rLCchLLj.4rH9fCFxYTuPFiUkZAVyX48wlST1EbQs"}

            # Send the image to the API
            response = requests.post(url, headers=headers, files={"image": uploaded_image})
            response.raise_for_status()  # Raise an error for bad responses

            # Process the JSON response
            data = response.json()
            entry.api_response = data  # Ensure `api_response` is a field in the model
            entry.save()
            return render(request, 'nutriwise/analysis_result.html', {'entry': entry, 'analysis_data': data})
        else:
            return HttpResponse('Invalid form submission.', status=400)

    form = FoodDiaryEntryForm()
    return render(request, 'nutriwise/upload_image.html', {'form': form})
    
def upload_image(request):
    if request.method == 'POST':
        form = FoodDiaryEntryForm(request.POST, request.FILES)
        if form.is_valid():
            entry = form.save(commit=False)  # Do not save to the database yet
            entry.user = request.user  # Assign the logged-in user
            entry.save()  # Save after assigning the user

            # Analyze the uploaded image using Foodvisor API
            try:
                api_response = analyze_food_image(entry.image.path)  # Process the uploaded image
                entry.api_response = api_response  # Save API response to the entry
                entry.save()
                messages.success(request, "Image uploaded and analyzed successfully!")
            except Exception as e:
              # Optionally delete the entry if analysis fails
                messages.error(request, "An error occurred while analyzing the image.")
                entry.delete()
                logger.error(f"Error analyzing image: {e}")

            return redirect('nutriwise:dashboard')  # Redirect to the dashboard
        else:
            messages.error(request, "Invalid form submission.")
    else:
        form = FoodDiaryEntryForm()

    return render(request, 'nutriwise/upload_image.html', {'form': form})


def analysis_result(request, entry_id):
    entry = get_object_or_404(FoodDiaryEntry, id=entry_id)
    # Assuming `entry.api_response` contains the analysis data
    analysis_data = entry.api_response
    return render(request, 'nutriwise/entry_detail.html', {'entry': entry, 'analysis_data': analysis_data})



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
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from .forms import UserProfileForm
from .models import UserProfile
from django.http import HttpResponse

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