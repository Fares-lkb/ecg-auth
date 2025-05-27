from django.shortcuts import redirect
from django.urls import reverse
from django.contrib.auth.models import User
from .models import UserProfile

class ForcePasswordChangeMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if not request.user.is_authenticated:
            return self.get_response(request)

        try:
            profile = request.user.userprofile
        except UserProfile.DoesNotExist:
            return self.get_response(request)

        if (
            not request.user.is_superuser and
            profile.must_change_password and
            request.path != reverse('admin:password_change') and
            not request.path.startswith('/static/')
        ):
            print("🔐 Redirecting to password change (must_change_password=True)")
            return redirect('admin:password_change')

        return self.get_response(request)
