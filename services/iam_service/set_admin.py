import os
import django

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "iam.settings")
django.setup()

from api.models import User

user = User.objects.get(username="Admin")
user.is_staff = True
user.save()
print(f"User {user.username} is_staff set to True")
