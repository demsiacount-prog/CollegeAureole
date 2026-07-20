# models/depenses.py
from datetime import datetime
from sqlalchemy import Column, Integer, String, Float, Date
from database import Base

class Depenses(Base):
    __tablename__ = "depenses"

    id          = Column(Integer, primary_key=True, autoincrement=True)
    libelle     = Column(String, nullable=False)
    montant     = Column(Float, nullable=False)
    categorie   = Column(String, nullable=False, default="AUTRE")
    date        = Column(Date, nullable=False, default=datetime.now().date)
    description = Column(String, nullable=True)
    created_at  = Column(String, nullable=False, default=lambda: datetime.now().isoformat())
    updated_at  = Column(String, nullable=False,
                         default=lambda: datetime.now().isoformat(),
                         onupdate=lambda: datetime.now().isoformat())