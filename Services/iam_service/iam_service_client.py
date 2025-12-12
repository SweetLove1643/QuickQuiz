"""
Client for IAM Service
Provides methods to interact with IAM Service from gateway
"""

import requests
import logging
from typing import Optional, Dict, Any

logger = logging.getLogger(__name__)


class IAMServiceClient:
    """Client for communicating with IAM Service"""

    def __init__(self, base_url: str = "http://localhost:8005/api"):
        self.base_url = base_url
        self.session = requests.Session()

    def register_user(self, user_data: Dict[str, Any]) -> Dict[str, Any]:
        """Register a new user"""
        try:
            response = self.session.post(f"{self.base_url}/users/", json=user_data)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            logger.error(f"Error registering user: {str(e)}")
            raise

    def login(self, username: str, password: str) -> Dict[str, Any]:
        """Login user and get JWT tokens"""
        try:
            response = self.session.post(
                f"{self.base_url}/users/login/",
                json={"username": username, "password": password},
            )
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            logger.error(f"Error logging in: {str(e)}")
            raise

    def logout(self, refresh_token: str) -> Dict[str, Any]:
        """Logout user and blacklist token"""
        try:
            response = self.session.post(
                f"{self.base_url}/users/logout/", json={"refresh": refresh_token}
            )
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            logger.error(f"Error logging out: {str(e)}")
            raise

    def get_current_user(self, access_token: str) -> Dict[str, Any]:
        """Get current user information"""
        try:
            headers = {"Authorization": f"Bearer {access_token}"}
            response = self.session.get(f"{self.base_url}/users/me/", headers=headers)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            logger.error(f"Error getting current user: {str(e)}")
            raise

    def get_user(self, user_id: str, access_token: str) -> Dict[str, Any]:
        """Get user by ID"""
        try:
            headers = {"Authorization": f"Bearer {access_token}"}
            response = self.session.get(
                f"{self.base_url}/users/{user_id}/", headers=headers
            )
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            logger.error(f"Error getting user: {str(e)}")
            raise

    def update_user(
        self, user_id: str, access_token: str, user_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Update user information"""
        try:
            headers = {"Authorization": f"Bearer {access_token}"}
            response = self.session.put(
                f"{self.base_url}/users/{user_id}/", json=user_data, headers=headers
            )
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            logger.error(f"Error updating user: {str(e)}")
            raise

    def change_password(
        self, user_id: str, access_token: str, password_data: Dict[str, str]
    ) -> Dict[str, Any]:
        """Change user password"""
        try:
            headers = {"Authorization": f"Bearer {access_token}"}
            response = self.session.post(
                f"{self.base_url}/users/{user_id}/change_password/",
                json=password_data,
                headers=headers,
            )
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            logger.error(f"Error changing password: {str(e)}")
            raise

    def list_users(
        self, access_token: str, page: int = 1, search: str = ""
    ) -> Dict[str, Any]:
        """List users with pagination and search"""
        try:
            headers = {"Authorization": f"Bearer {access_token}"}
            params = {"page": page}
            if search:
                params["search"] = search
            response = self.session.get(
                f"{self.base_url}/users/", headers=headers, params=params
            )
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            logger.error(f"Error listing users: {str(e)}")
            raise

    def get_roles(self, access_token: str) -> Dict[str, Any]:
        """Get all available roles"""
        try:
            headers = {"Authorization": f"Bearer {access_token}"}
            response = self.session.get(f"{self.base_url}/roles/", headers=headers)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            logger.error(f"Error getting roles: {str(e)}")
            raise

    def get_permissions(self, access_token: str) -> Dict[str, Any]:
        """Get all available permissions"""
        try:
            headers = {"Authorization": f"Bearer {access_token}"}
            response = self.session.get(
                f"{self.base_url}/permissions/", headers=headers
            )
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            logger.error(f"Error getting permissions: {str(e)}")
            raise

    def verify_token(self, access_token: str) -> bool:
        """Verify if token is valid"""
        try:
            headers = {"Authorization": f"Bearer {access_token}"}
            response = self.session.get(f"{self.base_url}/users/me/", headers=headers)
            return response.status_code == 200
        except:
            return False

    def refresh_token(self, refresh_token: str) -> Dict[str, Any]:
        """Refresh access token"""
        try:
            response = self.session.post(
                f"{self.base_url}/token/refresh/", json={"refresh": refresh_token}
            )
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            logger.error(f"Error refreshing token: {str(e)}")
            raise
