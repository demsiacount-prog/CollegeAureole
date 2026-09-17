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
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import mm
from reportlab.platypus import Image, PageBreak, Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

import models
from bareme import appreciation_for_moyenne, bareme_niveau, utilise_coefficient

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


def nom_fichier_bulletin_annuel(payload: dict) -> str:
    eleve = payload["eleve"]
    base = re.sub(r"[^A-Za-z0-9À-ÿ]+", "_", f"{eleve['prenom']} {eleve['nom']}").strip("_")
    return f"Bulletin_annuel_{base}.pdf"


def nom_fichier_annuel_classe(payloads: list[dict]) -> str:
    if not payloads:
        return "Bulletins_annuels_classe.pdf"
    classe = payloads[0]["classe"]
    return f"Bulletins_annuels_{_assainir(classe['niveau'])}_{_assainir(classe['nom'])}.pdf"


def nom_fichier_registre(payload: dict) -> str:
    cours = payload["cours"]
    classe = payload["classe"]
    return "Registre_{cours}_{niveau}_{nom}.pdf".format(
        cours=_assainir(cours["nom"]),
        niveau=_assainir(classe["niveau"]),
        nom=_assainir(classe["nom"]),
    )


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

    academie = _assainir(etab.academie if etab else None)
    cap = _assainir(etab.cap if etab else None)
    if academie or cap:
        cell_nom_children.append(
            _text_p(" · ".join(filter(None, [f"Académie : {academie}", f"CAP : {cap}"])), ST_CONTACT)
        )
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
    # Même règle partagée que le calcul des bulletins (bareme.utilise_coefficient) :
    # la 6ème (classe spéciale) a ses TRIMESTRES coefficientés (sur /10) ; on
    # affiche alors les colonnes Coeff / Note×Coeff comme pour le 2nd cycle.
    utilise_coeff = utilise_coefficient(bulletin.classe.niveau, bulletin.trimestre.type)

    entetes = [Paragraph("Matière", ST_HEAD_CELL), Paragraph("Moyenne", ST_HEAD_CELL)]
    if utilise_coeff:
        entetes += [Paragraph("Coeff", ST_HEAD_CELL), Paragraph("Note × Coeff", ST_HEAD_CELL)]

    corps = []
    total_coeff = 0
    total_points = 0.0
    for d in bulletin.details:
        moyenne_str = _format2(d.moyenne) if d.moyenne is not None else "—"
        ligne = [Paragraph(d.cours_nom, ST_CELL), Paragraph(moyenne_str, ST_CELL_NUM)]
        if utilise_coeff:
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
    if utilise_coeff:
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
    if utilise_coeff:
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


def _signatures(roles: Iterable[str] | None = None) -> Table:
    table_roles = list(roles) if roles is not None else [
        "Le Chef d'Établissement", "Le Professeur principal", "Signature du Parent"
    ]
    cellules = []
    for role in table_roles:
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


