from sqlalchemy import Column, DateTime, ForeignKey, Integer, String
from sqlalchemy.orm import relationship
from timeutils import now_utc
from database import Base


class MotDePasseReinitialisation(Base):
    """Jetons de réinitialisation du mot de passe (mot de passe oublié).

    Seul le hash SHA-256 du jeton est stocké, jamais le jeton brut (un vol de
    base ne permet pas de forger un lien valide). Le jeton expire à 30 minutes
    (expire_le) et est à usage unique : `utilise_le` est timbré à la
    consommation.
    """

    __tablename__ = "mot_de_passe_reinitialisations"

    id = Column(Integer, primary_key=True, autoincrement=True)
    id_utilisateur = Column(
        Integer, ForeignKey("utilisateurs.id", ondelete="CASCADE"),
        nullable=False, index=True,
    )
    jeton_hash = Column(String, nullable=False, unique=True, index=True)
    expire_le = Column(DateTime, nullable=False)
    utilise_le = Column(DateTime, nullable=True)
    created_at = Column(DateTime, nullable=False, default=now_utc)

    utilisateur = relationship("Utilisateurs")