# Auréole — Frontend

Frontend de gestion scolaire (React + TypeScript + Vite + Tailwind v4), branché sur le
backend FastAPI `backend_corrige`.

## Démarrage

```bash
npm install
cp .env.example .env   # ajuster VITE_API_URL si besoin (par défaut http://localhost:3000, cf. backend_corrige/dev.sh)
npm run dev
```

L'app tourne sur http://localhost:5173. Le backend doit déjà tourner (voir son `dev.sh`)
et autoriser cette origine dans `CORS_ORIGINS`.

## État actuel

**Fondations (posées) :**
- Authentification JWT (`/api/auth/connexion`, `/api/auth/moi`), déconnexion auto sur 401
- Routage protégé par rôle (admin / directeur / comptable), aligné sur les permissions du backend
- Système de design "Auréole" : dark mode premium, palette + typographie dans `src/index.css`
- Layout applicatif (sidebar + topbar), composants UI de base (`src/components/ui`)
- Toutes les routes des 16 modules métier sont câblées (menu + protection par rôle)

**Modules construits :**
- **Élèves** (`src/features/eleves`) : liste avec recherche, création, édition, activation/désactivation, fiche complète (profil, inscriptions, notes, absences, bulletins)

**Modules restants :** Enseignants, Tuteurs, Classes, Cours, Notes, Bulletins, Résultats,
Absences, Inscriptions, Séances, Salles, Paiements, Dépenses, Années scolaires, Comptes
— affichés en placeholder "à construire", à développer un par un sur le même modèle que
le module Élèves (`api.ts` + `types.ts` + page liste + éventuel formulaire).

## Structure

```
src/
  auth/         Contexte d'authentification, routes protégées
  components/   Design system (ui/) et layout applicatif (layout/)
  features/     Un dossier par module métier (api, types, pages)
  lib/          Client API, utilitaires (formatage, hooks)
  pages/        Pages transverses (connexion, dashboard, erreurs)
  routes/       Configuration du menu de navigation par rôle
```
