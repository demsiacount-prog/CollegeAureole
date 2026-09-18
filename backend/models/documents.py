from sqlalchemy import Column, Integer, String, ForeignKey, LargeBinary, DateTime
from timeutils import now_utc
from sqlalchemy.orm import relationship
from database import Base


class Documents(Base):
    """Pièces jointes attachées à une entité (élève, enseignant, tuteur).

    Une seule des trois colonnes d'attachement est renseignée selon l'entité.
    Les documents d'enseignant/tuteur sont rattachés par vraie clé étrangère ;
    la suppression de l'entité met la colonne à NULL (historique conservé).
    """

    __tablename__ = "documents"

    id = Column(Integer, primary_key=True, autoincrement=True)
    matricule_eleve = Column(String, ForeignKey("eleves.matricule", ondelete="CASCADE"), nullable=True, index=True)
    matricule_enseignant = Column(String, ForeignKey("enseignants.matricule", ondelete="SET NULL"), nullable=True, index=True)
    code_tuteur = Column(String, ForeignKey("tuteurs.code_tuteur", ondelete="SET NULL"), nullable=True, index=True)
    # Catégorie de regroupement (§ Type K) : identite / photo / naissance /
    # scolaire / medical / administratif / autre. Remplace le type_document
    # dans les nouveaux flux d'upload ; les anciennes pièces gardent leur
    # type_document d'origine (compat rétro).
    categorie = Column(String, nullable=False, default="autre")
    type_document = Column(String, nullable=True)
    filename = Column(String, nullable=False)
    # Nom d'origine du fichier (conservé pour le téléchargement).
    nom_fichier_original = Column(String, nullable=True)
    filepath = Column(String, nullable=False)
    # Contenu stocké en base : la base est autonome (sauvegarde = 1 fichier).
    contenu = Column(LargeBinary, nullable=True)
    taille = Column(Integer, nullable=True)
    mime_type = Column(String, nullable=True)
    uploaded_at = Column(DateTime, nullable=False, default=now_utc)

    eleve = relationship("Eleves", back_populates="documents")
    enseignant = relationship("Enseignants", back_populates="documents")
    tuteur = relationship("Tuteurs", back_populates="documents")
