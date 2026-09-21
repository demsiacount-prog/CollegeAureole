from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Integer, String
from sqlalchemy.orm import relationship
from timeutils import now_utc
from database import Base


class ClotureAlertes(Base):
    """Élèves non réinscrits lors d'une clôture d'année (classe suivante
    inexistante, doublon d'inscription…).

    La clôture persiste ici chaque cas passé dans `rapport.erreurs` afin que
    l'admin reçoive un RAPPEL actif (liste dédiée + résolution explicite) au
    lieu de perdre ces élèves de l'année suivante. La suppression de l'année
    emporte ses alertes (ondelete CASCADE).
    """

    __tablename__ = "cloture_alertes"

    id = Column(Integer, primary_key=True, autoincrement=True)
    id_annee_scolaire = Column(
        Integer,
        ForeignKey("annees_scolaires.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    matricule = Column(String, nullable=False, index=True)
    nom = Column(String, nullable=True)
    prenom = Column(String, nullable=True)
    motif = Column(String, nullable=False)
    resolue = Column(Boolean, nullable=False, default=False)
    cree_le = Column(DateTime, nullable=False, default=now_utc)
    resolue_le = Column(DateTime, nullable=True)

    annee_scolaire = relationship("AnneesScolaires")