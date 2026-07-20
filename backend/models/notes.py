from datetime import date, datetime
from sqlalchemy import Column, Integer, String, ForeignKey, Float
from sqlalchemy.orm import relationship
from database import Base

class Notes(Base):
    __tablename__ = "notes"
    id = Column(Integer, primary_key=True)
    date = Column(String, nullable=False, default=lambda: date.today().isoformat())
    note = Column(Float, nullable=False)
    created_at = Column(String, nullable=False, default=lambda: datetime.now().isoformat())
    updated_at = Column(String, nullable=False, default=lambda: datetime.now().isoformat(),
                        onupdate=lambda: datetime.now().isoformat())
    
    matricule_eleve = Column(String, ForeignKey("eleves.matricule", ondelete="CASCADE"), nullable=False, index=True)
    id_cours = Column(Integer, ForeignKey("cours.id", ondelete="CASCADE"), nullable=False)
    id_classe = Column(Integer, ForeignKey("classes.id", ondelete="CASCADE"), nullable=False, index=True)
    matricule_enseignant = Column(String, ForeignKey("enseignants.matricule", ondelete="CASCADE"), nullable=False)
    id_trimestre = Column(Integer, ForeignKey("trimestres.id", ondelete="CASCADE"), nullable=True)

    # Relations
    eleve = relationship("Eleves", back_populates="notes")
    cours = relationship("Cours", back_populates="notes")
    classe = relationship("Classes", back_populates="notes")
    enseignant = relationship("Enseignants", back_populates="notes")
    trimestre = relationship("Trimestres", back_populates="notes")