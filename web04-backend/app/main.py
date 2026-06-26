from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.routers.properties import router as properties_router
from app.routers.analysis import router as analysis_router
from app.routers.recommendations import router as recommendations_router
from app.routers.auth import router as auth_router
from app.routers.content import router as content_router
from app.routers.admin import router as admin_router

app = FastAPI(
    title="Jeonse Guard API",
    description="AI 전세사기 예방 및 매물 추천 API",
    version="0.1.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
def root():
    return {
        "message": "Jeonse Guard API is running",
        "docs": "/docs",
        "health": "/health",
        "properties": "/api/properties",
        "recommendations": "/api/recommendations"
    }


@app.get("/health")
def health():
    return {
        "status": "OK",
        "service": "jeonse-guard-api"
    }


app.include_router(properties_router)
app.include_router(recommendations_router)
app.include_router(analysis_router)
app.include_router(auth_router)
app.include_router(content_router)
app.include_router(admin_router)
