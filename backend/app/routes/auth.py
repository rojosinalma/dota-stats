from fastapi import APIRouter, Depends, Request, HTTPException
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session
from ..database import get_db
from ..models import User
from ..schemas import UserResponse
from ..services import SteamAuthService
from ..config import settings
from itsdangerous import URLSafeSerializer

router = APIRouter(prefix="/auth", tags=["auth"])
serializer = URLSafeSerializer(settings.SECRET_KEY)


def get_current_user(request: Request, db: Session = Depends(get_db)) -> User:
    """Dependency to get current authenticated user"""
    session_token = request.cookies.get(settings.SESSION_COOKIE_NAME)
    if not session_token:
        raise HTTPException(status_code=401, detail="Not authenticated")

    try:
        user_id = serializer.loads(session_token)
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            raise HTTPException(status_code=401, detail="User not found")
        return user
    except:
        raise HTTPException(status_code=401, detail="Invalid session")


@router.get("/login")
async def login():
    """Redirect to Steam login"""
    steam_auth = SteamAuthService()
    login_url = steam_auth.get_login_url()
    return RedirectResponse(url=login_url)


@router.get("/callback")
async def callback(request: Request, db: Session = Depends(get_db)):
    """Handle Steam OAuth callback"""
    steam_auth = SteamAuthService()

    # Get query parameters
    params = dict(request.query_params)

    # Verify authentication
    steam_id = await steam_auth.verify_authentication(params)
    if not steam_id:
        raise HTTPException(status_code=400, detail="Authentication failed")

    # Get player info from Steam
    player_info = await steam_auth.get_player_summaries(steam_id)
    if not player_info:
        raise HTTPException(status_code=400, detail="Could not fetch player info")

    # Create or update user
    user = db.query(User).filter(User.steam_id == steam_id).first()
    if user:
        user.persona_name = player_info.get("personaname", "")
        user.profile_url = player_info.get("profileurl", "")
        user.avatar_url = player_info.get("avatarfull", "")
    else:
        user = User(
            id=int(steam_id),
            steam_id=steam_id,
            persona_name=player_info.get("personaname", ""),
            profile_url=player_info.get("profileurl", ""),
            avatar_url=player_info.get("avatarfull", "")
        )
        db.add(user)

    db.commit()
    db.refresh(user)

    # Create session
    session_token = serializer.dumps(user.id)

    # Redirect to frontend with session cookie
    response = RedirectResponse(url="/")
    response.set_cookie(
        key=settings.SESSION_COOKIE_NAME,
        value=session_token,
        httponly=True,
        max_age=30 * 24 * 60 * 60,  # 30 days
        samesite="lax"
    )

    return response


@router.get("/me", response_model=UserResponse)
async def get_me(user: User = Depends(get_current_user)):
    """Get current user info"""
    return user


@router.post("/logout")
async def logout():
    """Logout current user"""
    from fastapi.responses import JSONResponse
    response = JSONResponse(content={"message": "Logged out successfully"})
    response.delete_cookie(
        key=settings.SESSION_COOKIE_NAME,
        path="/",
        samesite="lax"
    )
    return response
