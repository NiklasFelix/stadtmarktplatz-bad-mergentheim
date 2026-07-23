from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.routers import (
    ai_router,
    articles,
    auth_router,
    customers,
    dashboard_router,
    export_router,
    import_router,
    meta,
    reviews,
    suppliers,
)

app = FastAPI(
    title="Preisvergleich API",
    description="Interne API fuer den Artikel- und Preisvergleich ueber Lieferanten hinweg.",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_router.router)
app.include_router(articles.router)
app.include_router(reviews.router)
app.include_router(suppliers.router)
app.include_router(customers.router)
app.include_router(meta.router)
app.include_router(import_router.router)
app.include_router(export_router.router)
app.include_router(ai_router.router)
app.include_router(dashboard_router.router)


@app.get("/health")
def health():
    return {"status": "ok"}
