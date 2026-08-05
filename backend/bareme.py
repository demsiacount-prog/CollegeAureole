import re


def niveau_ordre(niveau: str) -> int | None:
    """Ordre (1-9 école fondamentale, 10-12 lycée) extrait du libellé de niveau."""
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


def bareme_niveau(niveau: str) -> int:
    """Barème selon le niveau : EF1 (1e-6e) → 10, EF2 (7e-9e) et lycée → 20."""
    if _est_lycee(niveau):
        return 20
    ordre = niveau_ordre(niveau)
    if ordre is None:
        return 20
    return 10 if 1 <= ordre <= 6 else 20


def appreciation_for_moyenne(moyenne: float, bareme: int) -> str:
    half = bareme / 2
    if moyenne >= bareme * 0.8:
        return "Excellent"
    if moyenne >= bareme * 0.7:
        return "Très bien"
    if moyenne >= bareme * 0.6:
        return "Bien"
    if moyenne >= half:
        return "Passable"
    return "Insuffisant"


def seuil_passage(bareme: int) -> float:
    return bareme / 2.0
