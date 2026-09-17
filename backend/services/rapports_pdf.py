"""Génération PDF des rapports et documents (carnet scolaire,
fiche de suivi/transfert, rapport des moyennes annuelles, proposition de passage).

Réutilise les blocs et styles de services/pdf.py (en-tête officiel, bandeau,
pied de page, signatures) pour une maquette cohérente sur A4.
"""

from __future__ import annotations

from io import BytesIO

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT, TA_JUSTIFY
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import mm
from reportlab.platypus import BaseDocTemplate, Frame, HRFlowable, PageBreak, PageTemplate, Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

import models
from bareme import appreciation_for_moyenne, niveau_ordre
from services.pdf import (
    _assainir,
    _date_francaise,
    _document,
    _en_tete,
    _format2,
    _logo_flowable,
    _pied_de_page,
    _signatures,
    _text_p,
    ST_APPRECIATION_LABEL,
    ST_APPRECIATION_TEXT,
    ST_CELL,
    ST_CELL_NUM,
    ST_HEAD_CELL,
    ST_LABEL,
    ST_SUMMARY_LABEL,
    ST_SUMMARY_VALUE,
    ST_TITRE,
    ST_TITRE_SUB,
    ST_VALUE,
)

_INK = colors.HexColor("#111111")
_LINE = colors.HexColor("#999999")
_SOFT = colors.HexColor("#dddddd")


def _sec_titre() -> ParagraphStyle:
    return ParagraphStyle(
        "sec-titre",
        fontName="Helvetica-Bold",
        fontSize=11,
        leading=14,
        textColor=_INK,
        spaceBefore=4,
        spaceAfter=4,
    )


def _bandeau_doc(titre: str, sous_titre: str | None = None) -> list:
    top = Table([[""]], colWidths=[None])
    top.setStyle(TableStyle([("LINEABOVE", (0, 0), (-1, 0), 2.2, _INK)]))
    bottom = Table([[""]], colWidths=[None])
    bottom.setStyle(TableStyle([("LINEBELOW", (0, 0), (-1, 0), 2.2, _INK)]))
    bloc = [Spacer(1, 6), top, Spacer(1, 3), _text_p(titre, ST_TITRE)]
    if sous_titre:
        bloc.append(_text_p(sous_titre, ST_TITRE_SUB))
    if not sous_titre:
        bloc.append(Spacer(1, 11))
    bloc += [Spacer(1, 3), bottom]
    return bloc


def _cellule(label: str, valeur: str | None):
    return [_text_p(label, ST_LABEL), _text_p(valeur or "—", ST_VALUE)]


def _grille_doc(lignes: list) -> Table:
    n_cols = max(len(l) for l in lignes)
    width = 186.0 / n_cols
    data = []
    spans = []
    for r, ligne in enumerate(lignes):
        row = []
        for i, item in enumerate(ligne):
            if item is None:
                row.append("")
                j = i - 1
                while j >= 0 and ligne[j] is None:
                    j -= 1
                spans.append(("SPAN", (max(j, 0), r), (i, r)))
            else:
                row.append(_cellule(item[0], item[1]))
        data.append(row)
    table = Table(data, colWidths=[width * mm] * n_cols, hAlign="CENTER")
    table.setStyle(
        TableStyle(
            [
                ("GRID", (0, 0), (-1, -1), 0.5, _LINE),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("LEFTPADDING", (0, 0), (-1, -1), 6),
                ("RIGHTPADDING", (0, 0), (-1, -1), 6),
                ("TOPPADDING", (0, 0), (-1, -1), 4),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
                *spans,
            ]
        )
    )
    return table


def _tableau_plein(entetes: list, rows: list, largeurs: list) -> Table:
    table = Table([entetes, *rows], colWidths=largeurs, hAlign="CENTER")
    table.setStyle(
        TableStyle(
            [
                ("GRID", (0, 0), (-1, -2), 0.5, _SOFT),
                ("LINEBELOW", (0, 0), (-1, 0), 1.4, _INK),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ("TOPPADDING", (0, 0), (-1, -1), 4),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
                ("ROWBACKGROUNDS", (0, 1), (-1, -2), [colors.white, colors.HexColor("#fafafa")]),
            ]
        )
    )
    return table


def _recap_3(cells: list) -> Table:
    row = [[_text_p(label, ST_SUMMARY_LABEL), _text_p(valeur, ST_SUMMARY_VALUE)] for label, valeur, _ in cells]
    table = Table([row], colWidths=[l*mm for _, _, l in cells], hAlign="RIGHT")
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


