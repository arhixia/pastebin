from sqlalchemy import Column, Integer, String, Text, ForeignKey, DateTime
from sqlalchemy.orm import relationship
from back.database import Base, engine

class User(Base):
    __tablename__ = 'users'

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True)
    hashed_password = Column(String)

    items = relationship("Item", order_by="Item.id", back_populates="user")


class Item(Base):
    __tablename__ = 'items'

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, index=True)
    content = Column(Text)
    user_id = Column(Integer, ForeignKey('users.id'))
    expiration_date = Column(DateTime, nullable=True)

    user = relationship("User", back_populates="items")

    @property
    def short_url(self):
        return f"http://localhost:3000/{self.id}"

# Create all tables
Base.metadata.create_all(bind=engine)
