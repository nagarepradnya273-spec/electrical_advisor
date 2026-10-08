import uuid
from typing import List

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.order import Cart, Order, OrderItem
from app.models.user import User
from app.schemas.order import OrderOut, OrderCreate
from app.dependencies import get_current_user

router = APIRouter(prefix="/orders", tags=["Orders"])


@router.post("/", response_model=OrderOut, status_code=201)
def create_order(
    payload: OrderCreate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)
):
    cart = db.query(Cart).filter(Cart.user_id == current_user.id).first()
    if not cart or not cart.items:
        raise HTTPException(status_code=400, detail="Cart is empty")

    total = sum((item.product.discount_price or item.product.price) * item.quantity for item in cart.items)
    order = Order(
        order_number=f"EL{uuid.uuid4().hex[:8].upper()}",
        user_id=current_user.id,
        address_id=payload.address_id,
        payment_method=payload.payment_method,
        total_amount=total,
    )
    for item in cart.items:
        order.items.append(
            OrderItem(
                product_id=item.product_id,
                quantity=item.quantity,
                price=item.product.discount_price or item.product.price,
            )
        )
    db.add(order)
    for item in list(cart.items):
        db.delete(item)
    db.commit()
    db.refresh(order)
    return order


@router.get("/", response_model=List[OrderOut])
def list_my_orders(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    return db.query(Order).filter(Order.user_id == current_user.id).all()


@router.get("/{order_id}", response_model=OrderOut)
def get_order(
    order_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)
):
    order = db.query(Order).filter(Order.id == order_id, Order.user_id == current_user.id).first()
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    return order
