from datetime import date
from sqlalchemy import Column, Date, Integer, String, DateTime
from timeutils import now_utc
from database import Base


class Etablissement(Base):
    """Fiche de l'établissement et marqueur de la configuration initiale.

    Une seule ligne (toujours id=1) est garantie par la logique applicative :
    sa présence signifie que la phase d'initialisation a été menée à bien.
    """

    __tablename__ = "etablissement"

    id = Column(Integer, primary_key=True)
    nom = Column(String, nullable=False)
    sigle = Column(String, nullable=True)
    devise = Column(String, nullable=True)
    adresse = Column(String, nullable=True)
    telephone = Column(String, nullable=True)
    email = Column(String, nullable=True)
    logo = Column(String, nullable=True)  # chemin (relatif) du logo
    date_initialisation = Column(Date, nullable=False, default=date.today)
    academie =Column(String, nullable=False)
    cap = Column(String, nullable=False)
    village_quartier = Column(String, nullable=True)
    commune = Column(String, nullable=True)
    cercle = Column(String, nullable=True)
    statut_administratif = Column(String, nullable=True)
    type_ecole = Column(String, nullable=True)
    mode = Column(String, nullable=True)
    created_at = Column(DateTime, nullable=False, default=now_utc)
    updated_at = Column(DateTime, nullable=False, default=now_utc, onupdate=now_utc)
