
from sqlalchemy import Column, Integer, String, Time, DateTime, ForeignKey
from timeutils import now_utc
from sqlalchemy.orm import relationship
from database import Base


class Seances(Base):
    __tablename__ = "seances"

    id = Column(Integer, primary_key=True, autoincrement=True)
    id_cours = Column(Integer, ForeignKey("cours.id", ondelete="CASCADE"), nullable=False, index=True)
    id_classe = Column(Integer, ForeignKey("classes.id", ondelete="CASCADE"), nullable=False, index=True)
    id_annee_scolaire = Column(Integer, ForeignKey("annees_scolaires.id", ondelete="CASCADE"), nullable=False, index=True)
    id_salle = Column(Integer, ForeignKey("salles.id", ondelete="SET NULL"), nullable=True, index=True)

    jour_semaine = Column(String, nullable=False)
    heure_debut = Column(Time, nullable=False)
    heure_fin = Column(Time, nullable=False)

    created_at = Column(DateTime, nullable=False, default=now_utc)
    updated_at = Column(DateTime, nullable=False, default=now_utc, onupdate=now_utc)

    cours = relationship("Cours", back_populates="seances")
    classe = relationship("Classes", back_populates="seances")
    annee_scolaire = relationship("AnneesScolaires", back_populates="seances")
    salle = relationship("Salles", back_populates="seances")
