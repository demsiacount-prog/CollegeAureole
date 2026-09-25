"""Tests unitaires du module identifiants.py.

Vérifie la génération des codes (EL, ENS, TUT, CLA, COU, SAL, PAI, DEP, INS),
le compteur par préfixe+année, la résolution d'année scolaire, et le
comportement en session (compteur courant dans session.info).
"""
import pytest
from datetime import date
from unittest.mock import MagicMock

from identifiants import (
    prochain_numero,
    generer_code,
    annee_creation,
    resoudre_annee,
    annee_scolaire_pour_date,
    annee_scolaire_depuis_inscription,
    _make_lock_key,
)


# ─── Fixtures ──────────────────────────────────────────────────────────────────
@pytest.fixture()
def fake_connection():
    """Connexion simulée avec le dialecte PostgreSQL."""
    conn = MagicMock()
    conn.dialect.name = "postgresql"
    return conn


@pytest.fixture()
def fake_session():
    """Session SQLAlchemy simulée avec un dict info."""
    sess = MagicMock()
    sess.info = {}
    return sess


@pytest.fixture()
def db_session_avec_annee(db_session):
    """Session de test avec une année scolaire active pour les tests de résolution."""
    from models import AnneesScolaires

    annee = AnneesScolaires(
        libelle="2025-2026", date_debut=date(2025, 9, 1),
        date_fin=date(2026, 6, 30), active=True,
    )
    db_session.add(annee)
    db_session.commit()
    return db_session


# ─── Tests prochain_numero ─────────────────────────────────────────────────────
class TestProchainNumero:
    def test_aucun_code_restant_retourne_1(self, fake_connection):
        """Aucun code existant → premier numéro = 1."""
        fake_connection.execute.return_value = MagicMock(scalars=lambda: MagicMock(all=lambda: []))
        from models.eleves import Eleves

        result = prochain_numero(fake_connection, Eleves.__table__.c.matricule, "EL", 25)
        assert result == 1

    def test_codes_existants_retourne_max_plus_1(self, fake_connection):
        """3 codes existants (EL2500001, EL2500002, EL2500003) → retourne 4."""
        fake_connection.execute.return_value = MagicMock(
            scalars=lambda: MagicMock(all=lambda: ["EL2500001", "EL2500002", "EL2500003"])
        )
        from models.eleves import Eleves

        result = prochain_numero(fake_connection, Eleves.__table__.c.matricule, "EL", 25)
        assert result == 4

    def test_code_dun_autre_prefixe_ignored(self, fake_connection):
        """Des codes d'un autre préfixe (ENS) ne perturbent pas le compteur EL."""
        fake_connection.execute.return_value = MagicMock(
            scalars=lambda: MagicMock(all=lambda: ["ENS2500001", "ENS2500002"])
        )
        from models.eleves import Eleves

        # prochain_numero reçoit une liste qui contient des codes ENS
        # mais elle filtre par le préfixe passé
        result = prochain_numero(fake_connection, Eleves.__table__.c.matricule, "EL", 25)
        # Les codes ENS ne commencent pas par "EL25" donc ne matchent pas
        assert result == 1


# ─── Tests generer_code ────────────────────────────────────────────────────────
class TestGenererCodeSansSession:
    def test_format_du_code(self, fake_connection):
        """Le format attendu est {prfixe}{annee:02d}{numero:05d}."""
        fake_connection.execute.return_value = MagicMock(
            scalars=lambda: MagicMock(all=lambda: [])
        )
        from models.eleves import Eleves

        result = generer_code(fake_connection, Eleves.__table__.c.matricule, "EL", 25)
        assert result == "EL2500001"

    def test_deuxieme_code(self, fake_connection):
        """Avec un code existant, le compteur incrémente."""
        fake_connection.execute.return_value = MagicMock(
            scalars=lambda: MagicMock(all=lambda: ["EL2500001"])
        )
        from models.eleves import Eleves

        result = generer_code(fake_connection, Eleves.__table__.c.matricule, "EL", 25)
        assert result == "EL2500002"


