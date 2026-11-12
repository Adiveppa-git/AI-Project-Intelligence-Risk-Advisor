from fastapi import FastAPI

from app.api.rag_routes import router as rag_router
from app.api.routes import router

app = FastAPI(
    title="AI Project Intelligence & Risk Advisor",
    version="0.1.0",
    description="Milestone 1 document ingestion API.",
)
app.include_router(router, prefix="/api")
app.include_router(rag_router, prefix="/api")


@app.get("/health", tags=["health"])
async def health() -> dict[str, str]:
    return {"status": "ok"}
