"""Tests d'intégration du router Notes via TestClient.

Couverture : CRUD complet, vérification barème par niveau, refus jardin,
doublon, verrouillage par trimestre (écriture requise, 423), période,
affectation cours-classe requise, état de saisie (saisie-autorisee).
"""
import pytest
from datetime import date, timedelta

import models


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
    annee = _creer_annee(client, auth_headers).json()
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
    # La création de l'année génère automatiquement les périodes (trimestres + compositions).
    trimestres = client.get(
        f"/api/trimestres/?annee_scolaire_id={annee['id']}", headers=auth_headers
    ).json()
    assert trimestres, "l'année doit avoir des périodes générées automatiquement"
    trimestre = next(t for t in trimestres if t["type"] == "TRIMESTRE")
    return {
        "eleve": eleve, "classe": cl, "enseignant": ens, "cours": cours,
        "annee": annee, "trimestre": trimestre,
    }


def _base_payload(ctx):
    """Payload commun à toutes les écritures de notes (trimestre inclus)."""
    return {
        "matricule_eleve": ctx["eleve"]["matricule"],
        "id_cours": ctx["cours"]["id"],
        "id_classe": ctx["classe"]["id"],
        "matricule_enseignant": ctx["enseignant"]["matricule"],
        "id_trimestre": ctx["trimestre"]["id"],
    }