def _bulletin_annuel_histoire(payload: dict, etab: models.Etablissement | None, annee_label: str | None) -> list:
    """Mise en page officielle du bulletin annuel (3 blocs trimestriels)."""
    eleve = payload["eleve"]
    classe = payload["classe"]
    bareme = payload.get("bareme", 20)
    annee = annee_label or payload.get("annee_libelle")

    def cellule(label: str, valeur: str):
        return [_text_p(label, ST_LABEL), _text_p(valeur or "—", ST_VALUE)]

    histoire = []
    histoire += _en_tete(etab, annee)

    top = Table([[""]], colWidths=[None])
    top.setStyle(TableStyle([("LINEABOVE", (0, 0), (-1, 0), 2.2, _INK)]))
    bottom = Table([[""]], colWidths=[None])
    bottom.setStyle(TableStyle([("LINEBELOW", (0, 0), (-1, 0), 2.2, _INK)]))
    histoire += [
        Spacer(1, 6),
        top,
        Spacer(1, 3),
        _text_p("BULLETIN DE NOTES ANNUEL", ST_TITRE),
        _text_p(f"{classe['niveau']} {classe['nom']}", ST_TITRE_SUB),
        Spacer(1, 3),
        bottom,
    ]

    grille = Table(
        [
            [
                cellule("Nom & Prénom", f"{eleve['nom']} {eleve['prenom']}"),
                "",
                cellule("Matricule", eleve["matricule"]),
                cellule("Classe", f"{classe['niveau']} {classe['nom']}"),
            ],
            [
                cellule("Année scolaire", annee or "—"),
                cellule("Moyenne annuelle", f"{_format2(payload['moyenne_annuelle'])}/{bareme}" if payload.get("moyenne_annuelle") is not None else "—"),
                cellule("Rang annuel", _format2(payload["rang_annuel"]) if payload.get("rang_annuel") is not None else "—"),
                cellule("Mention", payload.get("mention_annuelle") or "—"),
            ],
        ],
        colWidths=[46.5 * mm] * 4,
        hAlign="CENTER",
    )
    grille.setStyle(
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
    histoire += [Spacer(1, 6), grille]

    for bloque in payload["trimestres"]:
        titre = _text_p(f"— {bloque['nom']} —", ST_TITRE_SUB)
        en_tetes = [
            Paragraph("Matière", ST_HEAD_CELL),
            Paragraph("Coeff", ST_HEAD_CELL),
            Paragraph("Note Classe", ST_HEAD_CELL),
            Paragraph("Note Comp.", ST_HEAD_CELL),
            Paragraph("Moyenne", ST_HEAD_CELL),
            Paragraph("Moy. Coeff.", ST_HEAD_CELL),
            Paragraph("Appréciation", ST_HEAD_CELL),
        ]
        corps = [en_tetes]
        for ligne in bloque["lignes"]:
            corps.append(
                [
                    Paragraph(ligne["cours_nom"], ST_CELL),
                    Paragraph(_format2(ligne["coefficient"]), ST_CELL_NUM),
                    Paragraph(_format2(ligne["note_classe"]) if ligne["note_classe"] is not None else "—", ST_CELL_NUM),
                    Paragraph(_format2(ligne["note_comp"]) if ligne["note_comp"] is not None else "—", ST_CELL_NUM),
                    Paragraph(_format2(ligne["moyenne"]) if ligne["moyenne"] is not None else "—", ST_CELL_NUM),
                    Paragraph(_format2(ligne["points"]) if ligne["points"] is not None else "—", ST_CELL_NUM),
                    Paragraph(ligne["appreciation"] or "—", ST_CELL),
                ]
            )
        corps.append(
            [
                Paragraph("Totaux", ParagraphStyle("tot", fontName="Helvetica-Bold", fontSize=10, leading=12)),
                Paragraph(_format2(bloque["totaux_coefficients"]), ST_CELL_NUM),
                "", "", "",
                Paragraph(_format2(bloque["totaux_points"]), ST_CELL_NUM),
                "",
            ]
        )
        table_bloc = Table(corps, colWidths=[None, 12 * mm, 17 * mm, 17 * mm, 16 * mm, 20 * mm, 32 * mm], hAlign="CENTER")
        table_bloc.setStyle(
            TableStyle(
                [
                    ("GRID", (0, 0), (-1, -2), 0.4, _SOFT),
                    ("LINEBELOW", (0, 0), (-1, 0), 1.2, _INK),
                    ("LINEABOVE", (0, -1), (-1, -1), 1.2, _INK),
                    ("SPAN", (1, -1), (5, -1)),
                    ("BACKGROUND", (0, -1), (-1, -1), colors.HexColor("#f4f4f4")),
                    ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                    ("TOPPADDING", (0, 0), (-1, -1), 3),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
                    ("ROWBACKGROUNDS", (0, 1), (-1, -2), [colors.white, colors.HexColor("#fafafa")]),
                ]
            )
        )
        recap = _text_p(
            "Moyenne : {moy}/{b} — Rang : {rang}/{eff} — Moyenne du 1er élève : {p1}/{b}".format(
                moy=_format2(bloque["moyenne_generale"]) if bloque.get("moyenne_generale") is not None else "—",
                b=bloque.get("bareme", bareme),
                rang=bloque["rang"] if bloque.get("rang") is not None else "—",
                eff=bloque.get("effectif") or "—",
                p1=_format2(bloque["moyenne_premier"]) if bloque.get("moyenne_premier") is not None else "—",
            ),
            ST_TITRE_SUB,
        )
        histoire += [Spacer(1, 8), titre, Spacer(1, 2), table_bloc, Spacer(1, 2), recap]

    decision = payload.get("decision") or "—"
    decision_bloc = Table(
        [
            [_text_p("Décision du conseil des maîtres", ST_APPRECIATION_LABEL)],
            [_text_p(decision, ST_APPRECIATION_TEXT)],
        ]
    )
    decision_bloc.setStyle(
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
    histoire += [Spacer(1, 12), decision_bloc]
    histoire += [Spacer(1, 10), _pied_de_page(etab)]
    histoire += [Spacer(1, 16), _signatures(["Le Directeur", "Signature du Parent"])]
    return histoire


def _fmt_coef(c) -> str:
    if c is None:
        return ""
    v = float(c)
    return str(int(v)) if v.is_integer() else _format2(v)


def _bulletin_officiel_histoire(
    payload: dict,
    etab: models.Etablissement | None = None,
    annee_label: str | None = None,
) -> list:
    """Mise en page officielle du bulletin de note (6è-9è) sur A4 portrait.

    Reprend la maquette doc4 : en-tête logo+coordonnées | encadré pointillé
    (moyenne / rang / décision) | identité élève, bandeau « BULLETIN DE NOTE »,
    tableau 19 colonnes (3 trimestres × 6), puis trois blocs récapitulatifs
    trimestriels avec signatures Le Parent / Le Directeur.
    """
    total_w = 190 * mm  # A4 portrait, marges 8 mm
    histoire: list = []

    st_gauche = ParagraphStyle("bd-gauche", fontSize=8, leading=10, textColor=_INK)
    st_gauche_b = ParagraphStyle("bd-gauche-b", fontName="Helvetica-Bold", fontSize=8.5, leading=10, textColor=_INK)
    st_centre = ParagraphStyle(
        "bd-centre", fontName="Helvetica-Bold", fontSize=8, leading=12, textColor=_INK, alignment=TA_CENTER
    )
    st_droite = ParagraphStyle(
        "bd-droite", fontName="Helvetica-Bold", fontSize=8, leading=12, textColor=_INK, alignment=TA_RIGHT
    )
    st_titre = ParagraphStyle(
        "bd-titre", fontName="Helvetica-Bold", fontSize=13, leading=16, textColor=_INK, alignment=TA_CENTER,
        letterSpacing=3,
    )
    st_tr = ParagraphStyle("bd-tr", fontName="Helvetica-Bold", fontSize=8, leading=9.5, textColor=_INK, alignment=TA_CENTER)
    st_tg = ParagraphStyle("bd-tg", fontName="Helvetica-Bold", fontSize=7, leading=8.5, textColor=_INK)
    st_sub = ParagraphStyle("bd-sub", fontName="Helvetica-Bold", fontSize=6.3, leading=7.5, textColor=_INK, alignment=TA_CENTER)
    st_cell = ParagraphStyle("bd-cell", fontSize=7, leading=8.5, textColor=_INK)
    st_ital = ParagraphStyle("bd-ital", fontName="Helvetica-Oblique", fontSize=7, leading=8.5, textColor=_INK)
    st_num = ParagraphStyle("bd-num", fontSize=7, leading=8.5, textColor=_INK, alignment=TA_CENTER)
    st_total = ParagraphStyle("bd-total", fontName="Helvetica-Bold", fontSize=7, leading=8.5, textColor=_INK, alignment=TA_CENTER)
    st_recap = ParagraphStyle("bd-recap", fontName="Helvetica-Bold", fontSize=7.8, leading=10.5, textColor=_INK)
    st_sig = ParagraphStyle("bd-sig", fontName="Helvetica-Bold", fontSize=7.5, leading=9, textColor=_INK, alignment=TA_CENTER)

    etab_nom = _assainir(etab.nom if etab else None) or "COLLÈGE AURÉOLE"
    academie = _assainir(etab.academie if etab else None) or "Académie d'Enseignement de Kalaban Coro"
    cap = _assainir(etab.cap if etab else None) or "Centre d'Animation Pédagogique de Kalaban Coro"
    adresse = _assainir(etab.adresse if etab else None) or "Kalaban Coro Tiebani ; Carré face à la Station Shell"
    telephone = _assainir(etab.telephone if etab else None) or "94 30 48 59 / 90 31 74 86 / 76 06 31 34 / 76 10 83 92"

    logo = _logo_flowable(etab.logo if etab else None)
    if logo is None:
        logo = Table(
            [[_text_p(_assainir(etab.sigle if etab else None) or "COLLÈGE<br/>AURÉOLE", st_gauche_b)]],
            colWidths=[22 * mm],
            rowHeights=[18 * mm],
        )
        logo.setStyle(
            TableStyle(
                [
                    ("BOX", (0, 0), (-1, -1), 1.2, _INK),
                    ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                    ("ALIGN", (0, 0), (-1, -1), "CENTER"),
                    ("LEFTPADDING", (0, 0), (-1, -1), 2),
                    ("RIGHTPADDING", (0, 0), (-1, -1), 2),
                ]
            )
        )

    info_gauche = Table(
        [
            [_text_p(academie, st_gauche)],
            [_text_p(cap, st_gauche)],
            [_text_p(etab_nom, st_gauche_b)],
            [_text_p(adresse, st_gauche)],
            [_text_p(f"Tél : {telephone}", st_gauche)],
        ],
        colWidths=[52 * mm],
    )
    info_gauche.setStyle(TableStyle([("TOPPADDING", (0, 0), (-1, -1), 1), ("BOTTOMPADDING", (0, 0), (-1, -1), 1)]))
    gauche = Table([[logo, info_gauche]], colWidths=[24 * mm, 52 * mm])
    gauche.setStyle(
        TableStyle(
            [
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ("LEFTPADDING", (0, 0), (-1, -1), 0),
                ("RIGHTPADDING", (0, 0), (-1, -1), 4),
            ]
        )
    )

    moy_ann = _format2(payload["moyenne_annuelle"]) if payload.get("moyenne_annuelle") is not None else "____"
    rang_ann = str(payload.get("rang_annuel")) if payload.get("rang_annuel") is not None else "____"
    decision = payload.get("decision") or "______________________"
    centre = Table(
        [
            [_text_p(f"Moyenne annuelle : <u>{moy_ann}</u>", st_centre)],
            [_text_p(f"Rang annuel : <u>{rang_ann}</u>", st_centre)],
            [_text_p(f"Décision du conseil des maîtres :<br/><u>{decision}</u>", st_centre)],
        ],
        colWidths=[0.32 * total_w],
    )
    centre.setStyle(
        TableStyle(
            [
                ("BOX", (0, 0), (-1, -1), 0.8, _LINE, 0, (2, 2)),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ("ALIGN", (0, 0), (-1, -1), "CENTER"),
                ("TOPPADDING", (0, 0), (-1, -1), 4),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
                ("LEFTPADDING", (0, 0), (-1, -1), 3),
                ("RIGHTPADDING", (0, 0), (-1, -1), 3),
            ]
        )
    )

    classe_lib = " ".join(filter(None, [payload["classe"].get("niveau"), payload["classe"].get("nom")]))
    droite = Table(
        [
            [_text_p(f"Année scolaire : <u>{_assainir(annee_label)}</u>", st_droite)],
            [_text_p(f"Prénom : <u>{_assainir(payload['eleve'].get('prenom'))}</u>", st_droite)],
            [_text_p(f"Nom : <u>{_assainir(payload['eleve'].get('nom'))}</u>", st_droite)],
            [_text_p(f"Classe : <u>{_assainir(classe_lib)}</u>", st_droite)],
        ],
        colWidths=[0.28 * total_w],
    )
    droite.setStyle(
        TableStyle(
            [
                ("TOPPADDING", (0, 0), (-1, -1), 1),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
            ]
        )
    )

    entete = Table([[gauche, centre, droite]], colWidths=[0.40 * total_w, 0.32 * total_w, 0.28 * total_w])
    entete.setStyle(
        TableStyle(
            [
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("LEFTPADDING", (0, 0), (-1, -1), 2),
                ("RIGHTPADDING", (0, 0), (-1, -1), 2),
            ]
        )
    )
    histoire += [entete, Spacer(1, 5)]

    titre = Table([[_text_p("BULLETIN DE NOTE", st_titre)]], colWidths=[0.75 * total_w], hAlign="CENTER")
    titre.setStyle(
        TableStyle(
            [
                ("BOX", (0, 0), (-1, -1), 1.5, _INK),
                ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#f0f0f0")),
                ("TOPPADDING", (0, 0), (-1, -1), 4),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
            ]
        )
    )
    histoire += [titre, Spacer(1, 5)]

    trim_noms = [b.get("nom") for b in payload.get("trimestres", [])]
    if not trim_noms:
        trim_noms = ["1er Trimestre", "2e Trimestre", "3e Trimestre"]
    nblocs = min(max(len(payload.get("trimestres", [])) or 3, 1), 3)
    trim_noms = (trim_noms + ["", "", ""])[:3]

    entetes_sub = ["Coéf.", "Note Classe", "Note Comp.", "Moy.", "Moy. Coéf.", "Appréc. du Maître"]

    r0 = [Paragraph("Matières", st_tr)]
    for k in range(nblocs):
        r0.append(Paragraph(trim_noms[k], st_tr))
        r0 += [""] * 5
    r1 = [""]
    for _ in range(nblocs):
        r1 += [Paragraph(h, st_sub) for h in entetes_sub]

    data = [r0, r1]

    lignes_ref = payload["trimestres"][0]["lignes"] if payload.get("trimestres") else []
    italic_names = {"Informatique"}
    for i in range(len(lignes_ref)):
        prem = lignes_ref[i]
        nom = prem.get("cours_nom") or ""
        ligne = [Paragraph(nom, st_ital if nom in italic_names else st_tg)]
        for b in payload.get("trimestres", []):
            l = b["lignes"][i] if i < len(b["lignes"]) else {}
            ligne += [
                Paragraph(_fmt_coef(l.get("coefficient")), st_num),
                Paragraph(_format2(l["note_classe"]) if l.get("note_classe") is not None else "", st_num),
                Paragraph(_format2(l["note_comp"]) if l.get("note_comp") is not None else "", st_num),
                Paragraph(_format2(l["moyenne"]) if l.get("moyenne") is not None else "", st_num),
                Paragraph(_format2(l["points"]) if l.get("points") is not None else "", st_num),
                Paragraph(_assainir(l.get("appreciation")) or "", st_cell),
            ]
        data.append(ligne)

    total_row = [Paragraph("Totaux", st_total)]
    for b in payload.get("trimestres", []):
        total_row += [
            Paragraph(_format2(b.get("totaux_coefficients", 0.0)), st_total),
            "", "", "", "",
            Paragraph(_format2(b.get("totaux_points", 0.0)), st_total),
            "",
        ]
    data.append(total_row)

    per = [30 * mm, 7 * mm, 8 * mm, 8 * mm, 8 * mm, 9 * mm, 12 * mm]
    col_widths = [30 * mm] + per[1:] * nblocs
    spans = [("SPAN", (0, 0), (0, 1))]
    for k in range(nblocs):
        spans.append(("SPAN", (1 + 6 * k, 0), (6 + 6 * k, 0)))
    table = Table(data, colWidths=col_widths, hAlign="CENTER")
    table.setStyle(
        TableStyle(
            [
                *spans,
                ("GRID", (0, 0), (-1, -1), 0.5, _SOFT),
                ("BOX", (0, 0), (-1, -1), 0.9, _INK),
                ("LINEBELOW", (0, 0), (-1, 1), 1.0, _INK),
                ("BACKGROUND", (0, 0), (-1, 1), colors.HexColor("#f5f5f5")),
                ("BACKGROUND", (0, -1), (-1, -1), colors.HexColor("#f0f0f0")),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ("TOPPADDING", (0, 0), (-1, -1), 1.5),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 1.5),
                ("LEFTPADDING", (0, 0), (-1, -1), 2),
                ("RIGHTPADDING", (0, 0), (-1, -1), 2),
                ("ROWBACKGROUNDS", (0, 2), (-1, -2), [colors.white, colors.HexColor("#fafafa")]),
            ]
        )
    )
    histoire += [table, Spacer(1, 8)]

    blocs = list(payload.get("trimestres", []))
    blocs = (blocs + [None, None, None])[:3]

    def _bloc_recap(b: dict | None) -> Table:
        bareme_bloc = (b or {}).get("bareme", payload.get("bareme", 20))
        if b is None:
            lignes = [
                ("Total : ", "_______________"),
                ("Rang : ", "__ / __"),
                (f"Moyenne : ", f"____ / {bareme_bloc}"),
                ("Moyenne du 1er : ", f"____ / {bareme_bloc}"),
            ]
        else:
            total_points = _format2(b["totaux_points"]) if b.get("totaux_points") is not None else "___"
            rang = str(b["rang"]) if b.get("rang") is not None else "__"
            effectif = str(b.get("effectif")) if b.get("effectif") is not None else "__"
            moy = _format2(b["moyenne_generale"]) if b.get("moyenne_generale") is not None else "___"
            premier = _format2(b["moyenne_premier"]) if b.get("moyenne_premier") is not None else "___"
            lignes = [
                ("Total : ", total_points),
                ("Rang : ", f"{rang} / {effectif}"),
                (f"Moyenne : ", f"{moy} / {bareme_bloc}"),
                ("Moyenne du 1er : ", f"{premier} / {bareme_bloc}"),
            ]
        data = [[Paragraph(f"{label}&nbsp;&nbsp;{valeur}", st_recap), ""] for label, valeur in lignes]
        data += [
            [Paragraph("Appréciation du Directeur :", st_recap), ""],
            [Spacer(1, 26), ""],
            [Paragraph("Le Parent", st_sig), Paragraph("Le Directeur", st_sig)],
        ]
        largeur = 0.31 * total_w
        tbl = Table(data, colWidths=[largeur / 2, largeur / 2])
        tbl.setStyle(
            TableStyle(
                [
                    *[("SPAN", (0, r), (1, r)) for r in range(len(data) - 1)],
                    ("BOX", (0, 0), (-1, -1), 1.1, _INK),
                    ("LINEABOVE", (0, len(data) - 1), (-1, len(data) - 1), 0.6, _SOFT),
                    ("LEFTPADDING", (0, 0), (-1, -1), 5),
                    ("RIGHTPADDING", (0, 0), (-1, -1), 5),
                    ("TOPPADDING", (0, 0), (-1, -1), 2),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 2),
                ]
            )
        )
        return tbl

    recap_row = Table([[*(_bloc_recap(b) for b in blocs)]], colWidths=[0.31 * total_w] * 3, hAlign="CENTER")
    recap_row.setStyle(
        TableStyle(
            [
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("LEFTPADDING", (0, 0), (-1, -1), 3),
                ("RIGHTPADDING", (0, 0), (-1, -1), 3),
            ]
        )
    )
    histoire += [recap_row]
    return histoire


