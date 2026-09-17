import re


# Sections du jardin d'enfants (préscolaire) — ordre d'ancienneté.
SECTIONS_JARDIN = ("Petite Section", "Moyenne Section", "Grande Section")


def est_jardin(niveau: str | None) -> bool:
    """Vrai si le niveau correspond à une section du jardin d'enfants."""
    return (niveau or "").strip() in SECTIONS_JARDIN


def jardin_suivant(niveau: str | None) -> str | None:
    """Section de jardin suivante (Petite → Moyenne → Grande Section), puis
    « 1ère Année » en sortie de maternelle. None si le niveau n'est pas jardin."""
    section = (niveau or "").strip()
    try:
        i = SECTIONS_JARDIN.index(section)
    except ValueError:
        return None
    if i + 1 < len(SECTIONS_JARDIN):
        return SECTIONS_JARDIN[i + 1]
    return "1ère Année"


def est_6eme(niveau: str | None) -> bool:
    """Vrai si le niveau est la 6ème année (classe spéciale).

    La 6ème combine des compositions (moyenne simple) et des trimestres
    coefficies (mais toujours notés sur 10), contrairement aux autres classes
    du 1er cycle (1ère-5ème) qui n'utilisent que des compositions sans
    coefficients.
    """
    return niveau_ordre(niveau) == 6


def est_ef1(niveau: str | None) -> bool:
    """1er cycle fondamental (1ère-6ème) : notes sur /10."""
    ordre = niveau_ordre(niveau)
    return ordre is not None and 1 <= ordre <= 6


def utilise_coefficient(niveau: str | None, type_periode: str) -> bool:
    """Décide si les coefficients s'appliquent pour une période d'un niveau.

    - COMPOSITIONS (1er cycle) : toujours en moyenne SIMPLE, aucun coefficient.
    - TRIMESTRES EF2/lycée : moyenne pondérée (/20).
    - TRIMESTRES de la 6ème (classe spéciale) : moyenne pondérée mais sur /10.
    """
    if type_periode == "COMPOSITION":
        return False
    return not est_ef1(niveau) or est_6eme(niveau)


def cycle_niveau(niveau: str | None) -> str:
    """Cycle d'un niveau : « jardin », « ef1 », « ef2 » ou « lycee ».

    Utilisé pour la terminologie et les règles propres à chaque sous-système
    (évaluation manuelle en jardin, compositions EF1, trimestres EF2, etc.).
    """
    if est_jardin(niveau):
        return "jardin"
    if _est_lycee(niveau or ""):
        return "lycee"
    ordre = niveau_ordre(niveau)
    if ordre is not None and 1 <= ordre <= 6:
        return "ef1"
    return "ef2"


def niveau_ordre(niveau: str | None) -> int | None:
    """Ordre (1-9 école fondamentale, 10-12 lycée) extrait du libellé de niveau.
    Les sections du jardin d'enfants n'ont pas d'ordre numérique (None)."""
    if est_jardin(niveau):
        return None
    match = re.match(r"^(\d+)", niveau or "")
    return int(match.group(1)) if match else None


def _est_lycee(niveau: str) -> bool:
    """Détecte les libellés de lycée pour ne pas les confondre avec les années
    d'école fondamentale (le pivot « 1ère/2nde » du lycée partage le chiffre
    initial avec « 1ère Année / 2ème Année » de l'EF1). Le format « Xème Année »
    désigne toujours l'école fondamentale."""
    n = (niveau or "").strip().lower()
    if "année" in n or "annee" in n or " année" in n or " an" in n:
        return False
    if any(k in n for k in ("terminale", "tle", "seconde", "première", "premiere", "2nde", "2de")):
        return True
    if re.match(r"^1ère", n) or re.match(r"^1re\b", n):
        return True
    return False


def bareme_niveau(niveau: str | None) -> int:
    """Barème selon le niveau : EF1 (1e-6e) → 10, EF2 (7e-9e), lycée et jardin
    (non noté, barème par défaut) → 20."""
    if est_jardin(niveau):
        return 20
    if _est_lycee(niveau or ""):
        return 20
    ordre = niveau_ordre(niveau)
    if ordre is None:
        return 20
    return 10 if 1 <= ordre <= 6 else 20


def appreciation_for_moyenne(moyenne: float, bareme: int) -> str:
    """Mention officielle malienne (arrêté relatif aux évaluations scolaires) :
    proportionnelle au barème (/10 en EF1, /20 en EF2 et lycée).

    - Excellent   : ≥ 90 %   (≥ 9/10, ≥ 18/20)
    - Très bien   : 80-90 %  (8-9/10, 16-18/20)
    - Bien        : 70-80 %  (7-8/10, 14-16/20)
    - Assez bien  : 60-70 %  (6-7/10, 12-14/20)
    - Passable    : 50-60 %  (5-6/10, 10-12/20)
    - Insuffisant : < 50 %
    """
    if moyenne >= bareme * 0.9:
        return "Excellent"
    if moyenne >= bareme * 0.8:
        return "Très bien"
    if moyenne >= bareme * 0.7:
        return "Bien"
    if moyenne >= bareme * 0.6:
        return "Assez bien"
    if moyenne >= bareme * 0.5:
        return "Passable"
    return "Insuffisant"


def est_bulletin_officiel(niveau: str | None) -> bool:
    """Vrai si le niveau utilise le bulletin officiel (6è à 9è)."""
    if est_6eme(niveau):
        return True
    ordre = niveau_ordre(niveau)
    return ordre is not None and 7 <= ordre <= 9


def seuil_passage(bareme: int) -> float:
    return bareme / 2.0