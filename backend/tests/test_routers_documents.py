"""Tests d'intégration du router Documents — API générique §46 + rétro-compat.

Couvre l'API générique (GET/POST/PATCH, /preview, /fichier), la liste globale
enrichie, la non-collision avec les routes de liste par entité, et
l'authentification.
"""
from datetime import date

import models


def _peupler(db):
    """Crée un tuteur, un élève et un enseignant, chacun avec un document."""
    tuteur = models.Tuteurs(
        nom="Kante", prenom="Mariam", email="mariam.kante@test.com",
        telephone="0102030401", adresse="Bamako", profession="Commerçante",
    )
    db.add(tuteur)
    db.flush()

    eleve = models.Eleves(
        matricule="EL202501", nom="Traore", prenom="Awa",
        date_de_naissance=date(2015, 1, 1), lieu_de_naissance="Bamako",
        sexe="F", statut="actif", tuteur_id=tuteur.id,
    )
    db.add(eleve)

    enseignant = models.Enseignants(
        matricule="ENS0001", nom="Diallo", prenom="Ibrahim",
        email="ibrahim.diallo@test.com", telephone="0102030402",
        adresse="Bamako", specialite="Maths",
    )
    db.add(enseignant)
    db.commit()

    db.refresh(tuteur)
    db.refresh(eleve)
    db.refresh(enseignant)
    return tuteur, eleve, enseignant


def _importer_legacy(client, auth_headers, url, data, filename):
    return client.post(
        url,
        data=data,
        files={"file": (filename, b"%PDF-1.4 test", "application/pdf")},
        headers=auth_headers,
    )


def _importer_api(client, auth_headers, data, filename):
    return client.post(
        "/api/documents/",
        data=data,
        files={"fichier": (filename, b"%PDF-1.4 test", "application/pdf")},
        headers=auth_headers,
    )


def _peupler_avec_documents(client, auth_headers, db):
    tuteur, eleve, enseignant = _peupler(db)
    _importer_legacy(
        client, auth_headers, "/api/documents/upload",
        {"matricule_eleve": eleve.matricule, "type_document": "acte_naissance"},
        "acte_naissance.pdf",
    )
    _importer_legacy(
        client, auth_headers, "/api/documents/enseignant/upload",
        {"matricule_enseignant": enseignant.matricule, "type_document": "diplome"},
        "diplome.pdf",
    )
    _importer_legacy(
        client, auth_headers, "/api/documents/tuteur/upload",
        {"code_tuteur": tuteur.code_tuteur, "type_document": "justificatif_domicile"},
        "justificatif_domicile.pdf",
    )
    return tuteur, eleve, enseignant


class TestApiGenerique:
    def test_upload_puis_fichier_et_preview(self, client, auth_headers, db_session):
        _, eleve, _ = _peupler(db_session)
        resp = _importer_api(
            client, auth_headers,
            {"entite_type": "eleve", "entite_id": eleve.matricule, "nom": "CNI_Awa", "categorie": "identite"},
            "cni.jpg",
        )
        assert resp.status_code == 201
        doc = resp.json()
        assert doc["nom"] == "CNI_Awa"
        assert doc["categorie"] == "identite"
        assert doc["entite_type"] == "eleve"
        assert doc["entite_id"] == eleve.matricule
        assert doc["nom_fichier_original"] == "cni.jpg"
        assert doc["url_preview"] == f"/api/documents/{doc['id']}/preview"
        assert doc["url_download"] == f"/api/documents/{doc['id']}/fichier"

        fichier = client.get(doc["url_download"], headers=auth_headers)
        assert fichier.status_code == 200
        assert fichier.content == b"%PDF-1.4 test"
        assert "attachment" in fichier.headers.get("content-disposition", "")

        preview = client.get(doc["url_preview"], headers=auth_headers)
        assert preview.status_code == 200
        assert "inline" in preview.headers.get("content-disposition", "")

    def test_liste_filtree_par_entite(self, client, auth_headers, db_session):
        _, eleve, _ = _peupler_avec_documents(client, auth_headers, db_session)
        resp = client.get("/api/documents/", params={"entite_type": "eleve", "entite_id": eleve.matricule}, headers=auth_headers)
        assert resp.status_code == 200
        docs = resp.json()
        assert len(docs) == 1
        assert docs[0]["type_document"] == "acte_naissance"
        assert docs[0]["entite_type"] == "eleve"

    def test_patch_metadonnees(self, client, auth_headers, db_session):
        _, eleve, _ = _peupler_avec_documents(client, auth_headers, db_session)
        resp = client.get("/api/documents/", params={"entite_type": "eleve", "entite_id": eleve.matricule}, headers=auth_headers)
        doc_id = resp.json()[0]["id"]

        resp = client.patch(f"/api/documents/{doc_id}", json={"nom": "Acte_2025", "categorie": "scolaire"}, headers=auth_headers)
        assert resp.status_code == 200
        assert resp.json()["nom"] == "Acte_2025"
        assert resp.json()["categorie"] == "scolaire"

    def test_upload_entite_inconnue_404(self, client, auth_headers, db_session):
        _peupler(db_session)
        resp = _importer_api(
            client, auth_headers,
            {"entite_type": "eleve", "entite_id": "INCONNU", "categorie": "autre"},
            "doc.pdf",
        )
        assert resp.status_code == 404


class TestListeGlobale:
    def test_liste_vide_sans_documents(self, client, auth_headers):
        resp = client.get("/api/documents/", headers=auth_headers)
        assert resp.status_code == 200
        assert resp.json() == []

    def test_liste_enrichie_avec_entites(self, client, auth_headers, db_session):
        _peupler_avec_documents(client, auth_headers, db_session)
        resp = client.get("/api/documents/", headers=auth_headers)
        assert resp.status_code == 200
        docs = resp.json()
        assert len(docs) == 3
        by_ent = {d["entite_type"]: d for d in docs}
        assert set(by_ent) == {"eleve", "enseignant", "tuteur"}
        assert by_ent["eleve"]["entite_label"] == "Traore Awa"
        assert by_ent["eleve"]["type_document"] == "acte_naissance"
        # Les uploads legacy sont classés « autre ».
        assert by_ent["eleve"]["categorie"] == "autre"
        assert by_ent["enseignant"]["entite_label"] == "Diallo Ibrahim"
        assert by_ent["tuteur"]["entite_label"] == "Kante Mariam"
        # Tri du plus récent au plus ancien.
        assert [d["id"] for d in docs] == sorted((d["id"] for d in docs), reverse=True)

    def test_routes_par_entite_non_ombragees(self, client, auth_headers, db_session):
        tuteur, eleve, enseignant = _peupler_avec_documents(client, auth_headers, db_session)

        resp = client.get(f"/api/documents/{eleve.matricule}", headers=auth_headers)
        assert resp.status_code == 200
        assert {d["type_document"] for d in resp.json()} == {"acte_naissance"}

        resp = client.get(f"/api/documents/enseignant/{enseignant.matricule}", headers=auth_headers)
        assert resp.status_code == 200
        assert {d["type_document"] for d in resp.json()} == {"diplome"}

        resp = client.get(f"/api/documents/tuteur/{tuteur.code_tuteur}", headers=auth_headers)
        assert resp.status_code == 200
        assert {d["type_document"] for d in resp.json()} == {"justificatif_domicile"}


class TestAuthRequis:
    def test_liste_globale_sans_token_401(self, client):
        resp = client.get("/api/documents/")
        assert resp.status_code == 401