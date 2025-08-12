from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import Optional
import json
import os
import httpx
from datetime import datetime
import pytz
import logging

# httpx 로그를 현재 시간으로 설정
os.environ['TZ'] = 'Asia/Seoul'
logging.basicConfig(level=logging.INFO)

router = APIRouter(prefix="/user", tags=["User Management"])

class SignupRequest(BaseModel):
    email: str
    password: str

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

def get_current_time():
    """현재 시간을 한국 시간으로 반환"""
    korea_tz = pytz.timezone('Asia/Seoul')
    return datetime.now(korea_tz)

@router.post("/signup", response_model=SignupResponse)
async def signup(request: SignupRequest):
    """
    회원가입 처리
    - JSON 파일로 데이터 저장
    - Docker Desktop에서 로그 확인 가능
    """
    try:
        current_time = get_current_time()
        
        # JSON 데이터 생성
        signup_data = {
            "timestamp": current_time.isoformat(),
            "userData": {
                "email": request.email,
                "password": request.password
            }
        }
        
        # Docker Desktop에서 로그 확인을 위한 콘솔 출력
        print("=== 회원가입 데이터 로그 ===")
        print(f"🕐 현재 시간: {current_time.strftime('%Y-%m-%d %H:%M:%S')}")
        print("사용자 입력 데이터:", request.dict())
        print("JSON 형태:", json.dumps(request.dict(), indent=2, ensure_ascii=False))
        print("==========================")
        print("회원가입 데이터:", json.dumps(signup_data, indent=2, ensure_ascii=False))
        
        # JSON 파일로 저장 (선택사항)
        log_dir = "/app/logs"
        os.makedirs(log_dir, exist_ok=True)
        
        log_file = os.path.join(log_dir, f"signup_{current_time.strftime('%Y%m%d_%H%M%S')}.json")
        with open(log_file, 'w', encoding='utf-8') as f:
            json.dump(signup_data, f, indent=2, ensure_ascii=False)
        
        # Auth Service로 데이터 전달 (선택사항)
        try:
            print("=== Auth Service로 회원가입 데이터 전달 시도 ===")
            async with httpx.AsyncClient() as client:
                auth_response = await client.post(
                    "http://auth-service:8005/auth/signup",
                    json=request.dict(),
                    timeout=5.0
                )
                print(f"Auth Service 응답: {auth_response.status_code}")
        except Exception as auth_error:
            print(f"Auth Service 연결 실패 (무시됨): {str(auth_error)}")
            # Auth Service 연결 실패는 무시하고 계속 진행
        
        return SignupResponse(
            status="success",
            message="회원가입이 완료되었습니다! Docker Desktop에서 로그를 확인하세요.",
            timestamp=current_time.isoformat(),
            user_data=request.dict()
        )
        
    except Exception as e:
        print(f"회원가입 오류: {str(e)}")
        raise HTTPException(status_code=500, detail=f"회원가입 중 오류가 발생했습니다: {str(e)}")

@router.post("/login", response_model=LoginResponse)
async def login(request: LoginRequest):
    """
    로그인 처리
    - Gateway에서 로그 처리
    - Auth Service로 데이터 전달
    - Docker Desktop에서 로그 확인 가능
    """
    try:
        current_time = get_current_time()
        
        # Gateway에서 로그 처리
        login_data = {
            "timestamp": current_time.isoformat(),
            "userData": {
                "email": request.email,
                "password": request.password
            }
        }
        
        # Railway/Docker Desktop에서 로그 확인을 위한 콘솔 출력
        print("=" * 60)
        print("🚀 === Gateway 로그인 데이터 로그 ===")
        print("=" * 60)
        print(f"🕐 현재 시간: {current_time.strftime('%Y-%m-%d %H:%M:%S')}")
        print("📥 사용자 입력 데이터:", request.dict())
        print("📄 JSON 형태:", json.dumps(request.dict(), indent=2, ensure_ascii=False))
        print("-" * 60)
        print("📝 로그인 데이터:", json.dumps(login_data, indent=2, ensure_ascii=False))
        print("=" * 60)
        
        # JSON 파일로 저장 (선택사항)
        log_dir = "/app/logs"
        os.makedirs(log_dir, exist_ok=True)
        
        log_file = os.path.join(log_dir, f"gateway_login_{current_time.strftime('%Y%m%d_%H%M%S')}.json")
        with open(log_file, 'w', encoding='utf-8') as f:
            json.dump(login_data, f, indent=2, ensure_ascii=False)
        
        # Auth Service로 데이터 전달
        print("=" * 60)
        print("🔄 === Auth Service로 데이터 전달 ===")
        print("=" * 60)
        print(f"🕐 현재 시간: {current_time.strftime('%Y-%m-%d %H:%M:%S')}")
        print("📤 전달할 데이터:", json.dumps(request.dict(), indent=2, ensure_ascii=False))
        print("🌐 Auth Service URL: http://auth-service:8005/auth/login")
        print("=" * 60)
        
        async with httpx.AsyncClient() as client:
            auth_response = await client.post(
                "http://auth-service:8005/auth/login",
                json=request.dict(),
                timeout=10.0
            )
            
            if auth_response.status_code == 200:
                auth_data = auth_response.json()
                print("Auth Service 응답:", json.dumps(auth_data, indent=2, ensure_ascii=False))
                
                return LoginResponse(
                    status="success",
                    message="로그인 성공! Gateway와 Auth Service에서 로그를 확인하세요.",
                    timestamp=current_time.isoformat(),
                    user_data=request.dict()
                )
            else:
                print(f"Auth Service 오류: {auth_response.status_code}")
                raise HTTPException(status_code=500, detail="Auth Service 연결 오류")
        
    except httpx.RequestError as e:
        print(f"Auth Service 연결 오류: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Auth Service 연결 오류: {str(e)}")
    except Exception as e:
        print(f"로그인 오류: {str(e)}")
        raise HTTPException(status_code=500, detail=f"로그인 중 오류가 발생했습니다: {str(e)}")

@router.get("/health")
async def user_health():
    """사용자 서비스 상태 확인"""
    return {"status": "healthy", "service": "user-service"}
