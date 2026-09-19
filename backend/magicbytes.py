"""Détection du type réel d'un fichier par ses octets d'en-tête (magic bytes).

Le type MIME annoncé par le client (Content-Type du multipart) n'est pas
fiable : il peut être vide, trompeur ou falsifié. Un fichier `.html`/`.svg`
déguisé en `image/png` serait ensuite servi inline dans l'origine de
l'application (XSS stockée). On revalide donc ici le contenu réel avant de
stocker ou de servir un fichier.
"""

# Signatures les plus fréquentes pour les pièces acceptées par l'application.
_SIGNATURES = [
    ("image/jpeg", b"\xff\xd8\xff"),
    ("image/png", b"\x89PNG\r\n\x1a\n"),
    ("image/webp", b"RIFF"),
    ("image/gif", b"GIF8"),
    ("application/pdf", b"%PDF-"),
    # .doc ancien (OLE2) ; .docx est une archive ZIP signée PK\x03\x04.
    ("application/msword", b"\xd0\xcf\x11\xe0\xa1\xb1\x1a\xe1"),
    (
        "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        b"PK\x03\x04",
    ),
]

_TYPES_INLINE = ("image/", "application/pdf")


def detecter_type_mime(contenu: bytes) -> str | None:
    """Devine le type MIME d'un contenu d'après ses premiers octets.

    Retourne `None` si la signature ne correspond à aucun type connu.
    """
    if not contenu:
        return None
    for mime, signature in _SIGNATURES:
        n = len(signature)
        if len(contenu) < n or contenu[:n] != signature:
            continue
        if mime == "image/webp":
            # RIFF <taille> WEBP : la signature RIFF seule est trop vague.
            if len(contenu) < 12 or contenu[8:12] != b"WEBP":
                continue
        return mime
    return None


def type_autorise(
    contenu: bytes,
    annonce: str | None,
    autorises: set[str] | None = None,
) -> str | None:
    """Valide un contenu d'upload et retourne le type MIME réel à stocker.

    - Si `annonce` (Content-Type du client) est fournie, elle doit être
      générique (`application/octet-stream`) ou égale au type réel détecté.
    - Si `autorises` est fourni, le type réel doit y figurer.
    - Retourne `None` en cas de refus (contenu inconnu ou incohérent).
    """
    type_reel = detecter_type_mime(contenu)
    if type_reel is None:
        return None
    if autorises is not None and type_reel not in autorises:
        return None
    if annonce:
        norm = annonce.split(";")[0].strip().lower()
        if norm and norm not in ("application/octet-stream", type_reel):
            return None
    return type_reel


def servir_inline(type_mime: str) -> bool:
    """Les prévisualisations inline ne sont sûres que pour les images et PDF."""
    return type_mime.startswith(_TYPES_INLINE[0]) or type_mime == _TYPES_INLINE[1]