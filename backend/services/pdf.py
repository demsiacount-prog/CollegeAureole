"""Génération PDF des documents officiels (bulletins).

Remplaçant de l'impression navigateur : un vrai fichier PDF est produit côté
serveur, sans adresse du site, ni en-tête/pied de page du navigateur. Les
documents sortis respectent la même maquette que l'ancien rendu écran
(.print-doc / .doc-*) : en-tête officiel, bandeau titre, grille
d'informations, tableau des notes, récapitulatif, appréciation, pied de page
et zones de signature.
"""

from __future__ import annotations

import os
import re
from datetime import date
from io import BytesIO
from typing import Iterable

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_RIGHT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import mm
from reportlab.platypus import Image, PageBreak, Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

import models
from bareme import appreciation_for_moyenne, bareme_niveau

# ─── Chemins du logo ─────────────────────────────────────────────────────────
# Identiques à routers/etablissement.py : le fichier réel (pour reportlab, et
# non l'URL publique) n'existe que dans le répertoire d'uploads du serveur.
_UPLOADS_BASE = os.environ.get("AUREOLE_UPLOADS_DIR") or os.path.normpath(
    os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "uploads")
)

_LOGO_MAX_W = 20 * mm
_LOGO_MAX_H = 18 * mm

_INK = colors.HexColor("#111111")
_GRAY = colors.HexColor("#666666")
_LINE = colors.HexColor("#999999")
_SOFT = colors.HexColor("#dddddd")

# ─── Styles ──────────────────────────────────────────────────────────────────

ST_NOM = ParagraphStyle(
    "inform-name",
    fontName="Helvetica-Bold",
    fontSize=16,
    leading=19,
    alignment=TA_CENTER,
    textColor=_INK,
    letterSpacing=1.2,
)

ST_SOUS_TITRE = ParagraphStyle("inform-sub", fontSize=9, leading=11, alignment=TA_CENTER, textColor=_GRAY)

ST_CONTACT = ParagraphStyle("inform-contact", fontSize=7.5, leading=9.5, alignment=TA_CENTER, textColor=_GRAY)

ST_TITRE = ParagraphStyle(
    "doc-title",
    fontName="Helvetica-Bold",
    fontSize=16,
    leading=19,
    alignment=TA_CENTER,
    textColor=_INK,
    letterSpacing=3,
)

ST_TITRE_SUB = ParagraphStyle(
    "doc-title-sub",
    fontSize=10,
    leading=13,
    alignment=TA_CENTER,
    textColor=colors.HexColor("#333333"),
)

ST_LABEL = ParagraphStyle("info-label", fontSize=7.5, leading=9, textColor=_GRAY, spaceAfter=1)

ST_VALUE = ParagraphStyle(
    "info-value",
    fontName="Helvetica-Bold",
    fontSize=10.5,
    leading=13,
    textColor=_INK,
)

ST_HEAD_CELL = ParagraphStyle(
    "head-cell",
    fontName="Helvetica-Bold",
    fontSize=8.5,
    leading=10,
    textColor=colors.HexColor("#333333"),
)

ST_CELL = ParagraphStyle("cell", fontSize=10, leading=12, textColor=_INK)

ST_CELL_NUM = ParagraphStyle("cell-num", fontSize=10, leading=12, textColor=_INK, alignment=TA_RIGHT)

ST_SUMMARY_LABEL = ParagraphStyle("summary-label", fontSize=7.5, leading=9, alignment=TA_CENTER, textColor=_GRAY)

ST_SUMMARY_VALUE = ParagraphStyle(
    "summary-value",
    fontName="Helvetica-Bold",
    fontSize=12,
    leading=15,
    alignment=TA_CENTER,
    textColor=_INK,
)

ST_APPRECIATION_LABEL = ParagraphStyle(
    "appreciation-label",
    fontName="Helvetica-Bold",
    fontSize=7.5,
    leading=9,
    textColor=_GRAY,
    spaceAfter=2,
)

