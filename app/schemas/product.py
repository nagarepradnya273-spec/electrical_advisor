from typing import Optional, List

from pydantic import BaseModel, ConfigDict


class CategoryOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    name: str
    slug: str
    description: Optional[str] = None
    parent_id: Optional[int] = None


class CategoryCreate(BaseModel):
    name: str
    slug: str
    description: Optional[str] = None
    parent_id: Optional[int] = None


class BrandOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    name: str
    slug: str
    description: Optional[str] = None
    logo_url: Optional[str] = None


class BrandCreate(BaseModel):
    name: str
    slug: str
    description: Optional[str] = None
    logo_url: Optional[str] = None


class ProductImageOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    url: str
    is_primary: bool


class ProductSpecOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    key: str
    value: str


class ProductListOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    name: str
    slug: str
    short_description: Optional[str] = None
    price: float
    discount_price: Optional[float] = None
    rating: float
    review_count: int
    stock_qty: int
    category: CategoryOut
    brand: Optional[BrandOut] = None
    images: List[ProductImageOut] = []


class ProductDetailOut(ProductListOut):
    description: Optional[str] = None
    who_should_buy: Optional[str] = None
    before_you_buy: Optional[str] = None
    warranty: Optional[str] = None
    specifications: List[ProductSpecOut] = []


class ProductCreate(BaseModel):
    name: str
    slug: str
    category_id: int
    brand_id: Optional[int] = None
    short_description: Optional[str] = None
    description: Optional[str] = None
    who_should_buy: Optional[str] = None
    before_you_buy: Optional[str] = None
    price: float
    discount_price: Optional[float] = None
    stock_qty: int = 0
    warranty: Optional[str] = None