def _bloc_appreciation(label: str, texte: str) -> list:
    bloc = Table(
        [
            [_text_p(label, ST_APPRECIATION_LABEL)],
            [_text_p(texte, ST_APPRECIATION_TEXT)],
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


def _signatures_roles(roles: list) -> Table:
    cellules = []
    for role in roles:
        sous = Table(
            [[_text_p(role, ST_VALUE)], ["", ""]],
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
    table = Table([cellules], colWidths=[186.0 / len(roles) * mm] * len(roles), hAlign="CENTER")
    table.setStyle(TableStyle([("VALIGN", (0, 0), (-1, -1), "BOTTOM"), ("TOPPADDING", (0, 0), (-1, -1), 10)]))
    return table


# ─── Carnet scolaire (livret officiel mixte, modèle doc8) ─────────────────────
# 6 pages : couverture A5 rose + état civil A5, scolarité 1er/2ème cycle A4
# paysage, parties médicales A4 paysage, changements d'établissements A4
# paysage, résultats des visites médicales A5. Conforme à la maquette
# officielle « carnet scolaire.html » (Times, couverture rose #f8c8d8).

_CARNET_ROSE = colors.HexColor("#f8c8d8")
_CARNET_BORDURE = colors.HexColor("#8b3a62")

_ST_CARNET_TITRE = ParagraphStyle(
    "carnet-titre",
    fontName="Times-Bold",
    fontSize=19,
    leading=23,
    alignment=TA_CENTER,
    textColor=_INK,
)
_ST_CARNET_TITRE_PAGE = ParagraphStyle(
    "carnet-titre-page",
    fontName="Times-Bold",
    fontSize=13,
    leading=16,
    alignment=TA_CENTER,
    textColor=_INK,
)
_ST_CARNET_CHAMP = ParagraphStyle(
    "carnet-champ",
    fontName="Times-Roman",
    fontSize=9,
    leading=12,
    textColor=_INK,
)
_ST_CARNET_CHAMP_GRAS = ParagraphStyle(
    "carnet-champ-gras",
    fontName="Times-Bold",
    fontSize=9,
    leading=12,
    textColor=_INK,
)
_ST_CARNET_INFOS = ParagraphStyle(
    "carnet-infos",
    fontName="Times-Roman",
    fontSize=8.5,
    leading=12,
    textColor=_INK,
)
_ST_CARNET_INFOS_C = ParagraphStyle(
    "carnet-infos-c",
    fontName="Times-Roman",
    fontSize=8.5,
    leading=12,
    alignment=TA_CENTER,
    textColor=_INK,
)
_ST_CARNET_SLOGAN = ParagraphStyle(
    "carnet-slogan",
    fontName="Times-BoldItalic",
    fontSize=11,
    leading=14,
    alignment=TA_CENTER,
    textColor=_INK,
)
_ST_CARNET_NB = ParagraphStyle(
    "carnet-nb",
    fontName="Times-Italic",
    fontSize=8,
    leading=11,
    alignment=TA_JUSTIFY,
    textColor=_INK,
)
_ST_CARNET_ENT_TBL = ParagraphStyle(
    "carnet-top-tbl",
    fontName="Times-Bold",
    fontSize=8,
    leading=10,
    alignment=TA_CENTER,
    textColor=_INK,
)
_ST_CARNET_CELL = ParagraphStyle(
    "carnet-cell",
    fontName="Times-Roman",
    fontSize=8,
    leading=10,
    alignment=TA_CENTER,
    textColor=_INK,
)
_ST_CARNET_TXT_L = ParagraphStyle(
    "carnet-txt-l",
    fontName="Times-Roman",
    fontSize=8,
    leading=10,
    alignment=TA_LEFT,
    textColor=_INK,
)
_ST_CARNET_TXT_LB = ParagraphStyle(
    "carnet-txt-lb",
    fontName="Times-Bold",
    fontSize=8,
    leading=10,
    alignment=TA_LEFT,
    textColor=_INK,
)


def _carnet_entete(largeur: float, etab) -> Table:
    """En-tête de couverture : logo + nom de l'école (gauche), République du Mali (droite)."""
    nom = _assainir(etab.nom) if etab and etab.nom else "COLLÈGE AUREOLE"
    logo = _logo_flowable(etab.logo) if etab else None
    cellule = Table(
        [[logo or Spacer(1, 1), Paragraph(nom, _ST_CARNET_CHAMP_GRAS)]],
        colWidths=[18 * mm, None],
        hAlign="LEFT",
    )
    cellule.setStyle(
        TableStyle(
            [
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ("LEFTPADDING", (0, 0), (0, 0), 0),
                ("RIGHTPADDING", (0, 0), (-1, -1), 4),
            ]
        )
    )
    droite = [
        Paragraph("République du Mali", _ST_CARNET_INFOS),
        Paragraph("Un Peuple - Un But - Une Foi", _ST_CARNET_INFOS),
    ]
    tab = Table([[cellule, droite]], colWidths=[largeur * 0.62, largeur * 0.38], hAlign="LEFT")
    tab.setStyle(
        TableStyle(
            [
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("LEFTPADDING", (0, 0), (-1, -1), 0),
                ("RIGHTPADDING", (0, 0), (-1, -1), 0),
            ]
        )
    )
    return tab


def _carnet_champs(labels: list, valeurs: list, largeur_label: float = 40, largeur_valeur: float = 86) -> Table:
    rows = [
        [
            Paragraph(label, _ST_CARNET_CHAMP_GRAS),
            Paragraph(_assainir(v) if v else "", _ST_CARNET_CHAMP),
        ]
        for label, v in zip(labels, valeurs)
    ]
    tab = Table(rows, colWidths=[largeur_label * mm, largeur_valeur * mm], hAlign="LEFT")
    tab.setStyle(
        TableStyle(
            [
                ("LINEBELOW", (1, 0), (1, -1), 0.6, _INK),
                ("LEFTPADDING", (0, 0), (-1, -1), 0),
                ("RIGHTPADDING", (0, 0), (-1, -1), 3),
                ("TOPPADDING", (0, 0), (-1, -1), 3.2),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 3.2),
                ("VALIGN", (0, 0), (-1, -1), "BOTTOM"),
            ]
        )
    )
    return tab


def _carnet_ec_ligne(champs: list[tuple[str, str | None, float, float]]) -> Table:
    """Ligne d'état civil : 1 ou 2 champs (label gras + valeur soulignée)."""
    data, widths = [], []
    for label, valeur, wl, wv in champs:
        data.append(Paragraph(label, _ST_CARNET_CHAMP_GRAS))
        data.append(Paragraph(_assainir(valeur) if valeur else "", _ST_CARNET_CHAMP))
        widths.extend([wl * mm, wv * mm])
    tab = Table([data], colWidths=widths, hAlign="LEFT")
    style = [("LINEBELOW", (c, 0), (c, 0), 0.6, _INK) for c in range(1, len(data), 2)]
    style += [
        ("VALIGN", (0, 0), (-1, -1), "BOTTOM"),
        ("TOPPADDING", (0, 0), (-1, -1), 3.2),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 3.2),
        ("LEFTPADDING", (0, 0), (-1, -1), 0),
        ("RIGHTPADDING", (0, 0), (-1, -1), 3),
    ]
    tab.setStyle(TableStyle(style))
    return tab


def _carnet_tableau(entetes: list, lignes: list, largeurs: list, hauteurs: list | None = None) -> Table:
    donnees = [
        [Paragraph(h, _ST_CARNET_ENT_TBL) for h in entetes],
        *lignes,
    ]
    if hauteurs is not None and len(hauteurs) == len(lignes):
        hauteurs = [None, *hauteurs]
    table = Table(donnees, colWidths=largeurs, rowHeights=hauteurs, hAlign="LEFT")
    table.setStyle(
        TableStyle(
            [
                ("GRID", (0, 0), (-1, -1), 0.5, _INK),
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#f2f2f2")),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ("ALIGN", (0, 1), (-1, -1), "CENTER"),
                ("LEFTPADDING", (0, 0), (-1, -1), 5),
                ("RIGHTPADDING", (0, 0), (-1, -1), 5),
                ("TOPPADDING", (0, 0), (-1, -1), 5),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
            ]
        )
    )
    return table


def _carnet_fond_rose(canvas, doc):
    canvas.saveState()
    w, h = doc.pagesize
    canvas.setFillColor(_CARNET_ROSE)
    canvas.rect(0, 0, w, h, stroke=0, fill=1)
    canvas.setStrokeColor(_CARNET_BORDURE)
    canvas.setLineWidth(1)
    canvas.rect(1.5, 1.5, w - 3, h - 3, stroke=1, fill=0)
    canvas.restoreState()


def _carnet_page_vierge(canvas, doc):
    pass


def carnet_pdf(carnet, etab: models.Etablissement | None, annee_label: str | None) -> bytes:
    from reportlab.lib.pagesizes import A4, A5, landscape, portrait

    W5, H5 = portrait(A5)
    W4, H4 = landscape(A4)
    marge = 10 * mm
    largeur5 = W5 - 2 * marge
    demi = (W4 - 2 * marge) / 2

    tel = _assainir(etab.telephone) if etab and etab.telephone else "(+223) 79 61 88 86 / 96 51 93 63"
    email = _assainir(etab.email) if etab and etab.email else "collegeaureole@gmail.com"
    district = " · ".join(
        filter(None, [_assainir(etab.commune if etab else None), _assainir(etab.adresse if etab else None)])
    )
    pere = f"{_assainir(carnet.prenom_pere)} {_assainir(carnet.nom_pere)}".strip()
    mere = f"{_assainir(carnet.prenom_mere)} {_assainir(carnet.nom_mere)}".strip()
    date_recrut = _date_francaise(carnet.date_inscription) if carnet.date_inscription else None
    date_acte = _date_francaise(carnet.date_acte) if carnet.date_acte else None

    # ── Page 1 : couverture rose (A5) ───────────────────────────────────────────
    nb = Table(
        [
            [
                Paragraph(
                    "<b>NB:</b> 1. Ce carnet ne sera en aucun cas remis à l'Elève ni à ses parents. "
                    "En cas de changement d'établissement, il sera transmis, sur demande, au Directeur "
                    "de l'Ecole qui reçoit l'élève.<br/>2. Ce carnet ne doit comporter aucune surcharge ni rature.",
                    _ST_CARNET_NB,
                )
            ]
        ],
        colWidths=[largeur5],
    )
    nb.setStyle(TableStyle([("LINEABOVE", (0, 0), (-1, -1), 0.6, _INK), ("TOPPADDING", (0, 0), (-1, -1), 6)]))

    cov = [
        _carnet_entete(largeur5, etab),
        Spacer(1, 4),
        Paragraph(
            f"Cell: {tel}<br/>Siteweb: www.collegeaureole.org | Email: {email}",
            _ST_CARNET_INFOS_C,
        ),
        Spacer(1, 8),
        Table(
            [[Paragraph("CARNET SCOLAIRE", _ST_CARNET_TITRE)]],
            colWidths=[largeur5],
            hAlign="CENTER",
        ),
        Spacer(1, 12),
        _carnet_champs(
            [
                "De l'Elève: Prénom :",
                "Nom :",
                "De l'école :",
                "District de :",
                "Date de Recrutement :",
                "Numéro Matricule :",
            ],
            [
                carnet.prenom,
                carnet.nom,
                etab.nom if etab else None,
                district or None,
                date_recrut,
                carnet.matricule,
            ],
            largeur_label=44,
            largeur_valeur=82,
        ),
        Spacer(1, 14),
        nb,
        Spacer(1, 14),
        Paragraph("L'EXCELLENT N'A PAS DE CONCURRANT", _ST_CARNET_SLOGAN),
    ]

    # ── Page 2 : état civil (A5) ────────────────────────────────────────────────
    ec = [
        Spacer(1, 4),
        Paragraph("ETAT CIVIL", _ST_CARNET_TITRE_PAGE),
        Spacer(1, 12),
        _carnet_ec_ligne([("Prénoms :", carnet.prenom, 30, 94)]),
        _carnet_ec_ligne([("Nom de famille :", carnet.nom, 32, 92)]),
        _carnet_ec_ligne(
            [
                ("Acte de naissance N° :", carnet.numero_acte, 38, 22),
                ("Ou jugement Suppletif N° :", carnet.jugement_suppletif, 40, 22),
            ]
        ),
        _carnet_ec_ligne(
            [
                ("du :", date_acte, 10, 44),
                ("Délivré par :", carnet.delivre_par, 24, 36),
            ]
        ),
        _carnet_ec_ligne([("Fils de :", pere or None, 22, 100)]),
        _carnet_ec_ligne(
            [
                ("Profession :", carnet.fonction_pere, 22, 36),
                ("Et de :", mere or None, 14, 52),
            ]
        ),
        _carnet_ec_ligne([("Demeurant à :", carnet.adresse, 26, 96)]),
        _carnet_ec_ligne(
            [
                ("Tuteur: Prénoms :", carnet.tuteur_prenom, 32, 24),
                ("Noms :", carnet.tuteur_nom, 16, 52),
            ]
        ),
        _carnet_ec_ligne([("Lien de parenté :", carnet.tuteur_lien_parente, 30, 92)]),
        _carnet_ec_ligne([("Adresse complète des parents ou tuteur :", carnet.tuteur_adresse, 62, 58)]),
        _carnet_ec_ligne([("", None, 16, 100)]),
    ]

    # ── Page 3 : scolarité 1er & 2ème cycles (A4 paysage) ─────────────────────
    scol_gauche = [
        Spacer(1, 4),
        Paragraph("SCOLARITE", _ST_CARNET_TITRE_PAGE),
        Paragraph("1er Cycle fondamental", _ST_CARNET_INFOS_C),
        Spacer(1, 8),
        Paragraph(
            f"Date de recrutement: {date_recrut or '....................'}  "
            f"N° Mlle: {_assainir(carnet.matricule) or '....................'}",
            _ST_CARNET_CHAMP,
        ),
        Spacer(1, 6),
        _carnet_tableau(
            ["ANNEES", "ECOLES", "OBSERVATIONS"],
            [[Paragraph("1ère année<br/>à........", _ST_CARNET_CELL), "", ""] for _ in range(5)],
            [38 * mm, 42 * mm, 46 * mm],
            hauteurs=[10.5 * mm] * 5,
        ),
        Spacer(1, 10),
        Paragraph("CERTIFICAT DE FIN D'ETUDE PRIMAIRE CYCLE :", _ST_CARNET_CHAMP_GRAS),
        Spacer(1, 2),
        _carnet_champs(["Session du :", "Résultat :", "Orientation :"], [None, None, None], largeur_label=28, largeur_valeur=78),
    ]
    scol_droite = [
        Spacer(1, 4),
        Paragraph("2ème Cycle Fondamental", _ST_CARNET_TITRE_PAGE),
        Spacer(1, 12),
        _carnet_tableau(
            ["ANNEES", "ECOLES", "OBSERVATIONS"],
            [
                [Paragraph("7ème année<br/>à........", _ST_CARNET_CELL), "", ""],
                [Paragraph("8ème année<br/>à........", _ST_CARNET_CELL), "", ""],
                [Paragraph("9ème année<br/>à........", _ST_CARNET_CELL), "", ""],
            ],
            [38 * mm, 42 * mm, 46 * mm],
            hauteurs=[17.5 * mm] * 3,
        ),
        Spacer(1, 12),
        Paragraph("DIPLÔME D'ETUDES FONDAMENTALES :", _ST_CARNET_CHAMP_GRAS),
        Spacer(1, 2),
        _carnet_champs(["Session du :", "Résultat :", "Orientation :"], [None, None, None], largeur_label=28, largeur_valeur=78),
    ]

    # ── Page 4 : parties médicales (A4 paysage) ────────────────────────────────
    med_gauche = [
        Spacer(1, 4),
        Paragraph("PARTIES", _ST_CARNET_TITRE_PAGE),
        Spacer(1, 10),
        _carnet_tableau(
            ["RUBRIQUES", "........ à ........", "........ à ........", "........ à ........"],
            [
                [Paragraph("ANNEES SCOLAIRES", _ST_CARNET_TXT_LB), "", "", ""],
                [Paragraph("CLASSE", _ST_CARNET_TXT_L), "", "", ""],
                [Paragraph("POIDS", _ST_CARNET_TXT_L), "", "", ""],
                [Paragraph("TAILLE", _ST_CARNET_TXT_L), "", "", ""],
                [Paragraph("CUTI-REACTION", _ST_CARNET_TXT_L), "", "", ""],
                [Paragraph("VACCINATION CONTRE TUBERCULOSE (BCG)", _ST_CARNET_TXT_L), "", "", ""],
                [Paragraph("VACCIN ANTI-VARIOLIQUE", _ST_CARNET_TXT_L), "", "", ""],
                [Paragraph("VACCIN CONTRE LA FIEVRE JAUNE", _ST_CARNET_TXT_L), "", "", ""],
                [Paragraph("DEPISTAGE GRANDES ENDEMIES<br/>(LEPRE, ONCHOCERCOSE, TRYPANOSOMIASE)", _ST_CARNET_TXT_L), "", "", ""],
            ],
            [66 * mm, 22 * mm, 22 * mm, 22 * mm],
            hauteurs=[8 * mm, 7 * mm, 7 * mm, 7 * mm, 7 * mm, 8.5 * mm, 8.5 * mm, 8.5 * mm, 12 * mm],
        ),
    ]
    med_droite = [
        Spacer(1, 4),
        Paragraph("MEDICALES", _ST_CARNET_TITRE_PAGE),
        Spacer(1, 10),
        _carnet_tableau(
            ["........ à ........", "........ à ........", "........ à ........", "........ à ........"],
            [["", "", "", ""]],
            [33 * mm, 33 * mm, 33 * mm, 33 * mm],
            hauteurs=[73.5 * mm],
        ),
    ]

    # ── Page 5 : changements d'établissements (A4 paysage) ────────────────────
    chgt_gauche = [
        Spacer(1, 4),
        Paragraph("CHANGEMENTS", _ST_CARNET_TITRE_PAGE),
        Spacer(1, 10),
        _carnet_tableau(
            ["ÉCOLES FREQUENTÉES", "D. à ........", "N° Matricule", "Dernière classe suivie"],
            [
                [Paragraph(l, _ST_CARNET_TXT_L), "", "", ""]
                for l in [
                    "1ère classe (recrutement)", "2ème école", "3ème école", "4ème école",
                    "5ème école", "6ème école", "7ème école", "8ème école",
                ]
            ],
            [44 * mm, 24 * mm, 28 * mm, 40 * mm],
            hauteurs=[8.5 * mm] * 8,
        ),
    ]
    chgt_droite = [
        Spacer(1, 4),
        Paragraph("D'ETABLISSEMENTS", _ST_CARNET_TITRE_PAGE),
        Spacer(1, 10),
        _carnet_tableau(
            ["Dernier Classement", "Passe / Redouble / Exclu", "Motif du départ", "Appréciation du Directeur de l'école"],
            [["", "", "", ""] for _ in range(8)],
            [30 * mm, 34 * mm, 26 * mm, 46 * mm],
            hauteurs=[8.5 * mm] * 8,
        ),
    ]

    # ── Page 6 : résultats des visites médicales (A5) ─────────────────────────
    vm = [
        Spacer(1, 4),
        Paragraph("RÉSULTATS DES VISITES MÉDICALES", _ST_CARNET_TITRE_PAGE),
        Spacer(1, 12),
        _carnet_tableau(
            ["ANNEES<br/>SCOLAIRES", "SIGNATURE DU<br/>MEDECIN", "OBSERVATIONS"],
            [["", "", ""], ["", "", ""], ["", "", ""]],
            [38 * mm, 44 * mm, 42 * mm],
            hauteurs=[13 * mm] * 3,
        ),
    ]

    tampon = BytesIO()
    doc = BaseDocTemplate(
        tampon,
        pagesize=portrait(A5),
        leftMargin=marge,
        rightMargin=marge,
        topMargin=marge,
        bottomMargin=marge,
        title="Carnet scolaire",
        author="College Aureole",
    )

    def _cadre_a4_largeur():
        return (
            Frame(marge, marge, demi, H4 - 2 * marge, id="g"),
            Frame(marge + demi, marge, demi, H4 - 2 * marge, id="d"),
        )

    doc.addPageTemplates(
        [
            PageTemplate(
                id="couv",
                frames=[Frame(marge, marge, largeur5, H5 - 2 * marge, id="couv")],
                pagesize=portrait(A5),
                onPage=_carnet_fond_rose,
            ),
            PageTemplate(
                id="ec",
                frames=[Frame(marge, marge, largeur5, H5 - 2 * marge, id="ec")],
                pagesize=portrait(A5),
                onPage=_carnet_page_vierge,
            ),
            PageTemplate(id="scol", frames=_cadre_a4_largeur(), pagesize=landscape(A4), onPage=_carnet_page_vierge),
            PageTemplate(id="med", frames=_cadre_a4_largeur(), pagesize=landscape(A4), onPage=_carnet_page_vierge),
            PageTemplate(id="chgt", frames=_cadre_a4_largeur(), pagesize=landscape(A4), onPage=_carnet_page_vierge),
            PageTemplate(
                id="vm",
                frames=[Frame(marge, marge, largeur5, H5 - 2 * marge, id="vm")],
                pagesize=portrait(A5),
                onPage=_carnet_page_vierge,
            ),
        ]
    )

    from reportlab.platypus import FrameBreak, NextPageTemplate

    histoire = cov + [NextPageTemplate("ec"), PageBreak()]
    histoire += ec + [NextPageTemplate("scol"), PageBreak()]
    histoire += scol_gauche + [FrameBreak()] + scol_droite
    histoire += [NextPageTemplate("med"), PageBreak()]
    histoire += med_gauche + [FrameBreak()] + med_droite
    histoire += [NextPageTemplate("chgt"), PageBreak()]
    histoire += chgt_gauche + [FrameBreak()] + chgt_droite
    histoire += [NextPageTemplate("vm"), PageBreak()]
    histoire += vm

    doc.build(histoire)
    return tampon.getvalue()

# ─── Fiche de suivi au second cycle (formulaire officiel DEF) ─────────────────

_G_TITRE = ParagraphStyle(
    "fiche-titre",
    fontName="Helvetica-Bold",
    fontSize=11,
    leading=13,
    alignment=1,
    textColor=_INK,
)
_G_MINISTERE = ParagraphStyle(
    "fiche-ministere",
    fontName="Helvetica-Bold",
    fontSize=7.5,
    leading=9.5,
    alignment=0,
    textColor=_INK,
)
_G_ORGANE = ParagraphStyle(
    "fiche-organe",
    fontSize=7.5,
    leading=9.5,
    alignment=0,
    textColor=colors.HexColor("#333333"),
)
_G_ETOILES = ParagraphStyle(
    "fiche-etoiles",
    fontSize=7,
    leading=8.5,
    alignment=0,
    textColor=_INK,
)
_G_HEAD = ParagraphStyle("fiche-head", fontName="Helvetica-Bold", fontSize=6.5, leading=7.5, alignment=1, textColor=_INK)
_G_CELL = ParagraphStyle("fiche-cell", fontSize=6.5, leading=7, alignment=1, textColor=_INK)
_G_CELL_G = ParagraphStyle("fiche-cell-g", fontSize=6.5, leading=7, alignment=1, textColor=colors.HexColor("#777777"))
_G_CHAMP_LABEL = ParagraphStyle("fiche-champ-l", fontSize=6, leading=7, textColor=colors.HexColor("#333333"))
_G_CHAMP_VALUE = ParagraphStyle("fiche-champ-v", fontSize=7, leading=8.5, textColor=_INK)
_G_REMARQUE = ParagraphStyle("fiche-remarque", fontSize=7, leading=8.5, textColor=_INK)
_CELL_SIG = ParagraphStyle(
    "fiche-sig-role", fontName="Helvetica-Bold", fontSize=6.5, leading=7.5, alignment=1, textColor=_INK
)


def _boites_matricule(matricule: str) -> Table:
    """Les 8 boîtes du numéro matricule (une case par caractère)."""
    cases = (matricule or "")[-8:][::-1]
    cases = cases[::-1]
    cases = cases.ljust(8)
    boxes = Table(
        [[Paragraph(c, _G_CHAMP_VALUE) if c.strip() else "" for c in cases]],
        colWidths=[7 * mm] * 8,
        hAlign="LEFT",
    )
    boxes.setStyle(
        TableStyle(
            [
                ("GRID", (0, 0), (-1, -1), 0.7, _INK),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ("ALIGN", (0, 0), (-1, -1), "CENTER"),
                ("TOPPADDING", (0, 0), (-1, -1), 2),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
                ("LEFTPADDING", (0, 0), (-1, -1), 0),
                ("RIGHTPADDING", (0, 0), (-1, -1), 0),
            ]
        )
    )
    return boxes


def _ident_label(texte: str, largeur) -> Table:
    """Cellule « libellé » de la ligne d'identification (pas de cadre)."""
    t = Table([[_text_p(texte, _G_CHAMP_LABEL)]], colWidths=[largeur])
    t.setStyle(
        TableStyle(
            [
                ("LEFTPADDING", (0, 0), (-1, -1), 3),
                ("RIGHTPADDING", (0, 0), (-1, -1), 3),
                ("TOPPADDING", (0, 0), (-1, -1), 0),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 0),
                ("VALIGN", (0, 0), (-1, -1), "BOTTOM"),
            ]
        )
    )
    return t