# ─── Tests ─────────────────────────────────────────────────────────────────────
class TestCreationNote:
    def test_creer_note_ef2(self, client, auth_headers, db_session):
        ctx = _setup_eleve_cours(db_session, client, auth_headers, niveau="7ème Année")
        payload = _base_payload(ctx)
        payload["note"] = 15.5
        resp = client.post("/api/notes/", json=payload, headers=auth_headers)
        assert resp.status_code == 201
        assert resp.json()["note"] == 15.5
        assert resp.json()["peut_saisir"] is True

    def test_creer_note_ef1(self, client, auth_headers, db_session):
        ctx = _setup_eleve_cours(db_session, client, auth_headers, niveau="1ère Année")
        payload = _base_payload(ctx)
        payload["note"] = 8.5
        resp = client.post("/api/notes/", json=payload, headers=auth_headers)
        assert resp.status_code == 201

    def test_note_superieure_au_bareme_422(self, client, auth_headers, db_session):
        ctx = _setup_eleve_cours(db_session, client, auth_headers, niveau="1ère Année")
        payload = _base_payload(ctx)
        payload["note"] = 15.0  # > 10 pour EF1
        resp = client.post("/api/notes/", json=payload, headers=auth_headers)
        assert resp.status_code == 422

    def test_creer_note_avec_note_classe(self, client, auth_headers, db_session):
        ctx = _setup_eleve_cours(db_session, client, auth_headers, niveau="7ème Année")
        payload = _base_payload(ctx)
        payload["note"] = 15.5
        payload["note_classe"] = 12.0
        resp = client.post("/api/notes/", json=payload, headers=auth_headers)
        assert resp.status_code == 201
        assert resp.json()["note_classe"] == 12.0

    def test_note_classe_superieure_au_bareme_422(self, client, auth_headers, db_session):
        ctx = _setup_eleve_cours(db_session, client, auth_headers, niveau="1ère Année")
        payload = _base_payload(ctx)
        payload["note"] = 8.0
        payload["note_classe"] = 12.0  # > 10 pour EF1
        resp = client.post("/api/notes/", json=payload, headers=auth_headers)
        assert resp.status_code == 422

    def test_doublon_devient_upsert(self, client, auth_headers, db_session):
        ctx = _setup_eleve_cours(db_session, client, auth_headers)
        payload = _base_payload(ctx)
        payload["note"] = 12.0
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
        payload = _base_payload(ctx)
        payload["note"] = 10.0
        resp = client.post("/api/notes/", json=payload, headers=auth_headers)
        assert resp.status_code == 400

    def test_affectation_manquante_400(self, client, auth_headers, db_session):
        """Note pour un cours non affecté à la classe."""
        annee = _creer_annee(client, auth_headers).json()
        t = _creer_tuteur(client, auth_headers).json()
        cl = _creer_classe(client, auth_headers).json()
        ens = _creer_enseignant(client, auth_headers).json()
        cours = _creer_cours(client, auth_headers, ens["matricule"]).json()
        eleve = _creer_eleve(client, auth_headers, t["id"], cl["id"]).json()
        trimestres = client.get(
            f"/api/trimestres/?annee_scolaire_id={annee['id']}", headers=auth_headers
        ).json()
        payload = {
            "matricule_eleve": eleve["matricule"],
            "id_cours": cours["id"],
            "id_classe": cl["id"],
            "matricule_enseignant": ens["matricule"],
            "id_trimestre": trimestres[0]["id"],
            "note": 10.0,
        }
        resp = client.post("/api/notes/", json=payload, headers=auth_headers)
        assert resp.status_code == 400

    def test_eleve_introuvable_404(self, client, auth_headers, db_session):
        annee = _creer_annee(client, auth_headers).json()
        cl = _creer_classe(client, auth_headers).json()
        ens = _creer_enseignant(client, auth_headers).json()
        cours = _creer_cours(client, auth_headers, ens["matricule"]).json()
        trimestres = client.get(
            f"/api/trimestres/?annee_scolaire_id={annee['id']}", headers=auth_headers
        ).json()
        resp = client.post("/api/notes/", json={
            "matricule_eleve": "EL9900000",
            "id_cours": cours["id"],
            "id_classe": cl["id"],
            "matricule_enseignant": ens["matricule"],
            "id_trimestre": trimestres[0]["id"],
            "note": 10.0,
        }, headers=auth_headers)
        assert resp.status_code == 404

    def test_trimestre_requis_422(self, client, auth_headers, db_session):
        """Toute écriture de note exige id_trimestre : 422 si absent."""
        ctx = _setup_eleve_cours(db_session, client, auth_headers)
        payload = _base_payload(ctx)
        payload.pop("id_trimestre")
        payload["note"] = 10.0
        resp = client.post("/api/notes/", json=payload, headers=auth_headers)
        assert resp.status_code == 422

    def test_trimestre_introuvable_404(self, client, auth_headers, db_session):
        ctx = _setup_eleve_cours(db_session, client, auth_headers)
        payload = _base_payload(ctx)
        payload["id_trimestre"] = 99999
        payload["note"] = 10.0
        resp = client.post("/api/notes/", json=payload, headers=auth_headers)
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
        payload = _base_payload(ctx)
        payload["id_trimestre"] = trimestre["id"]
        payload["note"] = 10.0
        resp = client.post("/api/notes/", json=payload, headers=auth_headers)
        assert resp.status_code == 423

    def test_annee_cloturee_423(self, client, auth_headers, db_session):
        """Année scolaire clôturée : toute saisie (même sur trimestre ouvert) est bloquée."""
        ctx = _setup_eleve_cours(db_session, client, auth_headers)
        annee = db_session.query(models.AnneesScolaires).filter(
            models.AnneesScolaires.id == ctx["annee"]["id"]
        ).first()
        annee.cloturee = True
        db_session.commit()
        payload = _base_payload(ctx)
        payload["note"] = 10.0
        resp = client.post("/api/notes/", json=payload, headers=auth_headers)
        assert resp.status_code == 423

    def test_note_classe_seule_persistee(self, client, auth_headers, db_session):
        """Composition absente (note=null) + note_classe → la note est ENREGISTRÉE
        (colonne `note` désormais nullable) et relisible en base."""
        ctx = _setup_eleve_cours(db_session, client, auth_headers)
        payload = _base_payload(ctx)
        payload["note"] = None
        payload["note_classe"] = 12.0
        resp = client.post("/api/notes/", json=payload, headers=auth_headers)
        assert resp.status_code == 201
        body = resp.json()
        assert body["note"] is None
        assert body["note_classe"] == 12.0
        relue = client.get(f"/api/notes/{body['id']}", headers=auth_headers).json()
        assert relue["note"] is None
        assert relue["note_classe"] == 12.0

    def test_deux_notes_nulles_422(self, client, auth_headers, db_session):
        """Aucune note (note ET note_classe null) → validation rejetée."""
        ctx = _setup_eleve_cours(db_session, client, auth_headers)
        payload = _base_payload(ctx)
        payload["note"] = None
        payload["note_classe"] = None
        resp = client.post("/api/notes/", json=payload, headers=auth_headers)
        assert resp.status_code == 422


