-- Idempotent: safe to run on every `docker compose up`.
-- sqlcmd variables SOLVES_PWD and STATS_PWD are passed with -v.
IF DB_ID('solves') IS NULL CREATE DATABASE solves;
IF DB_ID('stats') IS NULL CREATE DATABASE stats;
GO

IF SUSER_ID('solves_user') IS NULL CREATE LOGIN solves_user WITH PASSWORD = '$(SOLVES_PWD)', CHECK_POLICY = OFF;
IF SUSER_ID('stats_user') IS NULL CREATE LOGIN stats_user WITH PASSWORD = '$(STATS_PWD)', CHECK_POLICY = OFF;
GO

-- Each login can only reach its own database.
USE solves;
GO
IF USER_ID('solves_user') IS NULL CREATE USER solves_user FOR LOGIN solves_user;
ALTER ROLE db_ddladmin ADD MEMBER solves_user;
ALTER ROLE db_datareader ADD MEMBER solves_user;
ALTER ROLE db_datawriter ADD MEMBER solves_user;
GO

USE stats;
GO
IF USER_ID('stats_user') IS NULL CREATE USER stats_user FOR LOGIN stats_user;
ALTER ROLE db_ddladmin ADD MEMBER stats_user;
ALTER ROLE db_datareader ADD MEMBER stats_user;
ALTER ROLE db_datawriter ADD MEMBER stats_user;
GO
