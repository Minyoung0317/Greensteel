from dotenv import load_dotenv
from fastapi import FastAPI, Request, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import uvicorn
import logging
import traceback
import os
import sys
import json
from datetime import datetime
import pytz

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

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://localhost:8080",
        "https://www.minyoung.cloud",  # 커스텀 도메인 (www)
        "https://minyoung.cloud",      # 커스텀 도메인 (루트)
    ],
    allow_credentials=True,  # HttpOnly 쿠키 사용을 위해 필수
    allow_methods=["*"],
    allow_headers=["*"],
)





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

def get_current_time():
    """현재 시간을 한국 시간으로 반환"""
    korea_tz = pytz.timezone('Asia/Seoul')
    return datetime.now(korea_tz)

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
async def login(request: LoginRequest):
    """
    로그인 처리 - Gateway에서 전달받은 사용자 데이터 처리
    """
    try:
        current_time = get_current_time()
        
        logger.info("=== Auth Service 로그인 처리 시작 ===")
        logger.info(f"Gateway에서 전달받은 사용자 데이터: {request.dict()}")
        
        # Railway/Docker Desktop에서 로그 확인을 위한 콘솔 출력
        print("=" * 60)
        print("🔐 === Auth Service 로그인 데이터 로그 ===")
        print("=" * 60)
        print(f"🕐 현재 시간: {current_time.strftime('%Y-%m-%d %H:%M:%S')}")
        print("📥 Gateway에서 전달받은 데이터:")
        print("사용자 입력 데이터:", request.dict())
        print("JSON 형태:", json.dumps(request.dict(), indent=2, ensure_ascii=False))
        print("-" * 60)
        
        # JSON 데이터 생성
        login_data = {
            "timestamp": current_time.isoformat(),
            "userData": {
                "email": request.email,
                "password": request.password
            }
        }
        
        print("📝 Auth Service에서 생성한 로그인 데이터:")
        print("로그인 데이터:", json.dumps(login_data, indent=2, ensure_ascii=False))
        print("=" * 60)
        
        # JSON 파일로 저장 (선택사항)
        log_dir = "/app/logs"
        os.makedirs(log_dir, exist_ok=True)
        
        log_file = os.path.join(log_dir, f"auth_login_{current_time.strftime('%Y%m%d_%H%M%S')}.json")
        with open(log_file, 'w', encoding='utf-8') as f:
            json.dump(login_data, f, indent=2, ensure_ascii=False)
        
        return LoginResponse(
            status="✅ success",
            message="✅ Auth Service에서 로그인 성공! Docker Desktop에서 로그를 확인하세요.",
            timestamp=current_time.isoformat(),
            user_data=request.dict()
        )
        
    except Exception as e:
        logger.error(f"Auth Service 로그인 오류: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Auth Service 로그인 중 오류가 발생했습니다: {str(e)}")

@app.post("/auth/signup")
async def signup(request: SignupRequest):
    """
    회원가입 처리 - Gateway에서 전달받은 사용자 데이터 처리
    """
    try:
        current_time = get_current_time()
        
        logger.info("=== Auth Service 회원가입 처리 시작 ===")
        logger.info(f"Gateway에서 전달받은 사용자 데이터: {request.dict()}")
        
        # Railway/Docker Desktop에서 로그 확인을 위한 콘솔 출력
        print("=" * 60)
        print("🔐 === Auth Service 회원가입 데이터 로그 ===")
        print("=" * 60)
        print(f"🕐 현재 시간: {current_time.strftime('%Y-%m-%d %H:%M:%S')}")
        print("📥 Gateway에서 전달받은 데이터:")
        print("사용자 입력 데이터:", request.dict())
        print("JSON 형태:", json.dumps(request.dict(), indent=2, ensure_ascii=False))
        print("-" * 60)
        
        # JSON 데이터 생성
        signup_data = {
            "timestamp": current_time.isoformat(),
            "userData": {
                "email": request.email,
                "password": request.password
            }
        }
        
        print("📝 Auth Service에서 생성한 회원가입 데이터:")
        print("회원가입 데이터:", json.dumps(signup_data, indent=2, ensure_ascii=False))
        print("=" * 60)
        
        # JSON 파일로 저장 (선택사항)
        log_dir = "/app/logs"
        os.makedirs(log_dir, exist_ok=True)
        
        log_file = os.path.join(log_dir, f"auth_signup_{current_time.strftime('%Y%m%d_%H%M%S')}.json")
        with open(log_file, 'w', encoding='utf-8') as f:
            json.dump(signup_data, f, indent=2, ensure_ascii=False)
        
        return SignupResponse(
            status="✅ success",
            message="✅ Auth Service에서 회원가입 성공! Docker Desktop에서 로그를 확인하세요.",
            timestamp=current_time.isoformat(),
            user_data=request.dict()
        )
        
    except Exception as e:
        logger.error(f"Auth Service 회원가입 오류: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Auth Service 회원가입 중 오류가 발생했습니다: {str(e)}")



if __name__ == "__main__":
    import os
    
    # Railway 환경에서는 PORT 환경 변수를 사용, 로컬에서는 8005 사용
    if os.getenv("RAILWAY_ENVIRONMENT") == "true":
        # Railway 환경에서는 할당된 포트 사용
        port_str = os.getenv("PORT", "8005")
        try:
            port = int(port_str)
        except ValueError:
            logger.error(f"잘못된 포트 값: {port_str}, 기본값 8005 사용")
            port = 8005
    else:
        # 로컬/Docker 환경에서는 8005 포트 사용
        port = 8005
    
    logger.info(f"💻 Auth Service 시작 - 포트: {port}")
    logger.info(f"환경: {'Railway' if os.getenv('RAILWAY_ENVIRONMENT') == 'true' else 'Local/Docker'}")
    logger.info(f"환경 변수 PORT: {os.getenv('PORT', '설정되지 않음')}")
    
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=port,
        reload=False,  # Railway에서는 reload 비활성화
        log_level="info"
    )