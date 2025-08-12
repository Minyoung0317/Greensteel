import httpx
import os
from typing import Dict, Any, Optional
from enum import Enum

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
    
    async def request(
        self,
        method: str,
        path: str,
        headers: Optional[Dict[str, str]] = None,
        body: Optional[bytes] = None,
        files: Optional[Dict[str, Any]] = None,
        params: Optional[Dict[str, Any]] = None,
        data: Optional[Dict[str, Any]] = None
    ):
        base_url = self.base_urls.get(self.service_type)
        if not base_url:
            raise ValueError(f"Unknown service type: {self.service_type}")
        
        url = f"{base_url}/{path}"
        
        async with httpx.AsyncClient() as client:
            response = await client.request(
                method=method,
                url=url,
                headers=headers,
                content=body,
                files=files,
                params=params,
                data=data
            )
            return response
