
from sqlalchemy import Column, Integer, String, Float, Date, DateTime, ForeignKey, UniqueConstraint
from timeutils import now_utc
from sqlalchemy.orm import relationship
from database import Base

MOIS_ANNEE_SCOLAIRE = [
    "Octobre", "Novembre", "Décembre", "Janvier", "Février",
    "Mars", "Avril", "Mai", "Juin"
]

class Echeances(Base):
    __tablename__ = "echeances"
    __table_args__ = (
        UniqueConstraint(
            "id_inscription", "type_echeance", "mois",
            name="uq_echeance_inscription_type_mois"
        ),
    )

    id             = Column(Integer, primary_key=True, autoincrement=True)
    id_inscription = Column(Integer, ForeignKey("inscriptions.id", ondelete="CASCADE"),
                            nullable=False, index=True)
    id_classe      = Column(Integer, ForeignKey("classes.id", ondelete="SET NULL"), nullable=True)

    # "INSCRIPTION" ou "MENSUALITE"
    type_echeance  = Column(String, nullable=False)
    # Nom du mois pour les mensualités ("Octobre"…"Juin"), None pour l'inscription
    mois           = Column(String, nullable=True)
    # Date théorique d'échéance
    date_echeance  = Column(Date, nullable=False)

    montant_du     = Column(Float, nullable=False, default=0.0)
    montant_paye   = Column(Float, nullable=False, default=0.0)

    statut         = Column(String, nullable=False, default="EN_ATTENTE")
    # EN_ATTENTE | PARTIEL | SOLDE | REPORTE

    # Impayé reporté d'une année précédente ?
    id_echeance_origine = Column(Integer, ForeignKey("echeances.id", ondelete="SET NULL"),
                                 nullable=True)

    created_at = Column(DateTime, nullable=False, default=now_utc)
    updated_at = Column(DateTime, nullable=False, default=now_utc, onupdate=now_utc)

    # Relations
    inscription      = relationship("Inscriptions", back_populates="echeances")
    classe           = relationship("Classes", back_populates="echeances")
    paiements        = relationship("Paiements", back_populates="echeance")
    remises          = relationship("Remises", back_populates="echeance", cascade="all, delete-orphan")
    echeance_origine = relationship("Echeances", remote_side="Echeances.id")

    @property
    def reste_a_payer(self):
        return max(self.montant_du - self.montant_paye, 0.0)

    @property
    def total_remises(self):
        return sum(r.montant for r in self.remises) if self.remises else 0.0