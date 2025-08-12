from enum import Enum

class ServiceType(str, Enum):
    CBAM = "cbam"
    CHATBOT = "chatbot"
    LCA = "lca"
    REPORT = "report"
    AUTH = "auth"
