from datetime import datetime
from sqlalchemy import Column, Integer, String, event
from sqlalchemy.orm import relationship
from database import Base

class Tuteurs(Base):
    __tablename__ = "tuteurs"
    id = Column(Integer, primary_key=True)
    code_tuteur = Column(String, nullable=True, unique=True, index=True)
    nom = Column(String, nullable=False)
    prenom = Column(String, nullable=False)
    email = Column(String, nullable=False)
    telephone = Column(String, nullable=False)
    adresse = Column(String, nullable=False)
    profession = Column(String, nullable=False)
    created_at = Column(String, nullable=False, default=lambda: datetime.now().isoformat())
    updated_at = Column(String, nullable=False, default=lambda: datetime.now().isoformat(),
                        onupdate=lambda: datetime.now().isoformat())
    
    eleves = relationship("Eleves", back_populates="tuteur")


@event.listens_for(Tuteurs, "before_insert")
def generer_code_tuteur(mapper, connection, target):
    """TUT{année de création}{n°} — compteur global."""
    from sqlalchemy.orm import object_session
    from identifiants import generer_code, annee_creation
    target.code_tuteur = generer_code(
        connection, Tuteurs.__table__.c.code_tuteur, "TUT", annee_creation(),
        session=object_session(target),
    )