#!/usr/bin/env python3.11
"""
Auth Service - Python 3.11
"""

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
from typing import Optional
import asyncpg
import asyncio

# 한국 시간대 설정
os.environ['TZ'] = 'Asia/Seoul'

# 로깅 설정 (한국 시간대 적용)
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler(sys.stdout)],
    datefmt="%Y-%m-%d %H:%M:%S"
)
logger = logging.getLogger("auth-service")

# Uvicorn 액세스 로그 형식 통일
uvicorn_access_logger = logging.getLogger("uvicorn.access")
uvicorn_access_logger.handlers.clear()
uvicorn_access_handler = logging.StreamHandler(sys.stdout)
uvicorn_access_handler.setFormatter(logging.Formatter(
    "%(asctime)s - uvicorn.access - %(levelname)s - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
))
uvicorn_access_logger.addHandler(uvicorn_access_handler)
uvicorn_access_logger.setLevel(logging.INFO)

if os.getenv("RAILWAY_ENVIRONMENT") != "true":
    load_dotenv()

# Railway 환경 감지 개선
RAILWAY_ENV = (
    os.getenv("RAILWAY_ENVIRONMENT", "false").lower() == "true" or
    os.getenv("RAILWAY_ENVIRONMENT", "").lower() == "production"
)

# Railway 환경변수 디버깅
logger.info(f"🔍 Auth Service Railway 환경변수 디버깅:")
logger.info(f"   RAILWAY_ENVIRONMENT: {os.getenv('RAILWAY_ENVIRONMENT', 'NOT_SET')}")
logger.info(f"   PORT: {os.getenv('PORT', 'NOT_SET')}")
logger.info(f"   DATABASE_URL: {os.getenv('DATABASE_URL', 'NOT_SET')[:50]}..." if os.getenv('DATABASE_URL') else "NOT_SET")

# Railway 환경에서 로그 지속성 설정
if RAILWAY_ENV:
    logger.info("🚂 Railway 환경에서 로그 지속성 설정")
    import sys
    sys.stdout.flush()
    sys.stderr.flush()
    
    # 모든 로거에 대해 강제 출력 설정
    for handler in logging.getLogger().handlers:
        handler.flush()
    
    logger.info("🔄 Auth Service Railway 로그 출력 강제 플러시 완료")
else:
    # Docker 환경에서도 동일한 로깅 설정
    logger.info("🐳 Docker 환경에서 로그 지속성 설정")
    import sys
    sys.stdout.flush()
    sys.stderr.flush()
    
    # 모든 로거에 대해 강제 출력 설정
    for handler in logging.getLogger().handlers:
        handler.flush()
    
    logger.info("🔄 Auth Service Docker 로그 출력 강제 플러시 완료")

app = FastAPI(
    title="Account Service API",
    description="Account 서비스",
    version="1.0.0",
)

@app.on_event("startup")
async def startup_event():
    """앱 시작 시 실행"""
    logger.info("🚀 Auth Service 시작")
    try:
        await init_database()
    except Exception as e:
        logger.error(f"❌ 데이터베이스 초기화 실패: {str(e)}")
        # 데이터베이스 연결 실패해도 서비스는 계속 실행

# Auth Service는 내부 통신만 하므로 CORS 설정 불필요
logger.info("🔒 Auth Service - 내부 통신만 처리 (CORS 설정 없음)")

# Postgres 연결
async def get_db_connection():
    """Postgres 데이터베이스 연결"""
    try:
        database_url = os.getenv("DATABASE_URL", "postgresql://postgres:password@postgres:5432/greensteel")
        conn = await asyncpg.connect(database_url)
        return conn
    except Exception as e:
        logger.error(f"❌ 데이터베이스 연결 실패: {str(e)}")
        raise

