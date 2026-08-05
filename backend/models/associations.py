# models/associations.py
# Remplace la simple Table d'association par un modèle porteur de données :
# le coefficient d'une matière dépend de la CLASSE dans laquelle elle est enseignée
# (ex: Maths peut être coef 4 en 9ème et coef 3 en 6ème).
from datetime import datetime
from sqlalchemy import Column, Integer, Float, ForeignKey, String
from sqlalchemy.orm import relationship
from database import Base


class AffectationCoursClasse(Base):
    """Association Cours <-> Classe, avec le coefficient de pondération
    utilisé pour le calcul de la moyenne générale des bulletins."""
    __tablename__ = "classe_cours"

    id_classe = Column(Integer, ForeignKey("classes.id", ondelete="CASCADE"), primary_key=True)
    id_cours = Column(Integer, ForeignKey("cours.id", ondelete="CASCADE"), primary_key=True)
    coefficient = Column(Float, nullable=False, default=1.0)
    created_at = Column(String, nullable=False, default=lambda: datetime.now().isoformat())
    updated_at = Column(String, nullable=False, default=lambda: datetime.now().isoformat(),
                        onupdate=lambda: datetime.now().isoformat())

    classe = relationship("Classes", back_populates="cours_affectations")
    cours = relationship("Cours", back_populates="classes_affectations")
