from typing import Optional, List
from fastapi import APIRouter, FastAPI, Request, UploadFile, File, Query, HTTPException, Form, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, FileResponse
from fastapi.staticfiles import StaticFiles
import os
import logging
import sys
import uvicorn
import datetime
import json
from dotenv import load_dotenv
from contextlib import asynccontextmanager

from app.router.auth_router import router as auth_router
from app.router.user_router import router as user_router
from app.router.chatbot_router import router as chatbot_router
from app.www.google.jwt_auth_middleware import AuthMiddleware
from app.domain.discovery.model.service_discovery import ServiceDiscovery
from app.domain.discovery.model.service_type import ServiceType
from app.common.utility.constant.settings import Settings
from app.common.utility.factory.response_factory import ResponseFactory

# Railway 환경에서는 dotenv 로드하지 않음
if os.getenv("RAILWAY_ENVIRONMENT") != "true":
    load_dotenv()

# 로깅 설정 강화
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger("gateway_api")

@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("🚀 Gateway API 서비스 시작")
    logger.info(f"환경: {'Railway' if os.getenv('RAILWAY_ENVIRONMENT') == 'true' else 'Local/Docker'}")
    logger.info(f"포트: {os.getenv('PORT', '8080')}")
    # Settings 초기화 및 앱 state에 등록
    app.state.settings = Settings()
    yield
    logger.info("🛑 Gateway API 서비스 종료")

app = FastAPI(
    title="Gateway API",
    description="Gateway API for GreenSteel",
    version="0.1.0",
    docs_url="/docs",
    lifespan=lifespan
)

# CORS 설정 - allow_credentials=True 시 wildcard 금지
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",  # 로컬 접근
        "http://127.0.0.1:3000",  # 로컬 IP 접근
        "http://frontend:3000",   # Docker 내부 네트워크
        "https://greensteel-48kl4yapx-bagm922-7953s-projects.vercel.app",  # Vercel 프론트엔드
        "https://www.minyoung.cloud",  # 커스텀 도메인 (www)
        "https://minyoung.cloud",  # 커스텀 도메인 (루트)
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

app.add_middleware(AuthMiddleware)

# Frontend 정적 파일 서빙 (개발 모드에서는 Next.js dev server 사용)
@app.get("/")
async def root():
    return {"message": "GreenSteel Gateway API", "docs": "/docs"}

gateway_router = APIRouter(prefix="/api/v1", tags=["Gateway API"])
gateway_router.include_router(auth_router)
gateway_router.include_router(user_router)
gateway_router.include_router(chatbot_router)
app.include_router(gateway_router)

# 🪡🪡🪡 파일이 필요한 서비스 목록 (현재는 없음)
FILE_REQUIRED_SERVICES = set()



# GET 프록시 제거 - POST 방식만 지원

# 파일 업로드 및 일반 JSON 요청 모두 처리, JWT 적용
@gateway_router.post("/{service}/{path:path}", summary="POST 프록시")
async def proxy_post(
    service: ServiceType, 
    path: str,
    request: Request,
    file: Optional[UploadFile] = None,
    sheet_names: Optional[List[str]] = Query(None, alias="sheet_name")
):
    try:
        # 로깅 강화
        logger.info(f"🌈 POST 요청 받음: 서비스={service}, 경로={path}")
        if file:
            logger.info(f"파일명: {file.filename}, 시트 이름: {sheet_names if sheet_names else '없음'}")
        
        # 요청 본문 로깅 (auth-service로 전달할 데이터)
        try:
            body = await request.body()
            if body:
                logger.info(f"📝 요청 데이터 크기: {len(body)} bytes")
                # auth-service로 데이터 로그 전달
                await log_to_auth_service(service, path, body)
        except Exception as e:
            logger.warning(f"요청 본문 읽기 실패: {str(e)}")

        # 서비스 팩토리 생성
        factory = ServiceDiscovery(service_type=service)
        
        # 요청 파라미터 초기화
        files = None
        params = None
        data = None
        
        # 헤더 전달 (JWT 및 사용자 ID - 미들웨어에서 이미 X-User-Id 헤더가 추가됨)
        headers = dict(request.headers)
        
        # 파일이 필요한 서비스 처리
        if service in FILE_REQUIRED_SERVICES:
            # 파일이 필요한 서비스인 경우
            
            # 서비스 URI가 upload인 경우만 파일 체크
            if "upload" in path and not file:
                raise HTTPException(status_code=400, detail=f"서비스 {service}에는 파일 업로드가 필요합니다.")
            
            # 파일이 제공된 경우 처리
            if file:
                file_content = await file.read()
                files = {'file': (file.filename, file_content, file.content_type)}
                
                # 파일 위치 되돌리기 (다른 코드에서 다시 읽을 수 있도록)
                await file.seek(0)
            
            # 시트 이름이 제공된 경우 처리
            if sheet_names:
                params = {'sheet_name': sheet_names}
        else:
            # 일반 서비스 처리 (body JSON 전달)
            try:
                body = await request.body()
                if not body:
                    # body가 비어있는 경우도 허용
                    logger.info("요청 본문이 비어 있습니다.")
            except Exception as e:
                logger.warning(f"요청 본문 읽기 실패: {str(e)}")
                
        # 서비스에 요청 전달
        response = await factory.request(
            method="POST",
            path=path,
            headers=headers,
            body=body,
            files=files,
            params=params,
            data=data
        )
        
        # 응답 처리 및 반환
        return ResponseFactory.create_response(response)
        
    except HTTPException as he:
        # HTTP 예외는 그대로 반환
        return JSONResponse(
            content={"detail": he.detail},
            status_code=he.status_code
        )
    except Exception as e:
        # 일반 예외는 로깅 후 500 에러 반환
        logger.error(f"POST 요청 처리 중 오류 발생: {str(e)}")
        return JSONResponse(
            content={"detail": f"Gateway error: {str(e)}"},
            status_code=500
        )

async def log_to_auth_service(service: ServiceType, path: str, body: bytes):
    """auth-service로 데이터 로그를 전달하는 함수"""
    try:
        # auth-service로 로그 전달
        auth_factory = ServiceDiscovery(service_type=ServiceType.AUTH)
        
        log_data = {
            "service": service.value,
            "path": path,
            "data_size": len(body),
            "timestamp": str(datetime.datetime.now()),
            "source": "gateway"
        }
        
        # auth-service의 로그 엔드포인트로 전달
        await auth_factory.request(
            method="POST",
            path="logs/data",
            headers={"Content-Type": "application/json"},
            body=json.dumps(log_data).encode('utf-8')
        )
        
        logger.info(f"📊 데이터 로그를 auth-service로 전달 완료: {service.value}/{path}")
        
    except Exception as e:
        logger.error(f"auth-service로 로그 전달 실패: {str(e)}")

# PUT - 일반 동적 라우팅 (JWT 적용)
# PUT, DELETE, PATCH 프록시 제거 - POST 방식만 지원

# ✅ 메인 라우터 등록 (동적 라우팅)
# app.include_router(gateway_router) # 중복된 라우터 등록 제거

# 404 에러 핸들러
@app.exception_handler(404)
async def not_found_handler(request: Request, exc):
    return JSONResponse(
        status_code=404,
        content={"detail": "요청한 리소스를 찾을 수 없습니다."}
    )

# 기본 루트 경로
@app.get("/")
async def root():
    logger.info("🌈 Gateway API 서비스 시작")
    return {"message": "Gateway API", "version": "0.1.0"}



