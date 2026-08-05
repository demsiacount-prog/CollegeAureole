# models/cours.py
from datetime import datetime
from sqlalchemy import Column, Integer, String, ForeignKey, event
from sqlalchemy.orm import relationship
from database import Base


class Cours(Base):
    __tablename__ = "cours"
    id = Column(Integer, primary_key=True)
    code_cours = Column(String, nullable=True, unique=True, index=True)
    nom = Column(String, nullable=False)
    description = Column(String, nullable=False)
    volume_horaire = Column(Integer, nullable=False)  # utilisé pour l'emploi du temps, plus pour la pondération
    created_at = Column(String, nullable=False, default=lambda: datetime.now().isoformat())
    updated_at = Column(String, nullable=False, default=lambda: datetime.now().isoformat(),
                        onupdate=lambda: datetime.now().isoformat())

    matricule_enseignant = Column(String, ForeignKey("enseignants.matricule", ondelete="SET NULL"), nullable=True)

    # Relations
    classes_affectations = relationship(
        "AffectationCoursClasse", back_populates="cours", cascade="all, delete-orphan"
    )
    enseignant = relationship("Enseignants", back_populates="cours")
    notes = relationship("Notes", back_populates="cours")
    seances = relationship("Seances", back_populates="cours", cascade="all, delete-orphan")

    @property
    def classes(self):
        """Liste des classes où ce cours est enseigné (via AffectationCoursClasse)."""
        return [a.classe for a in self.classes_affectations]

    def coefficient_pour_classe(self, id_classe: int) -> float:
        for a in self.classes_affectations:
            if a.id_classe == id_classe:
                return a.coefficient
        return 1.0


@event.listens_for(Cours, "before_insert")
def generer_code_cours(mapper, connection, target):
    """COU{année de création}{n°} — compteur global."""
    from sqlalchemy.orm import object_session
    from identifiants import generer_code, annee_creation
    target.code_cours = generer_code(
        connection, Cours.__table__.c.code_cours, "COU", annee_creation(),
        session=object_session(target),
    )
