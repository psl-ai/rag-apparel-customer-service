from fastapi import APIRouter

from app.api.v1.health import router as health_router
from app.api.v1.auth import router as auth_router
from app.api.v1.admin import router as admin_router
from app.api.v1.catalog import router as catalog_router
from app.api.v1.inventory import router as inventory_router
from app.api.v1.commerce import router as commerce_router
from app.api.v1.chat import router as chat_router
from app.api.v1.feedback import router as feedback_router
from app.api.v1.knowledge import router as knowledge_router
from app.api.v1.profile import router as profile_router
from app.api.v1.engagement import router as engagement_router


api_router = APIRouter(prefix="/api/v1")
api_router.include_router(health_router)
api_router.include_router(auth_router)
api_router.include_router(admin_router)
api_router.include_router(catalog_router)
api_router.include_router(inventory_router)
api_router.include_router(commerce_router)
api_router.include_router(chat_router)
api_router.include_router(feedback_router)
api_router.include_router(knowledge_router)
api_router.include_router(profile_router)
api_router.include_router(engagement_router)
