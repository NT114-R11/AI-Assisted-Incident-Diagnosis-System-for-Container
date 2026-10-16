from app.database.database import Base, engine
from app.models.customer import Customer
from app.models.order import Order
from app.models.order_item import OrderItem
from app.models.shipping_address import ShippingAddress
from app.models.billing_address import BillingAddress


print("Creating test database tables...")

Base.metadata.create_all(bind=engine)

print("Test database tables created successfully.")