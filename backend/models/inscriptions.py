from datetime import date, datetime
from sqlalchemy import Column, Integer, String, Date, Float, Boolean, ForeignKey, UniqueConstraint
from sqlalchemy.orm import relationship
from database import Base


class Inscriptions(Base):
    __tablename__ = "inscriptions"
    __table_args__ = (
        UniqueConstraint("matricule_eleve", "id_annee_scolaire", name="uq_inscription_eleve_annee"),
    )

    id = Column(Integer, primary_key=True, autoincrement=True)
    matricule_eleve = Column(String, ForeignKey("eleves.matricule", ondelete="CASCADE"), nullable=False, index=True)
    id_classe = Column(Integer, ForeignKey("classes.id", ondelete="SET NULL"), nullable=True, index=True)
    id_annee_scolaire = Column(Integer, ForeignKey("annees_scolaires.id", ondelete="RESTRICT"), nullable=False, index=True)

    statut = Column(String, nullable=False, default="Inscrit")
    statut_passage = Column(String, nullable=False, default="EN_ATTENTE")
    diplome = Column(Boolean, nullable=False, default=False)  # fin de cycle (9ème) réussie
    montant_total = Column(Float, nullable=False, default=0.0)
    credit_disponible = Column(Float, nullable=False, default=0.0)  # trop-perçu non encore affecté
    date_inscription = Column(Date, nullable=False, default=date.today)
    date_fin = Column(Date, nullable=True)
    observation = Column(String, nullable=True)

    created_at = Column(String, nullable=False, default=lambda: datetime.now().isoformat())
    updated_at = Column(String, nullable=False, default=lambda: datetime.now().isoformat(), onupdate=lambda: datetime.now().isoformat())

    eleve = relationship("Eleves", back_populates="inscriptions")
    classe = relationship("Classes", back_populates="inscriptions")
    annee_scolaire = relationship("AnneesScolaires", back_populates="inscriptions")
    paiements = relationship("Paiements", back_populates="inscription", cascade="all, delete-orphan")
    echeances = relationship("Echeances", back_populates="inscription", cascade="all, delete-orphan", order_by="Echeances.date_echeance")
