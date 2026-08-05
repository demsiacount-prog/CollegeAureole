# models/paiements.py
from datetime import datetime
from sqlalchemy import Column, Integer, String, Float, Date, ForeignKey, event
from sqlalchemy.orm import relationship
from database import Base

class Paiements(Base):
    __tablename__ = "paiements"

    id              = Column(Integer, primary_key=True, autoincrement=True)
    code_paiement   = Column(String, nullable=True, unique=True, index=True)
    id_inscription  = Column(Integer, ForeignKey("inscriptions.id", ondelete="CASCADE"),
                             nullable=False, index=True)
    id_echeance     = Column(Integer, ForeignKey("echeances.id", ondelete="SET NULL"),
                             nullable=True, index=True)

    date            = Column(Date, nullable=False, default=datetime.now().date)
    numero_recu     = Column(String, nullable=True)
    montant         = Column(Float, nullable=False)
    mode            = Column(String, nullable=True)
    observation     = Column(String, nullable=True)

    created_at = Column(String, nullable=False, default=lambda: datetime.now().isoformat())
    updated_at = Column(String, nullable=False, default=lambda: datetime.now().isoformat(),
                        onupdate=lambda: datetime.now().isoformat())

    # Relations
    inscription = relationship("Inscriptions", back_populates="paiements")
    echeance    = relationship("Echeances", back_populates="paiements")


@event.listens_for(Paiements, "before_insert")
def generer_code_paiement(mapper, connection, target):
    """PAI{année de l'inscription}{n°} — numérotation annuelle."""
    from sqlalchemy.orm import object_session
    from identifiants import generer_code, annee_scolaire_depuis_inscription
    annee = annee_scolaire_depuis_inscription(connection, target.id_inscription)
    target.code_paiement = generer_code(
        connection, Paiements.__table__.c.code_paiement, "PAI", annee,
        session=object_session(target),
    )