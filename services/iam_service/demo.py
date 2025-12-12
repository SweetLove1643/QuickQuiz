"""
Demo script to initialize IAM Service with sample data
Run this after migrations: python demo.py
"""

import os
import sys
import django

# Setup Django
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "iam.settings")
sys.path.insert(0, os.path.dirname(__file__))
django.setup()

from api.models import User, Role, Permission, UserProfile
from django.contrib.auth.models import Group


def create_permissions():
    """Create default permissions"""
    permissions_data = [
        # Quiz permissions
        ("quiz_create", "Create Quiz", "quiz", "create"),
        ("quiz_read", "Read Quiz", "quiz", "read"),
        ("quiz_update", "Update Quiz", "quiz", "update"),
        ("quiz_delete", "Delete Quiz", "quiz", "delete"),
        # Document permissions
        ("document_create", "Create Document", "document", "create"),
        ("document_read", "Read Document", "document", "read"),
        ("document_update", "Update Document", "document", "update"),
        ("document_delete", "Delete Document", "document", "delete"),
        # User permissions
        ("user_create", "Create User", "user", "create"),
        ("user_read", "Read User", "user", "read"),
        ("user_update", "Update User", "user", "update"),
        ("user_delete", "Delete User", "user", "delete"),
        # Evaluation permissions
        ("evaluation_create", "Create Evaluation", "evaluation", "create"),
        ("evaluation_read", "Read Evaluation", "evaluation", "read"),
        ("evaluation_update", "Update Evaluation", "evaluation", "update"),
    ]

    for code, name, resource, action in permissions_data:
        Permission.objects.get_or_create(
            code=code,
            defaults={
                "name": name,
                "resource": resource,
                "action": action,
            },
        )
        print(f"✓ Created permission: {code}")


def create_roles():
    """Create default roles with permissions"""

    # Student role
    student_role, created = Role.objects.get_or_create(
        name="Student", defaults={"description": "Student user role"}
    )
    if created:
        student_permissions = Permission.objects.filter(
            code__in=[
                "quiz_read",
                "quiz_create",
                "document_read",
                "document_create",
                "evaluation_read",
            ]
        )
        student_role.permissions.set(student_permissions)
        print("✓ Created Student role")

    # Teacher role
    teacher_role, created = Role.objects.get_or_create(
        name="Teacher", defaults={"description": "Teacher user role"}
    )
    if created:
        teacher_permissions = Permission.objects.filter(
            code__in=[
                "quiz_create",
                "quiz_read",
                "quiz_update",
                "quiz_delete",
                "document_create",
                "document_read",
                "document_update",
                "document_delete",
                "user_read",
                "evaluation_create",
                "evaluation_read",
                "evaluation_update",
            ]
        )
        teacher_role.permissions.set(teacher_permissions)
        print("✓ Created Teacher role")

    # Admin role
    admin_role, created = Role.objects.get_or_create(
        name="Admin",
        defaults={"description": "Administrator role with full permissions"},
    )
    if created:
        all_permissions = Permission.objects.all()
        admin_role.permissions.set(all_permissions)
        print("✓ Created Admin role")


def create_sample_users():
    """Create sample users"""

    # Admin user
    admin, created = User.objects.get_or_create(
        username="admin",
        defaults={
            "email": "admin@quickquiz.com",
            "first_name": "Admin",
            "last_name": "User",
            "role": "admin",
            "is_verified": True,
            "is_staff": True,
            "is_superuser": True,
        },
    )
    if created:
        admin.set_password("Admin123")
        admin.save()
        UserProfile.objects.create(user=admin)
        print("✓ Created admin user: admin / Admin123")

    # Teacher user
    teacher, created = User.objects.get_or_create(
        username="teacher1",
        defaults={
            "email": "teacher1@quickquiz.com",
            "first_name": "John",
            "last_name": "Teacher",
            "role": "teacher",
            "is_verified": True,
        },
    )
    if created:
        teacher.set_password("Teacher123")
        teacher.save()
        UserProfile.objects.create(user=teacher)
        print("✓ Created teacher user: teacher1 / Teacher123")

    # Student users
    for i in range(1, 4):
        student, created = User.objects.get_or_create(
            username=f"student{i}",
            defaults={
                "email": f"student{i}@quickquiz.com",
                "first_name": f"Student",
                "last_name": f"{i}",
                "role": "student",
                "is_verified": True,
            },
        )
        if created:
            student.set_password("Student123")
            student.save()
            UserProfile.objects.create(user=student)
            print(f"✓ Created student user: student{i} / Student123")


def main():
    """Initialize IAM Service with sample data"""
    print("=" * 50)
    print("QuickQuiz IAM Service Initialization")
    print("=" * 50)

    print("\n[1/3] Creating permissions...")
    create_permissions()

    print("\n[2/3] Creating roles...")
    create_roles()

    print("\n[3/3] Creating sample users...")
    create_sample_users()

    print("\n" + "=" * 50)
    print("✓ IAM Service initialized successfully!")
    print("=" * 50)
    print("\nSample credentials:")
    print("  Admin:    admin / Admin123")
    print("  Teacher:  teacher1 / Teacher123")
    print("  Student:  student1 / Student123")
    print("\nAccess admin at: http://localhost:8005/admin/")


if __name__ == "__main__":
    main()
