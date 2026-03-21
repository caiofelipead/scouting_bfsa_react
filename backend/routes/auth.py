"""Auth & user management routes."""

from fastapi import APIRouter, Depends, HTTPException
from starlette.requests import Request
from slowapi import Limiter
from slowapi.util import get_remote_address

from auth import (
    authenticate_user,
    create_access_token,
    create_user,
    delete_user,
    get_current_user,
    list_users,
    require_admin,
)
from schemas.models import LoginRequest, TokenResponse, UserCreate, UserOut

router = APIRouter(prefix="/api", tags=["auth"])
limiter = Limiter(key_func=get_remote_address)


@router.post("/auth/login", response_model=TokenResponse)
@limiter.limit("5/minute")
async def login(request: Request, req: LoginRequest):
    user = authenticate_user(req.email, req.password)
    if not user:
        raise HTTPException(status_code=401, detail="E-mail ou senha incorretos")
    token = create_access_token({"sub": user["email"], "role": user["role"], "name": user["name"]})
    return TokenResponse(
        access_token=token,
        user=UserOut(**user),
    )


@router.get("/auth/me", response_model=UserOut)
async def get_me(current_user: dict = Depends(get_current_user)):
    return UserOut(id=0, **current_user)


@router.get("/admin/users")
async def admin_list_users(admin: dict = Depends(require_admin)):
    return list_users()


@router.post("/admin/users")
@limiter.limit("10/minute")
async def admin_create_user(request: Request, req: UserCreate, admin: dict = Depends(require_admin)):
    err = create_user(req.email, req.password, req.name, req.role)
    if err:
        raise HTTPException(status_code=400, detail=err)
    return {"message": f"Usuário {req.email} cadastrado com sucesso"}


@router.delete("/admin/users/{user_id}")
async def admin_delete_user(user_id: int, admin: dict = Depends(require_admin)):
    err = delete_user(user_id)
    if err:
        raise HTTPException(status_code=400, detail=err)
    return {"message": "Usuário removido"}
