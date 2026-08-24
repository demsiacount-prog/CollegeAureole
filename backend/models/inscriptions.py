from datetime import date

from sqlalchemy import Column, Integer, String, Date, Float, Boolean, DateTime, ForeignKey, UniqueConstraint, event
from timeutils import now_utc
from sqlalchemy.orm import relationship
from database import Base


class Inscriptions(Base):
    __tablename__ = "inscriptions"
    __table_args__ = (
        UniqueConstraint("matricule_eleve", "id_annee_scolaire", name="uq_inscription_eleve_annee"),
    )

    id = Column(Integer, primary_key=True, autoincrement=True)
    code_inscription = Column(String, nullable=True, unique=True, index=True)
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

    created_at = Column(DateTime, nullable=False, default=now_utc)
    updated_at = Column(DateTime, nullable=False, default=now_utc, onupdate=now_utc)

    eleve = relationship("Eleves", back_populates="inscriptions")
    classe = relationship("Classes", back_populates="inscriptions")
    annee_scolaire = relationship("AnneesScolaires", back_populates="inscriptions")
    paiements = relationship("Paiements", back_populates="inscription", cascade="all, delete-orphan")
    echeances = relationship("Echeances", back_populates="inscription", cascade="all, delete-orphan", order_by="Echeances.date_echeance")


@event.listens_for(Inscriptions, "before_insert")
def generer_code_inscription(mapper, connection, target):
    """Génère l'identifiant INS{année}{n°} avec numérotation annuelle.

    Format : INS suivi de l'année de début de l'année scolaire (2 chiffres)
    et d'un compteur à 5 chiffres qui repart à 1 chaque année scolaire
    (ex. 1ère inscription de l'année 2025-2026 → INS2500001).
    """
    from sqlalchemy.orm import object_session
    from identifiants import generer_code, resoudre_annee

    session = object_session(target)
    cle_annee = ("_import_annee", target.id_annee_scolaire)
    annee = session.info.get(cle_annee) if session is not None else None
    if annee is None:
        annee = resoudre_annee(connection, target.id_annee_scolaire)
        if session is not None:
            session.info[cle_annee] = annee
    target.code_inscription = generer_code(
        connection, Inscriptions.__table__.c.code_inscription, "INS", annee,
        session=session,
    )
