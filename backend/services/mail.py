"""Envoi d'e-mails transactionnels par SMTP (relances, réinitialisation du mot
de passe).

Configuration lue dans l'environnement :
    SMTP_HOST, SMTP_PORT, SMTP_USER, SMTP_PASSWORD, SMTP_FROM
    SMTP_TLS   (optionnel : "true"/"1"/"oui"/"yes" → STARTTLS)

Aucune dépendance tierce : `smtplib` de la bibliothèque standard. Un échec
d'envoi n'est jamais propagé : `envoyer_email` retourne `False` (les emails
sont dégradables, pas la requête HTTP qui les déclenche).
"""
from __future__ import annotations

import logging
import os
import smtplib
from email.message import EmailMessage

logger = logging.getLogger("college_aureole")


def _env_bool(nom: str, defaut: bool = False) -> bool:
    valeur = os.getenv(nom, "").strip().lower()
    if not valeur:
        return defaut
    return valeur in ("1", "true", "oui", "yes")


def smtp_configue() -> bool:
    """True si un relais SMTP opérationnel est déclaré (hôte, port, expéditeur)."""
    return bool(os.getenv("SMTP_HOST") and os.getenv("SMTP_PORT") and os.getenv("SMTP_FROM"))


def envoyer_email(destinataire: str, sujet: str, corps_texte: str) -> bool:
    """Envoie un e-mail texte en UTF-8, puis retourne True si accepté.

    `SMTP_USER` / `SMTP_PASSWORD` sont utilisés s'ils sont présents (brokers
    sans authentification tolérés) ; `SMTP_TLS` active STARTTLS avant le
    login/envoi.
    """
    hote = os.getenv("SMTP_HOST")
    port = int(os.getenv("SMTP_PORT", "587"))
    expediteur = os.getenv("SMTP_FROM")
    utilisateur = os.getenv("SMTP_USER")
    mot_de_passe = os.getenv("SMTP_PASSWORD")
    tls = _env_bool("SMTP_TLS", False)

    if not (hote and expediteur):
        logger.warning("SMTP non configuré (SMTP_HOST/SMTP_FROM absent) : envoi ignoré")
        return False

    message = EmailMessage()
    message["From"] = expediteur
    message["To"] = destinataire
    message["Subject"] = sujet
    message.set_content(corps_texte)

    try:
        with smtplib.SMTP(hote, port, timeout=10) as serveur:
            if tls:
                serveur.starttls()
            if utilisateur:
                serveur.login(utilisateur, mot_de_passe)
            serveur.send_message(message)
        return True
    except Exception:
        logger.exception("Échec de l'envoi d'e-mail à %s", destinataire)
        return False