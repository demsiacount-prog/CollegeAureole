
from sqlalchemy import Column, String, DateTime, event
from timeutils import now_utc
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
    specialite = Column(String, nullable=False)

    created_at = Column(DateTime, nullable=False, default=now_utc)
    updated_at = Column(DateTime, nullable=False, default=now_utc, onupdate=now_utc)

    cours = relationship("Cours", back_populates="enseignant")
    notes = relationship("Notes", back_populates="enseignant")


@event.listens_for(Enseignants, "before_insert")
def receive_before_insert(mapper, connection, target):
    if target.matricule:
        return
    from identifiants import generer_code, resoudre_annee
    from sqlalchemy.orm import object_session
    session = object_session(target)
    annee = resoudre_annee(connection)
    target.matricule = generer_code(
        connection, Enseignants.matricule, "ENS", annee, session=session
    )
