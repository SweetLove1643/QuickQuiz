# QuickQuiz IAM Service

Identity and Access Management (IAM) Service for user management, authentication, and authorization in the QuickQuiz platform.

## Features

### User Management

- **User Registration & Authentication**

  - Secure user registration with password strength validation
  - JWT-based authentication
  - Login with access and refresh tokens
  - Automatic token refresh
  - Logout with token blacklisting

- **User Profiles**

  - Extended user profile information
  - Organization and department tracking
  - Language preferences
  - Notification settings

- **User Roles & Permissions**
  - Built-in roles: Student, Teacher, Admin
  - Fine-grained permission system
  - Role-based access control (RBAC)
  - Permission management

### Security Features

- **Password Security**

  - Strong password validation (uppercase, lowercase, numbers)
  - Password change functionality
  - Password history (planned)

- **Audit Logging**

  - All user actions logged
  - IP address tracking
  - User agent tracking
  - Action success/failure tracking

- **Token Management**
  - JWT with configurable expiration
  - Refresh token blacklisting on logout
  - Token rotation

## Architecture

```
IAM Service (Port 8005)
├── User Management
│   ├── Registration & Login
│   ├── Profile Management
│   └── Password Management
├── Role & Permission Management
├── Audit Logging
└── JWT Authentication
```

## API Endpoints

### Authentication

- `POST /api/users/login/` - Login
- `POST /api/users/logout/` - Logout
- `POST /api/token/refresh/` - Refresh access token

### User Management

- `POST /api/users/` - Register new user
- `GET /api/users/` - List users (with pagination & filtering)
- `GET /api/users/{id}/` - Get user details
- `GET /api/users/me/` - Get current user
- `PUT /api/users/{id}/` - Update user
- `DELETE /api/users/{id}/` - Delete user (admin only)
- `POST /api/users/{id}/change_password/` - Change password
- `POST /api/users/{id}/disable_user/` - Disable user (admin only)
- `POST /api/users/{id}/enable_user/` - Enable user (admin only)

### Profile Management

- `GET /api/profiles/` - List profiles
- `GET /api/profiles/{id}/` - Get profile
- `PUT /api/profiles/{id}/` - Update profile

### Roles & Permissions

- `GET /api/roles/` - List roles
- `GET /api/roles/{id}/` - Get role details
- `GET /api/permissions/` - List permissions
- `GET /api/permissions/{id}/` - Get permission details

### Audit Logging

- `GET /api/audit-logs/` - List audit logs (admin only)
- `GET /api/audit-logs/{id}/` - Get audit log (admin only)

## Database Models

### User

Extended Django User model with:

- UUID primary key
- Role (Student, Teacher, Admin)
- Verification status
- Avatar URL
- Bio
- Last login timestamp

### UserProfile

Extended profile information:

- Organization
- Department
- Location
- Date of birth
- Preferred language
- Notification preferences

### Role

Role definition with:

- Name
- Description
- Many-to-many relationship with Permissions

### Permission

Fine-grained permissions:

- Resource (quiz, document, user, etc.)
- Action (create, read, update, delete)

### AuditLog

Comprehensive audit trail:

- User action
- Resource and resource ID
- IP address
- User agent
- Status (success/failure)
- Details (JSON)

### RefreshTokenBlacklist

Blacklisted tokens on logout:

- User reference
- Token
- Blacklist timestamp
- Expiration timestamp

## Setup & Installation

### 1. Install Dependencies

```bash
cd services/iam_service
pip install -r requirements.txt
```

### 2. Run Migrations

```bash
python manage.py makemigrations
python manage.py migrate
```

### 3. Create Superuser (Admin)

```bash
python manage.py createsuperuser
```

### 4. Run Development Server

```bash
python manage.py runserver 8005
```

## Usage Examples

### Register New User

```bash
curl -X POST http://localhost:8005/api/users/ \
  -H "Content-Type: application/json" \
  -d '{
    "username": "student1",
    "email": "student1@example.com",
    "password": "SecurePass123",
    "password_confirm": "SecurePass123",
    "first_name": "John",
    "last_name": "Doe",
    "role": "student"
  }'
```

