"""Tests d'intégration du router Notes via TestClient.

Couverture : CRUD complet, vérification barème par niveau, refus jardin,
doublon, trimestre verrouillé, affectation cours-classe requise.
"""
import pytest
from datetime import date, timedelta


# ─── Helpers ───────────────────────────────────────────────────────────────────
def _creer_tuteur(client, auth_headers):
    return client.post("/api/tuteurs/", json={
        "nom": "T", "prenom": "T", "email": "t@ex.com",
        "telephone": "+22376000000", "adresse": "Bamako", "profession": "M",
    }, headers=auth_headers)


def _creer_classe(client, auth_headers, niveau="7ème Année", nom="A"):
    return client.post("/api/classes/", json={"niveau": niveau, "nom": nom}, headers=auth_headers)


def _creer_enseignant(client, auth_headers):
    return client.post("/api/enseignants/", json={
        "nom": "E", "prenom": "E", "email": "ens@ex.com",
        "telephone": "+22376000000", "adresse": "Bamako", "specialite": "X",
    }, headers=auth_headers)


def _creer_cours(client, auth_headers, enseignant_matricule=None):
    return client.post("/api/cours/", json={
        "nom": "Mathématiques", "description": "Algèbre",
        "volume_horaire": 4,
        "matricule_enseignant": enseignant_matricule,
        "affectations": [],
    }, headers=auth_headers)


def _creer_eleve(client, auth_headers, tuteur_id, classe_id=None):
    return client.post("/api/eleves/", json={
        "nom": "Konaté", "prenom": "Amadou",
        "date_de_naissance": "2012-03-15", "lieu_de_naissance": "Bamako",
        "sexe": "M", "tuteur_id": tuteur_id, "classe_id": classe_id,
    }, headers=auth_headers)


def _creer_annee(client, auth_headers):
    return client.post("/api/anneesScolaires/", json={
        "libelle": "2025-2026", "date_debut": "2025-09-01",
        "date_fin": "2026-06-30", "active": True,
    }, headers=auth_headers)


def _creer_trimestre(client, auth_headers, annee_id, nom="T1",
                     date_debut="2025-09-01", date_fin="2025-12-31"):
    return client.post("/api/trimestres/", json={
        "nom": nom, "annee_scolaire_id": annee_id,
        "date_debut": date_debut, "date_fin": date_fin,
    }, headers=auth_headers)


def _setup_eleve_cours(db_session, client, auth_headers, niveau="7ème Année"):
    """Crée le contexte complet (année active, tuteur, classe, enseignant,
    cours affecté, élève inscrit) et renvoie les ids."""
    _creer_annee(client, auth_headers)
    t = _creer_tuteur(client, auth_headers).json()
    cl = _creer_classe(client, auth_headers, niveau=niveau).json()
    ens = _creer_enseignant(client, auth_headers).json()
    cours = _creer_cours(client, auth_headers, enseignant_matricule=ens["matricule"]).json()
    # Affecter le cours à la classe avec coefficient
    # EF1 (niveau /10) impose coefficient=1.0, 2nd cycle autorise >1
    coefficient = 1.0 if niveau in ("1ère Année", "2ème Année", "3ème Année", "4ème Année", "5ème Année") else 2.0
    resp = client.put(
        f"/api/cours/{cours['id']}",
        json={
            "nom": "Mathématiques", "description": "Algèbre",
            "volume_horaire": 4, "matricule_enseignant": ens["matricule"],
            "affectations": [{"id_classe": cl["id"], "coefficient": coefficient}],
        },
        headers=auth_headers,
    )
    assert resp.status_code == 200, f"PUT cours failed: {resp.status_code} {resp.json()}"
    eleve = _creer_eleve(client, auth_headers, t["id"], cl["id"]).json()
    return {
        "eleve": eleve, "classe": cl, "enseignant": ens, "cours": cours,
    }


