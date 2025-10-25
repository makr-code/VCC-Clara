"""
Auth Utility Functions

Convenience functions for user claims extraction.
"""

from typing import Dict, Any, List


def get_current_user_id(user_claims: Dict[str, Any]) -> str:
    """Extract user ID from claims"""
    return user_claims.get("sub", "unknown")


def get_current_user_email(user_claims: Dict[str, Any]) -> str:
    """Extract user email from claims"""
    return user_claims.get("email", "unknown@unknown.local")


def get_current_user_roles(user_claims: Dict[str, Any]) -> List[str]:
    """Extract user roles from claims"""
    return user_claims.get("realm_access", {}).get("roles", [])


def has_role(user_claims: Dict[str, Any], role: str) -> bool:
    """Check if user has specific role"""
    return role in get_current_user_roles(user_claims)


def has_any_role(user_claims: Dict[str, Any], roles: List[str]) -> bool:
    """Check if user has any of the specified roles"""
    user_roles = get_current_user_roles(user_claims)
    return any(role in user_roles for role in roles)


def has_all_roles(user_claims: Dict[str, Any], roles: List[str]) -> bool:
    """Check if user has all of the specified roles"""
    user_roles = get_current_user_roles(user_claims)
    return all(role in user_roles for role in roles)
