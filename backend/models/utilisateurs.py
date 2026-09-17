
from sqlalchemy import Boolean, Column, DateTime, Integer, String
from timeutils import now_utc
from database import Base


class Utilisateurs(Base):
    __tablename__ = "utilisateurs"

    id = Column(Integer, primary_key=True)
    nom = Column(String, nullable=False)
    prenom = Column(String, nullable=False)
    email = Column(String, nullable=False, unique=True, index=True)
    mot_de_passe = Column(String, nullable=False)
    role = Column(String, nullable=False, default="ADMIN", server_default="ADMIN")

    actif = Column(Boolean, nullable=False, default=True)

    tentatives_echouees = Column(Integer, nullable=False, default=0)
    verrouille_jusqua = Column(DateTime, nullable=True)

    created_at = Column(DateTime, nullable=False, default=now_utc)
    updated_at = Column(DateTime, nullable=False, default=now_utc, onupdate=now_utc)