# ─── Tests ─────────────────────────────────────────────────────────────────────
class TestCreationNote:
    def test_creer_note_ef2(self, client, auth_headers, db_session):
        ctx = _setup_eleve_cours(db_session, client, auth_headers, niveau="7ème Année")
        resp = client.post("/api/notes/", json={
            "matricule_eleve": ctx["eleve"]["matricule"],
            "id_cours": ctx["cours"]["id"],
            "id_classe": ctx["classe"]["id"],
            "matricule_enseignant": ctx["enseignant"]["matricule"],
            "note": 15.5,
        }, headers=auth_headers)
        assert resp.status_code == 201
        assert resp.json()["note"] == 15.5

    def test_creer_note_ef1(self, client, auth_headers, db_session):
        ctx = _setup_eleve_cours(db_session, client, auth_headers, niveau="1ère Année")
        resp = client.post("/api/notes/", json={
            "matricule_eleve": ctx["eleve"]["matricule"],
            "id_cours": ctx["cours"]["id"],
            "id_classe": ctx["classe"]["id"],
            "matricule_enseignant": ctx["enseignant"]["matricule"],
            "note": 8.5,
        }, headers=auth_headers)
        assert resp.status_code == 201

    def test_note_superieure_au_bareme_422(self, client, auth_headers, db_session):
        ctx = _setup_eleve_cours(db_session, client, auth_headers, niveau="1ère Année")
        resp = client.post("/api/notes/", json={
            "matricule_eleve": ctx["eleve"]["matricule"],
            "id_cours": ctx["cours"]["id"],
            "id_classe": ctx["classe"]["id"],
            "matricule_enseignant": ctx["enseignant"]["matricule"],
            "note": 15.0,  # > 10 pour EF1
        }, headers=auth_headers)
        assert resp.status_code == 422

    def test_creer_note_avec_note_classe(self, client, auth_headers, db_session):
        ctx = _setup_eleve_cours(db_session, client, auth_headers, niveau="7ème Année")
        resp = client.post("/api/notes/", json={
            "matricule_eleve": ctx["eleve"]["matricule"],
            "id_cours": ctx["cours"]["id"],
            "id_classe": ctx["classe"]["id"],
            "matricule_enseignant": ctx["enseignant"]["matricule"],
            "note": 15.5,
            "note_classe": 12.0,
        }, headers=auth_headers)
        assert resp.status_code == 201
        assert resp.json()["note_classe"] == 12.0

    def test_note_classe_superieure_au_bareme_422(self, client, auth_headers, db_session):
        ctx = _setup_eleve_cours(db_session, client, auth_headers, niveau="1ère Année")
        resp = client.post("/api/notes/", json={
            "matricule_eleve": ctx["eleve"]["matricule"],
            "id_cours": ctx["cours"]["id"],
            "id_classe": ctx["classe"]["id"],
            "matricule_enseignant": ctx["enseignant"]["matricule"],
            "note": 8.0,
            "note_classe": 12.0,  # > 10 pour EF1
        }, headers=auth_headers)
        assert resp.status_code == 422

    def test_doublon_devient_upsert(self, client, auth_headers, db_session):
        ctx = _setup_eleve_cours(db_session, client, auth_headers)
        payload = {
            "matricule_eleve": ctx["eleve"]["matricule"],
            "id_cours": ctx["cours"]["id"],
            "id_classe": ctx["classe"]["id"],
            "matricule_enseignant": ctx["enseignant"]["matricule"],
            "note": 12.0,
        }
        client.post("/api/notes/", json=payload, headers=auth_headers)
        # Double soumission (auto-enregistrement blur + sauvegarde manuelle) :
        # l'upsert met à jour la note existante au lieu de lever un conflit.
        payload["note"] = 14.0
        resp = client.post("/api/notes/", json=payload, headers=auth_headers)
        assert resp.status_code == 201
        assert resp.json()["note"] == 14.0
        notes = client.get("/api/notes/", params={
            "matricule_eleve": ctx["eleve"]["matricule"],
            "id_cours": ctx["cours"]["id"],
        }, headers=auth_headers).json()
        assert len(notes) == 1
        assert notes[0]["note"] == 14.0

    def test_jardin_refuse_400(self, client, auth_headers, db_session):
        ctx = _setup_eleve_cours(db_session, client, auth_headers, niveau="Petite Section")
        resp = client.post("/api/notes/", json={
            "matricule_eleve": ctx["eleve"]["matricule"],
            "id_cours": ctx["cours"]["id"],
            "id_classe": ctx["classe"]["id"],
            "matricule_enseignant": ctx["enseignant"]["matricule"],
            "note": 10.0,
        }, headers=auth_headers)
        assert resp.status_code == 400

    def test_affectation_manquante_400(self, client, auth_headers, db_session):
        """Note pour un cours non affecté à la classe."""
        _creer_annee(client, auth_headers)
        t = _creer_tuteur(client, auth_headers).json()
        cl = _creer_classe(client, auth_headers).json()
        ens = _creer_enseignant(client, auth_headers).json()
        cours = _creer_cours(client, auth_headers, ens["matricule"]).json()
        eleve = _creer_eleve(client, auth_headers, t["id"], cl["id"]).json()
        resp = client.post("/api/notes/", json={
            "matricule_eleve": eleve["matricule"],
            "id_cours": cours["id"],
            "id_classe": cl["id"],
            "matricule_enseignant": ens["matricule"],
            "note": 10.0,
        }, headers=auth_headers)
        assert resp.status_code == 400

    def test_eleve_introuvable_404(self, client, auth_headers, db_session):
        cl = _creer_classe(client, auth_headers).json()
        ens = _creer_enseignant(client, auth_headers).json()
        cours = _creer_cours(client, auth_headers, ens["matricule"]).json()
        resp = client.post("/api/notes/", json={
            "matricule_eleve": "EL9900000",
            "id_cours": cours["id"],
            "id_classe": cl["id"],
            "matricule_enseignant": ens["matricule"],
            "note": 10.0,
        }, headers=auth_headers)
        assert resp.status_code == 404

    def test_trimestre_verrouille_423(self, client, auth_headers, db_session):
        ctx = _setup_eleve_cours(db_session, client, auth_headers)
        # Créer une 2e année (la première est déjà active)
        annee_resp = client.post("/api/anneesScolaires/", json={
            "libelle": "2026-2027", "date_debut": "2026-09-01", "date_fin": "2027-06-30",
            "active": True,
        }, headers=auth_headers)
        annee = annee_resp.json()
        trimestres_resp = client.get(f"/api/trimestres/?annee_scolaire_id={annee['id']}", headers=auth_headers)
        trimestres = trimestres_resp.json()
        # Le premier trimestre auto-généré
        trimestre = trimestres[0]
        client.put(f"/api/trimestres/{trimestre['id']}/verrouiller", headers=auth_headers)
        resp = client.post("/api/notes/", json={
            "matricule_eleve": ctx["eleve"]["matricule"],
            "id_cours": ctx["cours"]["id"],
            "id_classe": ctx["classe"]["id"],
            "matricule_enseignant": ctx["enseignant"]["matricule"],
            "note": 10.0,
            "id_trimestre": trimestre["id"],
        }, headers=auth_headers)
        assert resp.status_code == 423