ST_APPRECIATION_TEXT = ParagraphStyle("appreciation-text", fontSize=9.5, leading=12, textColor=_INK)

ST_FOOTER = ParagraphStyle("footer", fontSize=9.5, leading=12, alignment=TA_RIGHT, textColor=_INK)

ST_SIGNATURE = ParagraphStyle(
    "signature",
    fontSize=8.5,
    leading=11,
    alignment=TA_CENTER,
    textColor=colors.HexColor("#333333"),
)

ST_YEAR_BOX = ParagraphStyle(
    "year-box",
    fontName="Helvetica-Bold",
    fontSize=9,
    leading=11,
    alignment=TA_CENTER,
    textColor=_INK,
)


# ─── Helpers ─────────────────────────────────────────────────────────────────

def _assainir(texte: str | None, fallback: str = "") -> str:
    if not texte:
        return fallback
    return texte.strip()


def nom_fichier_bulletin(bulletin: models.Bulletins) -> str:
    base = re.sub(r"[^A-Za-z0-9À-ÿ]+", "_", f"{bulletin.eleve.prenom} {bulletin.eleve.nom}").strip("_")
    return f"Bulletin_{base}.pdf"


def nom_fichier_classe(bulletins: list[models.Bulletins]) -> str:
    if not bulletins:
        return "Bulletins_classe.pdf"
    classe = bulletins[0].classe
    return f"Bulletins_{_assainir(classe.niveau)}_{_assainir(classe.nom)}.pdf"


def _logo_flowable(chemin_public: str | None):
    """Charge le logo depuis le disque (chemin public → chemin relatif)."""
    if not chemin_public:
        return None
    relatif = chemin_public.removeprefix("/uploads/")
    chemin_abs = os.path.normpath(os.path.join(_UPLOADS_BASE, relatif))
    if not chemin_abs.startswith(os.path.normpath(_UPLOADS_BASE)) or not os.path.isfile(chemin_abs):
        return None
    try:
        return Image(chemin_abs, width=_LOGO_MAX_W, height=_LOGO_MAX_H, hAlign="CENTER")
    except Exception:
        return None


def _date_francaise(d: date | None) -> str:
    d = d or date.today()
    mois = [
        "janvier", "février", "mars", "avril", "mai", "juin",
        "juillet", "août", "septembre", "octobre", "novembre", "décembre",
    ]
    return f"{d.day} {mois[d.month - 1]} {d.year}"


def _format2(n: float) -> str:
    return f"{n:.2f}"


# ─── Blocs ───────────────────────────────────────────────────────────────────

def _en_tete(etab: models.Etablissement | None, annee_label: str | None) -> list:
    nom = _assainir(etab.nom if etab else None, "Établissement scolaire")
    sous_titre = " — ".join(
        filter(None, [_assainir(etab.sigle if etab else None), _assainir(etab.devise if etab else None)])
    )
    contact = " · ".join(
        filter(
            None,
            [
                _assainir(etab.adresse if etab else None),
                _assainir(etab.telephone if etab else None),
                _assainir(etab.email if etab else None),
            ],
        )
    )

    logo = _logo_flowable(etab.logo if etab else None)

    # Minimum height for a stable layout even without a logo.
    cell_logo = [logo or Spacer(1, 1)]

    cell_nom_children = [_text_p(nom, ST_NOM), Spacer(1, 2)]
    if sous_titre:
        cell_nom_children.append(_text_p(sous_titre, ST_SOUS_TITRE))
    if contact:
        cell_nom_children.append(_text_p(contact, ST_CONTACT))
    cell_nom = cell_nom_children

    if annee_label:
        cell_droite = [_text_p("Année Scolaire", ST_YEAR_BOX), _text_p(annee_label, ST_YEAR_BOX)]
        table = Table(
            [[cell_logo, cell_nom, cell_droite]],
            colWidths=[_LOGO_MAX_W, None, 34 * mm],
            hAlign="LEFT",
        )
        table.setStyle(
            TableStyle(
                [
                    ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                    ("LEFTPADDING", (0, 0), (0, 0), 0),
                    ("RIGHTPADDING", (2, 0), (2, 0), 0),
                    ("BOX", (2, 0), (2, 0), 1.2, _INK),
                    ("TOPPADDING", (0, 0), (-1, -1), 5),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
                ]
            )
        )
    else:
        table = Table([[cell_logo, cell_nom]], colWidths=[_LOGO_MAX_W, None], hAlign="LEFT")
        table.setStyle(
            TableStyle(
                [
                    ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                    ("LEFTPADDING", (0, 0), (0, 0), 0),
                ]
            )
        )

    trait = Table([[""]], colWidths=[None])
    trait.setStyle(TableStyle([("LINEBELOW", (0, 0), (-1, 0), 1.6, _INK), ("BOTTOMPADDING", (0, 0), (-1, 0), 3)]))
    return [table, Spacer(1, 6), trait]