async def init_database():
    """데이터베이스 초기화 (테이블 생성)"""
    try:
        conn = await get_db_connection()
        
        # 사용자 테이블 생성
        await conn.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id SERIAL PRIMARY KEY,
                email VARCHAR(255) UNIQUE NOT NULL,
                password_hash VARCHAR(255) NOT NULL,
                created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # 세션 테이블 생성
        await conn.execute('''
            CREATE TABLE IF NOT EXISTS sessions (
                id VARCHAR(255) PRIMARY KEY,
                user_id INTEGER REFERENCES users(id),
                email VARCHAR(255) NOT NULL,
                created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
                expires_at TIMESTAMP WITH TIME ZONE NOT NULL
            )
        ''')
        
        await conn.close()
        logger.info("✅ 데이터베이스 초기화 완료")
    except Exception as e:
        logger.error(f"❌ 데이터베이스 초기화 실패: {str(e)}")

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
        
        logger.info("🚀 === Auth Service 로그인 처리 시작 ===")
        logger.info(f"📥 로그인 요청: {request.dict()}")
        logger.info(f"⏰ 요청 시간: {current_time.isoformat()}")
        
        if not request.email or not request.password:
            raise HTTPException(status_code=400, detail="이메일과 비밀번호를 입력해주세요")
        
        # Postgres에서 사용자 검증
        try:
            conn = await get_db_connection()
            
            # 비밀번호 해시화 (실제로는 bcrypt 사용 권장)
            password_hash = str(hash(request.password))
            
            # 사용자 조회
            user = await conn.fetchrow(
                "SELECT id, email FROM users WHERE email = $1 AND password_hash = $2",
                request.email, password_hash
            )
            
            if not user:
                await conn.close()
                logger.warning(f"❌ 로그인 실패: 이메일 또는 비밀번호 불일치 - {request.email}")
                raise HTTPException(status_code=401, detail="이메일 또는 비밀번호가 올바르지 않습니다")
            
            logger.info(f"✅ 사용자 인증 성공: ID={user['id']}, Email={user['email']}")
            
            # 세션 ID 생성
            session_id = create_session_id()
            logger.info(f"🔑 세션 ID 생성: {session_id}")
            
            # Postgres에 세션 저장
            await conn.execute(
                """
                INSERT INTO sessions (id, user_id, email, expires_at)
                VALUES ($1, $2, $3, $4)
                """,
                session_id, user['id'], user['email'], 
                get_current_time() + timedelta(hours=24)
            )
            
            await conn.close()
            logger.info(f"💾 세션 데이터베이스 저장 완료: UserID={user['id']}, SessionID={session_id}")
            
            # HttpOnly 쿠키 설정
            response.set_cookie(
                key="session_id",
                value=session_id,
                httponly=True,
                secure=True,  # HTTPS 환경에서만 전송
                samesite="lax",  # CSRF 방지
                max_age=86400,  # 24시간
                path="/",
                domain=None  # 현재 도메인에서만 유효
            )
            
            logger.info(f"🍪 세션 쿠키 설정: {session_id}")
            
            # 응답 데이터 로깅
            response_data = {
                "status": "success",
                "message": "로그인이 완료되었습니다.",
                "timestamp": current_time.isoformat(),
                "user_data": {
                    "user_id": user['id'],
                    "email": user['email'],
                    "session_id": session_id
                }
            }
            logger.info(f"📤 로그인 응답 데이터: {response_data}")
            
            return LoginResponse(
                status="success",
                message="로그인이 완료되었습니다.",
                timestamp=current_time.isoformat(),
                user_data={
                    "user_id": user['id'],
                    "email": user['email'],
                    "session_id": session_id
                }
            )
            
        except Exception as db_error:
            logger.error(f"❌ 데이터베이스 오류: {str(db_error)}")
            raise HTTPException(status_code=500, detail="데이터베이스 오류가 발생했습니다")
        
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
        
        logger.info("🚀 === Auth Service 회원가입 처리 시작 ===")
        logger.info(f"📥 회원가입 요청: {request.dict()}")
        logger.info(f"⏰ 요청 시간: {current_time.isoformat()}")
        
        if not request.email or not request.password:
            raise HTTPException(status_code=400, detail="이메일과 비밀번호를 입력해주세요")
        
        # Postgres에 사용자 저장
        try:
            conn = await get_db_connection()
            
            # 이메일 중복 확인
            existing_user = await conn.fetchrow(
                "SELECT id FROM users WHERE email = $1",
                request.email
            )
            
            if existing_user:
                await conn.close()
                logger.warning(f"❌ 회원가입 실패: 이미 존재하는 이메일 - {request.email}")
                raise HTTPException(status_code=400, detail="이미 존재하는 이메일입니다")
            
            logger.info(f"✅ 이메일 중복 확인 통과: {request.email}")
            
            # 비밀번호 해시화 (실제로는 bcrypt 사용 권장)
            password_hash = str(hash(request.password))
            logger.info(f"🔐 비밀번호 해시화 완료: {request.email}")
            
            # 사용자 저장
            user = await conn.fetchrow(
                """
                INSERT INTO users (email, password_hash)
                VALUES ($1, $2)
                RETURNING id, email, created_at
                """,
                request.email, password_hash
            )
            
            await conn.close()
            
            logger.info(f"💾 사용자 저장 완료: {user['email']} (ID: {user['id']})")
            
            # 응답 데이터 로깅
            response_data = {
                "status": "success",
                "message": "회원가입이 완료되었습니다.",
                "timestamp": current_time.isoformat(),
                "user_data": {
                    "user_id": user['id'],
                    "email": user['email'],
                    "created_at": user['created_at'].isoformat()
                }
            }
            logger.info(f"📤 회원가입 응답 데이터: {response_data}")
            
            return SignupResponse(
                status="success",
                message="회원가입이 완료되었습니다.",
                timestamp=current_time.isoformat(),
                user_data={
                    "user_id": user['id'],
                    "email": user['email'],
                    "created_at": user['created_at'].isoformat()
                }
            )
            
        except asyncpg.UniqueViolationError:
            raise HTTPException(status_code=400, detail="이미 존재하는 이메일입니다")
        except Exception as db_error:
            logger.error(f"❌ 데이터베이스 오류: {str(db_error)}")
            raise HTTPException(status_code=500, detail="데이터베이스 오류가 발생했습니다")
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ 회원가입 처리 중 오류: {str(e)}")
        raise HTTPException(status_code=500, detail=f"회원가입 처리 실패: {str(e)}")

