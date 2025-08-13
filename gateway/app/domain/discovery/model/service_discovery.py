import httpx
import os
import logging
from typing import Dict, Any, Optional
from enum import Enum

logger = logging.getLogger("service_discovery")

class ServiceType(str, Enum):
    CBAM = "cbam"
    CHATBOT = "chatbot"
    LCA = "lca"
    REPORT = "report"
    AUTH = "auth"

class ServiceDiscovery:
    def __init__(self, service_type: ServiceType):
        self.service_type = service_type
        # Railway 환경에서는 환경변수에서 서비스 URL을 가져옴
        self.base_urls = {
            ServiceType.CBAM: os.getenv("CBAM_SERVICE_URL", "http://cbam-service:8082"),
            ServiceType.CHATBOT: os.getenv("CHATBOT_SERVICE_URL", "http://chatbot-service:8083"),
            ServiceType.LCA: os.getenv("LCA_SERVICE_URL", "http://lca-service:8084"),
            ServiceType.REPORT: os.getenv("REPORT_SERVICE_URL", "http://report-service:8085"),
            ServiceType.AUTH: os.getenv("AUTH_SERVICE_URL", "http://auth-service:8081")
        }
        
        # 모든 URL에서 끝 슬래시 제거
        for service_type, url in self.base_urls.items():
            if url:
                self.base_urls[service_type] = url.rstrip('/')
        
        # Railway 환경 감지
        railway_env = os.getenv("RAILWAY_ENVIRONMENT", "false").lower() == "true"
        if railway_env:
            logger.info(f"🚂 Railway 환경 감지됨 - {service_type.value} 서비스 URL: {self.base_urls.get(service_type)}")
        else:
            logger.info(f"🐳 Docker 환경 - {service_type.value} 서비스 URL: {self.base_urls.get(service_type)}")
    
    async def request(
        self,
        method: str,
        path: str,
        headers: Optional[Dict[str, str]] = None,
        body: Optional[bytes] = None,
        files: Optional[Dict[str, Any]] = None,
        params: Optional[Dict[str, Any]] = None,
        data: Optional[Dict[str, Any]] = None,
        cookies: Optional[Dict[str, str]] = None
    ):
        base_url = self.base_urls.get(self.service_type)
        if not base_url:
            raise ValueError(f"Unknown service type: {self.service_type}")
        
        url = f"{base_url}/{path}"
        logger.info(f"🌐 서비스 요청: {method} {url}")
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.request(
                    method=method,
                    url=url,
                    headers=headers,
                    content=body,
                    files=files,
                    params=params,
                    data=data,
                    cookies=cookies,
                    timeout=30.0
                )
                logger.info(f"✅ 서비스 응답: {response.status_code} - {url}")
                return response
        except httpx.ConnectError as e:
            logger.error(f"❌ 서비스 연결 실패: {url} - {str(e)}")
            raise
        except httpx.TimeoutException as e:
            logger.error(f"⏰ 서비스 요청 타임아웃: {url} - {str(e)}")
            raise
        except Exception as e:
            logger.error(f"❌ 서비스 요청 실패: {url} - {str(e)}")
            raise
