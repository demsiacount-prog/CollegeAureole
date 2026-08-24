
from sqlalchemy import Column, Integer, Float, ForeignKey, DateTime
from timeutils import now_utc
from sqlalchemy.orm import relationship
from database import Base


class AffectationCoursClasse(Base):
    """Association Cours <-> Classe, avec le coefficient de pondération
    utilisé pour le calcul de la moyenne générale des bulletins."""
    __tablename__ = "classe_cours"
    id_classe = Column(Integer, ForeignKey("classes.id", ondelete="CASCADE"), primary_key=True)
    id_cours = Column(Integer, ForeignKey("cours.id", ondelete="CASCADE"), primary_key=True)
    coefficient = Column(Float, nullable=False, default=1.0)
    created_at = Column(DateTime, nullable=False, default=now_utc)
    updated_at = Column(DateTime, nullable=False, default=now_utc, onupdate=now_utc)

    classe = relationship("Classes", back_populates="cours_affectations")
    cours = relationship("Cours", back_populates="classes_affectations")
