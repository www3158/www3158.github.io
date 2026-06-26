from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.db import Session, create_db_and_tables, engine
from app.routers import chat, guides, motorcycles, price_bands, recommendations
from app.seed import seed_initial_data


@asynccontextmanager
async def lifespan(app: FastAPI):
    create_db_and_tables()
    with Session(engine) as session:
        seed_initial_data(session)
    yield


app = FastAPI(title="Rider Starter AI API", version="0.1.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(motorcycles.router, prefix="/api")
app.include_router(price_bands.router, prefix="/api")
app.include_router(guides.router, prefix="/api")
app.include_router(recommendations.router, prefix="/api")
app.include_router(chat.router, prefix="/api")


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}
