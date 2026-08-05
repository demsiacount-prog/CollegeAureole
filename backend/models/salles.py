from datetime import datetime
from sqlalchemy import Column, Integer, String, event
from sqlalchemy.orm import relationship
from database import Base


class Salles(Base):
    __tablename__ = "salles"

    id = Column(Integer, primary_key=True)
    code_salle = Column(String, nullable=True, unique=True, index=True)
    nom = Column(String, nullable=False, unique=True)
    capacite = Column(Integer, nullable=True)
    created_at = Column(String, nullable=False, default=lambda: datetime.now().isoformat())
    updated_at = Column(String, nullable=False, default=lambda: datetime.now().isoformat(),
                        onupdate=lambda: datetime.now().isoformat())

    seances = relationship("Seances", back_populates="salle")


@event.listens_for(Salles, "before_insert")
def generer_code_salle(mapper, connection, target):
    """SAL{année de création}{n°} — compteur global."""
    from sqlalchemy.orm import object_session
    from identifiants import generer_code, annee_creation
    target.code_salle = generer_code(
        connection, Salles.__table__.c.code_salle, "SAL", annee_creation(),
        session=object_session(target),
    )
