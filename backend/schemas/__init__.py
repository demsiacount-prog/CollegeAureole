# schemas/__init__.py
from schemas.tuteurs import TuteurCreate, TuteurResponse, TuteurDetailResponse
from schemas.enseignants import EnseignantCreate, EnseignantResponse
from schemas.absences import (
    AbsenceBase, AbsenceCreate, AbsenceResponse,
    AbsenceJustifierRequest, AlerteAbsenceEleve,
)
from schemas.utilisateurs import (
    UtilisateurConnexion, UtilisateurChangerMotDePasse,
    UtilisateurCreate, UtilisateurStatutUpdate,
    UtilisateurReinitialiserMotDePasse,
    UtilisateurResponse, TokenResponse,
)
from schemas.dashboard import DashboardStatsResponse
from schemas.annees_scolaires import AnneeScolaireCreate, AnneeScolaireResponse, AnneeScolaireDetailResponse
from schemas.trimestres import TrimestreCreate, TrimestreResponse, TrimestreDetailResponse, TrimestresGenererRequest, TrimestresGenererResponse
from schemas.classes import ClasseCreate, ClasseResponse, ClasseDetailResponse
from schemas.salles import SalleCreate, SalleResponse
from schemas.cours import (
    CoursCreate, CoursResponse, AffectationCoursClasseInput, AffectationCoursClasseResponse,
)
from schemas.eleves import EleveCreate, EleveResponse
from schemas.notes import (
    NoteCreate, NoteResponse, NotePatch, NoteBulkItem, NoteBulkRequest, NoteBulkResponse,
)
from schemas.registre_notes import (
    RegistreNotesResponse, RegistreEleve, RegistreNoteLigne, RegistreTrimestre, RegistreCours,
)
from schemas.bulletins import (
    BulletinDetailResponse, BulletinGenerateRequest, BulletinGenerateClasseRequest,
    BulletinPublierRequest, BulletinResponse, BulletinDetailFullResponse,
)
from schemas.bulletins_annuels import BulletinAnnuelResponse, BulletinAnnuelBloc, BulletinAnnuelLigne
from schemas.paiements import PaiementResponse, PaiementStatsResponse
from schemas.inscriptions import (
    InscriptionCreate, InscriptionUpdate, InscriptionResponse, InscriptionDetailResponse,
    MoyenneTrimestre, PassageAnneeRequest, PassageAnneeResponse,
    DossierCompletCreate,
)
from schemas.seances import SeanceCreate, SeanceUpdate, SeanceResponse, SeanceDetailResponse
from schemas.dossierEleves import DossierEleveResponse
from schemas.noteParMatieres import NoteParMatiere
from schemas.dossierEnseignants import (
    DossierEnseignantResponse, HistoriqueAnneeResponse, AffectationResponse, StatsEnseignantResponse,
)
from schemas.echeances import PaiementEcheanceCreate, PaiementUpdate, EcheanceResponse, RelanceResponse, PaiementResultResponse
from schemas.remises import RemiseCreate, RemiseResponse, PaiementGroupeCreate
from schemas.depenses import DepenseCreate, DepenseUpdate, DepenseResponse
from schemas.cloture import (
    CloturePreviewResponse, NouvelleAnneePayload,
    ClotureExecuterPayload, ClotureExecuterResponse,
    CompteursPreview,ElevePreview,AnneeInfo,RapportCloture,EleveCloture
)
from schemas.documents import DocumentResponse, DocumentRead, DocumentUpdate, DocumentListeResponse
from schemas.rapports import (
    FicheSuiviResponse,
    FicheSuiviPassage, FicheSuiviLigne, ParcoursAnnee,
    EleveMoyenne, ClasseMoyennes, RapportMoyennesResponse,
    EleveProposition, ClasseProposition, PropositionPassageResponse,
)
from schemas.etablissement import (
    EtablissementUpdate, EtablissementResponse,
    EtablissementInfrastructuresPayload, EtablissementInfrastructuresResponse,
)
from schemas.effectifs import (
    ClassementEleve, ClassementClasseResponse, ClassementResponse,
    RapportRentreeClasse, RapportRentreeCycle, RapportRentreeResponse,
    FicheRenseignementsCellule, FicheRenseignementsLigne,
    FicheRenseignementsPersonnel, FicheRenseignementsResponse,
    FicheRensPCLigne, FicheRensPCPersonnel, FicheRenseignementsPremierCycleResponse,
    FicheNotesCompoMatiere, FicheNotesCompoResponse,
)

# Résolution des forward references — l'ordre compte (dépendances d'abord)
ClasseResponse.model_rebuild()
CoursResponse.model_rebuild()
EleveResponse.model_rebuild()
ClasseDetailResponse.model_rebuild()
NoteResponse.model_rebuild()
NoteBulkResponse.model_rebuild()
AnneeScolaireDetailResponse.model_rebuild()
TrimestreDetailResponse.model_rebuild()
BulletinDetailFullResponse.model_rebuild()
AbsenceResponse.model_rebuild()
InscriptionDetailResponse.model_rebuild()
SeanceDetailResponse.model_rebuild()
TuteurDetailResponse.model_rebuild()
FicheSuiviResponse.model_rebuild()