def bulletin_annuel_pdf(
    payload: dict,
    etab: models.Etablissement | None = None,
    annee_label: str | None = None,
) -> bytes:
    """PDF du bulletin annuel (3 blocs trimestriels) d'un élève."""
    if payload.get("officiel"):
        return _document(
            "Bulletin de note",
            _bulletin_officiel_histoire(payload, etab, annee_label),
            marge_gauche=8 * mm,
            marge_droite=8 * mm,
            marge_haut=7 * mm,
            marge_bas=7 * mm,
        )
    return _document("Bulletin annuel", _bulletin_annuel_histoire(payload, etab, annee_label))


def bulletins_annuels_classe_pdf(
    payloads: list[dict],
    etab: models.Etablissement | None = None,
    annee_label: str | None = None,
) -> bytes:
    """PDF regroupant les bulletins annuels d'une classe : un par page."""
    officiel = bool(payloads and payloads[0].get("officiel"))
    histoire: list = []
    for i, payload in enumerate(payloads):
        if i > 0:
            histoire.append(PageBreak())
        if officiel:
            histoire += _bulletin_officiel_histoire(payload, etab, annee_label)
        else:
            histoire += _bulletin_annuel_histoire(payload, etab, annee_label)
    titre = "Bulletins de note" if officiel else "Bulletins annuels de la classe"
    if officiel:
        return _document(
            titre,
            histoire,
            marge_gauche=8 * mm,
            marge_droite=8 * mm,
            marge_haut=7 * mm,
            marge_bas=7 * mm,
        )
    return _document(titre, histoire)


