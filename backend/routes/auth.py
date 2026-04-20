"""Auth & user management routes."""

from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from starlette.requests import Request
from slowapi import Limiter
from slowapi.util import get_remote_address

from auth import (
    authenticate_user,
    create_access_token,
    create_user,
    delete_user,
    get_current_user,
    list_access_logs,
    list_users,
    log_access,
    require_admin,
)
from schemas.models import LoginRequest, TokenResponse, UserCreate, UserOut

router = APIRouter(prefix="/api", tags=["auth"])
limiter = Limiter(key_func=get_remote_address)


def _client_ip(request: Request) -> str:
    xff = request.headers.get("x-forwarded-for")
    if xff:
        return xff.split(",")[0].strip()
    return request.client.host if request.client else ""


def _user_agent(request: Request) -> str:
    return request.headers.get("user-agent", "")


@router.post("/auth/login", response_model=TokenResponse)
@limiter.limit("5/minute")
async def login(request: Request, req: LoginRequest):
    ip = _client_ip(request)
    ua = _user_agent(request)
    user = authenticate_user(req.email, req.password)
    if not user:
        log_access(req.email, "login_failure", path="/auth/login", ip=ip, user_agent=ua,
                   detail="Credenciais inválidas")
        raise HTTPException(status_code=401, detail="E-mail ou senha incorretos")
    token = create_access_token({"sub": user["email"], "role": user["role"], "name": user["name"]})
    log_access(user["email"], "login_success", path="/auth/login", ip=ip, user_agent=ua,
               detail=f"role={user['role']}")
    return TokenResponse(
        access_token=token,
        user=UserOut(**user),
    )


@router.get("/auth/me", response_model=UserOut)
async def get_me(current_user: dict = Depends(get_current_user)):
    return UserOut(id=0, **current_user)


class PageViewEvent(BaseModel):
    tab: str = Field(min_length=1, max_length=80)


@router.post("/audit/page-view")
@limiter.limit("120/minute")
async def audit_page_view(
    request: Request,
    event: PageViewEvent,
    current_user: dict = Depends(get_current_user),
):
    log_access(
        current_user.get("email"),
        "page_view",
        path=event.tab,
        ip=_client_ip(request),
        user_agent=_user_agent(request),
    )
    return {"ok": True}


@router.get("/admin/users")
async def admin_list_users(admin: dict = Depends(require_admin)):
    return list_users()


@router.post("/admin/users")
@limiter.limit("10/minute")
async def admin_create_user(request: Request, req: UserCreate, admin: dict = Depends(require_admin)):
    err = create_user(req.email, req.password, req.name, req.role)
    if err:
        raise HTTPException(status_code=400, detail=err)
    log_access(admin.get("email"), "user_created", path="/admin/users",
               ip=_client_ip(request), user_agent=_user_agent(request),
               detail=f"created={req.email} role={req.role}")
    return {"message": f"Usuário {req.email} cadastrado com sucesso"}


@router.delete("/admin/users/{user_id}")
async def admin_delete_user(user_id: int, request: Request, admin: dict = Depends(require_admin)):
    err = delete_user(user_id)
    if err:
        raise HTTPException(status_code=400, detail=err)
    log_access(admin.get("email"), "user_deleted", path=f"/admin/users/{user_id}",
               ip=_client_ip(request), user_agent=_user_agent(request),
               detail=f"user_id={user_id}")
    return {"message": "Usuário removido"}


@router.get("/admin/access-logs")
async def admin_access_logs(
    limit: int = Query(200, ge=1, le=1000),
    offset: int = Query(0, ge=0),
    email: Optional[str] = Query(None, max_length=200),
    event_type: Optional[str] = Query(None, max_length=40),
    admin: dict = Depends(require_admin),
):
    return list_access_logs(limit=limit, offset=offset, email=email, event_type=event_type)