def _bandeau_titre(trimestre: models.Trimestres, classe: models.Classes) -> list:
    top = Table([[""]], colWidths=[None])
    top.setStyle(TableStyle([("LINEABOVE", (0, 0), (-1, 0), 2.2, _INK)]))
    bottom = Table([[""]], colWidths=[None])
    bottom.setStyle(TableStyle([("LINEBELOW", (0, 0), (-1, 0), 2.2, _INK)]))
    sous = _text_p(f"{_assainir(trimestre.nom)} — {_assainir(classe.niveau)} {_assainir(classe.nom)}", ST_TITRE_SUB)
    return [
        Spacer(1, 6),
        top,
        Spacer(1, 3),
        _text_p("BULLETIN DE NOTES", ST_TITRE),
        sous,
        Spacer(1, 3),
        bottom,
    ]


def _grille_infos(bulletin: models.Bulletins, effectif: int | None, bareme: int) -> Table:
    eleve = bulletin.eleve

    def cellule(label: str, valeur: str):
        return [_text_p(label, ST_LABEL), _text_p(valeur or "—", ST_VALUE)]

    rang = f"{bulletin.rang}{'er' if bulletin.rang == 1 else 'e'}" if bulletin.rang else "—"
    rang_full = f"{rang} / {effectif}" if effectif and bulletin.rang else rang
    eff = f"{effectif} élève(s)" if effectif else "—"

    # Ligne 1 : Nom & Prénom (2 cases) | Matricule | Classe
    row1 = [
        cellule("Nom & Prénom", f"{eleve.nom} {eleve.prenom}"),
        "",
        cellule("Matricule", eleve.matricule),
        cellule("Classe", f"{bulletin.classe.niveau} {bulletin.classe.nom}"),
    ]
    # Ligne 2 : Période | Effectif | Rang | Moyenne générale
    row2 = [
        cellule("Période", bulletin.trimestre.nom),
        cellule("Effectif", eff),
        cellule("Rang", rang_full),
        cellule("Moyenne générale", f"{_format2(bulletin.moyenne_generale)}/{bareme}"),
    ]

    table = Table(
        [row1, row2],
        colWidths=[46.5 * mm] * 4,
        hAlign="CENTER",
    )
    table.setStyle(
        TableStyle(
            [
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("SPAN", (0, 0), (1, 0)),
                ("GRID", (0, 0), (-1, -1), 0.5, _LINE),
                ("LEFTPADDING", (0, 0), (-1, -1), 6),
                ("RIGHTPADDING", (0, 0), (-1, -1), 6),
                ("TOPPADDING", (0, 0), (-1, -1), 4),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
            ]
        )
    )
    return table


