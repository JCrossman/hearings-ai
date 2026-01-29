"""Authentication and authorization for Hearings AI.

Implements role-based access control per confidentiality rules:
- Public: All users
- Protected A: Staff, Hearing Panel, own-party Interveners
- Confidential: Hearing Panel only

Demo Mode:
Set X-Demo-Role header to simulate different user roles without auth:
- "Hearing_Panel" - Full access including confidential
- "Staff" - Staff access (public + protected_a)
- "Intervener" - Intervener access (public + own party's protected_a)
- "Public" - Public access only
"""

import os
from typing import Annotated, Optional

from fastapi import Depends, HTTPException, Header, Request, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from src.models import ConfidentialityLevel, DocumentMetadata, Party, UserClaims

# Use optional bearer auth to support demo mode
security = HTTPBearer(auto_error=False)

# Demo user profiles for role switching
DEMO_USERS = {
    "Hearing_Panel": UserClaims(
        oid="demo-panel-001",
        name="Commissioner Demo",
        email="panel@aer.ca",
        roles=["Hearing_Panel"],
        party_affiliation=None,
        ba_code=None,
    ),
    "Staff": UserClaims(
        oid="demo-staff-001",
        name="Staff Demo",
        email="staff@example.com",
        roles=["Staff"],
        party_affiliation=None,
        ba_code=None,
    ),
    "Intervener": UserClaims(
        oid="demo-intervener-001",
        name="Intervener Demo",
        email="intervener@example.com",
        roles=["Intervener"],
        party_affiliation="Crowsnest Pass Residents Association",
        ba_code=None,
    ),
    "Public": UserClaims(
        oid="demo-public-001",
        name="Public User",
        email="public@example.com",
        roles=[],
        party_affiliation=None,
        ba_code=None,
    ),
}


async def get_current_user(
    request: Request,
    credentials: Annotated[Optional[HTTPAuthorizationCredentials], Depends(security)] = None,
    x_demo_role: Annotated[Optional[str], Header()] = None,
) -> UserClaims:
    """Extract and validate user claims from Entra ID token.

    In production, this validates the JWT against Entra ID.
    For demo mode, uses X-Demo-Role header to simulate different roles.
    """
    # Check for demo mode via header
    if x_demo_role and x_demo_role in DEMO_USERS:
        return DEMO_USERS[x_demo_role]
    
    # Check for demo mode via environment (for development)
    env_demo_role = os.environ.get("DEMO_ROLE")
    if env_demo_role and env_demo_role in DEMO_USERS:
        return DEMO_USERS[env_demo_role]
    
    # Check request state (set by middleware)
    if hasattr(request.state, "user_claims"):
        return request.state.user_claims
    
    # If no auth provided and not in demo mode, default to Staff for dev
    if os.environ.get("ENVIRONMENT", "development") == "development":
        return DEMO_USERS["AER_Staff"]
    
    # Production: require valid credentials
    if not credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"code": "AUTH_001", "message": "Authentication required"},
        )
    
    # TODO: Implement actual JWT validation with azure-identity
    # For now, return staff user
    return DEMO_USERS["AER_Staff"]


def can_access_document(user_claims: UserClaims, document: DocumentMetadata) -> bool:
    """Check if user can access document based on confidentiality level.

    Access rules per Rules of Practice s. 49:
    - Public: All users
    - Protected A: Staff, Hearing Panel, or own-party members
    - Confidential: Hearing Panel only (s. 49 order required)
    """
    level = document.confidentiality_level

    if level == ConfidentialityLevel.PUBLIC:
        return True

    if level == ConfidentialityLevel.PROTECTED_A:
        # Staff and Panel can see all Protected A
        if "Staff" in user_claims.roles or "Hearing_Panel" in user_claims.roles:
            return True

        # Interveners can see their own party's protected documents
        if user_claims.party_affiliation:
            party_names = [p.name for p in document.parties]
            if user_claims.party_affiliation in party_names:
                return True

        return False

    if level == ConfidentialityLevel.CONFIDENTIAL:
        # Only Hearing Panel can access confidential documents
        return "Hearing_Panel" in user_claims.roles

    return False


def build_search_filter(user_claims: UserClaims) -> Optional[str]:
    """Build OData filter for Azure AI Search based on user's access level.

    This filter is ALWAYS appended to search queries to enforce access control.
    Never bypass this - it's the security boundary.
    """
    filters: list[str] = []

    # Confidential documents only visible to Hearing Panel
    if "Hearing_Panel" not in user_claims.roles:
        filters.append("confidentialityLevel ne 'confidential'")

    # Protected A visible to Staff, Panel, or own-party
    if "Staff" not in user_claims.roles and "Hearing_Panel" not in user_claims.roles:
        if user_claims.party_affiliation:
            # Can see public OR own party's protected documents
            party_filter = (
                f"(confidentialityLevel eq 'public' or "
                f"parties/any(p: p eq '{user_claims.party_affiliation}'))"
            )
            filters.append(party_filter)
        else:
            # Public users see only public documents
            filters.append("confidentialityLevel eq 'public'")

    return " and ".join(filters) if filters else None


def require_roles(*required_roles: str):
    """Dependency to require specific roles for an endpoint."""

    async def role_checker(
        user_claims: Annotated[UserClaims, Depends(get_current_user)]
    ) -> UserClaims:
        if not any(role in user_claims.roles for role in required_roles):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail={
                    "code": "AUTH_002",
                    "message": f"Requires one of roles: {', '.join(required_roles)}",
                },
            )
        return user_claims

    return role_checker


def require_document_access(document: DocumentMetadata):
    """Dependency to verify user can access a specific document."""

    async def access_checker(
        user_claims: Annotated[UserClaims, Depends(get_current_user)]
    ) -> UserClaims:
        if not can_access_document(user_claims, document):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail={
                    "code": "DOC_003",
                    "message": "Confidentiality restriction - insufficient access level",
                },
            )
        return user_claims

    return access_checker