class TestLectureNote:
    def test_liste_avec_filtres(self, client, auth_headers, db_session):
        ctx = _setup_eleve_cours(db_session, client, auth_headers)
        payload = _base_payload(ctx)
        payload["note"] = 12.0
        client.post("/api/notes/", json=payload, headers=auth_headers)
        resp = client.get(f"/api/notes/?matricule_eleve={ctx['eleve']['matricule']}", headers=auth_headers)
        assert resp.status_code == 200
        assert len(resp.json()) == 1

    def test_liste_filtre_par_annee(self, client, auth_headers, db_session):
        """Consultation d'une année passée en lecture : `id_annee_scolaire`
        (nouvel alias) et `annee_id` (existant) filtrent les notes par année."""
        ctx = _setup_eleve_cours(db_session, client, auth_headers)
        payload = _base_payload(ctx)
        payload["note"] = 12.0
        client.post("/api/notes/", json=payload, headers=auth_headers)
        # Année antérieure (inactive, non clôturée) : ses périodes sont générées automatiquement.
        annee2 = client.post("/api/anneesScolaires/", json={
            "libelle": "2022-2023", "date_debut": "2022-09-01", "date_fin": "2023-06-30",
            "active": False,
        }, headers=auth_headers).json()
        trim2 = next(
            t for t in client.get(
                f"/api/trimestres/?annee_scolaire_id={annee2['id']}", headers=auth_headers
            ).json() if t["type"] == "TRIMESTRE"
        )
        p2 = _base_payload(ctx)
        p2["id_trimestre"] = trim2["id"]
        p2["note"] = 15.0
        client.post("/api/notes/", json=p2, headers=auth_headers)

        resp = client.get("/api/notes/", params={"id_annee_scolaire": ctx["annee"]["id"]}, headers=auth_headers)
        assert resp.status_code == 200
        assert [n["note"] for n in resp.json()] == [12.0]
        resp = client.get("/api/notes/", params={"annee_id": annee2["id"]}, headers=auth_headers)
        assert [n["note"] for n in resp.json()] == [15.0]
        # Sans filtre : les deux années sont retournées (aucun comportement cassé).
        resp = client.get("/api/notes/", params={"matricule_eleve": ctx["eleve"]["matricule"]}, headers=auth_headers)
        assert {n["note"] for n in resp.json()} == {12.0, 15.0}

    def test_get_note_par_id(self, client, auth_headers, db_session):
        ctx = _setup_eleve_cours(db_session, client, auth_headers)
        payload = _base_payload(ctx)
        payload["note"] = 12.0
        created = client.post("/api/notes/", json=payload, headers=auth_headers).json()
        resp = client.get(f"/api/notes/{created['id']}", headers=auth_headers)
        assert resp.status_code == 200

    def test_note_introuvable_404(self, client, auth_headers):
        resp = client.get("/api/notes/99999", headers=auth_headers)
        assert resp.status_code == 404

    def test_saisie_autorisee_trimestre_ouvert(self, client, auth_headers, db_session):
        ctx = _setup_eleve_cours(db_session, client, auth_headers)
        resp = client.get("/api/notes/saisie-autorisee", headers=auth_headers)
        assert resp.status_code == 200
        body = resp.json()
        assert body["annee_cloturee"] is False
        assert body["peut_saisir"] is True
        trimestres = {t["id"]: t for t in body["trimestres"]}
        assert ctx["trimestre"]["id"] in trimestres
        assert trimestres[ctx["trimestre"]["id"]]["peut_saisir"] is True

    def test_saisie_autorisee_trimestre_verrouille(self, client, auth_headers, db_session):
        ctx = _setup_eleve_cours(db_session, client, auth_headers)
        client.put(f"/api/trimestres/{ctx['trimestre']['id']}/verrouiller", headers=auth_headers)
        resp = client.get("/api/notes/saisie-autorisee", headers=auth_headers)
        body = resp.json()
        assert body["annee_cloturee"] is False
        by_id = {t["id"]: t for t in body["trimestres"]}
        assert by_id[ctx["trimestre"]["id"]]["peut_saisir"] is False
        assert by_id[ctx["trimestre"]["id"]]["verrouille"] is True
        # Les autres trimestres restent saisissables → l'année n'est pas bloquée.
        assert body["peut_saisir"] is True
        assert any(t["peut_saisir"] for t in body["trimestres"])