def _tableau_notes(bulletin: models.Bulletins, bareme: int) -> Table:
    est_ef1 = bareme == 10

    entetes = [Paragraph("Matière", ST_HEAD_CELL), Paragraph("Moyenne", ST_HEAD_CELL)]
    if not est_ef1:
        entetes += [Paragraph("Coeff", ST_HEAD_CELL), Paragraph("Note × Coeff", ST_HEAD_CELL)]

    corps = []
    total_coeff = 0
    total_points = 0.0
    for d in bulletin.details:
        moyenne_str = _format2(d.moyenne) if d.moyenne is not None else "—"
        ligne = [Paragraph(d.cours_nom, ST_CELL), Paragraph(moyenne_str, ST_CELL_NUM)]
        if not est_ef1:
            coeff = d.coefficient
            total_coeff += coeff
            points = (d.moyenne or 0) * coeff
            total_points += points
            ligne += [
                Paragraph(_format2(coeff), ST_CELL_NUM),
                Paragraph(_format2(points) if d.moyenne is not None else "—", ST_CELL_NUM),
            ]
        corps.append(ligne)

    data = [entetes, *corps]
    if not est_ef1:
        st_tot = ParagraphStyle("tot", fontName="Helvetica-Bold", fontSize=10, leading=12)
        data.append(
            [
                Paragraph("Totaux", st_tot),
                "",
                Paragraph(_format2(total_coeff), ST_CELL_NUM),
                Paragraph(_format2(total_points), ST_CELL_NUM),
            ]
        )

    largeurs = [None, 20 * mm, 20 * mm, 24 * mm][0:len(entetes)]
    table = Table(data, colWidths=largeurs, hAlign="CENTER")
    style = [
        ("GRID", (0, 0), (-1, -2), 0.5, _SOFT),
        ("LINEBELOW", (0, 0), (-1, 0), 1.4, _INK),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("TOPPADDING", (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
        ("ROWBACKGROUNDS", (0, 1), (-1, -2), [colors.white, colors.HexColor("#fafafa")]),
    ]
    if not est_ef1:
        style.append(("LINEABOVE", (0, -1), (-1, -1), 1.4, _INK))
        style.append(("SPAN", (0, -1), (1, -1)))
        style.append(("BACKGROUND", (0, -1), (-1, -1), colors.HexColor("#f4f4f4")))
    table.setStyle(TableStyle(style))
    return table


def _recapitulatif(bulletin: models.Bulletins, bareme: int) -> Table:
    mention = appreciation_for_moyenne(bulletin.moyenne_generale, bareme)
    rang = f"{bulletin.rang}{'er' if bulletin.rang == 1 else 'e'}" if bulletin.rang else "—"

    def item(label: str, valeur: str):
        return [_text_p(label, ST_SUMMARY_LABEL), _text_p(valeur, ST_SUMMARY_VALUE)]

    cellules = [
        item("Moyenne générale", f"{_format2(bulletin.moyenne_generale)}/{bareme}"),
        item("Mention", mention or "—"),
        item("Rang", rang),
    ]
    table = Table([cellules], colWidths=[62 * mm] * 3, hAlign="RIGHT")
    table.setStyle(
        TableStyle(
            [
                ("BOX", (0, 0), (-1, -1), 1.4, _INK),
                ("LINEAFTER", (0, 0), (-2, -1), 0.7, _LINE),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ("TOPPADDING", (0, 0), (-1, -1), 6),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
            ]
        )
    )
    return table


def _appreciation(bulletin: models.Bulletins) -> list:
    if not bulletin.appreciation:
        return []
    bloc = Table(
        [
            [_text_p("Appréciation du conseil de classe", ST_APPRECIATION_LABEL)],
            [_text_p(bulletin.appreciation, ST_APPRECIATION_TEXT)],
        ]
    )
    bloc.setStyle(
        TableStyle(
            [
                ("BOX", (0, 0), (-1, -1), 0.7, colors.HexColor("#bbbbbb")),
                ("LEFTPADDING", (0, 0), (-1, -1), 7),
                ("RIGHTPADDING", (0, 0), (-1, -1), 7),
                ("TOPPADDING", (0, 0), (-1, -1), 5),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
            ]
        )
    )
    return [Spacer(1, 5), bloc, Spacer(1, 4)]


def _pied_de_page(etab: models.Etablissement | None, le_jour: date | None = None) -> Paragraph:
    adresse = _assainir(etab.adresse if etab else None)
    lieu = (adresse.split(",")[0].strip() if adresse else "") or _assainir(etab.nom if etab else None)
    champ = "Fait le " if not lieu else f"Fait à {lieu}, le "
    return Paragraph(f"{champ}{_date_francaise(le_jour)}", ST_FOOTER)


def _signatures() -> Table:
    roles = ["Le Chef d'Établissement", "Le Professeur principal", "Signature du Parent"]
    cellules = []
    for role in roles:
        sous = Table(
            [[_text_p(role, ST_SIGNATURE)], ["", ""]],
            colWidths=[None],
            rowHeights=[None, 55],
        )
        sous.setStyle(
            TableStyle(
                [
                    ("ALIGN", (0, 0), (-1, -1), "CENTER"),
                    ("VALIGN", (0, 1), (-1, 1), "BOTTOM"),
                    ("LINEBELOW", (0, 1), (-1, 1), 0.8, _INK),
                    ("LEFTPADDING", (0, 0), (-1, -1), 0),
                    ("RIGHTPADDING", (0, 0), (-1, -1), 0),
                ]
            )
        )
        cellules.append(sous)
    table = Table([cellules], colWidths=[62 * mm] * 3, hAlign="CENTER")
    table.setStyle(TableStyle([("VALIGN", (0, 0), (-1, -1), "BOTTOM"), ("TOPPADDING", (0, 0), (-1, -1), 10)]))
    return table


# ─── Document complet ────────────────────────────────────────────────────────

def _bulletin_histoire(
    bulletin: models.Bulletins,
    etab: models.Etablissement | None,
    effectif: int | None,
    annee_label: str | None,
) -> list:
    bareme = bareme_niveau(bulletin.classe.niveau)

    histoire = []
    histoire += _en_tete(etab, annee_label)
    histoire += _bandeau_titre(bulletin.trimestre, bulletin.classe)
    histoire += [Spacer(1, 6), _grille_infos(bulletin, effectif, bareme)]
    histoire += [Spacer(1, 6), _tableau_notes(bulletin, bareme)]
    histoire += [Spacer(1, 6), _recapitulatif(bulletin, bareme)]
    histoire += _appreciation(bulletin)
    histoire += [Spacer(1, 12), _pied_de_page(etab)]
    histoire += [Spacer(1, 18), _signatures()]
    return histoire


def _document(fichier: str, histoire: list) -> bytes:
    tampon = BytesIO()
    doc = SimpleDocTemplate(
        tampon,
        pagesize=A4,
        leftMargin=12 * mm,
        rightMargin=12 * mm,
        topMargin=10 * mm,
        bottomMargin=10 * mm,
        title=fichier,
        author="College Aureole",
    )
    doc.build(histoire)
    return tampon.getvalue()


def bulletin_pdf(
    bulletin: models.Bulletins,
    etab: models.Etablissement | None = None,
    effectif: int | None = None,
    annee_label: str | None = None,
) -> bytes:
    """PDF d'un seul bulletin (une page A4 propre, sans URL du site)."""
    return _document("Bulletin de notes", _bulletin_histoire(bulletin, etab, effectif, annee_label))


def bulletins_classe_pdf(
    bulletins: Iterable[models.Bulletins],
    etab: models.Etablissement | None = None,
    annee_label: str | None = None,
) -> bytes:
    """PDF regroupant tous les bulletins d'une classe : un bulletin par page."""
    liste = list(bulletins)
    effectif = len(liste)
    histoire: list = []
    for i, bulletin in enumerate(liste):
        if i > 0:
            histoire.append(PageBreak())
        histoire += _bulletin_histoire(bulletin, etab, effectif, annee_label)
    return _document("Bulletins de la classe", histoire)


def _text_p(text: str, style: ParagraphStyle) -> Paragraph:
    return Paragraph(text, style)