class TestGenererCodeAvecSession:
    def test_premier_call_initialise_le_compteur(self, fake_connection, fake_session):
        """Le premier appel avec session initialise le compteur dans session.info."""
        fake_connection.execute.return_value = MagicMock(
            scalars=lambda: MagicMock(all=lambda: [])
        )
        from models.eleves import Eleves

        result = generer_code(
            fake_connection, Eleves.__table__.c.matricule, "EL", 25,
            session=fake_session,
        )
        assert result == "EL2500001"
        assert fake_session.info[("EL", 25)] == 1

    def test_deuxieme_call_incremente(self, fake_connection, fake_session):
        """Le 2e appel avec la même session incrémenté le compteur courant."""
        fake_connection.execute.return_value = MagicMock(
            scalars=lambda: MagicMock(all=lambda: [])
        )
        from models.eleves import Eleves

        generer_code(fake_connection, Eleves.__table__.c.matricule, "EL", 25, session=fake_session)
        result2 = generer_code(fake_connection, Eleves.__table__.c.matricule, "EL", 25, session=fake_session)
        assert result2 == "EL2500002"

    def test_prefixes_differents_independants(self, fake_connection, fake_session):
        """Deux préfixes différents ont des compteurs indépendants."""
        fake_connection.execute.return_value = MagicMock(
            scalars=lambda: MagicMock(all=lambda: [])
        )
        from models.eleves import Eleves

        r1 = generer_code(fake_connection, Eleves.__table__.c.matricule, "EL", 25, session=fake_session)
        r2 = generer_code(fake_connection, Eleves.__table__.c.matricule, "ENS", 25, session=fake_session)
        assert r1 == "EL2500001"
        assert r2 == "ENS2500001"


# ─── Tests annee_creation ──────────────────────────────────────────────────────
class TestAnneeCreation:
    def test_retourne_deux_chiffres(self):
        result = annee_creation()
        assert 0 <= result <= 99
        # Vérifier que c'est bien l'année courante modulo 100
        from datetime import datetime
        assert result == datetime.now().year % 100


# ─── Tests resoudre_annee ──────────────────────────────────────────────────────
class TestResoudreAnnee:
    def test_avec_id_annee_scolaire(self, db_session_avec_annee):
        """Retourne l'année de début de l'année scolaire donnée."""
        from models.annees_scolaires import AnneesScolaires

        annee = db_session_avec_annee.query(AnneesScolaires).first()
        result = resoudre_annee(db_session_avec_annee.connection(), annee.id)
        assert result == 25  # 2025 % 100

    def test_sans_id_et_avec_annee_active(self, db_session_avec_annee):
        """Sans id, utilise l'année active."""
        result = resoudre_annee(db_session_avec_annee.connection())
        assert result == 25

    def test_sans_id_sans_annee_active(self, db_session):
        """Sans id et sans année active, utilise l'année courante."""
        result = resoudre_annee(db_session.connection())
        assert result == annee_creation()


# ─── Tests annee_scolaire_pour_date ────────────────────────────────────────────
class TestAnneeScolairePourDate:
    def test_date_dans_la_plage(self, db_session_avec_annee):
        """Une date dans la plage de l'année scolaire retourne son année."""
        result = annee_scolaire_pour_date(db_session_avec_annee.connection(), date(2026, 1, 15))
        assert result == 25  # L'année 2025-2026 commence en 2025

    def test_date_hors_plage(self, db_session_avec_annee):
        """Une date hors de toute plage retourne l'année courante."""
        result = annee_scolaire_pour_date(db_session_avec_annee.connection(), date(2023, 6, 1))
        assert result == annee_creation()


# ─── Tests _make_lock_key ──────────────────────────────────────────────────────
class TestMakeLockKey:
    def test_cle_stable(self):
        k1 = _make_lock_key("EL", 25)
        k2 = _make_lock_key("EL", 25)
        assert k1 == k2

    def test_cle_differentes_par_prefixe(self):
        k1 = _make_lock_key("EL", 25)
        k2 = _make_lock_key("ENS", 25)
        assert k1 != k2

    def test_cle_differentes_par_annee(self):
        k1 = _make_lock_key("EL", 25)
        k2 = _make_lock_key("EL", 26)
        assert k1 != k2
