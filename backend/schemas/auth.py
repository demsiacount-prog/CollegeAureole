"""Schémas d'authentification : réinitialisation du mot de passe oublié.

La réponse de /mot-de-passe-oublie est volontairement identique en forme
quelle que soit la suite (anti-énumération de comptes) : seule la valeur de
`email_envoye` varie selon que le SMTP est actif et que l'envoi a abouti.
"""
from pydantic import BaseModel, EmailStr, Field


class MotDePasseOublieRequest(BaseModel):
    email: EmailStr


class MotDePasseOublieResponse(BaseModel):
    """Toujours la même forme ; seul `email_envoye` varie selon le SMTP."""
    email_envoye: bool
    message: str


class ReinitialiserMotDePasseRequest(BaseModel):
    jeton: str = Field(min_length=1, max_length=256)
    nouveau_mot_de_passe: str = Field(min_length=8, max_length=128)


class ReinitialiserMotDePasseResponse(BaseModel):
    message: str