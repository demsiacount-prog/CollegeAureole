-- ─────────────────────────────────────────────────────────────────────────────
-- Initialisation PostgreSQL pour College Aureole (poste-serveur LAN).
--
-- À exécuter UNE SEULE FOIS, lors de l'installation initiale du serveur.
-- NE PAS relancer après coup : le rôle et la base ne se créent qu'une fois.
--
--    psql -U postgres -f backend/scripts/init-db.sql
--
-- Le schéma (tables), lui, est généré et mis à jour automatiquement par le
-- backend à CHAQUE démarrage (migrations Alembic via AUTO_CREATE_TABLES=true) :
-- il est inutile, et contre-productif, de relancer ce script pour cela.
--
-- Le script est néanmoins idempotent (IF NOT EXISTS / \gexec) : le relancer
-- n'endommagerait rien, mais ce n'est pas nécessaire.
--
-- ⚠️ Remplacez le mot de passe ci-dessous par un mot de passe fort, puis
--    renseignez la même valeur dans le formulaire de l'installeur.
-- ─────────────────────────────────────────────────────────────────────────────

-- 1. Rôle (utilisateur) applicatif, si absent
DO $$
BEGIN
  IF NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'collegeaureole') THEN
    CREATE ROLE collegeaureole LOGIN PASSWORD 'ChoisissezUnMotDePasseFort';
  END IF;
END
$$;

-- 2. Base de données, si absente
SELECT 'CREATE DATABASE collegeaureole OWNER collegeaureole'
WHERE NOT EXISTS (SELECT 1 FROM pg_database WHERE datname = 'collegeaureole')
\gexec

-- 3. Propriétaire + droits explicites (robuste même si la base préexistait
--    avec un autre propriétaire ; tout est idempotent, relançable à volonté)
ALTER DATABASE collegeaureole OWNER TO collegeaureole;
GRANT ALL PRIVILEGES ON DATABASE collegeaureole TO collegeaureole;

-- Vérification : doit retourner exactement 1 ligne pour le rôle et 1 pour la base.
SELECT 'role OK'  WHERE EXISTS (SELECT 1 FROM pg_roles     WHERE rolname = 'collegeaureole');
SELECT 'base OK'  WHERE EXISTS (SELECT 1 FROM pg_database  WHERE datname = 'collegeaureole');
