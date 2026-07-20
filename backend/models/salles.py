from datetime import datetime
from sqlalchemy import Column, Integer, String
from sqlalchemy.orm import relationship
from database import Base


class Salles(Base):
    __tablename__ = "salles"

    id = Column(Integer, primary_key=True)
    nom = Column(String, nullable=False, unique=True)
    capacite = Column(Integer, nullable=True)
    created_at = Column(String, nullable=False, default=lambda: datetime.now().isoformat())
    updated_at = Column(String, nullable=False, default=lambda: datetime.now().isoformat(),
                        onupdate=lambda: datetime.now().isoformat())

    seances = relationship("Seances", back_populates="salle")
