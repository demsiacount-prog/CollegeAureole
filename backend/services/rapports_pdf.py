"""Génération PDF du relevé de notes (fiche de notes mensuelle / de composition
élève, doc7).

Seul document PDF conservé en dehors des bulletins de notes : la génération est
faite à la demande. Réutilise les blocs et styles de services/pdf.py pour une
maquette cohérente.
"""

from __future__ import annotations

from io import BytesIO

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import mm
from reportlab.platypus import BaseDocTemplate, Frame, PageTemplate, Paragraph, Spacer, Table, TableStyle

import models
from services.pdf import _assainir, _format2, _logo_flowable, _text_p, ST_HEAD_CELL

_INK = colors.HexColor("#111111")
_LINE = colors.HexColor("#999999")


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

