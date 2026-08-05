# schemas/echeances.py
from datetime import date
from pydantic import BaseModel, Field
from typing import Optional, Literal

TypeEcheance = Literal["INSCRIPTION", "MENSUALITE"]
StatutEcheance = Literal["EN_ATTENTE", "PARTIEL", "SOLDE", "REPORTE"]


class EcheanceResponse(BaseModel):
    id:                  int
    id_inscription:      int
    id_classe:           Optional[int] = None
    type_echeance:       TypeEcheance
    mois:                Optional[str] = None
    date_echeance:       date
    montant_du:          float
    montant_paye:        float
    reste_a_payer:       float
    statut:              StatutEcheance
    id_echeance_origine: Optional[int] = None

    model_config = {"from_attributes": True}


class RelanceResponse(EcheanceResponse):
    """Échéance en retard enrichie : élève, classe et contact du tuteur
    (prêt à brancher sur un envoi email/SMS de relance)."""
    matricule_eleve:     Optional[str] = None
    eleve_nom:           Optional[str] = None
    eleve_prenom:        Optional[str] = None
    classe_nom:          Optional[str] = None
    niveau_classe:       Optional[str] = None
    code_tuteur:         Optional[str] = None
    tuteur_nom:          Optional[str] = None
    tuteur_prenom:       Optional[str] = None
    telephone_tuteur:    Optional[str] = None
    email_tuteur:        Optional[str] = None


class PaiementEcheanceCreate(BaseModel):
    """Enregistrer un paiement sur une inscription.
    Le montant est distribué automatiquement sur les échéances impayées."""
    id_inscription: int
    montant:        float = Field(gt=0)
    date:           date
    mode:           Optional[str] = None
    numero_recu:    Optional[str] = None
    observation:    Optional[str] = None


class PaiementEcheanceResponse(BaseModel):
    """Résultat d'un paiement : liste des écheances soldées/partiellement payées."""
    paiements_crees:     list
    echeances_mises_a_jour: list[EcheanceResponse]
    reste_global:        float
    model_config = {"from_attributes": True}