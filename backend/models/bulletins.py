from sqlalchemy import Column, DateTime, Float, ForeignKey, Integer, String, UniqueConstraint
from timeutils import now_utc
from sqlalchemy.orm import relationship
from database import Base


class Bulletins(Base):
    __tablename__ = "bulletins"
    __table_args__ = (
        UniqueConstraint("matricule_eleve", "id_trimestre", name="uq_bulletin_eleve_trimestre"),
    )

    id = Column(Integer, primary_key=True)
    matricule_eleve = Column(String, ForeignKey("eleves.matricule", ondelete="CASCADE"), nullable=False)
    id_trimestre = Column(Integer, ForeignKey("trimestres.id", ondelete="CASCADE"), nullable=False)
    id_classe = Column(Integer, ForeignKey("classes.id", ondelete="CASCADE"), nullable=False)

    moyenne_generale = Column(Float, nullable=False)
    rang = Column(Integer, nullable=True)
    appreciation = Column(String, nullable=True)
    # Étape de relecture par la direction avant diffusion aux familles
    statut = Column(String, nullable=False, default="BROUILLON")  # BROUILLON | PUBLIE
    generated_at = Column(DateTime, nullable=False, default=now_utc)
    published_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, nullable=False, default=now_utc)
    updated_at = Column(DateTime, nullable=False, default=now_utc, onupdate=now_utc)

    # Relations
    eleve = relationship("Eleves", back_populates="bulletins")
    trimestre = relationship("Trimestres", back_populates="bulletins")
    classe = relationship("Classes", back_populates="bulletins")
    details = relationship("BulletinDetails", back_populates="bulletin", cascade="all, delete-orphan")


class BulletinDetails(Base):
    __tablename__ = "bulletin_details"

    id = Column(Integer, primary_key=True)
    id_bulletin = Column(Integer, ForeignKey("bulletins.id", ondelete="CASCADE"), nullable=False)
    id_cours = Column(Integer, ForeignKey("cours.id", ondelete="CASCADE"), nullable=False)

    moyenne = Column(Float, nullable=False)
    coefficient = Column(Float, nullable=False, default=1.0)
    created_at = Column(DateTime, nullable=False, default=now_utc)
    updated_at = Column(DateTime, nullable=False, default=now_utc, onupdate=now_utc)

    bulletin = relationship("Bulletins", back_populates="details")
    cours = relationship("Cours")

    @property
    def cours_nom(self):
        return self.cours.nom if self.cours else ""
