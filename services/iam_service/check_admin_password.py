import django
import os

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "iam.settings")
django.setup()

from api.models import User
from django.contrib.auth import authenticate

user = User.objects.filter(username="Admin").first()
print(f"User found: {user}")
if user:
    print(f"Username: {user.username}")
    print(f"is_active: {user.is_active}")
    print(f"is_staff: {user.is_staff}")
    print(f'check_password("Admin@123"): {user.check_password("Admin@123")}')
    print(f"password hash: {user.password[:50]}...")

    auth_user = authenticate(username="Admin", password="Admin@123")
    print(f"\nauthenticate() result: {auth_user}")
    print(
        f"authenticate() returned same user: {auth_user == user if auth_user else False}"
    )
