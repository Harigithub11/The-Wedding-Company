"""
Custom validation utilities for input sanitization and validation.
"""

import re
from typing import Optional


class ValidationError(Exception):
    """Custom exception for validation errors."""
    pass


class OrganizationNameValidator:
    """Validator for organization names."""

    @staticmethod
    def validate(name: str) -> str:
        """
        Validate and sanitize organization name.

        Args:
            name: Organization name to validate

        Returns:
            Sanitized organization name

        Raises:
            ValidationError: If validation fails
        """
        if not name:
            raise ValidationError("Organization name cannot be empty")

        # Strip whitespace
        name = name.strip()

        # Check length
        if len(name) < 3:
            raise ValidationError("Organization name must be at least 3 characters")
        
        if len(name) > 50:
            raise ValidationError("Organization name must not exceed 50 characters")

        # Convert to lowercase
        name = name.lower()

        # Replace spaces with underscores
        name = name.replace(' ', '_')

        # Remove any characters that aren't alphanumeric or underscore
        sanitized = re.sub(r'[^a-z0-9_]', '', name)

        if not sanitized:
            raise ValidationError(
                "Organization name must contain at least one alphanumeric character"
            )

        # Ensure it starts with a letter or number (not underscore)
        if sanitized[0] == '_':
            sanitized = sanitized.lstrip('_')
            if not sanitized:
                raise ValidationError(
                    "Organization name must contain alphanumeric characters"
                )

        return sanitized

    @staticmethod
    def to_collection_name(org_name: str) -> str:
        """
        Convert organization name to MongoDB collection name.

        Args:
            org_name: Organization name

        Returns:
            Collection name with 'org_' prefix
        """
        return f"org_{org_name}"


class EmailValidator:
    """Enhanced email validator."""

    @staticmethod
    def validate(email: str) -> str:
        """
        Validate email format.

        Args:
            email: Email address to validate

        Returns:
            Lowercase email address

        Raises:
            ValidationError: If email is invalid
        """
        if not email:
            raise ValidationError("Email cannot be empty")

        email = email.strip().lower()

        # Basic email regex pattern
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        
        if not re.match(pattern, email):
            raise ValidationError("Invalid email format")

        return email


class PasswordValidator:
    """Password strength validator."""

    @staticmethod
    def validate(password: str) -> None:
        """
        Validate password strength.

        Requirements:
        - At least 8 characters
        - At least one uppercase letter
        - At least one lowercase letter
        - At least one number

        Args:
            password: Password to validate

        Raises:
            ValidationError: If password doesn't meet requirements
        """
        if not password:
            raise ValidationError("Password cannot be empty")

        if len(password) < 8:
            raise ValidationError("Password must be at least 8 characters long")

        if not re.search(r'[A-Z]', password):
            raise ValidationError(
                "Password must contain at least one uppercase letter"
            )

        if not re.search(r'[a-z]', password):
            raise ValidationError(
                "Password must contain at least one lowercase letter"
            )

        if not re.search(r'\d', password):
            raise ValidationError("Password must contain at least one number")

    @staticmethod
    def get_strength(password: str) -> str:
        """
        Get password strength rating.

        Args:
            password: Password to evaluate

        Returns:
            Strength rating: 'weak', 'medium', 'strong'
        """
        strength = 0

        if len(password) >= 8:
            strength += 1
        if len(password) >= 12:
            strength += 1
        if re.search(r'[A-Z]', password):
            strength += 1
        if re.search(r'[a-z]', password):
            strength += 1
        if re.search(r'\d', password):
            strength += 1
        if re.search(r'[!@#$%^&*(),.?":{}|<>]', password):
            strength += 1

        if strength <= 2:
            return "weak"
        elif strength <= 4:
            return "medium"
        else:
            return "strong"


class InputSanitizer:
    """General input sanitization utilities."""

    @staticmethod
    def sanitize_string(value: Optional[str], max_length: int = 1000) -> Optional[str]:
        """
        Sanitize string input to prevent injection attacks.

        Args:
            value: String to sanitize
            max_length: Maximum allowed length

        Returns:
            Sanitized string or None
        """
        if value is None:
            return None

        # Strip whitespace
        value = value.strip()

        # Truncate to max length
        if len(value) > max_length:
            value = value[:max_length]

        # Remove null bytes
        value = value.replace('\x00', '')

        return value

    @staticmethod
    def sanitize_dict(data: dict, max_depth: int = 3, current_depth: int = 0) -> dict:
        """
        Recursively sanitize dictionary values.

        Args:
            data: Dictionary to sanitize
            max_depth: Maximum recursion depth
            current_depth: Current recursion depth

        Returns:
            Sanitized dictionary
        """
        if current_depth >= max_depth:
            return {}

        sanitized = {}
        for key, value in data.items():
            if isinstance(value, str):
                sanitized[key] = InputSanitizer.sanitize_string(value)
            elif isinstance(value, dict):
                sanitized[key] = InputSanitizer.sanitize_dict(
                    value,
                    max_depth,
                    current_depth + 1
                )
            else:
                sanitized[key] = value

        return sanitized
