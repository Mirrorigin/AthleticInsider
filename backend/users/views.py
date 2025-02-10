from django.http import JsonResponse
import json
from django.contrib.auth.hashers import make_password
from django.contrib.auth.models import User
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from models import Users


@csrf_exempt  # For testing; in production use proper CSRF handling
def signup(request):
    if request.method == "POST":
        try:
            data = json.loads(request.body)
            email = data.get('email')
            password = data.get('password')
            if not email or not password:
                return JsonResponse({'error': 'Email and password are required.'}, status=400)

            # Create a user in your custom model.
            # Here we hash the password for security.
            user = Users.objects.create(
                email=email,
                password=make_password(password),
                first_name='',   # You can update to capture first/last names if needed.
                last_name=''
            )
            return JsonResponse({'message': 'Signup successful.'}, status=201)
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=400)
    else:
        return JsonResponse({'error': 'Invalid method.'}, status=405)

def test_api(request):
    return JsonResponse({"message": "Backend is working!"})
