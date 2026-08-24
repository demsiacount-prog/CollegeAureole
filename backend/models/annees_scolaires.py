
from sqlalchemy import Boolean, Column, Date, Integer, String, DateTime
from timeutils import now_utc
from sqlalchemy.orm import relationship
from database import Base


class AnneesScolaires(Base):
    __tablename__ = "annees_scolaires"

    id = Column(Integer, primary_key=True)
    libelle = Column(String, nullable=False, unique=True)
    date_debut = Column(Date, nullable=False)
    date_fin = Column(Date, nullable=False)
    active = Column(Boolean, nullable=False, default=False)
    cloturee = Column(Boolean, nullable=False, default=False)  # bloque toute nouvelle saisie sur l'année
    created_at = Column(DateTime, nullable=False, default=now_utc)
    updated_at = Column(DateTime, nullable=False, default=now_utc, onupdate=now_utc)

    trimestres = relationship("Trimestres", back_populates="annee_scolaire", cascade="all, delete-orphan")
    inscriptions = relationship("Inscriptions", back_populates="annee_scolaire")
    seances = relationship("Seances", back_populates="annee_scolaire", cascade="all, delete-orphan")
