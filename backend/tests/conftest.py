"""Infrastructure de test partagée.

Stratégie : base SQLite en mémoire partagée par un StaticPool, totalement
isolée de la base de développement `collegeaureole`. On force DATABASE_URL
AVANT d'importer `database` (qui construit l'engine au chargement du module)
et on désactive le bootstrap Alembic du lifespan. Le schéma est créé/supprimé
via Base.metadata (drop_all/create_all) entre chaque test.

Le chemin racine du backend est ajouté au sys.path pour que les imports de
niveau racine (`database`, `models`, `routers`, …) fonctionnent depuis les tests.
"""
import os
import sys
import warnings
from pathlib import Path

BACKEND_ROOT = Path(__file__).resolve().parent.parent
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

# Bruit interne à FastAPI/Starlette : l'import de TestClient via httpx est
# déprécié (annonce de passage à httpx2), non corrigible de notre côté.
# Ce filtre est posé AVANT l'import de `fastapi.testclient` : ces warnings
# d'import surviennent pendant la collecte, avant que pytest n'applique ses
# propres filtrewarnings de pytest.ini, d'où la nécessité de les traiter ici.
try:
    from starlette.exceptions import StarletteDeprecationWarning as _StarletteDeprecationWarning  # noqa: E402
except Exception:  # pragma: no cover - dépend de la version de starlette
    _StarletteDeprecationWarning = UserWarning

warnings.filterwarnings(
    "ignore",
    message=r"Using `httpx` with `starlette\.testclient` is deprecated.*",
    category=_StarletteDeprecationWarning,
)

# Doit être posé avant tout import de `database` / `main`.
os.environ["DATABASE_URL"] = "sqlite:///:memory:"
os.environ["AUTO_CREATE_TABLES"] = "false"
os.environ["JWT_SECRET_KEY"] = "cle-de-test-avec-plus-de-32-caracteres"
os.environ["ENVIRONMENT"] = "test"

import pytest  # noqa: E402
from sqlalchemy.pool import StaticPool  # noqa: E402
import models  # noqa: E402
from database import Base, get_db  # noqa: E402
from main import app  # noqa: E402
from hashing import hash_password  # noqa: E402
from enums import RoleUtilisateur  # noqa: E402
from security import create_access_token  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402

# Moteur mémoire partagé : toutes les sessions partagent la même base en mémoire.
_TEST_ENGINE = None


def _test_engine():
    global _TEST_ENGINE
    if _TEST_ENGINE is None:
        from sqlalchemy import create_engine

        _TEST_ENGINE = create_engine(
            "sqlite://",
            connect_args={"check_same_thread": False},
            poolclass=StaticPool,
        )
        Base.metadata.create_all(_TEST_ENGINE)
    return _TEST_ENGINE


@pytest.fixture()
def db_session():
    """Session SQLAlchemy isolée ; schéma purgé entre chaque test."""
    from collections.abc import Generator
    from sqlalchemy.orm import Session

    engine = _test_engine()
    with engine.begin() as conn:
        # Purge complète (drop_all/create_all) pour une isolation stricte.
        Base.metadata.drop_all(bind=conn)
        Base.metadata.create_all(bind=conn)
    db: Session = Session(bind=engine, autocommit=False, autoflush=False)
    try:
        yield db
    finally:
        db.close()


@pytest.fixture()
def client(db_session):
    """TestClient FastAPI branché sur la session de test via dependency override."""

    def _override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = _override_get_db
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.pop(get_db, None)


@pytest.fixture()
def admin_user(db_session):
    """Crée un compte admin directement en base et renvoie l'objet."""
    from models.utilisateurs import Utilisateurs

    user = Utilisateurs(
        nom="Admin",
        prenom="Test",
        email="admin-test@etablissement.com",
        mot_de_passe=hash_password("Password123!"),
        role=RoleUtilisateur.ADMIN,
        actif=True,
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


@pytest.fixture()
def admin_token(admin_user, db_session):
    """JWT valide pour le compte admin de test."""
    return create_access_token(utilisateur_id=admin_user.id, role=admin_user.role.value)


@pytest.fixture()
def auth_headers(admin_token):
    return {"Authorization": f"Bearer {admin_token}"}
