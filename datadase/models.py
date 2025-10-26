from sqlalchemy import create_engine, Column, Integer, String, Float, Text, ForeignKey, DateTime, func, BigInteger, \
    Boolean
from sqlalchemy.orm import declarative_base
from sqlalchemy.orm import relationship, sessionmaker, Mapped
import json
from typing import Dict, List, Any
from datetime import datetime

Base = declarative_base()

# For type checking compatibility
DECLARATIVE_BASE = Base


class AbstractBase(Base):
    """Абстрактная базовая модель"""
    __abstract__ = True
    id = Column(Integer, primary_key=True, autoincrement=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)


class Category(AbstractBase):
    """Таблица для хранения категорий"""
    __tablename__ = 'categories'
    name = Column(String(255), nullable=False)
    url = Column(String(500), nullable=False)
    product_count = Column(Integer, default=0)

    products = relationship("Product", back_populates="category")

    def __repr__(self):
        return f"<Category(id={self.id}, name='{self.name}', product_count={self.product_count})>"


class Product(AbstractBase):
    """Таблица для хранения продуктов"""
    __tablename__ = 'products'
    name = Column(String(500), nullable=False)
    url = Column(String(500), nullable=False)
    image = Column(String(500))
    price = Column(Float, nullable=False)
    unit = Column(String(50))
    product_id = Column(String(100), nullable=False)
    article = Column(String(100))
    description = Column(Text)
    full_description = Column(Text)
    characteristics = Column(Text)  # Будем хранить как JSON строку
    main_image = Column(String(500))
    additional_images = Column(Text)  # Будем хранить как JSON строку
    weight = Column(String(100))
    calories = Column(String(100))
    nutrition_facts = Column(Text)  # Будем хранить как JSON строку

    # Внешний ключ для связи с категорией
    category_id = Column(Integer, ForeignKey('categories.id'))

    # Связь с категорией
    category = relationship("Category", back_populates="products")

    def __repr__(self):
        return f"<Product(id={self.id}, name='{self.name}', price={self.price})>"


class Costumer(AbstractBase):
    __tablename__ = 'costumers'
    is_admin = Column(Boolean, default=False)
    tg_id = Column(BigInteger, nullable=False, index=True)  # Telegram user id (int)
    username = Column(String(64), nullable=True, index=True)
    first_name = Column(String(200), nullable=True)
    last_name = Column(String(200), nullable=True)
    news = Column(Boolean, default=True)
    display_name = Column(String(400), nullable=True)  # cached concatenation, optional


    carts = relationship("Cart", back_populates="user")

    def __repr__(self):
        return f"<TelegramContact(user_id={self.tg_id}, username={self.username})>"


class Cart(AbstractBase):
    __tablename__ = 'carts'
    user_id = Column(Integer, ForeignKey('costumers.id'), nullable=False)
    name = Column(String(100), default="Основная корзина")  # Название корзины
    is_active = Column(Boolean, default=True)  # Активная корзина

    # Связь с пользователем
    user = relationship("Costumer", back_populates="carts")

    # Связь один-ко-многим с элементами корзины
    items = relationship("CartItem", back_populates="cart", cascade="all, delete-orphan")

    @property
    def total_amount(self):
        """Общая сумма корзины"""
        return sum(item.total_price for item in self.items)

    @property
    def total_items(self):
        """Общее количество товаров в корзине"""
        return sum(item.quantity for item in self.items)

    def __repr__(self):
        return f"<Cart(id={self.id}, user_id={self.user_id}, items={len(self.items)})>"


class CartItems(AbstractBase):
    __tablename__ = 'cart_items'
    cart_id = Column(Integer, ForeignKey('carts.id'), nullable=False)
    product_id = Column(Integer, ForeignKey('products.id'), nullable=False)
    quantity = Column(Integer, nullable=False, default=1)
    unit_price = Column(Float, nullable=False)  # Цена за единицу на момент добавления

    # Связь с корзиной
    cart = relationship("Cart", back_populates="items")

    # Связь с товаром
    product = relationship("Product", back_populates="cart_items")

    @property
    def total_price(self):
        """Общая цена за позицию (цена * количество)"""
        return self.unit_price * self.quantity

    def __repr__(self):
        return f"<CartItem(id={self.id}, product='{self.product.name}', quantity={self.quantity}, total={self.total_price})>"