def _ident_case(texte: str, largeur) -> Table:
    """Cellule « emplacement à remplir » (fond grisé, trait de soulignement)."""
    t = Table([[_text_p(texte, _G_CHAMP_VALUE)]], colWidths=[largeur])
    t.setStyle(
        TableStyle(
            [
                ("LEFTPADDING", (0, 0), (-1, -1), 4),
                ("RIGHTPADDING", (0, 0), (-1, -1), 4),
                ("TOPPADDING", (0, 0), (-1, -1), 1),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 2),
                ("VALIGN", (0, 0), (-1, -1), "BOTTOM"),
                ("LINEBELOW", (0, 0), (0, 0), 0.7, _INK),
                ("BACKGROUND", (0, 0), (0, 0), colors.HexColor("#f5f5f5")),
            ]
        )
    )
    return t


def _lignes_ecoles(fiche, etab: models.Etablissement | None) -> list:
    """Lignes du tableau école (N°/ECOLE/COURS/ANNEE/CAP/AE) depuis le parcours
    second cycle de l'élève — jusqu'à 5 établissements fréquentés."""
    nom_eco = _assainir(etab.nom if etab else None) or "Collège Auréole"
    cap = _assainir(etab.cap if etab else None) or "—"
    ae = _assainir(etab.academie if etab else None) or "—"
    lignes = []
    for p in fiche.parcours:
        if niveau_ordre(p.niveau) in (7, 8, 9):
            lignes.append(
                [
                    _text_p(str(len(lignes) + 1), _G_CELL),
                    _text_p(nom_eco, _G_CELL),
                    _text_p(_assainir(p.classe) or "—", _G_CELL),
                    _text_p(p.annee_label or "—", _G_CELL),
                    _text_p(cap, _G_CELL),
                    _text_p(ae, _G_CELL),
                ]
            )
        if len(lignes) == 5:
            break
    for i in range(len(lignes), 5):
        lignes.append([_text_p(str(i + 1), _G_CELL)] + [_text_p("", _G_CELL)] * 5)
    return lignes


def _remarques_officielles(remarques: list) -> list:
    bloc = [Spacer(1, 2), _text_p("REMARQUES IMPORTANTES (sur la fiche de suivi)", _G_HEAD)]
    bloc.append(Spacer(1, 1))
    for i, r in enumerate(remarques, start=1):
        bloc.append(_text_p(f"{i}. {r}", _G_REMARQUE))
    return bloc