class TestLectureNote:
    def test_liste_avec_filtres(self, client, auth_headers, db_session):
        ctx = _setup_eleve_cours(db_session, client, auth_headers)
        client.post("/api/notes/", json={
            "matricule_eleve": ctx["eleve"]["matricule"],
            "id_cours": ctx["cours"]["id"],
            "id_classe": ctx["classe"]["id"],
            "matricule_enseignant": ctx["enseignant"]["matricule"],
            "note": 12.0,
        }, headers=auth_headers)
        resp = client.get(f"/api/notes/?matricule_eleve={ctx['eleve']['matricule']}", headers=auth_headers)
        assert resp.status_code == 200
        assert len(resp.json()) == 1

    def test_get_note_par_id(self, client, auth_headers, db_session):
        ctx = _setup_eleve_cours(db_session, client, auth_headers)
        created = client.post("/api/notes/", json={
            "matricule_eleve": ctx["eleve"]["matricule"],
            "id_cours": ctx["cours"]["id"],
            "id_classe": ctx["classe"]["id"],
            "matricule_enseignant": ctx["enseignant"]["matricule"],
            "note": 12.0,
        }, headers=auth_headers).json()
        resp = client.get(f"/api/notes/{created['id']}", headers=auth_headers)
        assert resp.status_code == 200

    def test_note_introuvable_404(self, client, auth_headers):
        resp = client.get("/api/notes/99999", headers=auth_headers)
        assert resp.status_code == 404


