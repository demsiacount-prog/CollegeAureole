from datetime import datetime
from typing import Optional
from pydantic import BaseModel, ConfigDict


class DocumentResponse(BaseModel):
    id: int
    matricule_eleve: Optional[str] = None
    matricule_enseignant: Optional[str] = None
    code_tuteur: Optional[str] = None
    categorie: str = "autre"
    type_document: Optional[str] = None
    filename: str
    nom_fichier_original: Optional[str] = None
    taille: Optional[int] = None
    mime_type: Optional[str] = None
    uploaded_at: datetime

    model_config = ConfigDict(from_attributes=True)


class DocumentRead(BaseModel):
    """Forme REST générique (§46) — c'est le contrat de l'API documents.

    `categorie` désigne ici le regroupement Type K (identite, photo, …).
    les champs `matricule_eleve`, `filename`, `uploaded_at`… sont conservés
    comme alias rétro-compat pour les routes historiques.
    """

    id: int
    nom: str
    categorie: str = "autre"
    entite_type: Optional[str] = None   # "eleve" | "enseignant" | "tuteur"
    entite_id: Optional[str] = None     # matricule ou code
    nom_fichier_original: Optional[str] = None
    type_mime: Optional[str] = None
    taille_octets: Optional[int] = None
    created_at: datetime
    url_preview: str
    url_download: str
    # Alias rétro-compat (routes historiques et embeds de dossier).
    matricule_eleve: Optional[str] = None
    matricule_enseignant: Optional[str] = None
    code_tuteur: Optional[str] = None
    type_document: Optional[str] = None
    filename: str
    taille: Optional[int] = None
    mime_type: Optional[str] = None
    uploaded_at: datetime
    # Informations de contexte (liste globale « Documents scolaires »).
    entite_label: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


class DocumentUpdate(BaseModel):
    nom: Optional[str] = None
    categorie: Optional[str] = None

    model_config = ConfigDict(extra="forbid")


class DocumentListeResponse(DocumentRead):
    """Vue enrichie pour la page globale « Documents scolaires » (rétro)."""

    entite_label: str