def fiche_pdf(fiche, etab: models.Etablissement | None, annee_label: str | None) -> bytes:
    histoire = []
    total_w = 273 * mm

    # ── En-tête : ministère (40 %) + cadre titre (60 %) ────────────────────────
    gauche = Table(
        [
            [_text_p("MINISTERE D'EDUCATION DE BASE, DE", _G_MINISTERE)],
            [_text_p("L'ALPHABETISATION ET DES LANGUES", _G_MINISTERE)],
            [_text_p("NATIONALES", _G_MINISTERE)],
            [_text_p("***********", _G_ETOILES)],
            [_text_p("CELLULE DE PLANIFICATION", _G_ORGANE)],
            [_text_p("ET DE STATISTIQUE", _G_ORGANE)],
            [_text_p("Commission d'Orientation DEF", _G_ORGANE)],
            [_text_p("***********", _G_ETOILES)],
        ],
        colWidths=[0.40 * total_w],
    )
    gauche.setStyle(
        TableStyle(
            [
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ("TOPPADDING", (0, 0), (-1, -1), 0),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 0),
            ]
        )
    )

    cadre_titre = Table(
        [[_text_p("FICHE DE SUIVI AU SECOND CYCLE DE L'ENSEIGNEMENT FONDAMENTAL", _G_TITRE)]],
        colWidths=[0.60 * total_w],
    )
    cadre_titre.setStyle(
        TableStyle(
            [
                ("BOX", (0, 0), (-1, -1), 1.0, _INK),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ("TOPPADDING", (0, 0), (-1, -1), 2),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
            ]
        )
    )

    entete = Table([[gauche, cadre_titre]], colWidths=[0.40 * total_w, 0.60 * total_w])
    entete.setStyle(
        TableStyle(
            [
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ("LEFTPADDING", (0, 0), (-1, -1), 0),
                ("RIGHTPADDING", (0, 0), (-1, -1), 0),
                ("TOPPADDING", (0, 0), (-1, -1), 0),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 0),
            ]
        )
    )
    histoire += [entete, Spacer(1, 3)]

    # ── Tableau de suivi des écoles (pleine largeur) ──────────────────────────
    entetes_ecole = [_text_p(x, _G_HEAD) for x in ("N°", "NOM DE L'ECOLE", "COURS", "ANNEE", "CAP", "AE")]
    tableau_ecole = Table(
        [entetes_ecole, *_lignes_ecoles(fiche, etab)],
        colWidths=[9 * mm, 100 * mm, 55 * mm, 45 * mm, 35 * mm, 29 * mm],
        hAlign="CENTER",
    )
    tableau_ecole.setStyle(
        TableStyle(
            [
                ("GRID", (0, 0), (-1, -1), 0.5, _INK),
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#f2f2f2")),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ("TOPPADDING", (0, 0), (-1, -1), 2),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 2),
            ]
        )
    )
    histoire += [tableau_ecole, Spacer(1, 3)]

    # ── Identification de l'élève (3 lignes officielles) ──────────────────────
    sexe = "M" if fiche.sexe == "M" else "F"
    pere = _assainir(fiche.pere) or "........................"
    mere = _assainir(fiche.mere) or "........................"
    lieu_naiss = _assainir(fiche.lieu_de_naissance) or "........................"
    ligne1 = Table(
        [[
            _ident_label("Numéro Matricule", 24 * mm),
            _ident_case(fiche.matricule or "", 56 * mm),
            _ident_label("Prénom (s)", 15 * mm),
            _ident_case(f"{fiche.prenom or ''}", 62 * mm),
            _ident_label("Nom(s)", 13 * mm),
            _ident_case(f"{fiche.nom or ''}", 68 * mm),
            _ident_label("Sexe", 11 * mm),
            _ident_case(sexe, 10 * mm),
        ]],
        colWidths=[24 * mm, 56 * mm, 15 * mm, 62 * mm, 13 * mm, 68 * mm, 11 * mm, 10 * mm],
        hAlign="LEFT",
    )
    ligne2 = Table(
        [[
            _ident_label("FIL/Fille de", 20 * mm),
            _ident_case(pere, 120 * mm),
            _ident_label("et de", 12 * mm),
            _ident_case(mere, 112 * mm),
        ]],
        colWidths=[20 * mm, 120 * mm, 12 * mm, 112 * mm],
        hAlign="LEFT",
    )
    ligne3 = Table(
        [[
            _ident_label("Né(e) le", 13 * mm),
            _ident_case(
                fiche.date_de_naissance.strftime("%d/%m/%Y")
                if fiche.date_de_naissance else "........../........../20........",
                58 * mm,
            ),
            _ident_label("à", 8 * mm),
            _ident_case(lieu_naiss, 88 * mm),
            _ident_label("Cercle de", 18 * mm),
            _ident_case("", 70 * mm),
        ]],
        colWidths=[13 * mm, 58 * mm, 8 * mm, 88 * mm, 18 * mm, 70 * mm],
        hAlign="LEFT",
    )
    for ligne in (ligne1, ligne2, ligne3):
        ligne.setStyle(
            TableStyle(
                [
                    ("LEFTPADDING", (0, 0), (-1, -1), 0),
                    ("RIGHTPADDING", (0, 0), (-1, -1), 0),
                    ("TOPPADDING", (0, 0), (-1, -1), 1),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 1),
                    ("VALIGN", (0, 0), (-1, -1), "BOTTOM"),
                ]
            )
        )
    histoire += [ligne1, Spacer(1, 1), ligne2, Spacer(1, 1), ligne3, Spacer(1, 3)]

    # ── Grille principale des notes (23 colonnes) ─────────────────────────────
    if not fiche.est_jardin and fiche.lignes:
        sous = [max(1, len(c.moyennes)) for c in fiche.colonnes]
        nb_notes = sum(sous)
        nb_x = 1            # colonne « hachurée » de la zone Tendance
        nb_fois = 3         # « 1er Fois / 2e Fois / 3e Fois »
        n_cols = 1 + nb_notes + nb_x + nb_fois  # 23
        assert n_cols == 23, f"grille non conforme : {n_cols} colonnes"

        largeur = [36 * mm] + [8.2 * mm] * nb_notes + [18 * mm] * nb_x + [12 * mm] * nb_fois

        starts = []
        col = 1
        for s in sous:
            starts.append(col)
            col += s
        debut_hatch = 1 + nb_notes    # 19
        debut_fois = debut_hatch + 1  # 20

        def rang_vide() -> list:
            return [""] * n_cols

        libelles_tr = ["1er Tr", "2e Tr", "3e Tr"]

        # Ligne 0 : groupes de périodes + « Tendance »
        r0 = rang_vide()
        r0[0] = _text_p("Matières", _G_HEAD)
        for (s, c), start_col in zip(zip(sous, fiche.colonnes), starts):
            r0[start_col] = _text_p(c.label, _G_HEAD)
        r0[debut_hatch] = _text_p("Tendance", _G_HEAD)

        # Ligne 1 : libellés de trimestres + colonne hachurée + « … Fois »
        r1 = rang_vide()
        for s, start_col in zip(sous, starts):
            for k in range(s):
                r1[start_col + k] = _text_p(libelles_tr[k], _G_HEAD)
        r1[debut_hatch] = _text_p("", _G_CELL_G)
        r1[debut_fois] = _text_p("1er Fois", _G_HEAD)
        r1[debut_fois + 1] = _text_p("2e Fois", _G_HEAD)
        r1[debut_fois + 2] = _text_p("3e Fois", _G_HEAD)

        corps = [r0, r1]
        for i, ligne in enumerate(fiche.lignes, start=1):
            line = [""] * n_cols
            line[0] = _text_p(f"{i}. {ligne.matiere}", _G_CELL)
            for j, v in enumerate(ligne.valeurs):
                line[1 + j] = _text_p(_format2(v) if v is not None else "", _G_CELL)
            line[debut_hatch] = _text_p(ligne.tendance or "", _G_CELL_G) if ligne.tendance else ""
            for k in range(1, nb_fois + 1):
                line[debut_fois + k - 1] = _text_p("×" if k == fiche.fois_x else "", _G_CELL)
            corps.append(line)

        # Lignes signature (2 lignes physiques)
        s1_idx = len(corps)
        s1 = rang_vide()
        s2 = rang_vide()
        s1[0] = _text_p("Date, Signature et Cachet du Directeur d'école", _CELL_SIG)
        litt = f"{'× ' if fiche.orientation == 'Littéraire' else ''}Littéraire"
        scient = f"{'× ' if fiche.orientation == 'Scientifique' else ''}Scientifique"
        s1[debut_hatch] = _text_p(litt, _CELL_SIG)
        s2[debut_hatch] = _text_p(scient, _CELL_SIG)
        corps += [s1, s2]

        table = Table(corps, colWidths=largeur, hAlign="CENTER", repeatRows=2)

        spans = [
            ("SPAN", (0, 0), (0, 1)),
            ("SPAN", (debut_hatch, 0), (debut_fois + 2, 1)),
            ("SPAN", (0, s1_idx), (18, s1_idx + 1)),
            ("SPAN", (debut_fois, s1_idx), (debut_fois + 2, s1_idx + 1)),
        ]
        for s, start_col in zip(sous, starts):
            spans.append(("SPAN", (start_col, 0), (start_col + s - 1, 0)))
            spans.append(("SPAN", (start_col, 1), (start_col + s - 1, 1)))

        style = [
            ("GRID", (0, 0), (-1, -1), 0.4, _LINE),
            ("BOX", (0, 0), (-1, -1), 1.0, _INK),
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ("TOPPADDING", (0, 0), (-1, -1), 1),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 1),
            ("LEFTPADDING", (0, 0), (-1, -1), 0),
            ("RIGHTPADDING", (0, 0), (-1, -1), 0),
            ("LINEBELOW", (0, 1), (-1, 1), 0.9, _INK),
            ("LINEBELOW", (0, s1_idx - 1), (-1, s1_idx - 1), 1.0, _INK),
            ("BACKGROUND", (debut_hatch, 1), (debut_hatch, -1), colors.HexColor("#d9d9d9")),
            *spans,
        ]
        table.setStyle(TableStyle(style))
        histoire.append(table)
    else:
        histoire += _bloc_appreciation(
            "Évaluation",
            "Évaluation par appréciation de l'enseignant — pas de notes chiffrées.",
        )

    # ── Remarques officielles ────────────────────────────────────────────────
    histoire += _remarques_officielles(fiche.remarques)

    # ── Pied : lieu/date + Directeur d'école ─────────────────────────────────
    lieu = _assainir(etab.adresse if etab else None) if etab and etab.adresse else ""
    faite = f"Fait à {lieu}, le" if lieu else "Fait à"
    histoire += [Spacer(1, 4)]
    histoire.append(_text_p(f"{faite} ..............., ........./.............20........", _G_REMARQUE))
    histoire += [Spacer(1, 8)]
    bloc_dir = Table(
        [[_text_p("Le Directeur d'école", _G_HEAD)], ["", ""]],
        colWidths=[60 * mm],
        rowHeights=[None, 18],
        hAlign="RIGHT",
    )
    bloc_dir.setStyle(
        TableStyle(
            [
                ("ALIGN", (0, 0), (-1, -1), "CENTER"),
                ("VALIGN", (0, 1), (-1, 1), "BOTTOM"),
                ("LINEBELOW", (0, 1), (-1, 1), 0.8, _INK),
                ("LEFTPADDING", (0, 0), (-1, -1), 0),
                ("RIGHTPADDING", (0, 0), (-1, -1), 0),
                ("TOPPADDING", (0, 0), (-1, -1), 0),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 0),
            ]
        )
    )
    histoire.append(bloc_dir)
    return _document("Fiche de suivi au second cycle", histoire, paysage=True)


# ─── Rapport des moyennes annuelles ────────────────────────────────────────────


def moyennes_pdf(rapport, etab: models.Etablissement | None, annee_label: str | None) -> bytes:
    histoire = []
    histoire += _en_tete(etab, annee_label)
    histoire += _bandeau_doc("RAPPORT DES MOYENNES ANNUELLES", f"Année scolaire {annee_label or '—'}")
    for i, c in enumerate(rapport.classes):
        if i > 0:
            histoire.append(PageBreak())
        titre = f"{c.niveau} {c.nom} — Effectif : {c.effectif}"
        if c.moyenne_classe is not None:
            titre += f" — Moyenne de classe : {_format2(c.moyenne_classe)}/{c.bareme}"
        histoire.append(Spacer(1, 6))
        histoire.append(_text_p(titre, _sec_titre()))
        rows = [
            [
                Paragraph(str(e.rang) if e.rang else "—", ST_CELL_NUM),
                Paragraph(e.matricule, ST_CELL),
                Paragraph(f"{e.nom} {e.prenom}", ST_CELL),
                Paragraph(
                    f"{_format2(e.moyenne_annuelle)}/{c.bareme}" if e.moyenne_annuelle is not None else "—",
                    ST_CELL_NUM,
                ),
                Paragraph(e.statut_passage, ST_CELL),
            ]
            for e in c.eleves
        ]
        histoire.append(
            _tableau_plein(
                [
                    Paragraph("Rang", ST_HEAD_CELL),
                    Paragraph("Matricule", ST_HEAD_CELL),
                    Paragraph("Nom & Prénom", ST_HEAD_CELL),
                    Paragraph("Moyenne", ST_HEAD_CELL),
                    Paragraph("Statut", ST_HEAD_CELL),
                ],
                rows,
                [20 * mm, 34 * mm, 74 * mm, 26 * mm, 30 * mm],
            )
        )
    histoire.append(Spacer(1, 12))
    histoire.append(_pied_de_page(etab))
    histoire.append(Spacer(1, 18))
    histoire.append(_signatures())
    return _document("Rapport des moyennes annuelles", histoire)


# ─── Proposition de passage ────────────────────────────────────────────────────


def proposition_pdf(rapport, etab: models.Etablissement | None, annee_label: str | None) -> bytes:
    histoire = []
    histoire += _en_tete(etab, annee_label)
    histoire += _bandeau_doc("PROPOSITION DE PASSAGE", f"Année scolaire {annee_label or '—'}")
    for i, c in enumerate(rapport.classes):
        if i > 0:
            histoire.append(PageBreak())
        titre = f"{c.niveau} {c.nom} — Seuil de passage : {_format2(c.seuil)}/{c.bareme}"
        if c.est_fin_cycle:
            titre += " (fin de cycle)"
        histoire.append(Spacer(1, 6))
        histoire.append(_text_p(titre, _sec_titre()))
        histoire.append(
            _text_p(
                f"Admis : {c.admis} · Recalés : {c.recales} · En attente : {c.en_attente} · Exclus : {c.exclus}",
                ST_TITRE_SUB,
            )
        )
        rows = [
            [
                Paragraph(str(idx), ST_CELL_NUM),
                Paragraph(e.matricule, ST_CELL),
                Paragraph(f"{e.nom} {e.prenom}", ST_CELL),
                Paragraph(
                    f"{_format2(e.moyenne_annuelle)}/{c.bareme}" if e.moyenne_annuelle is not None else "—",
                    ST_CELL_NUM,
                ),
                Paragraph(e.statut_actuel, ST_CELL),
                Paragraph(e.proposition, ST_CELL),
            ]
            for idx, e in enumerate(c.eleves, start=1)
        ]
        histoire.append(
            _tableau_plein(
                [
                    Paragraph("N°", ST_HEAD_CELL),
                    Paragraph("Matricule", ST_HEAD_CELL),
                    Paragraph("Nom & Prénom", ST_HEAD_CELL),
                    Paragraph("Moyenne", ST_HEAD_CELL),
                    Paragraph("Statut actuel", ST_HEAD_CELL),
                    Paragraph("Proposition", ST_HEAD_CELL),
                ],
                rows,
                [14 * mm, 30 * mm, 66 * mm, 24 * mm, 24 * mm, 28 * mm],
            )
        )
    histoire.append(Spacer(1, 12))
    histoire.append(_pied_de_page(etab))
    return _document("Proposition de passage", histoire)

# ─── Classement des élèves (doc1) ──────────────────────────────────────────────

_ST_CLAS_ECOLE = ParagraphStyle("clas-ecole", fontName="Helvetica-Bold", fontSize=10, leading=13, textColor=_INK, alignment=TA_LEFT)
_ST_CLAS_ECOLE_ADR = ParagraphStyle("clas-ecole-adr", fontSize=8.5, leading=11, textColor=_INK, alignment=TA_LEFT)
_ST_CLAS_REP = ParagraphStyle("clas-rep", fontName="Helvetica-Bold", fontSize=10, leading=13, textColor=_INK, alignment=TA_RIGHT)
_ST_CLAS_DEV = ParagraphStyle("clas-dev", fontSize=8.5, leading=11, textColor=_INK, alignment=TA_RIGHT)
_ST_CLAS_TITRE = ParagraphStyle("clas-titre", fontName="Helvetica-Bold", fontSize=15, leading=19, textColor=_INK, alignment=TA_CENTER, uppercase=1)
_ST_CLAS_SUB = ParagraphStyle("clas-sub", fontSize=9.5, leading=12, textColor=colors.HexColor("#333333"), alignment=TA_LEFT)
_ST_CLAS_SIG = ParagraphStyle("clas-sig", fontName="Helvetica-Bold", fontSize=9.5, leading=12, textColor=_INK, alignment=TA_CENTER)


def _crayon_classement(nom: str, adresse: str):
    """Dessine l'en-tête (école / République) en haut et le pied de page
    (visas du Directeur et de l'Encadreur) en bas : chaque classe forme ainsi
    une fiche autonome, comme un document séparé."""
    def on_page(canvas, doc):
        w, h = A4
        m = 12 * mm
        canvas.saveState()
        canvas.setStrokeColor(_INK)
        canvas.setFont("Helvetica-Bold", 11)
        canvas.drawString(m, h - 14 * mm, nom)
        canvas.setFont("Helvetica", 9)
        canvas.drawString(m, h - 18.5 * mm, adresse)
        canvas.setFont("Helvetica-Bold", 11)
        canvas.drawRightString(w - m, h - 14 * mm, "RÉPUBLIQUE DU MALI")
        canvas.setFont("Helvetica", 9)
        canvas.drawRightString(w - m, h - 18.5 * mm, "Un Peuple - Un But - Une Foi")
        canvas.setLineWidth(1.6)
        canvas.line(m, h - 22 * mm, w - m, h - 22 * mm)

        y = 24 * mm
        canvas.setLineWidth(0.6)
        canvas.line(m, y, w / 2 - 8 * mm, y)
        canvas.line(w / 2 + 8 * mm, y, w - m, y)
        canvas.setFont("Helvetica", 10)
        canvas.drawCentredString((m + w / 2 - 8 * mm) / 2, y - 4.5 * mm, "Visa du Directeur")
        canvas.drawCentredString((w / 2 + 8 * mm + w - m) / 2, y - 4.5 * mm, "Visa de l'Encadreur")

        canvas.setFont("Helvetica", 8.5)
        canvas.drawCentredString(w / 2, 10 * mm, f"Page {canvas.getPageNumber()}")
        canvas.restoreState()
    return on_page


