from fastapi import FastAPI

from app.api.agent_routes import router as agent_router
from app.api.rag_routes import router as rag_router
from app.api.routes import router

app = FastAPI(
    title="AI Project Intelligence & Risk Advisor",
    version="0.2.0",
    description="AI-Driven Enterprise Project Intelligence & Risk Management Platform with Multi-Agent Orchestration.",
)
app.include_router(router, prefix="/api")
app.include_router(rag_router, prefix="/api")
app.include_router(agent_router, prefix="/api")


@app.get("/health", tags=["health"])
async def health() -> dict[str, str]:
    return {"status": "ok"}
