"""Tests de sécurité des uploads (validation du contenu réel, en-têtes).

Le Content-Type envoyé par le client n'est plus une source de confiance :
le type est vérifié par les octets réels (magic bytes), et les réponses de
fichier portent X-Content-Type-Options: nosniff avec un inline restreint aux
images/PDF.
"""
from datetime import date

import models

_PNG_BYTES = b"\x89PNG\r\n\x1a\n" + b"\x00" * 20
_PDF_BYTES = b"%PDF-1.4 test"
_HTML_BYTES = b"<html><script>alert(1)</script></html>"


def _peupler_eleve(db):
    tuteur = models.Tuteurs(
        nom="Kante", prenom="Mariam", email="mariam.kante@test.com",
        telephone="0102030401", adresse="Bamako", profession="Commerçante",
    )
    db.add(tuteur)
    db.flush()
    eleve = models.Eleves(
        matricule="EL202502", nom="Traore", prenom="Awa",
        date_de_naissance=date(2015, 1, 1), lieu_de_naissance="Bamako",
        sexe="F", statut="actif", tuteur_id=tuteur.id,
    )
    db.add(eleve)
    db.commit()
    db.refresh(eleve)
    return eleve


class TestValidationDuContenuReel:
    def test_html_deguise_en_png_refuse(self, client, auth_headers, db_session):
        eleve = _peupler_eleve(db_session)
        resp = client.post(
            "/api/documents/",
            data={"entite_type": "eleve", "entite_id": eleve.matricule, "categorie": "identite"},
            files={"fichier": ("cni.png", _HTML_BYTES, "image/png")},
            headers=auth_headers,
        )
        assert resp.status_code == 400
        assert resp.json()["detail"] == "Type de fichier non reconnu ou incohérent avec le contenu réel"

    def test_contenu_inconnu_refuse(self, client, auth_headers, db_session):
        eleve = _peupler_eleve(db_session)
        resp = client.post(
            "/api/documents/",
            data={"entite_type": "eleve", "entite_id": eleve.matricule, "categorie": "autre"},
            files={"fichier": ("binaire.bin", b"\x00\x01\x02\x03\x04", "application/octet-stream")},
            headers=auth_headers,
        )
        assert resp.status_code == 400

    def test_png_reel_accepte_et_stocke_png(self, client, auth_headers, db_session):
        eleve = _peupler_eleve(db_session)
        resp = client.post(
            "/api/documents/",
            data={"entite_type": "eleve", "entite_id": eleve.matricule, "categorie": "photo"},
            files={"fichier": ("photo.png", _PNG_BYTES, "image/png")},
            headers=auth_headers,
        )
        assert resp.status_code == 201
        assert resp.json()["mime_type"] == "image/png"

    def test_type_annonce_incoherent_avec_contenu_refuse(self, client, auth_headers, db_session):
        eleve = _peupler_eleve(db_session)
        resp = client.post(
            "/api/documents/",
            data={"entite_type": "eleve", "entite_id": eleve.matricule, "categorie": "autre"},
            files={"fichier": ("faux.pdf", _PNG_BYTES, "application/pdf")},
            headers=auth_headers,
        )
        assert resp.status_code == 400


class TestReponsesDeFichierSecurisees:
    def test_preview_porte_nosniff_et_inline_pdf(self, client, auth_headers, db_session):
        eleve = _peupler_eleve(db_session)
        resp = client.post(
            "/api/documents/",
            data={"entite_type": "eleve", "entite_id": eleve.matricule, "categorie": "scolaire"},
            files={"fichier": ("bulletin.pdf", _PDF_BYTES, "application/pdf")},
            headers=auth_headers,
        )
        doc = resp.json()
        preview = client.get(doc["url_preview"], headers=auth_headers)
        assert preview.status_code == 200
        assert preview.headers.get("x-content-type-options") == "nosniff"
        assert "inline" in preview.headers.get("content-disposition", "")


class TestLogoParOctetsReels:
    def test_extension_derivee_du_contenu_pas_du_header(self, client, auth_headers):
        # Header trompeur (text/html) mais contenu réellement PNG : accepté.
        resp = client.post(
            "/api/etablissement/logo",
            files={"file": ("logo", _PNG_BYTES, "text/html")},
            headers=auth_headers,
        )
        assert resp.status_code == 200
        assert resp.json()["logo"].endswith(".png")

    def test_html_refuse_comme_logo(self, client, auth_headers):
        resp = client.post(
            "/api/etablissement/logo",
            files={"file": ("logo.png", _HTML_BYTES, "image/png")},
            headers=auth_headers,
        )
        assert resp.status_code == 400