import httpx
from typing import Dict, Any, Optional
from enum import Enum

class ServiceType(str, Enum):
    CBAM = "cbam"
    CHATBOT = "chatbot"
    LCA = "lca"
    REPORT = "report"

class ServiceDiscovery:
    def __init__(self, service_type: ServiceType):
        self.service_type = service_type
        self.base_urls = {
            ServiceType.CBAM: "http://cbam-service:8001",
            ServiceType.CHATBOT: "http://chatbot-service:8002",
            ServiceType.LCA: "http://lca-service:8003",
            ServiceType.REPORT: "http://report-service:8004"
        }
    
    async def request(
        self,
        method: str,
        path: str,
        headers: Optional[Dict[str, str]] = None,
        data: Optional[Dict[str, Any]] = None,
        files: Optional[Dict[str, Any]] = None
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
                data=data,
                files=files
            )
            return response
