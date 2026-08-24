"""Export complet de la base → XLSX (un onglet par table)."""
import io
from datetime import date, datetime, time
from decimal import Decimal

from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse
from openpyxl import Workbook
from sqlalchemy.orm import Session

from database import get_db
import models
from security import require_role

router = APIRouter(
    prefix="/api/import-export",
    tags=["Import / Export"],
    dependencies=[Depends(require_role("admin"))],
)


# ── Ordre d'export/import (respects FK) ──────────────────────────────
_TABLES = [
    ("etablissement",       models.Etablissement),
    ("utilisateurs",        models.Utilisateurs),
    ("annees_scolaires",    models.AnneesScolaires),
    ("trimestres",          models.Trimestres),
    ("tuteurs",             models.Tuteurs),
    ("enseignants",         models.Enseignants),
    ("salles",              models.Salles),
    ("classes",             models.Classes),
    ("cours",               models.Cours),
    ("classe_cours",        models.AffectationCoursClasse),
    ("eleves",              models.Eleves),
    ("inscriptions",        models.Inscriptions),
    ("echeances",           models.Echeances),
    ("paiements",           models.Paiements),
    ("remises",             models.Remises),
    ("notes",               models.Notes),
    ("absences",            models.Absences),
    ("bulletins",           models.Bulletins),
    ("bulletin_details",    models.BulletinDetails),
    ("depenses",            models.Depenses),
    ("documents",           models.Documents),
    ("seances",             models.Seances),
]

# Colonnes à ignorer lors de l'export/import (données binaires volumineuses)
_SKIP_EXPORT = {
    "documents": {"contenu"},
}

# Colonnes dont la valeur est auto-générée par un before_insert :
# on les inclut dans l'export (données existantes) mais on les restaure
# aussi lors de l'import via Core insert (bypass ORM).
_AUTO_GEN_COLUMNS = {
    "eleves":       {"matricule"},
    "enseignants":  {"matricule"},
    "classes":      {"code_classe"},
    "cours":        {"code_cours"},
    "tuteurs":      {"code_tuteur"},
    "salles":       {"code_salle"},
    "depenses":     {"code_depense"},
    "inscriptions": {"code_inscription"},
    "paiements":    {"code_paiement"},
}


# ── Serialisation ─────────────────────────────────────────────────────

def _cell_value(v):
    """Convertit une valeur Python en chose lisible par openpyxl."""
    if v is None:
        return None
    if isinstance(v, bool):
        return v
    if isinstance(v, (date, datetime)):
        return v.isoformat()
    if isinstance(v, time):
        return v.strftime("%H:%M:%S")
    if isinstance(v, Decimal):
        return float(v)
    if hasattr(v, "value"):
        return v.value
    return v


# ── EXPORT ────────────────────────────────────────────────────────────

@router.get("/export")
def exporter(db: Session = Depends(get_db)):
    wb = Workbook()
    wb.remove(wb.active)

    for sheet_name, model_cls in _TABLES:
        ws = wb.create_sheet(title=sheet_name)
        table = model_cls.__table__
        skip = _SKIP_EXPORT.get(sheet_name, set())

        colonnes = [c.name for c in table.columns if c.name not in skip]
        ws.append(colonnes)

        rows = db.query(model_cls).all()
        for obj in rows:
            ws.append([_cell_value(getattr(obj, c)) for c in colonnes])

    buf = io.BytesIO()
    wb.save(buf)
    buf.seek(0)

    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    return StreamingResponse(
        buf,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": f'attachment; filename="collegeaureole_export_{ts}.xlsx"'},
    )
