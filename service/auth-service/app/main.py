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

@app.on_event("startup")
async def startup_event():
    """앱 시작 시 실행"""
    logger.info("🚀 Auth Service 시작")
    try:
        await init_database()
    except Exception as e:
        logger.error(f"❌ 데이터베이스 초기화 실패: {str(e)}")
        # 데이터베이스 연결 실패해도 서비스는 계속 실행

# CORS 설정 - allow_credentials=True 시 와일드카드 금지
def get_cors_origins():
    """환경변수에서 CORS origins 가져오기"""
    origins_str = os.getenv("FRONTEND_ORIGIN", "")
    if origins_str:
        origins = [origin.strip() for origin in origins_str.split(",") if origin.strip()]
    else:
        # 기본값
        origins = [
            "http://localhost:3000",
            "http://localhost:8080",
            "http://127.0.0.1:3000",
            "https://www.minyoung.cloud",  # 커스텀 도메인 (www)
            "https://minyoung.cloud",      # 커스텀 도메인 (루트)
            "https://greensteel.vercel.app",  # Vercel 도메인
            "https://greensteel-gateway-production.up.railway.app",  # Railway Gateway
            "https://greensteel-gateway-production-eeb5.up.railway.app",  # 실제 Railway Gateway
            "https://greensteel-frontend.vercel.app",  # Vercel 프론트엔드
            "https://greensteel-gateway.railway.app",  # Railway Gateway
        ]
    logger.info(f"[Auth Service CORS] allow_origins={origins}")
    return origins

app.add_middleware(
    CORSMiddleware,
    allow_origins=get_cors_origins(),
    allow_credentials=True,  # HttpOnly 쿠키 사용을 위해 필수
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
    expose_headers=["*"],  # 응답 헤더 노출
)

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
        
        logger.info("=== Auth Service 로그인 처리 시작 ===")
        logger.info(f"로그인 요청: {request.dict()}")
        
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
                raise HTTPException(status_code=401, detail="이메일 또는 비밀번호가 올바르지 않습니다")
            
            # 세션 ID 생성
            session_id = create_session_id()
            
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
        
        logger.info("=== Auth Service 회원가입 처리 시작 ===")
        logger.info(f"회원가입 요청: {request.dict()}")
        
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
                raise HTTPException(status_code=400, detail="이미 존재하는 이메일입니다")
            
            # 비밀번호 해시화 (실제로는 bcrypt 사용 권장)
            password_hash = str(hash(request.password))
            
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
        session_id = request.cookies.get("session_id")
        
        if session_id:
            # Postgres에서 세션 삭제
            try:
                conn = await get_db_connection()
                await conn.execute("DELETE FROM sessions WHERE id = $1", session_id)
                await conn.close()
                logger.info(f"🚪 로그아웃: 세션 {session_id} 삭제")
            except Exception as db_error:
                logger.error(f"❌ 세션 삭제 중 데이터베이스 오류: {str(db_error)}")
        
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

@app.options("/{path:path}")
async def options_handler(request: Request, path: str):
    """
    OPTIONS 요청 처리 (CORS preflight)
    """
    # Origin 기반 동적 설정
    origin = request.headers.get("origin")
    allowed_origins = get_cors_origins()
    
    if origin and origin in allowed_origins:
        allow_origin = origin
    else:
        allow_origin = "https://www.minyoung.cloud"
    
    logger.info(f"🔄 Auth Service OPTIONS 요청 처리: {path} from {origin}")
    
    return Response(
        status_code=200,
        headers={
            "Access-Control-Allow-Origin": allow_origin,
            "Access-Control-Allow-Credentials": "true",
            "Access-Control-Allow-Methods": "GET, POST, PUT, DELETE, OPTIONS",
            "Access-Control-Allow-Headers": "*",
            "Access-Control-Expose-Headers": "*",
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

