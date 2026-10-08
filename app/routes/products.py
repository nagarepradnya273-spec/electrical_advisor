from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.product import Product
from app.schemas.product import ProductListOut, ProductDetailOut, ProductCreate
from app.dependencies import require_admin

router = APIRouter(prefix="/products", tags=["Products"])


@router.get("/", response_model=List[ProductListOut])
def list_products(
    db: Session = Depends(get_db),
    category: Optional[str] = Query(None, description="Filter by category slug"),
    brand: Optional[str] = Query(None, description="Filter by brand slug"),
    search: Optional[str] = Query(None, description="Search in product name"),
    min_price: Optional[float] = None,
    max_price: Optional[float] = None,
    skip: int = 0,
    limit: int = 24,
):
    q = db.query(Product).filter(Product.is_active == True)  # noqa: E712
    if category:
        q = q.join(Product.category).filter_by(slug=category)
    if brand:
        q = q.join(Product.brand).filter_by(slug=brand)
    if search:
        q = q.filter(Product.name.ilike(f"%{search}%"))
    if min_price is not None:
        q = q.filter(Product.price >= min_price)
    if max_price is not None:
        q = q.filter(Product.price <= max_price)
    return q.offset(skip).limit(limit).all()


@router.get("/{slug}", response_model=ProductDetailOut)
def get_product(slug: str, db: Session = Depends(get_db)):
    product = db.query(Product).filter(Product.slug == slug).first()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    return product


@router.post("/", response_model=ProductDetailOut, status_code=201, dependencies=[Depends(require_admin)])
def create_product(payload: ProductCreate, db: Session = Depends(get_db)):
    product = Product(**payload.model_dump())
    db.add(product)
    db.commit()
    db.refresh(product)
    return product
