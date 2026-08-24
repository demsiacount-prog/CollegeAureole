"""Rate limiting en mémoire (sliding window par adresse IP).

Adapté à un usage scolaire : un ou quelques serveurs, pas de Redis requis.
Les fenêtres sont tenues en RAM par processus ; sous Gunicorn multi-workers
chaque worker limite indépendamment, ce qui reste acceptable pour une école.

Usage :
    from ratelimit import limiter
    @router.post("/connexion", dependencies=[Depends(limiter("connexion", 10, 60))])
    def connexion(...): ...
"""
import os
import threading
import time

from fastapi import Depends, Request
from exceptions import TooManyRequestsError

# En développement (et dans les tests e2e), le limiteur est désactivé : les
# suites automatisées se connectent très souvent depuis la même IP (localhost).
# Il ne s'active qu'en production (ENVIRONMENT=production) ou explicitement
# via RATE_LIMIT_ENABLED=1 pour les vérifications manuelles.
_ENV = os.environ.get("ENVIRONMENT", "development").strip().lower()
_RATE_LIMIT_ACTIF = _ENV == "production" or os.environ.get("RATE_LIMIT_ENABLED", "").strip().lower() in ("1", "true", "yes")


class _Fenetre:
    __slots__ = ("hits", "debut")

    def __init__(self) -> None:
        self.hits: list[float] = []
        self.debut: float = time.monotonic()


class RateLimiter:
    """Limiteur générique : `max_requetes` autorisées sur `fenetre_secondes`.

    Les clés de limitation combinent le nom de la limite et l'adresse IP du
    client. Le nettoyage est opportuniste (les fenêtres vides sont retirées).
    """

    def __init__(self) -> None:
        self._fenetres: dict[tuple[str, str], _Fenetre] = {}
        self._lock = threading.Lock()

    def _purge(self, maintenant: float) -> None:
        perimes = [
            cle
            for cle, f in self._fenetres.items()
            if maintenant - f.debut > 3600 and not f.hits
        ]
        for cle in perimes:
            del self._fenetres[cle]

    def autoriser(self, nom: str, ip: str, max_requetes: int, fenetre_secondes: int) -> None:
        cle = (nom, ip)
        maintenant = time.monotonic()
        with self._lock:
            f = self._fenetres.get(cle)
            if f is None:
                f = self._fenetres[cle] = _Fenetre()
            f.hits = [t for t in f.hits if maintenant - t < fenetre_secondes]
            if len(f.hits) >= max_requetes:
                self._purge(maintenant)
                raise TooManyRequestsError(
                    "Requêtes trop fréquentes"
                )
            f.hits.append(maintenant)

    def limiter(self, nom: str, max_requetes: int, fenetre_secondes: int):
        """Dépendance FastAPI : limite par IP + nom de limite."""

        def dependance(request: Request = None):
            if not _RATE_LIMIT_ACTIF:
                return
            ip = "inconnu"
            if request is not None:
                fwd = request.headers.get("x-forwarded-for")
                ip = fwd.split(",")[0].strip() if fwd else request.client.host if request.client else "inconnu"
            self.autoriser(nom, ip, max_requetes, fenetre_secondes)

        return Depends(dependance)

    def __call__(self, nom: str, max_requetes: int, fenetre_secondes: int):
        return self.limiter(nom, max_requetes, fenetre_secondes)


# Instance unique partagée par tous les routeurs.
limiter = RateLimiter()

# Limites prédéfinies (ajustables selon la taille de l'établissement).
L_CONNEXION = (5, 60)          # 5 tentatives de connexion / minute / IP
L_IMPORT = (3, 300)            # 3 imports / 5 min / IP
L_SAUVEGARDE = (6, 300)        # 6 sauvegardes / 5 min / IP
