from typing import List

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.product import Brand
from app.schemas.product import BrandOut, BrandCreate
from app.dependencies import require_admin

router = APIRouter(prefix="/brands", tags=["Brands"])


@router.get("/", response_model=List[BrandOut])
def list_brands(db: Session = Depends(get_db)):
    return db.query(Brand).all()


@router.get("/{slug}", response_model=BrandOut)
def get_brand(slug: str, db: Session = Depends(get_db)):
    brand = db.query(Brand).filter(Brand.slug == slug).first()
    if not brand:
        raise HTTPException(status_code=404, detail="Brand not found")
    return brand


@router.post("/", response_model=BrandOut, status_code=201, dependencies=[Depends(require_admin)])
def create_brand(payload: BrandCreate, db: Session = Depends(get_db)):
    brand = Brand(**payload.model_dump())
    db.add(brand)
    db.commit()
    db.refresh(brand)
    return brand
