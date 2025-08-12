from dotenv import load_dotenv
from fastapi import FastAPI, Request, HTTPException, Response
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import uvicorn
import logging
import traceback
import os
import sys
import json
from datetime import datetime, timedelta
import pytz
import secrets
from typing import Optional, Dict, Any

# httpx 로그를 현재 시간으로 설정
os.environ['TZ'] = 'Asia/Seoul'

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger("auth-service")

if os.getenv("RAILWAY_ENVIRONMENT") != "true":
    load_dotenv()

app = FastAPI(
    title="Account Service API",
    description="Account 서비스",
    version="1.0.0",
)

# CORS 설정 - allow_credentials=True 시 wildcard 금지
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://localhost:8080",
        "https://www.minyoung.cloud",  # 커스텀 도메인 (www)
        "https://minyoung.cloud",      # 커스텀 도메인 (루트)
        "https://greensteel.vercel.app",  # Vercel 도메인
        "https://greensteel-gateway-production.up.railway.app",  # Railway Gateway
        "https://*.vercel.app",  # Vercel 서브도메인
        "https://*.railway.app",  # Railway 서브도메인
    ],
    allow_credentials=True,  # HttpOnly 쿠키 사용을 위해 필수
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
    expose_headers=["*"],  # 응답 헤더 노출
)

# 세션 저장소 (실제로는 Redis나 Postgres 사용)
sessions: Dict[str, Dict[str, Any]] = {}

# Pydantic 모델 정의
class LoginRequest(BaseModel):
    email: str
    password: str

class SignupRequest(BaseModel):
    email: str
    password: str

class LoginResponse(BaseModel):
    status: str
    message: str
    timestamp: str
    user_data: dict

class SignupResponse(BaseModel):
    status: str
    message: str
    timestamp: str
    user_data: dict

class SessionData(BaseModel):
    user_id: str
    email: str
    created_at: datetime
    expires_at: datetime

def get_current_time():
    """현재 시간을 한국 시간으로 반환"""
    korea_tz = pytz.timezone('Asia/Seoul')
    return datetime.now(korea_tz)

def create_session_id() -> str:
    """세션 ID 생성"""
    return secrets.token_urlsafe(32)

def create_session(user_id: str, email: str) -> str:
    """새 세션 생성"""
    session_id = create_session_id()
    expires_at = get_current_time() + timedelta(hours=24)  # 24시간 유효
    
    sessions[session_id] = {
        "user_id": user_id,
        "email": email,
        "created_at": get_current_time(),
        "expires_at": expires_at
    }
    
    logger.info(f"🔐 세션 생성: {session_id} for user: {email}")
    return session_id

def get_session(session_id: str) -> Optional[Dict[str, Any]]:
    """세션 조회"""
    if session_id not in sessions:
        return None
    
    session = sessions[session_id]
    if get_current_time() > session["expires_at"]:
        del sessions[session_id]
        return None
    
    return session

def delete_session(session_id: str):
    """세션 삭제"""
    if session_id in sessions:
        del sessions[session_id]
        logger.info(f"🗑️ 세션 삭제: {session_id}")

@app.middleware("http")
async def log_requests(request: Request, call_next):
    logger.info(f"📥 요청: {request.method} {request.url.path} (클라이언트: {request.client.host})")
    try:
        response = await call_next(request)
        logger.info(f"📤 응답: {response.status_code}")
        return response
    except Exception as e:
        logger.error(f"❌ 요청 처리 중 오류: {str(e)}")
        logger.error(traceback.format_exc())
        raise

