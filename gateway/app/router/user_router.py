from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import Optional
import json
import os
from datetime import datetime

router = APIRouter(prefix="/user", tags=["User Management"])

class SignupRequest(BaseModel):
    name: str
    unit: str
    method: str

class LoginRequest(BaseModel):
    email: str
    password: str

class SignupResponse(BaseModel):
    status: str
    message: str
    timestamp: str
    user_data: dict

class LoginResponse(BaseModel):
    status: str
    message: str
    timestamp: str
    user_data: dict

@router.post("/signup", response_model=SignupResponse)
async def signup(request: SignupRequest):
    """
    회원가입 처리
    - JSON 파일로 데이터 저장
    - Docker Desktop에서 로그 확인 가능
    """
    try:
        # JSON 데이터 생성
        signup_data = {
            "timestamp": datetime.now().isoformat(),
            "userData": {
                "name": request.name,
                "unit": request.unit,
                "method": request.method
            }
        }
        
        # Docker Desktop에서 로그 확인을 위한 콘솔 출력
        print("=== 회원가입 데이터 로그 ===")
        print("사용자 입력 데이터:", request.dict())
        print("JSON 형태:", json.dumps(request.dict(), indent=2, ensure_ascii=False))
        print("==========================")
        print("회원가입 데이터:", json.dumps(signup_data, indent=2, ensure_ascii=False))
        
        # JSON 파일로 저장 (선택사항)
        log_dir = "/app/logs"
        os.makedirs(log_dir, exist_ok=True)
        
        log_file = os.path.join(log_dir, f"signup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json")
        with open(log_file, 'w', encoding='utf-8') as f:
            json.dump(signup_data, f, indent=2, ensure_ascii=False)
        
        return SignupResponse(
            status="success",
            message="회원가입이 완료되었습니다! Docker Desktop에서 로그를 확인하세요.",
            timestamp=datetime.now().isoformat(),
            user_data=request.dict()
        )
        
    except Exception as e:
        print(f"회원가입 오류: {str(e)}")
        raise HTTPException(status_code=500, detail=f"회원가입 중 오류가 발생했습니다: {str(e)}")

@router.post("/login", response_model=LoginResponse)
async def login(request: LoginRequest):
    """
    로그인 처리
    - JSON 파일로 데이터 저장
    - Docker Desktop에서 로그 확인 가능
    """
    try:
        # JSON 데이터 생성
        login_data = {
            "timestamp": datetime.now().isoformat(),
            "userData": {
                "email": request.email,
                "password": request.password
            }
        }
        
        # Docker Desktop에서 로그 확인을 위한 콘솔 출력
        print("=== 로그인 데이터 로그 ===")
        print("사용자 입력 데이터:", request.dict())
        print("JSON 형태:", json.dumps(request.dict(), indent=2, ensure_ascii=False))
        print("==========================")
        print("로그인 데이터:", json.dumps(login_data, indent=2, ensure_ascii=False))
        
        # JSON 파일로 저장 (선택사항)
        log_dir = "/app/logs"
        os.makedirs(log_dir, exist_ok=True)
        
        log_file = os.path.join(log_dir, f"login_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json")
        with open(log_file, 'w', encoding='utf-8') as f:
            json.dump(login_data, f, indent=2, ensure_ascii=False)
        
        return LoginResponse(
            status="success",
            message="로그인 성공! Docker Desktop에서 로그를 확인하세요.",
            timestamp=datetime.now().isoformat(),
            user_data=request.dict()
        )
        
    except Exception as e:
        print(f"로그인 오류: {str(e)}")
        raise HTTPException(status_code=500, detail=f"로그인 중 오류가 발생했습니다: {str(e)}")

@router.get("/health")
async def user_health():
    """사용자 서비스 상태 확인"""
    return {"status": "healthy", "service": "user-service"}
