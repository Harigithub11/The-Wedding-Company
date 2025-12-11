"""
Database models for CRUD operations.
"""

from .organization import OrganizationModel
from .admin import AdminModel

__all__ = [
    "OrganizationModel",
    "AdminModel",
]
