from fastapi import APIRouter
from .routers import admin, analytics, assessments, auth, contents, courses, health, rag, sync, users

api_router = APIRouter()
for router in (health.router, auth.router, users.router, courses.router, contents.router, rag.router, assessments.router, analytics.router, sync.router, admin.router):
    api_router.include_router(router)
