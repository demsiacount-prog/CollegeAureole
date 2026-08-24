from datetime import date

from sqlalchemy import Column, Integer, String, Date, Boolean, DateTime, ForeignKey
from timeutils import now_utc
from sqlalchemy.orm import relationship
from database import Base


class Absences(Base):
    __tablename__ = "absences"

    id = Column(Integer, primary_key=True, autoincrement=True)
    matricule_eleve = Column(String, ForeignKey("eleves.matricule", ondelete="CASCADE"), nullable=False, index=True)
    id_cours = Column(Integer, ForeignKey("cours.id", ondelete="SET NULL"), nullable=True, index=True)
    date_absence = Column(Date, nullable=False, default=date.today, index=True)
    justifiee = Column(Boolean, nullable=False, default=False)
    motif = Column(String, nullable=True)

    justifiee_par_id = Column(Integer, ForeignKey("utilisateurs.id", ondelete="SET NULL"), nullable=True)
    date_justification = Column(DateTime, nullable=True)

    created_at = Column(DateTime, nullable=False, default=now_utc)
    updated_at = Column(DateTime, nullable=False, default=now_utc, onupdate=now_utc)

    eleve = relationship("Eleves", back_populates="absences")
    cours = relationship("Cours")
    justifiee_par = relationship("Utilisateurs")
