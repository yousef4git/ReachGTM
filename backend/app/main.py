from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from backend.app.db.connection import init_pool, close_pool
from backend.app.middleware.tenant import TenantMiddleware
from backend.app.middleware.rate_limit import RateLimitMiddleware
from backend.app.api import auth, chat, strategy, content, knowledge

@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_pool()
    yield
    await close_pool()

app = FastAPI(title="ReachGTM Backend", version="0.1.0", lifespan=lifespan)

app.add_middleware(CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.add_middleware(TenantMiddleware)
app.add_middleware(RateLimitMiddleware)

app.include_router(auth.router, prefix="/api/v1")
app.include_router(chat.router, prefix="/api/v1")
app.include_router(strategy.router, prefix="/api/v1")
app.include_router(content.router, prefix="/api/v1")
app.include_router(knowledge.router, prefix="/api/v1")

@app.get("/health")
async def health():
    return {"service": "backend", "status": "ok"}