### Login

```bash
curl -X POST http://localhost:8005/api/users/login/ \
  -H "Content-Type: application/json" \
  -d '{
    "username": "student1",
    "password": "SecurePass123"
  }'
```

Response:

```json
{
  "user": {
    "user_id": "uuid",
    "username": "student1",
    "email": "student1@example.com",
    "role": "student",
    "is_verified": false,
    "is_active": true
  },
  "refresh": "refresh_token",
  "access": "access_token"
}
```

### Get Current User

```bash
curl -X GET http://localhost:8005/api/users/me/ \
  -H "Authorization: Bearer {access_token}"
```

### Update User Profile

```bash
curl -X PUT http://localhost:8005/api/users/{user_id}/ \
  -H "Authorization: Bearer {access_token}" \
  -H "Content-Type: application/json" \
  -d '{
    "first_name": "John",
    "last_name": "Doe",
    "phone_number": "+84912345678",
    "bio": "I am a student"
  }'
```

### Change Password

```bash
curl -X POST http://localhost:8005/api/users/{user_id}/change_password/ \
  -H "Authorization: Bearer {access_token}" \
  -H "Content-Type: application/json" \
  -d '{
    "old_password": "SecurePass123",
    "new_password": "NewSecurePass456",
    "new_password_confirm": "NewSecurePass456"
  }'
```

## Configuration

Environment variables in `.env`:

```env
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1,0.0.0.0
DJANGO_SECRET_KEY=your-secret-key
IAM_SECRET_KEY=your-iam-secret-key
CORS_ALLOWED_ORIGINS=http://localhost:3000
```

## JWT Configuration

Default token lifetimes:

- Access Token: 1 hour
- Refresh Token: 7 days

Customize in `iam/settings.py`:

```python
SIMPLE_JWT = {
    'ACCESS_TOKEN_LIFETIME': timedelta(hours=1),
    'REFRESH_TOKEN_LIFETIME': timedelta(days=7),
}
```

## Security Considerations

1. **Password Requirements**

   - Minimum 8 characters
   - At least one uppercase letter
   - At least one lowercase letter
   - At least one digit

2. **Token Security**

   - Tokens signed with SECRET_KEY
   - Refresh tokens blacklisted on logout
   - Token rotation enabled

3. **Audit Trail**

   - All actions logged with IP and user agent
   - Success/failure tracking
   - Resource modification tracking

4. **CORS Protection**
   - Configured allowed origins
   - Credentials allowed for trusted origins

## Testing

### Run Tests

```bash
python manage.py test api
```

### Test Coverage

```bash
coverage run --source='.' manage.py test api
coverage report
```

## Admin Interface

Access Django admin at `http://localhost:8005/admin/` with superuser credentials.

Features:

- User management
- Profile management
- Role and permission configuration
- Audit log viewing
- Token blacklist management

## Troubleshooting

### Issue: Token not working

**Solution**: Verify token is not blacklisted and hasn't expired. Check `Authorization` header format: `Bearer {token}`

### Issue: Permission denied

**Solution**: Check user role and associated permissions. Admins can modify permissions in Django admin.

### Issue: Database migrations fail

**Solution**: Ensure database is accessible and run `python manage.py makemigrations` before `migrate`

## Future Enhancements

1. **OAuth 2.0 Integration**

   - Social login (Google, GitHub, Facebook)

2. **Two-Factor Authentication (2FA)**

   - Email/SMS verification
   - TOTP support

3. **Role-Based Access Control (RBAC)**

   - Advanced permission inheritance
   - Custom role creation via API

4. **User Groups**

   - Department-based grouping
   - Custom group management

5. **API Documentation**
   - Auto-generated Swagger/OpenAPI docs

## Dependencies

- Django 5.2+
- Django REST Framework 3.14+
- Simple JWT 5.3+
- django-cors-headers 4.0+
- Python 3.9+

## License

Part of QuickQuiz platform
