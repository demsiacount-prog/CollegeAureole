"""Tests de la mécanique de rate-limiting (ratelimit.py).

Couvre la fenêtre glissante anti-bruteforce du login : un nombre maximal de
requêtes par fenêtre puis blocage (TooManyRequestsError), et l'expiration des
hits après la fenêtre. On teste la classe RateLimiter directement avec une
fenêtre courte pour s'affranchir de l'état global de la session de test.
On vérifie aussi que le limiteur s'active réellement en ENVIRONMENT=production
(sous-processus, pour ne pas altérer l'état importé de la session).
"""
import os
import subprocess
import sys
import textwrap
import time

import pytest

from ratelimit import RateLimiter
from exceptions import TooManyRequestsError


class TestActivationProduction:
    def test_rate_limit_actif_en_production(self):
        # Dans la session de test, ENVIRONMENT=test → limiteur inactif.
        # En production, il doit être actif : on le vérifie dans un
        # sous-processus isolé pour ne pas perturber l'état importé.
        code = textwrap.dedent(
            """
            import os
            os.environ['ENVIRONMENT'] = 'production'
            import ratelimit
            from exceptions import TooManyRequestsError
            limiteur = ratelimit.RateLimiter()
            for _ in range(5):
                limiteur.autoriser('connexion', '203.0.113.1', *ratelimit.L_CONNEXION)
            try:
                limiteur.autoriser('connexion', '203.0.113.1', *ratelimit.L_CONNEXION)
                print('PAS_BLOQUE')
            except TooManyRequestsError:
                print('BLOQUE')
            """
        )
        env = dict(os.environ)
        env["PYTHONPATH"] = os.pathsep.join(
            p for p in [env.get("PYTHONPATH", ""), os.path.dirname(os.path.dirname(os.path.abspath(__file__)))] if p
        )
        result = subprocess.run(
            [sys.executable, "-c", code],
            capture_output=True,
            text=True,
            env=env,
        )
        assert result.returncode == 0, result.stderr
        assert "BLOQUE" in result.stdout

    def test_rate_limit_inactif_par_defaut_dev(self):
        # En développement, le limiteur réseau ne doit pas gêner les tests/dev.
        import ratelimit
        assert ratelimit._RATE_LIMIT_ACTIF is False


class TestRateLimiter:
    def test_autorise_jusqu_a_la_limite_puis_bloque(self):
        limiteur = RateLimiter()
        # 3 requêtes autorisées sur une fenêtre de 60 s, puis blocage.
        for _ in range(3):
            limiteur.autoriser("connexion", "127.0.0.1", 3, 60)
        with pytest.raises(TooManyRequestsError):
            limiteur.autoriser("connexion", "127.0.0.1", 3, 60)

    def test_cles_differentes_independantes(self):
        limiteur = RateLimiter()
        # IP différente = fenêtre distincte : administrée indépendamment.
        for _ in range(3):
            limiteur.autoriser("connexion", "10.0.0.1", 3, 60)
        # Une autre IP n'est pas bloquée.
        limiteur.autoriser("connexion", "10.0.0.2", 3, 60)

    def test_hits_expirent_apres_la_fenetre(self):
        limiteur = RateLimiter()
        ETROITE = 0.1  # fenêtre de 100 ms pour le test
        for _ in range(3):
            limiteur.autoriser("connexion", "127.0.0.1", 3, ETROITE)
        # Bloqué tant que la fenêtre n'est pas écoulée.
        with pytest.raises(TooManyRequestsError):
            limiteur.autoriser("connexion", "127.0.0.1", 3, ETROITE)
        # Après écoulement de la fenêtre, les hits expirent et l'accès revient.
        time.sleep(ETROITE + 0.2)
        limiteur.autoriser("connexion", "127.0.0.1", 3, ETROITE)

    def test_limites_par_defaut_connexion(self):
        # La règle réelle du login : 5 tentatives / minute / IP.
        from ratelimit import L_CONNEXION
        assert L_CONNEXION == (5, 60)
        limiteur = RateLimiter()
        for _ in range(5):
            limiteur.autoriser("connexion", "127.0.0.1", *L_CONNEXION)
        with pytest.raises(TooManyRequestsError):
            limiteur.autoriser("connexion", "127.0.0.1", *L_CONNEXION)
