"""Infrastructure de test partagée.

Stratégie : base PostgreSQL de test dédiée (par défaut `collegeaureole_test`,
dérivée de DATABASE_URL ou surchargée par TEST_DATABASE_URL), créée
automatiquement si absente et totalement isolée de la base de dev. On force
DATABASE_URL AVANT d'importer `database` (qui construit l'engine au chargement
du module) et on désactive le bootstrap Alembic du lifespan. Le schéma est
recréé entre chaque test (DROP/CREATE schema public + create_all).

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

# .env de dev : sert à dériver l'URL de la base de test locale. python-dotenv ne
# surcharge pas les variables déjà définies (TEST_DATABASE_URL en CI prime).
from dotenv import load_dotenv  # noqa: E402

load_dotenv()

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


def _test_database_url() -> str:
    """URL de la base de test : TEST_DATABASE_URL, sinon DATABASE_URL suffixé
    en `_test`, sinon une valeur par défaut locale."""
    from sqlalchemy.engine.url import make_url

    explicite = os.environ.get("TEST_DATABASE_URL")
    if explicite:
        return explicite
    base = os.environ.get("DATABASE_URL")
    if base:
        url = make_url(base)
        return url.set(database=f"{url.database}_test").render_as_string(hide_password=False)
    return "postgresql://localhost:5432/collegeaureole_test"


def _assurer_base_de_test(url: str) -> None:
    """Crée la base de test si elle n'existe pas (connexion de maintenance)."""
    from sqlalchemy import create_engine, text
    from sqlalchemy.engine.url import make_url

    url_obj = make_url(url)
    maintenance = url_obj.set(database="postgres").render_as_string(hide_password=False)
    moteur = create_engine(maintenance, isolation_level="AUTOCOMMIT")
    try:
        with moteur.connect() as conn:
            existe = conn.execute(
                text("SELECT 1 FROM pg_database WHERE datname = :nom"),
                {"nom": url_obj.database},
            ).first()
            if not existe:
                conn.execute(text(f'CREATE DATABASE "{url_obj.database}"'))
    except Exception as exc:
        raise RuntimeError(
            f"Base de test inaccessible ({exc}) : vérifier le serveur PostgreSQL"
        ) from exc
    finally:
        moteur.dispose()


_TEST_URL = _test_database_url()
_assurer_base_de_test(_TEST_URL)

# Doit être posé avant tout import de `database` / `main`.
os.environ["DATABASE_URL"] = _TEST_URL
os.environ["AUTO_CREATE_TABLES"] = "false"
os.environ["JWT_SECRET_KEY"] = "cle-de-test-avec-plus-de-32-caracteres"
os.environ["ENVIRONMENT"] = "test"

import pytest  # noqa: E402
from sqlalchemy import create_engine, text  # noqa: E402
from sqlalchemy.pool import NullPool  # noqa: E402
from credentials import ADMIN_EMAIL, ADMIN_PASSWORD  # noqa: E402
import models  # noqa: E402
from database import Base, get_db  # noqa: E402
from main import app  # noqa: E402
from hashing import hash_password  # noqa: E402
from security import create_access_token  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402

# Moteur dédié aux tests : connexion neuve par session (NullPool) pour ne
# laisser aucune transaction résiduelle entre tests.
_TEST_ENGINE = None


def _test_engine():
    global _TEST_ENGINE
    if _TEST_ENGINE is None:
        _TEST_ENGINE = create_engine(os.environ["DATABASE_URL"], poolclass=NullPool)
    return _TEST_ENGINE


@pytest.fixture(autouse=True)
def _schema_purge():
    """Schéma vierge par test : recréation complète du schéma public."""
    engine = _test_engine()
    with engine.begin() as conn:
        conn.execute(text("DROP SCHEMA public CASCADE"))
        conn.execute(text("CREATE SCHEMA public"))
        Base.metadata.create_all(bind=conn)
    yield


@pytest.fixture()
def db_session():
    """Session SQLAlchemy sur la base de test ; schéma purgé par _schema_purge."""
    from sqlalchemy.orm import Session

    db: Session = Session(bind=_test_engine(), autocommit=False, autoflush=False)
    try:
        yield db
    finally:
        db.close()


@pytest.fixture()
def client(db_session):
    """TestClient FastAPI branché sur la session de test via dependency override."""

    def _override_get_db():
        try:
            yield db_session
        finally:
            # Si une requête a avorté la transaction (erreur DB non rattrapée),
            # la remettre à zéro pour ne pas contaminer les requêtes suivantes.
            if not db_session.is_active:
                db_session.rollback()

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
        email=ADMIN_EMAIL,
        mot_de_passe=hash_password(ADMIN_PASSWORD),
        actif=True,
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


@pytest.fixture()
def admin_token(admin_user, db_session):
    """JWT valide pour le compte admin de test."""
    return create_access_token(utilisateur_id=admin_user.id)


@pytest.fixture()
def auth_headers(admin_token):
    return {"Authorization": f"Bearer {admin_token}"}