def classement_pdf(rapport, etab: models.Etablissement | None, annee_label: str | None) -> bytes:
    """Un classement par classe : chaque classe forme une fiche (une page) avec
    en-tête et pied de page propres, comme des documents séparés."""
    nom = _assainir(etab.nom if etab else None) or "Collège Auréole"
    adresse = " · ".join(filter(None, [
        _assainir(etab.adresse if etab else None),
        _assainir(etab.telephone if etab else None),
    ]))

    m = 12 * mm
    marge_haut = 26 * mm
    marge_bas = 30 * mm
    tampon = BytesIO()
    doc = BaseDocTemplate(
        tampon,
        pagesize=A4,
        leftMargin=m,
        rightMargin=m,
        topMargin=marge_haut,
        bottomMargin=marge_bas,
        title="Classement des élèves",
        author="College Aureole",
    )
    doc.addPageTemplates([
        PageTemplate(
            id="classement",
            frames=[Frame(m, marge_bas, A4[0] - 2 * m, A4[1] - marge_haut - marge_bas, id="corps")],
            onPage=_crayon_classement(nom, adresse),
        ),
    ])

    histoire: list = []
    for i, c in enumerate(rapport.classes):
        if i > 0:
            histoire.append(PageBreak())
        histoire.append(_text_p("CLASSEMENT DES ÉLÈVES", _ST_CLAS_TITRE))
        moy_classe = f"{_format2(c.moyenne_classe)}/{c.bareme}" if c.moyenne_classe is not None else "________"
        histoire.append(Spacer(1, 4))
        histoire.append(_text_p(
            f"Classe : {_assainir(c.niveau)} {_assainir(c.nom)} — Moyenne annuelle : {moy_classe}",
            _ST_CLAS_SUB,
        ))
        histoire.append(Spacer(1, 6))

        rows = [
            [
                Paragraph(str(idx), _ST_CLAS_SIG),
                Paragraph(f"{e.prenom} {e.nom}", ST_CELL),
                Paragraph(f"{_format2(e.moyenne_annuelle)}/{c.bareme}" if e.moyenne_annuelle is not None else "—", ST_CELL_NUM),
                Paragraph(str(e.rang) if e.rang else "—", ST_CELL_NUM),
                Paragraph(e.observation or "", ST_CELL),
            ]
            for idx, e in enumerate(c.eleves, start=1)
        ]
        table = Table(
            [
                [Paragraph("N°", ST_HEAD_CELL), Paragraph("Prénom et nom de l'élève", ST_HEAD_CELL),
                 Paragraph("Moyenne", ST_HEAD_CELL), Paragraph("Rang", ST_HEAD_CELL),
                 Paragraph("Observations", ST_HEAD_CELL)],
                *rows,
            ],
            colWidths=[9 * mm, 84 * mm, 28 * mm, 28 * mm, 37 * mm],
            hAlign="CENTER",
        )
        table.setStyle(TableStyle([
            ("GRID", (0, 0), (-1, -1), 0.7, _SOFT),
            ("LINEBELOW", (0, 0), (-1, 0), 1.4, _INK),
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ("TOPPADDING", (0, 0), (-1, -1), 6),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
            ("LEFTPADDING", (0, 0), (-1, -1), 7),
            ("RIGHTPADDING", (0, 0), (-1, -1), 7),
            ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#fafafa")]),
        ]))
        histoire.append(table)

    doc.build(histoire)
    return tampon.getvalue()


# ─── Rapport succinct de rentrée (doc5) ───────────────────────────────────────

_ST_RR_MINIS = ParagraphStyle("rr-minis", fontName="Helvetica-Bold", fontSize=8.5, leading=11, textColor=_INK, alignment=TA_LEFT)
_ST_RR_ORGANE = ParagraphStyle("rr-organe", fontSize=8.5, leading=11, textColor=colors.HexColor("#333333"), alignment=TA_LEFT)
_ST_RR_TITLE = ParagraphStyle("rr-title", fontName="Helvetica-Bold", fontSize=13, leading=16, textColor=_INK, alignment=TA_CENTER)
_ST_RR_TITLE_SUB = ParagraphStyle("rr-title-sub", fontSize=8.5, leading=11, textColor=colors.HexColor("#333333"), alignment=TA_CENTER)
_ST_RR_REP = ParagraphStyle("rr-rep", fontName="Helvetica-Bold", fontSize=8.5, leading=11, textColor=_INK, alignment=TA_RIGHT)
_ST_RR_DEV = ParagraphStyle("rr-dev", fontSize=8, leading=10, textColor=_INK, alignment=TA_RIGHT)
_ST_RR_ANNEE = ParagraphStyle("rr-annee", fontSize=8.5, leading=11, textColor=_INK, alignment=TA_RIGHT)
_ST_RR_SECT = ParagraphStyle("rr-sect", fontName="Helvetica-Bold", fontSize=10, leading=13, textColor=_INK, alignment=TA_CENTER, spaceBefore=10, spaceAfter=4)
_ST_RR_LIB = ParagraphStyle("rr-lib", fontSize=8.5, leading=11, textColor=_INK, alignment=TA_LEFT)
_ST_RR_COCHE = ParagraphStyle("rr-coche", fontSize=8, leading=10.5, textColor=_INK, alignment=TA_LEFT)
_ST_RR_NOTE = ParagraphStyle("rr-note", fontName="Helvetica-Oblique", fontSize=8.5, leading=11, textColor=colors.HexColor("#444444"))
_ST_RR_SIG_NOM = ParagraphStyle("rr-sig-nom", fontName="Helvetica-Bold", fontSize=9.5, leading=12, textColor=_INK, alignment=TA_CENTER)
_ST_RR_SIG_ROLE = ParagraphStyle("rr-sig-role", fontSize=8.5, leading=11, textColor=_INK, alignment=TA_CENTER)


def _rr_encadre(titre: str, sous: str | None = None) -> Table:
    cellules = [_text_p(titre, _ST_RR_TITLE)]
    if sous:
        cellules.append(_text_p(sous, _ST_RR_TITLE_SUB))
    cadre = Table([[c] for c in cellules], colWidths=[97 * mm])
    cadre.setStyle(TableStyle([
        ("BOX", (0, 0), (-1, -1), 1.4, _INK),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("TOPPADDING", (0, 0), (-1, -1), 2),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
        ("LEFTPADDING", (0, 0), (-1, -1), 5),
        ("RIGHTPADDING", (0, 0), (-1, -1), 5),
    ]))
    return cadre


def _entete_rentree(data, annee_label: str | None) -> Table:
    gauche = Table(
        [
            [_text_p("MINISTÈRE DE L'ÉDUCATION NATIONALE", _ST_RR_MINIS)],
            [_text_p("CELLULE DE PLANIFICATION ET DE STATISTIQUE", _ST_RR_ORGANE)],
        ],
        colWidths=[97 * mm],
    )
    centre = _rr_encadre("RAPPORT SUCCINCT DE RENTRÉE", "(Formulaire à remplir par les directeurs d'écoles)")
    droite = Table(
        [
            [_text_p("RÉPUBLIQUE DU MALI", _ST_RR_REP)],
            [_text_p("Un Peuple - Un But - Une Foi", _ST_RR_DEV)],
            [_text_p(f"Année scolaire : {annee_label or '20____-20____'}", _ST_RR_ANNEE)],
        ],
        colWidths=[79 * mm],
    )
    for part in (gauche, centre, droite):
        part.setStyle(TableStyle([
            ("LEFTPADDING", (0, 0), (-1, -1), 0),
            ("RIGHTPADDING", (0, 0), (-1, -1), 0),
            ("TOPPADDING", (0, 0), (-1, -1), 1),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 1),
        ]))
    entete = Table([[gauche, centre, droite]], colWidths=[97 * mm, 97 * mm, 79 * mm])
    entete.setStyle(TableStyle([
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("LEFTPADDING", (0, 0), (-1, -1), 0),
        ("RIGHTPADDING", (0, 0), (-1, -1), 0),
    ]))
    return entete


