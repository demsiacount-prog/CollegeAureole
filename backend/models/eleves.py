from sqlalchemy import Boolean, Column, String, DateTime, Date, event, Integer, ForeignKey
from timeutils import now_utc
from sqlalchemy.orm import relationship
from database import Base

class Eleves(Base):
    __tablename__ = "eleves"

    matricule = Column(String, primary_key=True)
    nom = Column(String, nullable=False)
    prenom = Column(String, nullable=False)
    photo = Column(String, nullable=True)
    date_de_naissance = Column(Date, nullable=False)
    lieu_de_naissance = Column(String, nullable=False)
    sexe = Column(String, nullable=False)
    adresse = Column(String, nullable=True)
    statut = Column(String, nullable=False, default="actif")
    acte_naissance = Column(Boolean, nullable=False, default=False)
    carnet_sante = Column(Boolean, nullable=False, default=False)

    created_at = Column(DateTime, nullable=False, default=now_utc)
    updated_at = Column(DateTime, nullable=False, default=now_utc, onupdate=now_utc)

    tuteur_id = Column(Integer, ForeignKey("tuteurs.id", ondelete="RESTRICT"), nullable=False)
    classe_id = Column(Integer, ForeignKey("classes.id", ondelete="SET NULL"), nullable=True)

    # Relations
    tuteur = relationship("Tuteurs", back_populates="eleves")
    classe_relation = relationship("Classes", back_populates="eleves")
    notes = relationship("Notes", back_populates="eleve")
    bulletins = relationship("Bulletins", back_populates="eleve", cascade="all, delete-orphan")
    absences = relationship("Absences", back_populates="eleve")
    inscriptions = relationship("Inscriptions", back_populates="eleve", cascade="all, delete-orphan")
    documents = relationship("Documents", back_populates="eleve", cascade="all, delete-orphan")

@event.listens_for(Eleves, "before_insert")
def receive_before_insert(mapper, connection, target):
    """Matricule EL{année scolaire d'inscription}{n°} — numérotation annuelle.

    L'année provient de `target.annee_scolaire_id` (attribut transitoire posé
    à la création), sinon de l'année scolaire active. Le compteur repart à 1
    chaque année scolaire.
    """
    from sqlalchemy.orm import object_session
    from identifiants import generer_code, resoudre_annee
    session = object_session(target)
    annee_id = getattr(target, "annee_scolaire_id", None)
    cle_annee = ("_import_annee", annee_id)
    annee = session.info.get(cle_annee) if session is not None else None
    if annee is None:
        annee = resoudre_annee(connection, annee_id)
        if session is not None:
            session.info[cle_annee] = annee
    target.matricule = generer_code(
        connection, Eleves.__table__.c.matricule, "EL", annee,
        session=session,
    )