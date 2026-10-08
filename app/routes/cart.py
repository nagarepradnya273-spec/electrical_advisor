from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.order import Cart, CartItem
from app.models.product import Product
from app.models.user import User
from app.schemas.order import CartOut, CartItemCreate
from app.dependencies import get_current_user

router = APIRouter(prefix="/cart", tags=["Cart"])


def _get_or_create_cart(db: Session, user: User) -> Cart:
    cart = db.query(Cart).filter(Cart.user_id == user.id).first()
    if not cart:
        cart = Cart(user_id=user.id)
        db.add(cart)
        db.commit()
        db.refresh(cart)
    return cart


@router.get("/", response_model=CartOut)
def get_cart(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    return _get_or_create_cart(db, current_user)


@router.post("/items", response_model=CartOut)
def add_item(
    item: CartItemCreate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)
):
    product = db.query(Product).filter(Product.id == item.product_id, Product.is_active == True).first()  # noqa: E712
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")

    cart = _get_or_create_cart(db, current_user)
    existing = next((i for i in cart.items if i.product_id == item.product_id), None)
    if existing:
        existing.quantity += item.quantity
    else:
        cart.items.append(CartItem(product_id=item.product_id, quantity=item.quantity))
    db.commit()
    db.refresh(cart)
    return cart


@router.delete("/items/{item_id}", response_model=CartOut)
def remove_item(
    item_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)
):
    cart = _get_or_create_cart(db, current_user)
    item = next((i for i in cart.items if i.id == item_id), None)
    if not item:
        raise HTTPException(status_code=404, detail="Cart item not found")
    db.delete(item)
    db.commit()
    db.refresh(cart)
    return cart