def rapport_rentree_pdf(data, etab: models.Etablissement | None, annee_label: str | None) -> bytes:
    histoire: list = [Spacer(1, 6), _entete_rentree(data, annee_label), Spacer(1, 6)]

    def cases(textes: list) -> list:
        return [_text_p(f"{'☒' if t.startswith('__coche__') else '☐'} {t.removeprefix('__coche__')}", _ST_RR_COCHE)
                for t in textes]

    # ── Tableau 1 : renseignements généraux ───────────────────────────────────
    lib_g = _text_p(
        "École de : <u>{nl}</u><br/>Village / Quartier : <u>{v}</u><br/>Commune de : <u>{c}</u><br/>"
        "CAP de : <u>{cap}</u><br/>Cercle de : <u>{ce}</u><br/>AE de : <u>{ae}</u>".format(
            nl=_assainir(data.ecole) or "________", v=_assainir(data.village_quartier) or "________",
            c=_assainir(data.commune) or "________", cap=_assainir(data.cap) or "________",
            ce=_assainir(data.cercle) or "________", ae=_assainir(data.ae) or "________"),
        _ST_RR_LIB,
    )

    options_cycles = ["1. 1er cycle", "2. 2è cycle", "3. Cycles complets"]
    cell_cycles = cases([("__coche__" if t in data.cycles else "") + t for t in options_cycles])
    options_statuts = ["1. Public", "2. Privé catholique", "3. Médersa", "4. Privé laïc", "5. École communautaire"]
    cell_statuts = cases([("__coche__" if t in data.statuts else "") + t for t in options_statuts])
    options_types = ["1. Classique", "2. École à PC", "3. Franco-arabe"]
    options_modes = ["1. Annuel", "2. Biennal"]
    cell_types = cases([("__coche__" if t in data.types_modes else "") + t for t in options_types])
    cell_modes = cases([("__coche__" if t in data.types_modes else "") + t for t in options_modes])

    t1 = Table(
        [[
            lib_g,
            [_text_p("Cycles d'enseignement :", _ST_RR_MINIS), *cell_cycles],
            [_text_p("Statut administratif :", _ST_RR_MINIS), *cell_statuts],
            [_text_p("Type & Mode :", _ST_RR_MINIS), *cell_types, HRFlowable(width="100%", thickness=0.5, color=_SOFT), *cell_modes],
        ]],
        colWidths=[108 * mm, 55 * mm, 55 * mm, 55 * mm],
    )
    t1.setStyle(TableStyle([
        ("GRID", (0, 0), (-1, -1), 0.7, _SOFT),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("LEFTPADDING", (0, 0), (-1, -1), 6),
        ("RIGHTPADDING", (0, 0), (-1, -1), 6),
        ("TOPPADDING", (0, 0), (-1, -1), 5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
    ]))
    histoire += [_text_p("Tableau 1 : Renseignements Généraux", _ST_RR_SECT), t1]

    # ── Tableau 2 : groupes pédagogiques et effectifs scolaires ───────────────
    entetes2 = [
        [Paragraph("Année d'Études", ST_HEAD_CELL),
         Paragraph("Nombre de Groupes pédagogiques", ST_HEAD_CELL),
         Paragraph("Nombre Élèves / sexe", ST_HEAD_CELL), "",
         Paragraph("Total élève", ST_HEAD_CELL),
         Paragraph("Redoublants", ST_HEAD_CELL), "", ""],
        ["", "", Paragraph("G", ST_HEAD_CELL), Paragraph("F", ST_HEAD_CELL), "",
         Paragraph("Sexe G", ST_HEAD_CELL), Paragraph("Sexe F", ST_HEAD_CELL), Paragraph("Total", ST_HEAD_CELL)],
    ]
    corps2 = [
        [
            Paragraph(c.annee_etude, _ST_RR_LIB),
            Paragraph(str(c.groupes), ST_CELL_NUM),
            Paragraph(str(c.garcons), ST_CELL_NUM),
            Paragraph(str(c.filles), ST_CELL_NUM),
            Paragraph(str(c.total), ST_CELL_NUM),
            Paragraph(str(c.redoublants_g), ST_CELL_NUM),
            Paragraph(str(c.redoublants_f), ST_CELL_NUM),
            Paragraph(str(c.redoublants_total), ST_CELL_NUM),
        ]
        for c in data.classes
    ]
    grd = ParagraphStyle("rr-tot", parent=ST_CELL_NUM, fontName="Helvetica-Bold")
    corps2.append([
        Paragraph("Total Général", ParagraphStyle("rr-total", parent=_ST_RR_LIB, fontName="Helvetica-Bold")),
        Paragraph("", ST_CELL_NUM),
        Paragraph(str(data.total_garcons), grd),
        Paragraph(str(data.total_filles), grd),
        Paragraph(str(data.total_general), grd),
        Paragraph(str(data.total_redoublants_g), grd),
        Paragraph(str(data.total_redoublants_f), grd),
        Paragraph(str(data.total_redoublants), grd),
    ])
    t2 = Table([*entetes2, *corps2],
               colWidths=[41*mm, 47*mm, 24*mm, 24*mm, 32*mm, 29*mm, 29*mm, 47*mm], hAlign="CENTER")
    t2.setStyle(TableStyle([
        ("GRID", (0, 0), (-1, -1), 0.7, _SOFT),
        ("LINEBELOW", (0, 0), (-1, 0), 1.2, _INK),
        ("SPAN", (0, 0), (0, 1)),
        ("SPAN", (1, 0), (1, 1)),
        ("SPAN", (2, 0), (3, 0)),
        ("SPAN", (4, 0), (4, 1)),
        ("SPAN", (5, 0), (7, 0)),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("BACKGROUND", (0, -1), (-1, -1), colors.HexColor("#f2f2f2")),
        ("TOPPADDING", (0, 0), (-1, -1), 3),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
    ]))
    histoire += [_text_p("Tableau 2 : Groupes Pédagogiques et Effectifs scolaires", _ST_RR_SECT), t2]

    # ── Tableau 3 : maîtres et salles de classe ───────────────────────────────
    entetes3 = [Paragraph("Cycles d'enseignement", ST_HEAD_CELL), Paragraph("FE", ST_HEAD_CELL),
                Paragraph("FC", ST_HEAD_CELL), Paragraph("CE", ST_HEAD_CELL), Paragraph("CC", ST_HEAD_CELL),
                Paragraph("Autres", ST_HEAD_CELL), Paragraph("EM", ST_HEAD_CELL), Paragraph("Total", ST_HEAD_CELL)]
    lignes3 = [
        [Paragraph(cycle.cycle, _ST_RR_LIB),
         Paragraph(str(cycle.fe), ST_CELL_NUM), Paragraph(str(cycle.fc), ST_CELL_NUM),
         Paragraph(str(cycle.ce), ST_CELL_NUM), Paragraph(str(cycle.cc), ST_CELL_NUM),
         Paragraph(str(cycle.autres), ST_CELL_NUM), Paragraph(str(cycle.em), ST_CELL_NUM),
         Paragraph(str(cycle.total), ST_CELL_NUM)]
        for cycle in (data.premiers_cycle, data.second_cycle)
    ]
    t3 = Table([entetes3, *lignes3],
               colWidths=[65*mm, 23*mm, 23*mm, 23*mm, 26*mm, 26*mm, 29*mm], hAlign="LEFT")
    t3_salles = Table(
        [
            [Paragraph("Nbre de salles", ST_HEAD_CELL)],
            [Paragraph(str(data.nb_salles_1er), ST_CELL_NUM)],
            [Paragraph(str(data.nb_salles_2nd), ST_CELL_NUM)],
        ],
        colWidths=[48*mm],
    )
    style3 = TableStyle([
        ("GRID", (0, 0), (-1, -1), 0.7, _SOFT),
        ("LINEBELOW", (0, 0), (-1, 0), 1.2, _INK),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("TOPPADDING", (0, 0), (-1, -1), 3),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
    ])
    t3.setStyle(style3)
    t3_salles.setStyle(style3)
    t3_bloc = Table([[t3, t3_salles]], colWidths=[225*mm, 48*mm])
    t3_bloc.setStyle(TableStyle([
        ("LEFTPADDING", (0, 0), (-1, -1), 0),
        ("RIGHTPADDING", (0, 0), (-1, -1), 0),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
    ]))
    histoire += [_text_p("Tableau 3 : Maîtres et Salles de classe", _ST_RR_SECT), t3_bloc]

    # ── Note et signature ─────────────────────────────────────────────────────
    histoire += [Spacer(1, 6), _text_p(
        "Cette fiche doit être remplie et envoyée au CAP dans les 10 jours qui suivent la rentrée scolaire.",
        _ST_RR_NOTE,
    ), Spacer(1, 8)]
    signature = Table(
        [[_text_p((etab.nom if etab else None) or "Collège Auréole", _ST_RR_SIG_NOM)],
         [_text_p("Le Directeur", _ST_RR_SIG_ROLE)]],
        colWidths=[100 * mm],
        hAlign="RIGHT",
    )
    signature.setStyle(TableStyle([
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("ALIGN", (0, 0), (-1, -1), "CENTER"),
        ("LEFTPADDING", (0, 0), (-1, -1), 0),
        ("RIGHTPADDING", (0, 0), (-1, -1), 0),
        ("TOPPADDING", (0, 0), (-1, -1), 24),
    ]))
    histoire.append(signature)
    return _document("Rapport succinct de rentrée", histoire, paysage=True)


# ─── Fiche de renseignements de rentrée, 2nd cycle (doc6) ─────────────────────
#
# Formulaire officiel à deux tableaux de 17 colonnes : toujours édité au format
# paysage. Les styles sont volontairement plus grands (polices ≥ 8 pt, paddings
# généreux) pour rester lisibles sur la largeur de 273 mm.

_ST_FR_MINIS = ParagraphStyle("fr-minis", fontName="Helvetica-Bold", fontSize=9.5, leading=13, textColor=_INK, alignment=TA_LEFT)
_ST_FR_ORGANE = ParagraphStyle("fr-organe", fontSize=8.5, leading=11.5, textColor=colors.HexColor("#333333"), alignment=TA_LEFT)
_ST_FR_REP = ParagraphStyle("fr-rep", fontName="Helvetica-Bold", fontSize=9.5, leading=13, textColor=_INK, alignment=TA_RIGHT)
_ST_FR_DEV = ParagraphStyle("fr-dev", fontSize=8.5, leading=11.5, textColor=_INK, alignment=TA_RIGHT)
_ST_FR_ANNEE = ParagraphStyle("fr-annee", fontSize=9, leading=12, textColor=_INK, alignment=TA_LEFT)
_ST_FR_TITRE = ParagraphStyle("fr-titre", fontName="Helvetica-Bold", fontSize=14, leading=18, textColor=_INK, alignment=TA_CENTER)
_ST_FR_SUB = ParagraphStyle("fr-sub", fontSize=9.5, leading=12, textColor=colors.HexColor("#333333"), alignment=TA_CENTER)
_ST_FR_SECT = ParagraphStyle("fr-sect", fontName="Helvetica-Bold", fontSize=11.5, leading=15, textColor=_INK, alignment=TA_LEFT, spaceBefore=12, spaceAfter=6)
_ST_FR_TETE = ParagraphStyle("fr-tete", fontName="Helvetica-Bold", fontSize=8, leading=10, textColor=_INK, alignment=TA_CENTER)
_ST_FR_CELL = ParagraphStyle("fr-cell", fontSize=8.5, leading=10.5, textColor=_INK)
_ST_FR_CELL_SM = ParagraphStyle("fr-cell-sm", fontSize=8, leading=10, textColor=_INK)
_ST_FR_NUM = ParagraphStyle("fr-num", fontSize=8.5, leading=10.5, textColor=_INK, alignment=TA_CENTER)


def _j(d) -> str:
    return d.strftime("%d/%m/%Y") if d else ""


def _entete_fiche_renseignements(data, annee_label: str | None) -> Table:
    academie = _assainir(data.academie) or "______________"
    cap = _assainir(data.cap) or "______________"
    gauche = Table(
        [
            [_text_p("MINISTÈRE DE L'ÉDUCATION NATIONALE", _ST_FR_MINIS)],
            [_text_p(f"ACADÉMIE D'ENSEIGNEMENT DE {academie}", _ST_FR_ORGANE)],
            [_text_p(f"CENTRE D'ANIMATION PÉDAGOGIQUE DE {cap}", _ST_FR_ORGANE)],
            [_text_p(
                f"École dirigée par : <u>{_assainir(data.dirigee_par) or '____________________'}</u>",
                _ST_FR_ORGANE,
            )],
        ],
        colWidths=[100 * mm],
    )
    centre = Table(
        [[_text_p(f"ANNÉE SCOLAIRE {annee_label or '20____-20____'}", _ST_FR_TITRE)],
         [_text_p("(2ème Cycle)", _ST_FR_SUB)]],
        colWidths=[90 * mm],
    )
    centre.setStyle(TableStyle([
        ("BOX", (0, 0), (-1, -1), 2.0, _INK),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("ALIGN", (0, 0), (-1, -1), "CENTER"),
        ("TOPPADDING", (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
    ]))
    droite = Table(
        [
            [_text_p("RÉPUBLIQUE DU MALI", _ST_FR_REP)],
            [_text_p("Un Peuple - Un But - Une Foi", _ST_FR_DEV)],
            [_text_p(f"École : <b>{_assainir(data.ecole) or '______________'}</b>", _ST_FR_REP)],
            [_text_p(f"Tél. : {_assainir(data.telephone) or '______'}", _ST_FR_REP)],
            [_text_p(f"CAP : {cap}", _ST_FR_REP)],
        ],
        colWidths=[83 * mm],
    )
    for part in (gauche, droite):
        part.setStyle(TableStyle([
            ("LEFTPADDING", (0, 0), (-1, -1), 0),
            ("RIGHTPADDING", (0, 0), (-1, -1), 0),
            ("TOPPADDING", (0, 0), (-1, -1), 1),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 1),
        ]))
    entete = Table([[gauche, centre, droite]], colWidths=[100 * mm, 90 * mm, 83 * mm])
    entete.setStyle(TableStyle([
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("LEFTPADDING", (0, 0), (-1, -1), 0),
        ("RIGHTPADDING", (0, 0), (-1, -1), 0),
    ]))
    return entete


def fiche_renseignements_pdf(data, etab: models.Etablissement | None, annee_label: str | None) -> bytes:
    histoire: list = [Spacer(1, 8), _entete_fiche_renseignements(data, annee_label), Spacer(1, 8)]
    histoire += [
        _text_p("FICHE DE RENSEIGNEMENTS DE RENTRÉE", _ST_FR_TITRE),
        Spacer(1, 6),
    ]

    # ── Section I : nombre de cours / effectifs par classe (17 colonnes) ───────
    groupes = [
        ("7ème Année", data.effectifs[0].sept if data.effectifs else None),
        ("8ème Année", data.effectifs[0].huit if data.effectifs else None),
        ("9ème Année", data.effectifs[0].neuf if data.effectifs else None),
        ("TOTAL", data.effectifs[0].total if data.effectifs else None),
    ]
    r0 = [_text_p("Niveau / Statut", _ST_FR_TETE)]
    r1 = [_text_p("", _ST_FR_TETE)]
    for label, _cell in groupes:
        r0 += [_text_p(label, _ST_FR_TETE), *[""] * 3]
        r1 += [_text_p(h, _ST_FR_TETE) for h in ("R C", "G", "F", "T")]
    corps = [r0, r1]

    for ligne in data.effectifs:
        def case(c):
            return [_text_p(str(c.rc), _ST_FR_NUM), _text_p(str(c.garcons), _ST_FR_NUM),
                    _text_p(str(c.filles), _ST_FR_NUM), _text_p(str(c.total), _ST_FR_NUM)]
        corps.append([_text_p(ligne.libelle, _ST_FR_CELL_SM),
                      *case(ligne.sept), *case(ligne.huit), *case(ligne.neuf), *case(ligne.total)])

    sub = 14 * mm
    t1 = Table(corps, colWidths=[61 * mm, *([sub] * 16)], hAlign="CENTER")
    t1.setStyle(TableStyle([
        ("GRID", (0, 0), (-1, -1), 0.6, _SOFT),
        ("LINEBELOW", (0, 0), (-1, 1), 1.2, _INK),
        ("BOX", (0, 0), (-1, -1), 1.0, _INK),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("SPAN", (0, 0), (0, 1)),
        ("SPAN", (1, 0), (4, 0)),
        ("SPAN", (5, 0), (8, 0)),
        ("SPAN", (9, 0), (12, 0)),
        ("SPAN", (13, 0), (16, 0)),
        ("BACKGROUND", (0, 0), (-1, 1), colors.HexColor("#f2f2f2")),
        ("TOPPADDING", (0, 0), (-1, -1), 5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
    ]))
    histoire += [_text_p("I. NOMBRE DE COURS - EFFECTIFS PAR CLASSE", _ST_FR_SECT), t1]

    # ── Section II : liste du personnel administratif et enseignant (17 cols) ──
    entetes2 = ["N°", "PRENOM", "NOM", "GENRE", "N° NINA", "DATE NAISSANCE", "Catégorie", "Classe",
                "Échelon", "Fonction", "SF et nbre Enf", "Date contrat", "Classe Tenue",
                "Dernier Poste", "Date Arrivée CAP", "Observations", "Diplôme"]
    r_h = [Paragraph(h, _ST_FR_TETE) for h in entetes2]
    corps2 = [r_h]
    for idx, p in enumerate(data.personnel, start=1):
        corps2.append([
            Paragraph(str(idx), _ST_FR_NUM),
            Paragraph(_assainir(p.prenom), _ST_FR_CELL_SM),
            Paragraph(_assainir(p.nom), _ST_FR_CELL_SM),
            Paragraph(_assainir(p.genre), _ST_FR_NUM),
            Paragraph(_assainir(p.nina), _ST_FR_CELL_SM),
            Paragraph(_j(p.date_naissance), _ST_FR_NUM),
            Paragraph(_assainir(p.categorie), _ST_FR_CELL_SM),
            Paragraph(_assainir(p.classe), _ST_FR_CELL_SM),
            Paragraph(_assainir(p.echelon), _ST_FR_NUM),
            Paragraph(_assainir(p.fonction), _ST_FR_CELL_SM),
            Paragraph(_assainir(p.sf_nombre_enfants), _ST_FR_CELL_SM),
            Paragraph(_j(p.date_contrat), _ST_FR_NUM),
            Paragraph(_assainir(p.classe_tenue), _ST_FR_CELL_SM),
            Paragraph(_assainir(p.dernier_poste), _ST_FR_CELL_SM),
            Paragraph(_j(p.date_arrivee_cap), _ST_FR_NUM),
            Paragraph(_assainir(p.observations), _ST_FR_CELL_SM),
            Paragraph(_assainir(p.diplome), _ST_FR_CELL_SM),
        ])
    t2 = Table(corps2, colWidths=[11*mm, 17*mm, 17*mm, 14*mm, 17*mm, 19*mm, 14*mm, 13*mm, 13*mm,
                                  16*mm, 17*mm, 19*mm, 19*mm, 13*mm, 19*mm, 15*mm, 20*mm], hAlign="CENTER")
    t2.setStyle(TableStyle([
        ("GRID", (0, 0), (-1, -1), 0.5, _SOFT),
        ("LINEBELOW", (0, 0), (-1, 0), 1.2, _INK),
        ("BOX", (0, 0), (-1, -1), 1.0, _INK),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#f2f2f2")),
        ("TOPPADDING", (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#fafafa")]),
    ]))
    histoire += [_text_p("II. LISTE DU PERSONNEL ADMINISTRATIF ET ENSEIGNANT", _ST_FR_SECT), t2]
    histoire += [Spacer(1, 10), _pied_de_page(etab), Spacer(1, 18)]
    histoire.append(_signatures(["Le Directeur", "La Secrétaire", "Le Président du Matériel"]))
    return _document("Fiche de renseignements de rentrée", histoire, paysage=True)


def _entete_fiche_renseignements_pc(data) -> Table:
    gauche = Table(
        [
            [Paragraph(f"CENTRE D'ANIMATION PÉDAGOGIQUE DE {_assainir(data.cap) or '________________'}", _ST_FR_MINIS)],
            [Paragraph(
                f"COMMUNE DE : <u>{_assainir(data.commune) or '____________'}</u> &nbsp;&nbsp; "
                f"École Fondamentale de : <u>{_assainir(data.ecole) or '____________'}</u>",
                _ST_FR_ORGANE)],
            [Paragraph(
                f"VILLAGE DE : <u>{_assainir(data.village_quartier) or '____________'}</u> &nbsp;&nbsp; "
                f"Dirigée par : <u>{_assainir(data.dirige_par) or '____________________'}</u>",
                _ST_FR_ORGANE)],
            [Paragraph(
                f"ANNÉE SCOLAIRE : {data.annee_label or '20____-20____'} &nbsp;&nbsp;&nbsp;&nbsp; "
                f"Tél : {_assainir(data.telephone) or '__________'}",
                _ST_FR_ORGANE)],
        ],
        colWidths=[220 * mm],
    )
    droite = Table(
        [
            [_text_p("RÉPUBLIQUE DU MALI", _ST_FR_REP)],
            [_text_p("Un Peuple - Un But - Une Foi", _ST_FR_DEV)],
        ],
        colWidths=[53 * mm],
    )
    for part in (gauche, droite):
        part.setStyle(TableStyle([
            ("LEFTPADDING", (0, 0), (-1, -1), 0),
            ("RIGHTPADDING", (0, 0), (-1, -1), 0),
            ("TOPPADDING", (0, 0), (-1, -1), 1),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 1),
        ]))
    entete = Table([[gauche, droite]], colWidths=[220 * mm, 53 * mm])
    entete.setStyle(TableStyle([
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("LEFTPADDING", (0, 0), (-1, -1), 0),
        ("RIGHTPADDING", (0, 0), (-1, -1), 0),
        ("BOX", (0, 0), (-1, -1), 1.0, _INK),
    ]))
    return entete


def fiche_renseignements_premier_cycle_pdf(data, etab: models.Etablissement | None, annee_label: str | None) -> bytes:
    """Tableau de bord recto/verso du 1er cycle (distinct du 2nd cycle)."""
    histoire: list = [Spacer(1, 8), _entete_fiche_renseignements_pc(data), Spacer(1, 8)]

    # ── Section I : nombre de cours / effectifs par classe (1ère→6ème + TOTAL) ─
    def pc(c):
        return [_text_p(str(c.rc), _ST_FR_NUM), _text_p(str(c.garcons), _ST_FR_NUM),
                _text_p(str(c.filles), _ST_FR_NUM), _text_p(str(c.total), _ST_FR_NUM)]

    r0 = [_text_p("Statut / Niveau", _ST_FR_TETE)]
    r1 = [_text_p("", _ST_FR_TETE)]
    for label in ("1ère Année", "2ème Année", "3ème Année", "4ème Année",
                  "5ème Année", "6ème Année", "TOTAL"):
        r0 += [_text_p(label, _ST_FR_TETE), *[""] * 3]
        r1 += [_text_p(h, _ST_FR_TETE) for h in ("N.C", "G", "F", "T")]
    corps = [r0, r1]
    for ligne in data.effectifs:
        corps.append([_text_p(ligne.libelle, _ST_FR_CELL_SM),
                      *pc(ligne.annee_1), *pc(ligne.annee_2), *pc(ligne.annee_3),
                      *pc(ligne.annee_4), *pc(ligne.annee_5), *pc(ligne.annee_6), *pc(ligne.total)])

    sub = 7.5 * mm
    t1 = Table(corps, colWidths=[61 * mm, *([sub] * 28)], hAlign="CENTER")
    t1.setStyle(TableStyle([
        ("GRID", (0, 0), (-1, -1), 0.5, _SOFT),
        ("LINEBELOW", (0, 0), (-1, 1), 1.2, _INK),
        ("BOX", (0, 0), (-1, -1), 1.0, _INK),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("SPAN", (0, 0), (0, 1)),
        ("SPAN", (1, 0), (4, 0)),
        ("SPAN", (5, 0), (8, 0)),
        ("SPAN", (9, 0), (12, 0)),
        ("SPAN", (13, 0), (16, 0)),
        ("SPAN", (17, 0), (20, 0)),
        ("SPAN", (21, 0), (24, 0)),
        ("SPAN", (25, 0), (28, 0)),
        ("BACKGROUND", (0, 0), (-1, 1), colors.HexColor("#f2f2f2")),
        ("TOPPADDING", (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
    ]))
    histoire += [_text_p("I. NOMBRE DE COURS - EFFECTIFS PAR CLASSE", _ST_FR_SECT), t1]

    # ── Infrastructures et mobiliers (à renseigner sur papier) ────────────────
    infra_tetes = [
        Paragraph("Nombre de Salles de Classes Construites en", _ST_FR_TETE), "", "", "", "",
        Paragraph("Direction Construite en", _ST_FR_TETE), "", "", "",
        Paragraph("Mobiliers", _ST_FR_TETE), "", "", "",
    ]
    infra_sous = [Paragraph(h, _ST_FR_TETE) for h in
                  ("Dur", "Semi-dur", "Banco-Tôle", "Autres", "Total",
                   "Dur", "Semi-dur", "Banco-Tôle", "Autres",
                   "TB", "B", "Ch", "Ar")]
    t_infra = Table([infra_tetes, infra_sous, [_text_p("", _ST_FR_NUM)] * 13],
                    colWidths=[22 * mm] * 13, hAlign="CENTER")
    t_infra.setStyle(TableStyle([
        ("GRID", (0, 0), (-1, -1), 0.5, _SOFT),
        ("BOX", (0, 0), (-1, -1), 1.0, _INK),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("SPAN", (0, 0), (4, 0)),
        ("SPAN", (5, 0), (8, 0)),
        ("SPAN", (9, 0), (12, 0)),
        ("BACKGROUND", (0, 0), (-1, 1), colors.HexColor("#f2f2f2")),
        ("TOPPADDING", (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
    ]))
    histoire.append(t_infra)

    # ── Sections II et III : personnel administratif puis enseignant ──────────
    entetes_admin = ["N°", "Prénoms", "Noms", "N° Mle", "Date de Naissance", "Grade", "SF",
                     "Nbre Enf", "Fonction", "Date Recrutement", "Date Titularisation",
                     "Date dern. Avancmt", "Dernier Poste", "Date Arrivée ds le CAP",
                     "Observations / classe tenue", "Diplôme"]
    entetes_ens = ["N°", "Prénoms", "Noms", "N° Mle", "Date de Naissance", "Grade", "SF",
                   "Nbre Enf", "Classes Tenues", "Date Recrutement", "Date Titularisation",
                   "Date dern. Avancmt", "Dernier Poste", "Date Arrivée ds le CAP",
                   "Observations", "Diplôme"]
    largeurs_pc = [10, 20, 20, 17, 20, 15, 12, 15, 18, 19, 19, 19, 19, 16, 17, 17]

    def table_personnel(entetes: list, personnels: list) -> Table:
        ent = [Paragraph(h, _ST_FR_TETE) for h in entetes]
        corps_t = [ent]
        for idx, p in enumerate(personnels, start=1):
            def cell(v: Optional[str]) -> Paragraph:
                return Paragraph(_assainir(v), _ST_FR_CELL_SM) if v else Paragraph("", _ST_FR_CELL_SM)
            def cell_date(d) -> Paragraph:
                return Paragraph(_j(d), _ST_FR_NUM) if d else Paragraph("", _ST_FR_NUM)
            corps_t.append([
                Paragraph(str(idx), _ST_FR_NUM),
                cell(p.prenom), cell(p.nom), cell(p.numero_mle), cell_date(p.date_naissance),
                cell(p.grade), cell(p.sf), cell(p.nbre_enfants),
                cell(len(entetes) == 16 and getattr(p, "classe_tenue", None) or p.fonction),
                cell_date(p.date_recrutement), cell_date(p.date_titularisation),
                cell_date(p.date_dernier_avancement), cell(p.dernier_poste),
                cell_date(p.date_arrivee_cap), cell(p.observations), cell(p.diplome),
            ])
        t = Table(corps_t, colWidths=[w * mm for w in largeurs_pc], hAlign="CENTER")
        t.setStyle(TableStyle([
            ("GRID", (0, 0), (-1, -1), 0.5, _SOFT),
            ("LINEBELOW", (0, 0), (-1, 0), 1.2, _INK),
            ("BOX", (0, 0), (-1, -1), 1.0, _INK),
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#f2f2f2")),
            ("TOPPADDING", (0, 0), (-1, -1), 3),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
        ]))
        return t

    histoire += [_text_p("II. LISTE DU PERSONNEL ADMINISTRATIF (Directeur, Secrétaire, Gardien, .....)", _ST_FR_SECT),
                 table_personnel(entetes_admin, data.personnel_admin)]
    histoire += [_text_p("III. LISTE DU PERSONNEL ENSEIGNANT (Titulaires et Suppléants)", _ST_FR_SECT),
                 table_personnel(entetes_ens, data.personnel_enseignant)]

    # ── NB et signatures ───────────────────────────────────────────────────────
    for note in (
        "NB :",
        "1- Grade (Préciser MP 2-4 ou MPC 2-6)",
        "2- Écrire en rouge les noms des femmes",
        "3- Situation de Famille : M (marié-e), C (célibataire), D (divorcé-e), V (veuve)",
        "4- Observation : Fonctionnaire (F), Fonct de l'Etat (FE), Fonct de Collect. (FC), "
        "Cont. Etat (CE), Cont. Collect (CC), Privée (Cont), Local (L)",
    ):
        histoire.append(_text_p(note, _ST_FR_CELL_SM))
    histoire += [Spacer(1, 12)]
    sig = Table([
        [_text_p("Fiche établie le : _________________", _ST_FR_ORGANE)],
    ], colWidths=[130 * mm])
    sig2 = Table([
        [_text_p("Le Directeur", _ST_FR_REP)],
    ], colWidths=[130 * mm])
    for t in (sig, sig2):
        t.setStyle(TableStyle([
            ("LEFTPADDING", (0, 0), (-1, -1), 0),
            ("RIGHTPADDING", (0, 0), (-1, -1), 0),
            ("TOPPADDING", (0, 0), (-1, -1), 22),
        ]))
    histoire.append(Table([[sig, sig2]], colWidths=[150 * mm, 123 * mm]))
    return _document("Fiche de renseignements 1er cycle", histoire, paysage=True)


# ─── Fiche de notes mensuelle / de composition, élève (doc7 + doc3) ───────────
#
# Carte compacte (cadre arrondi) conforme au modèle « Fiche de Notes Mensuelle » :
# logo circulaire + nom de l'école, « Mois de », tableau Matière/Notes/Coef/
# Observation, totaux, évaluation à cocher en 5 positions, signatures.

_ST_NC_CARD_NOM = ParagraphStyle(
    "nc-card-nom", fontName="Helvetica-Bold", fontSize=14, leading=17, alignment=TA_CENTER, textColor=_INK
)
_ST_NC_CARD_TEL = ParagraphStyle(
    "nc-card-tel", fontSize=9, leading=11.5, alignment=TA_CENTER, textColor=colors.HexColor("#333333")
)
_ST_NC_LOGO = ParagraphStyle(
    "nc-logo", fontName="Helvetica-Bold", fontSize=7, leading=9, alignment=TA_CENTER, textColor=_INK
)
_ST_NC_MOIS = ParagraphStyle(
    "nc-mois", fontName="Helvetica-Bold", fontSize=10.5, leading=13, textColor=_INK, alignment=TA_LEFT
)
_ST_NC_ELEVE = ParagraphStyle(
    "nc-eleve", fontSize=9, leading=12, textColor=_INK, alignment=TA_LEFT
)
_ST_NC_MATIERE = ParagraphStyle(
    "nc-matiere", fontName="Helvetica-Bold", fontSize=9, leading=11.5, textColor=_INK, alignment=TA_LEFT
)
_ST_NC_NUM = ParagraphStyle("nc-num", fontSize=9.5, leading=12, textColor=_INK, alignment=TA_CENTER)
_ST_NC_OBS = ParagraphStyle("nc-obs", fontSize=9, leading=11.5, textColor=_INK, alignment=TA_LEFT)
_ST_NC_RECAP = ParagraphStyle(
    "nc-recap", fontName="Helvetica-Bold", fontSize=9.5, leading=12, textColor=_INK
)
_ST_NC_COCHE = ParagraphStyle(
    "nc-coche", fontSize=8.5, leading=11, textColor=_INK, alignment=TA_CENTER
)


def _logo_circulaire(etab: models.Etablissement | None = None) -> Table:
    logo_flowable = _logo_flowable(etab.logo if etab else None)
    if logo_flowable is not None:
        cadre = Table([[logo_flowable]], colWidths=[17 * mm], rowHeights=[17 * mm])
        cadre.setStyle(TableStyle([
            ("BOX", (0, 0), (-1, -1), 1.0, colors.HexColor("#999999")),
            ("ROUNDEDCORNERS", [8.5, 8.5, 8.5, 8.5]),
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ("ALIGN", (0, 0), (-1, -1), "CENTER"),
            ("LEFTPADDING", (0, 0), (-1, -1), 2),
            ("RIGHTPADDING", (0, 0), (-1, -1), 2),
            ("TOPPADDING", (0, 0), (-1, -1), 2),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 2),
        ]))
        return cadre
    logo = Table([[_text_p("LOGO", _ST_NC_LOGO)]], colWidths=[17 * mm], rowHeights=[17 * mm])
    logo.setStyle(TableStyle([
        ("BOX", (0, 0), (-1, -1), 1.0, colors.HexColor("#999999")),
        ("ROUNDEDCORNERS", [8.5, 8.5, 8.5, 8.5]),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("ALIGN", (0, 0), (-1, -1), "CENTER"),
        ("LEFTPADDING", (0, 0), (-1, -1), 0),
        ("RIGHTPADDING", (0, 0), (-1, -1), 0),
    ]))
    return logo


def fiche_notes_compo_pdf(data, etab: models.Etablissement | None, annee_label: str | None) -> bytes:
    nom_eco = _assainir(etab.nom if etab else None) or "COLLÈGE AUREOLE"
    tel = _assainir(etab.telephone if etab else None) or "(+223) 79 61 88 86 / 90 31 74 86"

    # ── En-tête : logo circulaire + nom + téléphone, séparés par un trait ──────
    titre = Table(
        [
            [_text_p(nom_eco, _ST_NC_CARD_NOM)],
            [_text_p(f"Tél: {tel}", _ST_NC_CARD_TEL)],
        ],
        colWidths=[126 * mm],
    )
    entete = Table([[ _logo_circulaire(etab), titre]], colWidths=[20 * mm, 130 * mm])
    entete.setStyle(TableStyle([
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("LINEBELOW", (0, 0), (-1, -1), 2.0, _INK),
        ("LEFTPADDING", (0, 0), (-1, -1), 0),
        ("RIGHTPADDING", (0, 0), (-1, -1), 0),
        ("TOPPADDING", (0, 0), (-1, -1), 1),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
    ]))

    # ── Mois de + identité de l'élève ──────────────────────────────────────────
    mois = Table(
        [[_text_p(f"Mois de : {_assainir(data.mois) or '_____________________'}", _ST_NC_MOIS)]],
        colWidths=[150 * mm],
    )
    mois.setStyle(TableStyle([("LEFTPADDING", (0, 0), (-1, -1), 0), ("RIGHTPADDING", (0, 0), (-1, -1), 0)]))
    eleve = _text_p(
        "Élève : {p} {n} — {lvl} {cls} — Matricule : {m}".format(
            p=data.prenom or "___", n=data.nom or "___",
            lvl=_assainir(data.niveau), cls=_assainir(data.classe),
            m=data.matricule or "___",
        ).strip(),
        _ST_NC_ELEVE,
    )

    # ── Tableau des notes ──────────────────────────────────────────────────────
    st_tot = ParagraphStyle("nc-tot", fontName="Helvetica-Bold", fontSize=9, leading=11, textColor=_INK)
    corps = [
        [Paragraph("MATIÈRE", ST_HEAD_CELL), Paragraph("NOTES", ST_HEAD_CELL),
         Paragraph("COEF", ST_HEAD_CELL), Paragraph("OBSERVATION", ST_HEAD_CELL)],
    ]
    matieres = list(data.matieres)
    taille = max(len(matieres), 8)
    for i in range(taille):
        if i < len(matieres):
            m = matieres[i]
            corps.append([
                Paragraph(_assainir(m.matiere) or "—", _ST_NC_MATIERE),
                Paragraph(_format2(m.note) if m.note is not None else "", _ST_NC_NUM),
                Paragraph(_format2(m.coef) if m.coef is not None else "", _ST_NC_NUM),
                Paragraph(_assainir(m.observation) or "", _ST_NC_OBS),
            ])
        else:
            corps.append(["", "", "", ""])
    corps.append([
        Paragraph("Total", st_tot),
        Paragraph(_format2(data.total_notes) if data.total_notes is not None else "", _ST_NC_NUM),
        "", "",
    ])
    table = Table(corps, colWidths=[60 * mm, 22 * mm, 22 * mm, 46 * mm], hAlign="CENTER")
    table.setStyle(TableStyle([
        ("GRID", (0, 0), (-1, -1), 1.0, _INK),
        ("SPAN", (0, -1), (0, -1)),
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#dedede")),
        ("BACKGROUND", (0, -1), (-1, -1), colors.HexColor("#f0f0f0")),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("TOPPADDING", (0, 0), (-1, -1), 3),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
    ]))

    # ── Totaux et moyennes ─────────────────────────────────────────────────────
    recap = Table(
        [
            [_text_p("Moyenne : {m}".format(
                m=(f"{_format2(data.moyenne)}/{data.bareme}") if data.moyenne is not None else "_________"), _ST_NC_RECAP),
             _text_p("Rang : {r} / {e}".format(r=data.rang if data.rang is not None else "___",
                                              e=data.effectif if data.effectif else "___"), _ST_NC_RECAP)],
            [_text_p("Moyenne Annuelle : {m}".format(
                m=(f"{_format2(data.moyenne_annuelle)}/{data.bareme}") if data.moyenne_annuelle is not None else "_________"), _ST_NC_RECAP),
             _text_p("Rang : {r} / {e}".format(r=data.rang_annuel if data.rang_annuel is not None else "___",
                                              e=data.effectif_annuel if data.effectif_annuel else "___"), _ST_NC_RECAP)],
        ],
        colWidths=[75 * mm, 75 * mm],
    )
    recap.setStyle(TableStyle([("LEFTPADDING", (0, 0), (-1, -1), 0), ("RIGHTPADDING", (0, 0), (-1, -1), 0)]))

    # ── Appréciations à cocher (5 positions) ───────────────────────────────────
    appr_options = ["Félicitation", "Bien", "Assez-bien", "Passable", "Insuffisant"]
    apprec = Table(
        [
            [_text_p("Appréciation", _ST_NC_MOIS)],
            [_text_p(f"☐ {t}", _ST_NC_COCHE) for t in appr_options],
        ],
        colWidths=[30 * mm] * 5,
    )
    apprec.setStyle(TableStyle([
        ("SPAN", (0, 0), (-1, 0)),
        ("BOX", (0, 0), (-1, -1), 1.0, _INK),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("ALIGN", (0, 0), (0, 0), "CENTER"),
        ("TOPPADDING", (0, 0), (-1, -1), 2),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
        ("LEFTPADDING", (0, 0), (-1, -1), 3),
        ("RIGHTPADDING", (0, 0), (-1, -1), 3),
    ]))

    # ── Signatures ─────────────────────────────────────────────────────────────
    st_sig = ParagraphStyle("nc-sig", fontName="Helvetica-Bold", fontSize=9.5, leading=11.5, alignment=TA_CENTER, textColor=_INK)
    signatures = Table(
        [[Paragraph("Directeur", st_sig), Paragraph("Maître", st_sig), Paragraph("Parents", st_sig)]],
        colWidths=[50 * mm] * 3,
        rowHeights=[14 * mm],
        hAlign="CENTER",
    )
    signatures.setStyle(TableStyle([
        ("VALIGN", (0, 0), (-1, -1), "BOTTOM"),
        ("LINEBELOW", (0, 0), (-1, -1), 0.7, _LINE),
        ("TOPPADDING", (0, 0), (-1, -1), 6),
    ]))

    # ── Carte : cadre arrondi dessiné sur le canvas, contenu en flux libre ─────
    histoire = [
        Spacer(1, 4), entete, Spacer(1, 7), mois, Spacer(1, 3), eleve, Spacer(1, 7), table,
        Spacer(1, 6), recap, Spacer(1, 6), apprec, Spacer(1, 7), signatures,
    ]

    tampon = BytesIO()

    def on_page(canvas, doc):
        canvas.saveState()
        canvas.setStrokeColor(_INK)
        canvas.setLineWidth(1.8)
        canvas.roundRect(
            8 * mm, 8 * mm, A4[0] - 16 * mm, A4[1] - 16 * mm, 6 * mm,
            stroke=1, fill=0,
        )
        canvas.restoreState()

    doc = BaseDocTemplate(
        tampon,
        pagesize=A4,
        leftMargin=14 * mm,
        rightMargin=14 * mm,
        topMargin=14 * mm,
        bottomMargin=14 * mm,
        title="Fiche de notes mensuelle",
        author="College Aureole",
    )
    cadre = Frame(14 * mm, 14 * mm, A4[0] - 28 * mm, A4[1] - 28 * mm, id="card")
    doc.addPageTemplates([PageTemplate(id="card", frames=[cadre], onPage=on_page)])
    doc.build(histoire)
    return tampon.getvalue()