class TestModificationNote:
    def test_modifier_note(self, client, auth_headers, db_session):
        ctx = _setup_eleve_cours(db_session, client, auth_headers)
        created = client.post("/api/notes/", json={
            "matricule_eleve": ctx["eleve"]["matricule"],
            "id_cours": ctx["cours"]["id"],
            "id_classe": ctx["classe"]["id"],
            "matricule_enseignant": ctx["enseignant"]["matricule"],
            "note": 12.0,
        }, headers=auth_headers).json()
        resp = client.put(f"/api/notes/{created['id']}", json={
            "matricule_eleve": ctx["eleve"]["matricule"],
            "id_cours": ctx["cours"]["id"],
            "id_classe": ctx["classe"]["id"],
            "matricule_enseignant": ctx["enseignant"]["matricule"],
            "note": 18.0,
        }, headers=auth_headers)
        assert resp.status_code == 200
        assert resp.json()["note"] == 18.0


class TestPatchNote:
    def test_patch_partiel_note_seule(self, client, auth_headers, db_session):
        ctx = _setup_eleve_cours(db_session, client, auth_headers)
        created = client.post("/api/notes/", json={
            "matricule_eleve": ctx["eleve"]["matricule"],
            "id_cours": ctx["cours"]["id"],
            "id_classe": ctx["classe"]["id"],
            "matricule_enseignant": ctx["enseignant"]["matricule"],
            "note": 12.0,
            "note_classe": 10.0,
        }, headers=auth_headers).json()
        resp = client.patch(f"/api/notes/{created['id']}", json={"note": 14.5}, headers=auth_headers)
        assert resp.status_code == 200
        body = resp.json()
        assert body["note"] == 14.5
        assert body["note_classe"] == 10.0  # champ non fourni → inchangé

    def test_patch_efface_note_classe_avec_null(self, client, auth_headers, db_session):
        ctx = _setup_eleve_cours(db_session, client, auth_headers)
        created = client.post("/api/notes/", json={
            "matricule_eleve": ctx["eleve"]["matricule"],
            "id_cours": ctx["cours"]["id"],
            "id_classe": ctx["classe"]["id"],
            "matricule_enseignant": ctx["enseignant"]["matricule"],
            "note": 12.0,
            "note_classe": 10.0,
        }, headers=auth_headers).json()
        resp = client.patch(f"/api/notes/{created['id']}", json={"note_classe": None}, headers=auth_headers)
        assert resp.status_code == 200
        assert resp.json()["note_classe"] is None

    def test_patch_depasse_bareme_422(self, client, auth_headers, db_session):
        ctx = _setup_eleve_cours(db_session, client, auth_headers, niveau="1ère Année")
        created = client.post("/api/notes/", json={
            "matricule_eleve": ctx["eleve"]["matricule"],
            "id_cours": ctx["cours"]["id"],
            "id_classe": ctx["classe"]["id"],
            "matricule_enseignant": ctx["enseignant"]["matricule"],
            "note": 8.0,
        }, headers=auth_headers).json()
        resp = client.patch(f"/api/notes/{created['id']}", json={"note": 15.0}, headers=auth_headers)
        assert resp.status_code == 422

    def test_patch_note_introuvable_404(self, client, auth_headers):
        resp = client.patch("/api/notes/99999", json={"note": 12.0}, headers=auth_headers)
        assert resp.status_code == 404