class TestModificationNote:
    def test_modifier_note(self, client, auth_headers, db_session):
        ctx = _setup_eleve_cours(db_session, client, auth_headers)
        payload = _base_payload(ctx)
        payload["note"] = 12.0
        created = client.post("/api/notes/", json=payload, headers=auth_headers).json()
        payload["note"] = 18.0
        resp = client.put(f"/api/notes/{created['id']}", json=payload, headers=auth_headers)
        assert resp.status_code == 200
        assert resp.json()["note"] == 18.0

    def test_modifier_trimestre_verrouille_423(self, client, auth_headers, db_session):
        ctx = _setup_eleve_cours(db_session, client, auth_headers)
        payload = _base_payload(ctx)
        payload["note"] = 12.0
        created = client.post("/api/notes/", json=payload, headers=auth_headers).json()
        client.put(f"/api/trimestres/{ctx['trimestre']['id']}/verrouiller", headers=auth_headers)
        payload["note"] = 18.0
        resp = client.put(f"/api/notes/{created['id']}", json=payload, headers=auth_headers)
        assert resp.status_code == 423

    def test_patch_modifier_trimestre_verrouille_423(self, client, auth_headers, db_session):
        ctx = _setup_eleve_cours(db_session, client, auth_headers)
        payload = _base_payload(ctx)
        payload["note"] = 12.0
        created = client.post("/api/notes/", json=payload, headers=auth_headers).json()
        client.put(f"/api/trimestres/{ctx['trimestre']['id']}/verrouiller", headers=auth_headers)
        resp = client.patch(f"/api/notes/{created['id']}", json={"note": 18.0}, headers=auth_headers)
        assert resp.status_code == 423


class TestPatchNote:
    def test_patch_partiel_note_seule(self, client, auth_headers, db_session):
        ctx = _setup_eleve_cours(db_session, client, auth_headers)
        payload = _base_payload(ctx)
        payload["note"] = 12.0
        payload["note_classe"] = 10.0
        created = client.post("/api/notes/", json=payload, headers=auth_headers).json()
        resp = client.patch(f"/api/notes/{created['id']}", json={"note": 14.5}, headers=auth_headers)
        assert resp.status_code == 200
        body = resp.json()
        assert body["note"] == 14.5
        assert body["note_classe"] == 10.0  # champ non fourni → inchangé

    def test_patch_efface_note_classe_avec_null(self, client, auth_headers, db_session):
        ctx = _setup_eleve_cours(db_session, client, auth_headers)
        payload = _base_payload(ctx)
        payload["note"] = 12.0
        payload["note_classe"] = 10.0
        created = client.post("/api/notes/", json=payload, headers=auth_headers).json()
        resp = client.patch(f"/api/notes/{created['id']}", json={"note_classe": None}, headers=auth_headers)
        assert resp.status_code == 200
        assert resp.json()["note_classe"] is None

    def test_patch_efface_note_composition_persiste(self, client, auth_headers, db_session):
        """note -> null (note de composition) est PERSISTÉ : la colonne est
        nullable. L'invariant « au moins une note » reste porté par le schéma."""
        ctx = _setup_eleve_cours(db_session, client, auth_headers)
        payload = _base_payload(ctx)
        payload["note"] = 12.0
        payload["note_classe"] = 10.0
        created = client.post("/api/notes/", json=payload, headers=auth_headers).json()
        resp = client.patch(f"/api/notes/{created['id']}", json={"note": None}, headers=auth_headers)
        assert resp.status_code == 200
        body = resp.json()
        assert body["note"] is None
        assert body["note_classe"] == 10.0
        relue = client.get(f"/api/notes/{created['id']}", headers=auth_headers).json()
        assert relue["note"] is None
        assert relue["note_classe"] == 10.0

    def test_patch_efface_les_deux_notes_422(self, client, auth_headers, db_session):
        """note ET note_classe simultanément à null → 422 (au moins une note requise)."""
        ctx = _setup_eleve_cours(db_session, client, auth_headers)
        payload = _base_payload(ctx)
        payload["note"] = 12.0
        payload["note_classe"] = 10.0
        created = client.post("/api/notes/", json=payload, headers=auth_headers).json()
        resp = client.patch(
            f"/api/notes/{created['id']}",
            json={"note": None, "note_classe": None},
            headers=auth_headers,
        )
        assert resp.status_code == 422

    def test_patch_depasse_bareme_422(self, client, auth_headers, db_session):
        ctx = _setup_eleve_cours(db_session, client, auth_headers, niveau="1ère Année")
        payload = _base_payload(ctx)
        payload["note"] = 8.0
        created = client.post("/api/notes/", json=payload, headers=auth_headers).json()
        resp = client.patch(f"/api/notes/{created['id']}", json={"note": 15.0}, headers=auth_headers)
        assert resp.status_code == 422

    def test_patch_note_introuvable_404(self, client, auth_headers):
        resp = client.patch("/api/notes/99999", json={"note": 12.0}, headers=auth_headers)
        assert resp.status_code == 404


