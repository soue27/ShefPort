from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from data.config import DB_URL, ECHO
from datadase.models import Base, Costumer, Cart, CartItems, Product, Category

print(DB_URL)


