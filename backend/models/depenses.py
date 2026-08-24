from datetime import date

from sqlalchemy import Column, Integer, String, Float, Date, DateTime, event
from timeutils import now_utc
from database import Base

class Depenses(Base):
    __tablename__ = "depenses"

    id          = Column(Integer, primary_key=True, autoincrement=True)
    code_depense = Column(String, nullable=True, unique=True, index=True)
    libelle     = Column(String, nullable=False)
    montant     = Column(Float, nullable=False)
    categorie   = Column(String, nullable=False, default="AUTRE")
    date        = Column(Date, nullable=False, default=date.today)
    description = Column(String, nullable=True)
    created_at  = Column(DateTime, nullable=False, default=now_utc)
    updated_at  = Column(DateTime, nullable=False, default=now_utc, onupdate=now_utc)


@event.listens_for(Depenses, "before_insert")
def generer_code_depense(mapper, connection, target):
    """DEP{année scolaire de la date}{n°} — numérotation annuelle."""
    from sqlalchemy.orm import object_session
    from identifiants import generer_code, annee_scolaire_pour_date
    session = object_session(target)
    date_depense = target.date or date.today()
    annee = annee_scolaire_pour_date(connection, date_depense)
    target.code_depense = generer_code(
        connection, Depenses.__table__.c.code_depense, "DEP", annee,
        session=session,
    )