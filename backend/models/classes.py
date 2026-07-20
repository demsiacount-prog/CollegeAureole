# models/classes.py
from datetime import datetime
from sqlalchemy import Column, Integer, String, Float
from sqlalchemy.orm import relationship
from database import Base


class Classes(Base):
    __tablename__ = "classes"
    id = Column(Integer, primary_key=True)
    niveau = Column(String, nullable=False)
    nom = Column(String, nullable=False)
    frais_inscription = Column(Float, nullable=False, default=0.0)
    mensualite = Column(Float, nullable=False, default=0.0)
    capacite_max = Column(Integer, nullable=True)  # None = pas de limite
    created_at = Column(String, nullable=False, default=lambda: datetime.now().isoformat())
    updated_at = Column(String, nullable=False, default=lambda: datetime.now().isoformat(),
                        onupdate=lambda: datetime.now().isoformat())

    # Relations
    eleves = relationship("Eleves", back_populates="classe_relation")
    cours_affectations = relationship(
        "AffectationCoursClasse", back_populates="classe", cascade="all, delete-orphan"
    )
    notes = relationship("Notes", back_populates="classe")
    bulletins = relationship("Bulletins", back_populates="classe")
    inscriptions = relationship("Inscriptions", back_populates="classe")
    seances = relationship("Seances", back_populates="classe", cascade="all, delete-orphan")
    echeances = relationship("Echeances", back_populates="classe")

    @property
    def cours(self):
        """Liste des cours affectés à cette classe (via AffectationCoursClasse)."""
        return [a.cours for a in self.cours_affectations]

    @property
    def effectif_actuel(self) -> int:
        return len([e for e in self.eleves if e.statut == "actif"])
