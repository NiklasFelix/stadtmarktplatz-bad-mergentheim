from fastapi import FastAPI

from app.routers import articles, reviews

app = FastAPI(
    title="Preisvergleich API",
    description="Interne API fuer den Artikel- und Preisvergleich ueber Lieferanten hinweg.",
)

app.include_router(articles.router)
app.include_router(reviews.router)


@app.get("/health")
def health():
    return {"status": "ok"}
