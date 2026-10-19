import os

from fastapi import APIRouter, Depends, FastAPI
from fastapi.testclient import TestClient


def test_customer_token_is_rejected_by_admin_role_dependency():
    os.environ["JWT_SECRET_KEY"] = "rbac-secret"
    from app.core.config import get_settings
    from app.core.security import create_access_token
    from app.core.rbac import require_roles

    get_settings.cache_clear()
    app = FastAPI()
    router = APIRouter()

    @router.get("/admin-only")
    def admin_only(_: dict = Depends(require_roles("admin", "super_admin"))) -> dict:
        return {"ok": True}

    app.include_router(router)
    client = TestClient(app)
    token = create_access_token("customer-id", "customer")

    response = client.get("/admin-only", headers={"Authorization": f"Bearer {token}"})

    assert response.status_code == 403
    assert response.json()["detail"] == "insufficient_permissions"
