from typing import List, Optional

from pydantic import BaseModel, ConfigDict

from app.schemas.product import ProductListOut


class CartItemCreate(BaseModel):
    product_id: int
    quantity: int = 1


class CartItemOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    quantity: int
    product: ProductListOut


class CartOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    items: List[CartItemOut] = []


class OrderCreate(BaseModel):
    address_id: Optional[int] = None
    payment_method: str = "cod"


class OrderItemOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    product_id: int
    quantity: int
    price: float


class OrderOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    order_number: str
    status: str
    payment_method: str
    payment_status: str
    total_amount: float
    items: List[OrderItemOut] = []
