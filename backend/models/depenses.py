# models/depenses.py
from datetime import datetime
from sqlalchemy import Column, Integer, String, Float, Date, event
from database import Base

class Depenses(Base):
    __tablename__ = "depenses"

    id          = Column(Integer, primary_key=True, autoincrement=True)
    code_depense = Column(String, nullable=True, unique=True, index=True)
    libelle     = Column(String, nullable=False)
    montant     = Column(Float, nullable=False)
    categorie   = Column(String, nullable=False, default="AUTRE")
    date        = Column(Date, nullable=False, default=datetime.now().date)
    description = Column(String, nullable=True)
    created_at  = Column(String, nullable=False, default=lambda: datetime.now().isoformat())
    updated_at  = Column(String, nullable=False,
                         default=lambda: datetime.now().isoformat(),
                         onupdate=lambda: datetime.now().isoformat())


@event.listens_for(Depenses, "before_insert")
def generer_code_depense(mapper, connection, target):
    """DEP{année scolaire de la date}{n°} — numérotation annuelle."""
    from sqlalchemy.orm import object_session
    from identifiants import generer_code, annee_scolaire_pour_date
    date_depense = target.date or datetime.now().date()
    annee = annee_scolaire_pour_date(connection, date_depense)
    target.code_depense = generer_code(
        connection, Depenses.__table__.c.code_depense, "DEP", annee,
        session=object_session(target),
    )