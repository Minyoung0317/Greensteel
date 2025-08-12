from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
import os
import logging

# 로깅 설정
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("report-service")

app = FastAPI(title="Report Service", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
async def root():
    return {"message": "Report Service is running"}

@app.get("/health")
async def health_check():
    return {"status": "healthy", "service": "report-service"}

if __name__ == "__main__":
    # Railway 환경에서는 PORT 환경 변수를 사용, 로컬에서는 8004 사용
    port_str = os.getenv("PORT", "8004")
    try:
        port = int(port_str)
    except ValueError:
        logger.error(f"잘못된 포트 값: {port_str}, 기본값 8004 사용")
        port = 8004
    
    logger.info(f"🚀 Report Service 시작 - 포트: {port}")
    logger.info(f"환경: {'Railway' if os.getenv('RAILWAY_ENVIRONMENT') == 'true' else 'Local/Docker'}")
    logger.info(f"환경 변수 PORT: {os.getenv('PORT', '설정되지 않음')}")
    
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=port,
        reload=False,  # Railway에서는 reload 비활성화
        log_level="info"
    )