def registre_pdf(payload: dict, etab: models.Etablissement | None = None) -> bytes:
    """PDF du registre de notes d'une matière (doc3 : une seule fiche en paysage)."""
    return _document("Fiche de notes", _registre_histoire(payload, etab), paysage=True)


def _registre_histoire(payload: dict, etab: models.Etablissement | None) -> list:
    """Mise en page doc3 : en-tête succinct, titre, matière/classe, tableau
    unique avec, pour chaque période : Notes Class / Note Comp / Moy / 20 /
    Note Coef."""
    cours = payload["cours"]
    classe = payload["classe"]
    bareme = payload.get("bareme", 20)
    periodes = payload["trimestres"]

    st_meta = ParagraphStyle(
        "reg-meta",
        fontName="Helvetica-Bold",
        fontSize=9,
        leading=12,
        textColor=_INK,
    )
    st_titre = ParagraphStyle(
        "reg-titre",
        fontName="Helvetica-Bold",
        fontSize=15,
        leading=18,
        alignment=TA_CENTER,
        textColor=_INK,
    )
    st_matiere = ParagraphStyle(
        "reg-matiere",
        fontName="Helvetica-Bold",
        fontSize=10.5,
        leading=13,
        textColor=_INK,
    )

    def _transcrire(n: float | None) -> Paragraph:
        return Paragraph(_format2(n) if n is not None else "", ST_CELL_NUM)

    histoire = [Spacer(1, 4)]
    histoire.append(
        _text_p(
            "Année scolaire : {annee}<br/>AE : {ae}<br/>CAP : {cap}<br/>École : {ecole}".format(
                annee=_assainir(payload.get("annee_libelle")) or "_______________",
                ae=_assainir(etab.academie if etab else None) or "_______________",
                cap=_assainir(etab.cap if etab else None) or "_______________",
                ecole=_assainir(etab.nom if etab else None) or "_______________",
            ),
            st_meta,
        )
    )
    histoire += [Spacer(1, 12), _text_p("Fiche de notes", st_titre), Spacer(1, 10)]
    histoire.append(
        _text_p(
            "Matière : {matiere}   —   Classe : {classe}".format(
                matiere=_assainir(cours.get("nom")) or "__________",
                classe=" ".join(filter(None, [_assainir(classe.get("niveau")), _assainir(classe.get("nom"))]))
                or "__________",
            ),
            st_matiere,
        )
    )
    histoire.append(Spacer(1, 10))

    tete1 = [Paragraph("N°", ST_HEAD_CELL), Paragraph("Prénoms et Nom", ST_HEAD_CELL)]
    tete2 = ["", ""]
    for periode in periodes:
        tete1 += [Paragraph(_assainir(periode["nom"]) or "—", ST_HEAD_CELL), "", "", ""]
        tete2 += [Paragraph(h, ST_HEAD_CELL) for h in ("Notes Class", "Note Comp", "Moy / 20", "Note Coef")]

    corps = []
    for index, eleve in enumerate(payload["eleves"], start=1):
        ligne = [
            Paragraph(str(index), ST_CELL_NUM),
            Paragraph(" ".join(filter(None, [_assainir(eleve.get("prenom")), _assainir(eleve.get("nom"))])), ST_CELL),
        ]
        for periode in periodes:
            donnees = next((l for l in eleve["lignes"] if l["id_trimestre"] == periode["id"]), None)
            note_classe = donnees.get("note_classe") if donnees else None
            note_comp = donnees.get("note_comp") if donnees else None
            moyenne = donnees.get("moyenne") if donnees else None
            points = donnees.get("points") if donnees else None
            moy20 = moyenne * (20.0 / bareme) if moyenne is not None else None
            ligne += [
                _transcrire(note_classe),
                _transcrire(note_comp),
                _transcrire(moy20),
                _transcrire(points),
            ]
        corps.append(ligne)

    nb_periodes = len(periodes)
    largeurs = [14 * mm, 64 * mm]
    largeur_sous = (273 * mm - sum(largeurs)) / (4 * nb_periodes)
    largeurs += [largeur_sous] * (4 * nb_periodes)

    spans = [("SPAN", (0, 0), (0, 1)), ("SPAN", (1, 0), (1, 1))]
    for i in range(nb_periodes):
        spans.append(("SPAN", (2 + 4 * i, 0), (5 + 4 * i, 0)))

    table = Table([tete1, tete2, *corps], colWidths=largeurs, hAlign="LEFT", repeatRows=2)
    table.setStyle(
        TableStyle(
            [
                *spans,
                ("GRID", (0, 0), (-1, -1), 0.4, _INK),
                ("LINEBELOW", (0, 0), (-1, 1), 1.2, _INK),
                ("BACKGROUND", (0, 0), (1, 1), colors.HexColor("#f2f2f2")),
                ("BACKGROUND", (2, 0), (-1, 1), colors.HexColor("#f2f2f2")),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ("TOPPADDING", (0, 0), (-1, -1), 3),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
                ("LEFTPADDING", (0, 0), (-1, -1), 3),
                ("RIGHTPADDING", (0, 0), (-1, -1), 3),
            ]
        )
    )

    histoire.append(table)
    return histoire


def _document(
    fichier: str,
    histoire: list,
    *,
    paysage: bool = False,
    marge_gauche: float = 12 * mm,
    marge_droite: float = 12 * mm,
    marge_haut: float = 10 * mm,
    marge_bas: float = 10 * mm,
) -> bytes:
    tampon = BytesIO()
    doc = SimpleDocTemplate(
        tampon,
        pagesize=landscape(A4) if paysage else A4,
        leftMargin=marge_gauche,
        rightMargin=marge_droite,
        topMargin=marge_haut,
        bottomMargin=marge_bas,
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