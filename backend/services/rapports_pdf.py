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




# ─── Carnet scolaire (livret officiel mixte, modèle doc8) ─────────────────────
# 6 pages : couverture A5 rose + état civil A5, scolarité 1er/2ème cycle A4
# paysage, parties médicales A4 paysage, changements d'établissements A4
# paysage, résultats des visites médicales A5. Conforme à la maquette
# officielle « carnet scolaire.html » (Times, couverture rose #f8c8d8).

_CARNET_ROSE = colors.HexColor("#f8c8d8")
_CARNET_BORDURE = colors.HexColor("#8b3a62")

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
_ST_CARNET_ENT_TBL = ParagraphStyle(
    "carnet-top-tbl",
    fontName="Times-Bold",
    fontSize=8,
    leading=10,
    alignment=TA_CENTER,
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



# ─── Fiche de suivi au second cycle (formulaire officiel DEF) ─────────────────

_G_HEAD = ParagraphStyle("fiche-head", fontName="Helvetica-Bold", fontSize=6.5, leading=7.5, alignment=1, textColor=_INK)
_G_CELL = ParagraphStyle("fiche-cell", fontSize=6.5, leading=7, alignment=1, textColor=_INK)
_G_CHAMP_LABEL = ParagraphStyle("fiche-champ-l", fontSize=6, leading=7, textColor=colors.HexColor("#333333"))
_G_CHAMP_VALUE = ParagraphStyle("fiche-champ-v", fontSize=7, leading=8.5, textColor=_INK)
_G_REMARQUE = ParagraphStyle("fiche-remarque", fontSize=7, leading=8.5, textColor=_INK)


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



# ─── Classement des élèves (doc1) ──────────────────────────────────────────────



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




# ─── Rapport succinct de rentrée (doc5) ───────────────────────────────────────

_ST_RR_MINIS = ParagraphStyle("rr-minis", fontName="Helvetica-Bold", fontSize=8.5, leading=11, textColor=_INK, alignment=TA_LEFT)
_ST_RR_ORGANE = ParagraphStyle("rr-organe", fontSize=8.5, leading=11, textColor=colors.HexColor("#333333"), alignment=TA_LEFT)
_ST_RR_TITLE = ParagraphStyle("rr-title", fontName="Helvetica-Bold", fontSize=13, leading=16, textColor=_INK, alignment=TA_CENTER)
_ST_RR_TITLE_SUB = ParagraphStyle("rr-title-sub", fontSize=8.5, leading=11, textColor=colors.HexColor("#333333"), alignment=TA_CENTER)
_ST_RR_REP = ParagraphStyle("rr-rep", fontName="Helvetica-Bold", fontSize=8.5, leading=11, textColor=_INK, alignment=TA_RIGHT)
_ST_RR_DEV = ParagraphStyle("rr-dev", fontSize=8, leading=10, textColor=_INK, alignment=TA_RIGHT)
_ST_RR_ANNEE = ParagraphStyle("rr-annee", fontSize=8.5, leading=11, textColor=_INK, alignment=TA_RIGHT)


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




# ─── Fiche de renseignements de rentrée, 2nd cycle (doc6) ─────────────────────
#
# Formulaire officiel à deux tableaux de 17 colonnes : toujours édité au format
# paysage. Les styles sont volontairement plus grands (polices ≥ 8 pt, paddings
# généreux) pour rester lisibles sur la largeur de 273 mm.

_ST_FR_MINIS = ParagraphStyle("fr-minis", fontName="Helvetica-Bold", fontSize=9.5, leading=13, textColor=_INK, alignment=TA_LEFT)
_ST_FR_ORGANE = ParagraphStyle("fr-organe", fontSize=8.5, leading=11.5, textColor=colors.HexColor("#333333"), alignment=TA_LEFT)
_ST_FR_REP = ParagraphStyle("fr-rep", fontName="Helvetica-Bold", fontSize=9.5, leading=13, textColor=_INK, alignment=TA_RIGHT)
_ST_FR_DEV = ParagraphStyle("fr-dev", fontSize=8.5, leading=11.5, textColor=_INK, alignment=TA_RIGHT)
_ST_FR_TITRE = ParagraphStyle("fr-titre", fontName="Helvetica-Bold", fontSize=14, leading=18, textColor=_INK, alignment=TA_CENTER)
_ST_FR_SUB = ParagraphStyle("fr-sub", fontSize=9.5, leading=12, textColor=colors.HexColor("#333333"), alignment=TA_CENTER)


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

