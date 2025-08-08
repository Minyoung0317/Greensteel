from pydantic_settings import BaseSettings
from typing import Optional

class Settings(BaseSettings):
    # 기본 설정
    APP_NAME: str = "GreenSteel Gateway"
    DEBUG: bool = True
    
    # 데이터베이스 설정
    DATABASE_URL: Optional[str] = None
    
    # JWT 설정
    JWT_SECRET_KEY: str = "your-secret-key"
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    
    # 서비스 URL 설정
    CBAM_SERVICE_URL: str = "http://cbam-service:8001"
    CHATBOT_SERVICE_URL: str = "http://chatbot-service:8002"
    LCA_SERVICE_URL: str = "http://lca-service:8003"
    REPORT_SERVICE_URL: str = "http://report-service:8004"
    
    class Config:
        env_file = ".env"
        extra = "allow"  # 추가 필드 허용
