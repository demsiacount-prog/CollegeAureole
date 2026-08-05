from datetime import datetime
from sqlalchemy import Boolean, Column, DateTime, Enum, Integer, String
from database import Base
from enums import RoleUtilisateur


class Utilisateurs(Base):
    __tablename__ = "utilisateurs"

    id = Column(Integer, primary_key=True)
    nom = Column(String, nullable=False)
    prenom = Column(String, nullable=False)
    email = Column(String, nullable=False, unique=True, index=True)
    mot_de_passe = Column(String, nullable=False)

    role = Column(Enum(RoleUtilisateur), nullable=False, default=RoleUtilisateur.COMPTABLE)
    actif = Column(Boolean, nullable=False, default=True)

    tentatives_echouees = Column(Integer, nullable=False, default=0)
    verrouille_jusqua = Column(DateTime, nullable=True)

    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)
