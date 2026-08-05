# models/echeances.py
from datetime import datetime
from sqlalchemy import Column, Integer, String, Float, Date, ForeignKey, UniqueConstraint
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

    created_at = Column(String, nullable=False, default=lambda: datetime.now().isoformat())
    updated_at = Column(String, nullable=False, default=lambda: datetime.now().isoformat(),
                        onupdate=lambda: datetime.now().isoformat())

    # Relations
    inscription      = relationship("Inscriptions", back_populates="echeances")
    classe           = relationship("Classes", back_populates="echeances")
    paiements        = relationship("Paiements", back_populates="echeance")
    echeance_origine = relationship("Echeances", remote_side="Echeances.id")

    @property
    def reste_a_payer(self):
        return max(self.montant_du - self.montant_paye, 0.0)