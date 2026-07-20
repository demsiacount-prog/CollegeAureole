from datetime import datetime
from sqlalchemy import Column, String, Float, event, select, func
from sqlalchemy.orm import relationship
from database import Base


class Enseignants(Base):
    __tablename__ = "enseignants"

    matricule = Column(String, primary_key=True)
    nom = Column(String, nullable=False)
    prenom = Column(String, nullable=False)
    email = Column(String, nullable=False, unique=True)
    telephone = Column(String, nullable=False)
    adresse = Column(String, nullable=False)
    profession = Column(String, nullable=False)
    heures_hebdo_max = Column(Float, nullable=True)  # None = pas de quota contrôlé

    created_at = Column(String, nullable=False, default=lambda: datetime.now().isoformat())
    updated_at = Column(String, nullable=False, default=lambda: datetime.now().isoformat(), onupdate=lambda: datetime.now().isoformat())

    cours = relationship("Cours", back_populates="enseignant")
    notes = relationship("Notes", back_populates="enseignant")


@event.listens_for(Enseignants, "before_insert")
def receive_before_insert(mapper, connection, target):
    result = connection.execute(select(func.count()).select_from(Enseignants.__table__))
    compteur = result.scalar() + 1
    annee = datetime.now().strftime("%y")
    target.matricule = f"ENS{annee}{compteur:05d}"
