
from sqlalchemy import Column, Date, Float, ForeignKey, Integer, String, DateTime
from timeutils import now_utc
from sqlalchemy.orm import relationship
from database import Base


class Remises(Base):
    __tablename__ = "remises"

    id = Column(Integer, primary_key=True)
    id_echeance = Column(Integer, ForeignKey("echeances.id", ondelete="CASCADE"), nullable=False, index=True)
    montant = Column(Float, nullable=False)
    motif = Column(String, nullable=True)
    utilisateur_id = Column(Integer, ForeignKey("utilisateurs.id", ondelete="SET NULL"), nullable=True)
    date = Column(Date, nullable=False)
    created_at = Column(DateTime, nullable=False, default=now_utc)
    updated_at = Column(DateTime, nullable=False, default=now_utc, onupdate=now_utc)

    echeance = relationship("Echeances", back_populates="remises")
    utilisateur = relationship("Utilisateurs")
