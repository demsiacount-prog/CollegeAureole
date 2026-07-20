from datetime import datetime
from sqlalchemy import Column, String, event, Integer, ForeignKey, select, func
from sqlalchemy.orm import relationship
from database import Base

class Eleves(Base):
    __tablename__ = "eleves"

    matricule = Column(String, primary_key=True)
    nom = Column(String, nullable=False)
    prenom = Column(String, nullable=False)
    photo = Column(String, nullable=True)
    date_de_naissance = Column(String, nullable=False)
    lieu_de_naissance = Column(String, nullable=False)
    sexe = Column(String, nullable=False)
    adresse = Column(String, nullable=False)
    statut = Column(String, nullable=False, default="actif")

    created_at = Column(
        String,
        nullable=False,
        default=lambda: datetime.now().isoformat()
    )
    updated_at = Column(
        String,
        nullable=False,
        default=lambda: datetime.now().isoformat(),
        onupdate=lambda: datetime.now().isoformat()
    )

    tuteur_id = Column(Integer, ForeignKey("tuteurs.id", ondelete="RESTRICT"), nullable=False)
    classe_id = Column(Integer, ForeignKey("classes.id", ondelete="SET NULL"), nullable=True)

    # Relations
    tuteur = relationship("Tuteurs", back_populates="eleves")
    classe_relation = relationship("Classes", back_populates="eleves")
    notes = relationship("Notes", back_populates="eleve")
    bulletins = relationship("Bulletins", back_populates="eleve", cascade="all, delete-orphan")
    absences = relationship("Absences", back_populates="eleve")
    inscriptions = relationship("Inscriptions", back_populates="eleve", cascade="all, delete-orphan")

@event.listens_for(Eleves, "before_insert")
def receive_before_insert(mapper, connection, target):
    result = connection.execute(select(func.count()).select_from(Eleves.__table__))
    compteur = result.scalar() + 1
    annee = datetime.now().strftime("%y")
    target.matricule = f"EL{annee}{compteur:05d}"