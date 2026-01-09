"""
Модуль database.models

Содержит определения таблиц для хранения данных в базе данных.

"""
from sqlalchemy import Column, Integer, String, Float, Text, ForeignKey, DateTime, func, BigInteger, \
    Boolean, Date
from sqlalchemy.orm import declarative_base
from sqlalchemy.orm import relationship

Base = declarative_base()

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
    ostatok = Column(Float)
    # Внешний ключ для связи с категорией
    category_id = Column(Integer, ForeignKey('categories.id'))

    # Связь с категорией
    category = relationship("Category", back_populates="products")
    
    # Связь с элементами корзины
    cart_items = relationship("CartItems", back_populates="product")

    # Связь с элементами заказа
    order_items = relationship("OrderItems", back_populates="product")
    
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
    questions = relationship("Question", back_populates="user")
    orders = relationship("Order", back_populates="user")


    def __repr__(self):
        return f"<TelegramContact(user_id={self.tg_id}, username={self.username})>"


class CostumerActivity(AbstractBase):
    __tablename__ = "costumer_activity"
    chat_id = Column(BigInteger)
    event_type = Column(String(32))
    action = Column(String(255))
    payload = Column(String(255), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    activity_date = Column(Date, index=True)
    week = Column(Integer, index=True)
    month = Column(Integer, index=True)
    year = Column(Integer, index=True)


# Define CartItems before Cart to avoid forward reference issues
class CartItems(AbstractBase):
    __tablename__ = 'cart_items'
    
    cart_id = Column(Integer, ForeignKey('carts.id'), nullable=False)
    product_id = Column(Integer, ForeignKey('products.id'), nullable=False)
    quantity = Column(Float, nullable=False, default=1)
    unit_price = Column(Float, nullable=False)
    
    # Relationships
    cart = relationship("Cart", back_populates="items")
    product = relationship("Product", back_populates="cart_items")
    
    @property
    def total_price(self):
        """Общая цена за позицию (цена * количество)"""
        return self.unit_price * self.quantity
        
    def __repr__(self):
        return f"<CartItem(id={self.id}, product_id={self.product_id}, quantity={self.quantity})>"


class Cart(AbstractBase):
    __tablename__ = 'carts'
    user_id = Column(Integer, ForeignKey('costumers.id'), nullable=False)
    name = Column(String(100), default="Основная корзина")  # Название корзины
    is_active = Column(Boolean, default=True)  # Активная корзина
    is_done = Column(Boolean, default=False)  # Отметка о там, что сбор корзины закончен
    is_issued = Column(Boolean, default=False)  # Отметка о там, что товар из корзины выдан
    is_done_at = Column(DateTime, nullable=True)  # дата сбора корзины
    is_issued_at = Column(DateTime, nullable=True)  # Дата выдачи корзины

    # Relationships
    user = relationship("Costumer", back_populates="carts")
    items = relationship("CartItems", back_populates="cart", cascade="all, delete-orphan")

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


class News(AbstractBase):
    __tablename__ = 'news'
    title = Column(String(100), nullable=True)
    post = Column(Text)
    image_url = Column(String(300), nullable=True)
    url = Column(String(100), nullable=True)
    media_type = Column(String(10), nullable=True)
    vk_id = Column(Integer, nullable=True)
    vk_url = Column(String(300), nullable=True)

    def __repr__(self):
        return f"<News(id={self.id}, title={self.title}, url={self.url})>"


class Question(AbstractBase):
    """
    Модель для хранения вопросов от пользователей

    Attributes:
        user_id (int): ID пользователя, который задал вопрос
        questions_id (int): ID вопроса
        text (str): текст вопроса
        is_answered (bool): ответ на вопрос задан или нет
    """
    __tablename__ = "questions"
    user_id = Column(Integer, ForeignKey('costumers.id'), nullable=False)
    questions_id = Column(BigInteger) #Ай ди чата
    text = Column(Text)
    is_answered = Column(Boolean, default=False)
    answer = Column(Text, nullable=True)
    answer_at =Column(DateTime, nullable=True)

    user = relationship("Costumer", back_populates="questions")

    def __repr__(self):
        return f"<Question (text={self.text[:30]}, from {self.user_id}"


class OrderItems(AbstractBase):
    __tablename__ = 'order_items'

    order_id = Column(Integer, ForeignKey('orders.id'), nullable=False)
    product_id = Column(Integer, ForeignKey('products.id'), nullable=False)
    quantity = Column(Integer, nullable=False, default=1)
    unit_price = Column(Float, nullable=False)

    # Relationships
    order = relationship("Order", back_populates="items")
    product = relationship("Product", back_populates="order_items")

    @property
    def total_price(self):
        """Общая цена за позицию (цена * количество)"""
        return self.unit_price * self.quantity

    def __repr__(self):
        return f"<OrderItem(id={self.id}, product_id={self.product_id}, quantity={self.quantity})>"


class Order(AbstractBase):
    __tablename__ = 'orders'
    user_id = Column(Integer, ForeignKey('costumers.id'), nullable=False)
    name = Column(String(100), default="Заказ")  # Название заказа
    is_active = Column(Boolean, default=True)  # Заказ активен - False - завешен
    is_done = Column(Boolean, default=False)  #  True проводится сбор корзины
    is_done_at = Column(DateTime, nullable=True) # дата оконачания заказа
    is_issued = Column(Boolean, default=False)  # True - проводится выдача корзины
    is_issued_at = Column(DateTime, nullable=True)  # Дата выдачи корзины


    # Relationships
    user = relationship("Costumer", back_populates="orders")
    items = relationship("OrderItems", back_populates="order", cascade="all, delete-orphan")

    @property
    def total_amount(self):
        """Общая сумма заказа"""
        return sum(item.total_price for item in self.items)

    @property
    def total_items(self):
        """Общее количество товаров в заказе"""
        return sum(item.quantity for item in self.items)

    def __repr__(self):
        return f"<Order(id={self.id}, user_id={self.user_id}, items={len(self.items)})>"



