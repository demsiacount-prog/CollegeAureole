"""Infrastructures et mobiliers de l'établissement (fiche renseignements 1er cycle).

Une ligne par année scolaire : blocs « Salles construites », « Directions » et
« Mobiliers » de la Fiche de renseignements (document 4, collège 1er cycle).
"""
from sqlalchemy import Column, DateTime, ForeignKey, Integer, UniqueConstraint
from sqlalchemy.orm import relationship
from timeutils import now_utc
from database import Base


class EtablissementInfrastructures(Base):
    __tablename__ = "etablissement_infrastructures"
    __table_args__ = (
        UniqueConstraint("id_annee_scolaire", name="uq_etab_infra_annee"),
    )

    id = Column(Integer, primary_key=True)
    id_annee_scolaire = Column(
        Integer, ForeignKey("annees_scolaires.id"), nullable=False
    )

    # Salles construites
    salles_dur = Column(Integer, nullable=True)
    salles_semi_dur = Column(Integer, nullable=True)
    salles_banco = Column(Integer, nullable=True)
    salles_autres = Column(Integer, nullable=True)

    # Directions / constructions
    direction_dur = Column(Integer, nullable=True)
    direction_banco = Column(Integer, nullable=True)
    direction_autres = Column(Integer, nullable=True)
    logement_direction = Column(Integer, nullable=True)

    # Mobiliers
    tables_bancs = Column(Integer, nullable=True)
    chaises = Column(Integer, nullable=True)
    armoires = Column(Integer, nullable=True)
    tableaux = Column(Integer, nullable=True)
    mobilier_divers = Column(Integer, nullable=True)

    created_at = Column(DateTime, nullable=False, default=now_utc)
    updated_at = Column(DateTime, nullable=False, default=now_utc, onupdate=now_utc)

    annee_scolaire = relationship("AnneesScolaires")
