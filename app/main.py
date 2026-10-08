from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.database import Base, engine
from app import models  # noqa: F401  (registers all models with Base before create_all)
from app.config import settings
from app.routes import auth, categories, brands, products, advisor, cart, orders, services, knowledge

# Dev convenience: auto-create tables. In production, use Alembic migrations instead.
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title=settings.PROJECT_NAME,
    description=(
        "API for an Indian electrical advisor + e-commerce platform: "
        "problem-based guidance, product discovery, shopping and services."
    ),
    version="0.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(categories.router)
app.include_router(brands.router)
app.include_router(products.router)
app.include_router(advisor.router)
app.include_router(cart.router)
app.include_router(orders.router)
app.include_router(services.router)
app.include_router(knowledge.router)


@app.get("/")
def root():
    return {"message": "Electrical Advisor & E-Commerce API is running", "docs": "/docs"}
