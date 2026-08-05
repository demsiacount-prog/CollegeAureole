from datetime import datetime
from sqlalchemy import Column, Date, ForeignKey, Integer, String, Boolean
from sqlalchemy.orm import relationship
from database import Base


class Trimestres(Base):
    __tablename__ = "trimestres"

    id = Column(Integer, primary_key=True)
    nom = Column(String, nullable=False)
    type = Column(String, nullable=False, default="TRIMESTRE")  # TRIMESTRE (7e-9e) | COMPOSITION (1e-6e)
    date_debut = Column(Date, nullable=False)
    date_fin = Column(Date, nullable=False)
    verrouille = Column(Boolean, nullable=False, default=False)  # empêche la saisie/modif de notes
    created_at = Column(String, nullable=False, default=lambda: datetime.now().isoformat())
    updated_at = Column(String, nullable=False, default=lambda: datetime.now().isoformat(),
                        onupdate=lambda: datetime.now().isoformat())

    annee_scolaire_id = Column(Integer, ForeignKey("annees_scolaires.id", ondelete="CASCADE"), nullable=False)

    annee_scolaire = relationship("AnneesScolaires", back_populates="trimestres")
    notes = relationship("Notes", back_populates="trimestre")
    bulletins = relationship("Bulletins", back_populates="trimestre", cascade="all, delete-orphan")
