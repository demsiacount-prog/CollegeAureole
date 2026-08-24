# Auréole — Frontend

Frontend de gestion scolaire (React + TypeScript + Vite + Tailwind v4), branché sur le
backend FastAPI (`backend`).

## Démarrage

```bash
npm install
cp .env.example .env   # VITE_API_URL ne sert qu'au dev (vite : http://localhost:3000).
npm run dev
```

L'app tourne sur http://localhost:5173. Le backend FastAPI doit tourner en parallèle
(`cd backend && uvicorn main:app --reload --port 3000`) ; la proxy Vite redirige
`/api` et `/uploads` vers `http://localhost:3000`, et CORS est déjà configuré
pour l'origine Vite.

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