@app.post("/auth/login")
async def login(request: LoginRequest, response: Response):
    """
    로그인 처리 - 세션 쿠키 기반
    """
    try:
        current_time = get_current_time()
        
        logger.info("=== Auth Service 로그인 처리 시작 ===")
        logger.info(f"로그인 요청: {request.dict()}")
        
        # 실제로는 Postgres에서 사용자 검증
        # 여기서는 간단한 검증 로직 사용
        if not request.email or not request.password:
            raise HTTPException(status_code=400, detail="이메일과 비밀번호를 입력해주세요")
        
        # 사용자 검증 (실제로는 DB 조회)
        user_id = f"user_{hash(request.email) % 10000}"
        
        # 세션 생성
        session_id = create_session(user_id, request.email)
        
        # HttpOnly 쿠키 설정
        response.set_cookie(
            key="session_id",
            value=session_id,
            httponly=True,
            secure=False,  # 개발 환경에서는 False, 프로덕션에서는 True
            samesite="lax",  # CSRF 방지
            max_age=86400,  # 24시간
            path="/",
            domain=None  # 현재 도메인에서만 유효
        )
        
        logger.info(f"🍪 세션 쿠키 설정: {session_id}")
        
        return LoginResponse(
            status="success",
            message="로그인이 완료되었습니다.",
            timestamp=current_time.isoformat(),
            user_data={
                "user_id": user_id,
                "email": request.email,
                "session_id": session_id
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ 로그인 처리 중 오류: {str(e)}")
        raise HTTPException(status_code=500, detail=f"로그인 처리 실패: {str(e)}")

@app.post("/auth/signup")
async def signup(request: SignupRequest):
    """
    회원가입 처리
    """
    try:
        current_time = get_current_time()
        
        logger.info("=== Auth Service 회원가입 처리 시작 ===")
        logger.info(f"회원가입 요청: {request.dict()}")
        
        # 실제로는 Postgres에 사용자 저장
        # 여기서는 간단한 처리
        if not request.email or not request.password:
            raise HTTPException(status_code=400, detail="이메일과 비밀번호를 입력해주세요")
        
        user_id = f"user_{hash(request.email) % 10000}"
        
        # JSON 파일로 저장 (임시)
        log_dir = "/app/logs"
        os.makedirs(log_dir, exist_ok=True)
        
        signup_data = {
            "user_id": user_id,
            "email": request.email,
            "password": request.password,  # 실제로는 해시화
            "created_at": current_time.isoformat()
        }
        
        log_file = os.path.join(log_dir, f"signup_{current_time.strftime('%Y%m%d_%H%M%S')}.json")
        with open(log_file, 'w', encoding='utf-8') as f:
            json.dump(signup_data, f, indent=2, ensure_ascii=False)
        
        logger.info(f"💾 사용자 데이터 저장: {log_file}")
        
        return SignupResponse(
            status="success",
            message="회원가입이 완료되었습니다.",
            timestamp=current_time.isoformat(),
            user_data={
                "user_id": user_id,
                "email": request.email
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ 회원가입 처리 중 오류: {str(e)}")
        raise HTTPException(status_code=500, detail=f"회원가입 처리 실패: {str(e)}")

@app.post("/auth/logout")
async def logout(request: Request, response: Response):
    """
    로그아웃 처리 - 세션 쿠키 삭제
    """
    try:
        session_id = request.cookies.get("session_id")
        
        if session_id:
            delete_session(session_id)
            logger.info(f"🚪 로그아웃: 세션 {session_id} 삭제")
        
        # 쿠키 삭제
        response.delete_cookie(
            key="session_id",
            path="/"
        )
        
        return {"status": "success", "message": "로그아웃이 완료되었습니다."}
        
    except Exception as e:
        logger.error(f"❌ 로그아웃 처리 중 오류: {str(e)}")
        raise HTTPException(status_code=500, detail=f"로그아웃 처리 실패: {str(e)}")

@app.get("/auth/verify")
async def verify_session(request: Request):
    """
    세션 검증
    """
    try:
        session_id = request.cookies.get("session_id")
        
        if not session_id:
            raise HTTPException(status_code=401, detail="세션이 없습니다")
        
        session = get_session(session_id)
        if not session:
            raise HTTPException(status_code=401, detail="유효하지 않은 세션입니다")
        
        logger.info(f"✅ 세션 검증 성공: {session_id}")
        
        return {
            "status": "success",
            "user_data": {
                "user_id": session["user_id"],
                "email": session["email"],
                "created_at": session["created_at"].isoformat()
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ 세션 검증 중 오류: {str(e)}")
        raise HTTPException(status_code=500, detail=f"세션 검증 실패: {str(e)}")

@app.options("/{path:path}")
async def options_handler(request: Request, path: str):
    """
    OPTIONS 요청 처리 (CORS preflight)
    """
    return Response(
        status_code=200,
        headers={
            "Access-Control-Allow-Origin": request.headers.get("origin", "*"),
            "Access-Control-Allow-Credentials": "true",
            "Access-Control-Allow-Methods": "GET, POST, PUT, DELETE, OPTIONS",
            "Access-Control-Allow-Headers": "*",
            "Access-Control-Max-Age": "86400",
        }
    )

@app.get("/")
async def root():
    return {"message": "Auth Service is running", "endpoints": ["/auth/login", "/auth/signup", "/auth/logout", "/auth/verify"]}

if __name__ == "__main__":
    port = int(os.getenv("PORT", 8081))
    logger.info(f"🚀 Auth Service 시작 - 포트: {port}")
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=port,
        reload=False,
        log_level="info"
    )

