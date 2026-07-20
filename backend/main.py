import logging
import os
from contextlib import asynccontextmanager

from fastapi import FastAPI, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy import text

from routers import (
    auth,
    classes,
    cours,
    eleves,
    enseignants,
    tuteurs,
    notes,
    annees_scolaires,
    trimestres,
    bulletins, utilisateurs, absences, dashboard,
    inscriptions,
    paiements,
    seances,
    salles,
    depenses,
    resultats,
)
from database import engine, Base, SessionLocal

logging.basicConfig(level=os.getenv("LOG_LEVEL", "INFO"))
logger = logging.getLogger("college_aureole")

# En production, la création/évolution du schéma doit passer par Alembic
# (voir /alembic), jamais par create_all() qui ne migre pas un schéma existant
# et peut masquer des migrations manquantes. Ce comportement reste activé par
# défaut pour ne pas casser un usage local/démo simple, mais on peut le
# désactiver explicitement en production avec AUTO_CREATE_TABLES=false.
AUTO_CREATE_TABLES = os.getenv("AUTO_CREATE_TABLES", "true").strip().lower() not in ("false", "0", "no")


@asynccontextmanager
async def lifespan(app: FastAPI):
    if AUTO_CREATE_TABLES:
        Base.metadata.create_all(bind=engine)
    else:
        logger.info("AUTO_CREATE_TABLES=false : création de schéma ignorée, migrations Alembic attendues.")
    yield


app = FastAPI(title="College Aureole Management API", version="2.2", lifespan=lifespan)

# Origines autorisées configurables via la variable d'environnement CORS_ORIGINS
# (liste séparée par des virgules). Fallback sur les ports de dev Vite.
_default_origins = "http://localhost:5173,http://localhost:5174"
allow_origins = [o.strip() for o in os.getenv("CORS_ORIGINS", _default_origins).split(",") if o.strip()]

app.add_middleware(
    CORSMiddleware,
    allow_origins=allow_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.exception_handler(Exception)
async def unhandled_exception_handler(request, exc):
    # Filet de sécurité pour la production : évite qu'une exception non prévue
    # ne renvoie une stack trace complète au client (fuite d'information),
    # tout en la journalisant côté serveur pour le débogage.
    logger.exception("Erreur non gérée sur %s %s", request.method, request.url.path)
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"detail": "Une erreur interne est survenue."},
    )


# Inclusion des routeurs CRUD complets
app.include_router(auth.router)
app.include_router(annees_scolaires.router)
app.include_router(trimestres.router)
app.include_router(classes.router)
app.include_router(cours.router)
app.include_router(eleves.router)
app.include_router(enseignants.router)
app.include_router(tuteurs.router)
app.include_router(notes.router)
app.include_router(bulletins.router)
app.include_router(utilisateurs.router)
app.include_router(absences.router)
app.include_router(dashboard.router)
app.include_router(inscriptions.router)
app.include_router(paiements.router)
app.include_router(seances.router)
app.include_router(salles.router)
app.include_router(depenses.router)
app.include_router(resultats.router)


@app.get("/")
def health_check():
    # Vérifie réellement la connexion DB (SELECT 1) au lieu de retourner un
    # statut "connected" figé qui masquerait une base indisponible.
    try:
        db = SessionLocal()
        try:
            db.execute(text("SELECT 1"))
            db_status = "connected"
        finally:
            db.close()
    except Exception:
        logger.exception("Health check : échec de connexion à la base de données.")
        db_status = "unavailable"

    return {"status": "running", "database": db_status}
