# models/__init__.py
from models.tuteurs import Tuteurs
from models.enseignants import Enseignants
from models.utilisateurs import Utilisateurs
from models.annees_scolaires import AnneesScolaires
from models.trimestres import Trimestres
from models.classes import Classes
from models.associations import AffectationCoursClasse
from models.cours import Cours
from models.eleves import Eleves
from models.notes import Notes
from models.bulletins import Bulletins, BulletinDetails
from models.absences import Absences
from models.inscriptions import Inscriptions
from models.echeances import Echeances
from models.paiements import Paiements
from models.remises import Remises
from models.salles import Salles
from models.seances import Seances
from models.depenses import Depenses
from models.documents import Documents
from models.etablissement import Etablissement
__all__ = [
    "Tuteurs", "Enseignants", "Utilisateurs",
    "AnneesScolaires", "Trimestres", "Classes", "AffectationCoursClasse", "Cours",
    "Eleves", "Notes", "Bulletins", "BulletinDetails",
    "Absences", "Inscriptions", "Echeances", "Paiements", "Remises",
    "Salles", "Seances", "Depenses", "Documents", "Etablissement",
]
