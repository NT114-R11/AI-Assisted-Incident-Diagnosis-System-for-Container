from app.database.database import Base, engine

from app.models import User
from app.models.authority import Authority

print("Creating test database tables...")
Base.metadata.create_all(bind=engine)

print("Test database tables created successfully.")