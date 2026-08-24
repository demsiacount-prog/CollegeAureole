
from sqlalchemy import Column, Date, ForeignKey, Integer, String, Boolean, DateTime, UniqueConstraint
from timeutils import now_utc
from sqlalchemy.orm import relationship
from database import Base


class Trimestres(Base):
    __tablename__ = "trimestres"
    __table_args__ = (
        UniqueConstraint("annee_scolaire_id", "nom", name="uq_trimestre_annee_nom"),
    )

    id = Column(Integer, primary_key=True)
    nom = Column(String, nullable=False)
    type = Column(String, nullable=False, default="TRIMESTRE")  # TRIMESTRE (7e-9e) | COMPOSITION (1e-6e)
    date_debut = Column(Date, nullable=False)
    date_fin = Column(Date, nullable=False)
    verrouille = Column(Boolean, nullable=False, default=False)  # empêche la saisie/modif de notes
    created_at = Column(DateTime, nullable=False, default=now_utc)
    updated_at = Column(DateTime, nullable=False, default=now_utc, onupdate=now_utc)

    annee_scolaire_id = Column(Integer, ForeignKey("annees_scolaires.id", ondelete="CASCADE"), nullable=False)

    annee_scolaire = relationship("AnneesScolaires", back_populates="trimestres")
    notes = relationship("Notes", back_populates="trimestre")
    bulletins = relationship("Bulletins", back_populates="trimestre", cascade="all, delete-orphan")