class TestBulkNotes:
    def _payload(self, ctx, note, id_=None, note_classe=None):
        return {
            "id": id_,
            "matricule_eleve": ctx["eleve"]["matricule"],
            "id_cours": ctx["cours"]["id"],
            "id_classe": ctx["classe"]["id"],
            "matricule_enseignant": ctx["enseignant"]["matricule"],
            "note": note,
            "note_classe": note_classe,
        }

    def test_bulk_creation_et_mise_a_jour(self, client, auth_headers, db_session):
        ctx = _setup_eleve_cours(db_session, client, auth_headers)
        created = client.post("/api/notes/", json={
            "matricule_eleve": ctx["eleve"]["matricule"],
            "id_cours": ctx["cours"]["id"],
            "id_classe": ctx["classe"]["id"],
            "matricule_enseignant": ctx["enseignant"]["matricule"],
            "note": 10.0,
        }, headers=auth_headers).json()

        # 2e élève dans la même classe pour tester la création en lot (évite le doublon)
        second = client.post("/api/eleves/", json={
            "nom": "Traoré", "prenom": "Moussa",
            "date_de_naissance": "2011-06-20", "lieu_de_naissance": "Ségou",
            "sexe": "M", "tuteur_id": ctx["eleve"]["tuteur"]["id"] if ctx["eleve"].get("tuteur") else None,
            "classe_id": ctx["classe"]["id"],
        }, headers=auth_headers).json()
        second_payload = self._payload(ctx, 13.5, id_=None)
        second_payload["matricule_eleve"] = second["matricule"]
        second_payload["id_classe"] = ctx["classe"]["id"]

        resp = client.post("/api/notes/bulk", json={"notes": [
            self._payload(ctx, 11.0, id_=created["id"]),   # mise à jour
            second_payload,                                # création (autre élève)
        ]}, headers=auth_headers)
        assert resp.status_code == 200
        body = resp.json()
        assert body["creees"] == 1
        assert body["modifiees"] == 1
        notes = {n["id"]: n for n in body["notes"]}
        assert notes[created["id"]]["note"] == 11.0
        assert len(notes) == 2

    def test_bulk_depasse_bareme_422(self, client, auth_headers, db_session):
        ctx = _setup_eleve_cours(db_session, client, auth_headers, niveau="1ère Année")
        resp = client.post("/api/notes/bulk", json={"notes": [
            self._payload(ctx, 15.0),
        ]}, headers=auth_headers)
        assert resp.status_code == 422

    def test_bulk_doublon_upsert(self, client, auth_headers, db_session):
        ctx = _setup_eleve_cours(db_session, client, auth_headers)
        client.post("/api/notes/", json={
            "matricule_eleve": ctx["eleve"]["matricule"],
            "id_cours": ctx["cours"]["id"],
            "id_classe": ctx["classe"]["id"],
            "matricule_enseignant": ctx["enseignant"]["matricule"],
            "note": 10.0,
        }, headers=auth_headers)
        # Lot : note déjà créée (id inconnu, auto-enregistrement en vol) → l'upsert
        # la met à jour au lieu de lever un conflit.
        resp = client.post("/api/notes/bulk", json={"notes": [
            self._payload(ctx, 12.0),  # même (élève, cours, trimestre=null)
        ]}, headers=auth_headers)
        assert resp.status_code == 200
        body = resp.json()
        assert body["creees"] == 0
        assert body["modifiees"] == 1
        assert body["notes"][0]["note"] == 12.0


class TestSuppressionNote:
    def test_supprimer_note(self, client, auth_headers, db_session):
        ctx = _setup_eleve_cours(db_session, client, auth_headers)
        created = client.post("/api/notes/", json={
            "matricule_eleve": ctx["eleve"]["matricule"],
            "id_cours": ctx["cours"]["id"],
            "id_classe": ctx["classe"]["id"],
            "matricule_enseignant": ctx["enseignant"]["matricule"],
            "note": 12.0,
        }, headers=auth_headers).json()
        resp = client.delete(f"/api/notes/{created['id']}", headers=auth_headers)
        assert resp.status_code == 204

    def test_supprimer_note_404(self, client, auth_headers):
        resp = client.delete("/api/notes/99999", headers=auth_headers)
        assert resp.status_code == 404
