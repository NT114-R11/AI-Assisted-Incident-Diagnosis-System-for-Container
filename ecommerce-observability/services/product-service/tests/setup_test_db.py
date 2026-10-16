from app.database.database import Base, engine

from app.models.product import Product
from app.models.seller import Seller

print("Creating test database tables...")
Base.metadata.create_all(bind=engine)

print("Test database tables created successfully.")