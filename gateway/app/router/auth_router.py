from fastapi import APIRouter, HTTPException, Depends
from fastapi.security import HTTPBearer
from typing import Optional

auth_router = APIRouter(prefix="/auth", tags=["Authentication"])

security = HTTPBearer()



@auth_router.post("/login")
async def login():
    """로그인 엔드포인트"""
    return {"message": "Login endpoint"}

@auth_router.post("/logout")
async def logout():
    """로그아웃 엔드포인트"""
    return {"message": "Logout endpoint"}

@auth_router.get("/verify")
async def verify_token():
    """토큰 검증 엔드포인트"""
    return {"message": "Token verification endpoint"}
