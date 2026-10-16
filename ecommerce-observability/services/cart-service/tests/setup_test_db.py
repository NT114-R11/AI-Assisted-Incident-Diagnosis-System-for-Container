from app.database.database import Base, engine
from app.models.cart import Cart
from app.models.cart_item import CartItem


print("Creating test database tables...")

Base.metadata.create_all(bind=engine)

print("Test database tables created successfully.")