@app.post("/auth/logout")
async def logout(request: Request, response: Response):
    """
    로그아웃 처리 - Postgres에서 세션 삭제
    """
    try:
        current_time = get_current_time()
        logger.info("🚀 === Auth Service 로그아웃 처리 시작 ===")
        logger.info(f"⏰ 요청 시간: {current_time.isoformat()}")
        
        session_id = request.cookies.get("session_id")
        logger.info(f"🍪 세션 ID 확인: {session_id}")
        
        if session_id:
            # Postgres에서 세션 삭제
            try:
                conn = await get_db_connection()
                
                # 세션 정보 조회 (삭제 전)
                session_info = await conn.fetchrow(
                    "SELECT user_id, email FROM sessions WHERE id = $1",
                    session_id
                )
                
                if session_info:
                    logger.info(f"👤 로그아웃 사용자: UserID={session_info['user_id']}, Email={session_info['email']}")
                
                await conn.execute("DELETE FROM sessions WHERE id = $1", session_id)
                await conn.close()
                logger.info(f"🚪 로그아웃: 세션 {session_id} 삭제 완료")
            except Exception as db_error:
                logger.error(f"❌ 세션 삭제 중 데이터베이스 오류: {str(db_error)}")
        else:
            logger.warning("⚠️ 로그아웃: 세션 ID가 없음")
        
        # 쿠키 삭제
        response.delete_cookie(
            key="session_id",
            path="/"
        )
        logger.info("🍪 세션 쿠키 삭제 완료")
        
        response_data = {"status": "success", "message": "로그아웃이 완료되었습니다."}
        logger.info(f"📤 로그아웃 응답 데이터: {response_data}")
        
        return response_data
        
    except Exception as e:
        logger.error(f"❌ 로그아웃 처리 중 오류: {str(e)}")
        raise HTTPException(status_code=500, detail=f"로그아웃 처리 실패: {str(e)}")

@app.get("/auth/verify")
async def verify_session(request: Request):
    """
    세션 검증 - Postgres에서 세션 확인
    """
    try:
        session_id = request.cookies.get("session_id")
        
        if not session_id:
            raise HTTPException(status_code=401, detail="세션이 없습니다")
        
        # Postgres에서 세션 확인
        try:
            conn = await get_db_connection()
            
            session = await conn.fetchrow(
                """
                SELECT s.id, s.user_id, s.email, s.created_at, s.expires_at, u.email as user_email
                FROM sessions s
                JOIN users u ON s.user_id = u.id
                WHERE s.id = $1 AND s.expires_at > NOW()
                """,
                session_id
            )
            
            await conn.close()
            
            if not session:
                raise HTTPException(status_code=401, detail="유효하지 않은 세션입니다")
            
            logger.info(f"✅ 세션 검증 성공: {session_id}")
            
            return {
                "status": "success",
                "user_data": {
                    "user_id": session["user_id"],
                    "email": session["user_email"],
                    "created_at": session["created_at"].isoformat()
                }
            }
            
        except Exception as db_error:
            logger.error(f"❌ 데이터베이스 오류: {str(db_error)}")
            raise HTTPException(status_code=500, detail="데이터베이스 오류가 발생했습니다")
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ 세션 검증 중 오류: {str(e)}")
        raise HTTPException(status_code=500, detail=f"세션 검증 실패: {str(e)}")



@app.get("/")
async def root():
    return {"message": "Auth Service is running", "endpoints": ["/auth/login", "/auth/signup", "/auth/logout", "/auth/verify"]}

@app.get("/healthz")
async def health_check():
    """헬스 체크 엔드포인트"""
    try:
        # 데이터베이스 연결 테스트
        conn = await get_db_connection()
        await conn.close()
        db_status = "healthy"
    except Exception as e:
        db_status = f"unhealthy: {str(e)}"
    
    return {
        "status": "healthy",
        "service": "auth-service",
        "database": db_status,
        "timestamp": datetime.now().isoformat(),
        "environment": "Railway" if os.getenv("RAILWAY_ENVIRONMENT") == "true" else "Local/Docker",
        "environment_vars": {
            "RAILWAY_ENVIRONMENT": os.getenv("RAILWAY_ENVIRONMENT", "NOT_SET"),
            "PORT": os.getenv("PORT", "NOT_SET"),
            "DATABASE_URL": "SET" if os.getenv("DATABASE_URL") else "NOT_SET"
        }
    }

if __name__ == "__main__":
    port = int(os.getenv("PORT", 8081))
    logger.info(f"🚀 Auth Service 시작 - 포트: {port}")
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=port,
        reload=False,
        log_level="info",
        access_log=True,
        log_config=None  # 우리가 설정한 로깅 설정 사용
    )

