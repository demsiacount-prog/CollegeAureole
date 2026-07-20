# models/paiements.py
from datetime import datetime
from sqlalchemy import Column, Integer, String, Float, Date, ForeignKey
from sqlalchemy.orm import relationship
from database import Base

class Paiements(Base):
    __tablename__ = "paiements"

    id              = Column(Integer, primary_key=True, autoincrement=True)
    id_inscription  = Column(Integer, ForeignKey("inscriptions.id", ondelete="CASCADE"),
                             nullable=False, index=True)
    id_echeance     = Column(Integer, ForeignKey("echeances.id", ondelete="SET NULL"),
                             nullable=True, index=True)

    date            = Column(Date, nullable=False, default=datetime.now().date)
    numero_recu     = Column(String, nullable=True)
    montant         = Column(Float, nullable=False)
    mode            = Column(String, nullable=True)
    observation     = Column(String, nullable=True)

    created_at = Column(String, nullable=False, default=lambda: datetime.now().isoformat())
    updated_at = Column(String, nullable=False, default=lambda: datetime.now().isoformat(),
                        onupdate=lambda: datetime.now().isoformat())

    # Relations
    inscription = relationship("Inscriptions", back_populates="paiements")
    echeance    = relationship("Echeances", back_populates="paiements")