class TestBulkNotes:
    def _payload(self, ctx, note, id_=None, note_classe=None):
        p = _base_payload(ctx)
        p["id"] = id_
        p["note"] = note
        p["note_classe"] = note_classe
        return p

    def test_bulk_creation_et_mise_a_jour(self, client, auth_headers, db_session):
        ctx = _setup_eleve_cours(db_session, client, auth_headers)
        payload = _base_payload(ctx)
        payload["note"] = 10.0
        created = client.post("/api/notes/", json=payload, headers=auth_headers).json()

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
        payload = _base_payload(ctx)
        payload["note"] = 10.0
        client.post("/api/notes/", json=payload, headers=auth_headers)
        # Lot : note déjà créée (id inconnu, auto-enregistrement en vol) → l'upsert
        # la met à jour au lieu de lever un conflit.
        resp = client.post("/api/notes/bulk", json={"notes": [
            self._payload(ctx, 12.0),  # même (élève, cours, trimestre)
        ]}, headers=auth_headers)
        assert resp.status_code == 200
        body = resp.json()
        assert body["creees"] == 0
        assert body["modifiees"] == 1
        assert body["notes"][0]["note"] == 12.0

    def test_bulk_sans_trimestre_422(self, client, auth_headers, db_session):
        """Le lot refuse une note sans trimestre (pas de contournement du verrou)."""
        ctx = _setup_eleve_cours(db_session, client, auth_headers)
        p = self._payload(ctx, 12.0)
        p.pop("id_trimestre")
        resp = client.post("/api/notes/bulk", json={"notes": [p]}, headers=auth_headers)
        assert resp.status_code == 422


class TestSuppressionNote:
    def test_supprimer_note(self, client, auth_headers, db_session):
        ctx = _setup_eleve_cours(db_session, client, auth_headers)
        payload = _base_payload(ctx)
        payload["note"] = 12.0
        created = client.post("/api/notes/", json=payload, headers=auth_headers).json()
        resp = client.delete(f"/api/notes/{created['id']}", headers=auth_headers)
        assert resp.status_code == 204

    def test_supprimer_note_404(self, client, auth_headers):
        resp = client.delete("/api/notes/99999", headers=auth_headers)
        assert resp.status_code == 404

    def test_supprimer_note_trimestre_verrouille_423(self, client, auth_headers, db_session):
        ctx = _setup_eleve_cours(db_session, client, auth_headers)
        payload = _base_payload(ctx)
        payload["note"] = 12.0
        created = client.post("/api/notes/", json=payload, headers=auth_headers).json()
        client.put(f"/api/trimestres/{ctx['trimestre']['id']}/verrouiller", headers=auth_headers)
        resp = client.delete(f"/api/notes/{created['id']}", headers=auth_headers)
        assert resp.status_code == 423
