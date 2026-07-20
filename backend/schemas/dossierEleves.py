from typing import List, Optional

from schemas.eleves import EleveResponse
from schemas.notes import NoteResponse
from schemas.absences import AbsenceResponse
from schemas.inscriptions import InscriptionDetailResponse
from schemas.bulletins import BulletinResponse
from schemas.annees_scolaires import AnneeScolaireResponse
# ClasseResponse/CoursResponse/TrimestreResponse ne sont pas utilisées directement
# dans ce fichier, mais DOIVENT rester importées ici : model_rebuild() ci-dessous
# résout les références différées ("ClasseResponse", "CoursResponse", ...) des
# modèles imbriqués (InscriptionDetailResponse, NoteResponse, ...) en utilisant
# le namespace global de CE module. Les retirer casse le chargement de l'app.
from schemas.classes import ClasseResponse
from schemas.cours import CoursResponse
from schemas.trimestres import TrimestreResponse


class DossierEleveResponse(EleveResponse):
    inscriptions: List[InscriptionDetailResponse] = []
    notes: List[NoteResponse] = []
    absences: List[AbsenceResponse] = []
    bulletins: List[BulletinResponse] = []
    annee_scolaire: Optional[AnneeScolaireResponse] = None


DossierEleveResponse.model_rebuild()