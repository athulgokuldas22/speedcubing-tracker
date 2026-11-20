# Speedcubing Tracker

A small web app for timing 3x3 solves and tracking averages and personal bests.
It runs as two services (`solves` and `stats`), each with its own SQL Server database, plus a static UI.

## Features
- **Solves service:** sessions, timed solves with +2/DNF penalties, and a random-move 3x3 scramble generator. Owns the `sessions` and `solves` tables.
- **Stats service:** WCA-style ao5/ao12/ao100 and personal bests (single, ao5, ao12, ao100). Owns the `personal_bests` table.
- Stats reads solve data only through the solves service: `GET /api/sessions/<id>/times`. If solves is down, stats answers 503 after a 2 s timeout.

## Run
    cp .env.example .env          # change the passwords
    docker compose up --build     # first start takes about 30 s: SQL Server must be healthy before db-init runs

- UI: http://localhost:8080 · solves: http://localhost:8001/health · stats: http://localhost:8002/health
- Each service applies its pending `migrations/*.sql` on startup and records them in `schema_migrations`, so a second start applies nothing.
- Each service's API is described in its `openapi.yaml`.
- Reset the local data: `docker compose down -v` (local only).

Press space to start the timer and space again to stop it.

## Configuration (environment variables)
| Variable | Service | Meaning |
|---|---|---|
| DATABASE_URL | both | `mssql://user:password@host:port/database` |
| SOLVES_URL | stats | Address of the solves service |
| CORS_ORIGINS | both | Addresses allowed to call the service from a browser (the UI) |
| PORT | both | Port to listen on (default 8000) |

Locally the passwords live in `.env` (git-ignored). `.env.example` shows the names.

## API

All paths are on the solves service except `/stats`.

| Method | Path | Purpose |
|---|---|---|
| GET | `/api/scramble` | New random-move scramble |
| GET, POST | `/api/sessions` | List or create sessions |
| GET, POST | `/api/sessions/<id>/solves` | List or add solves |
| PATCH | `/api/solves/<id>` | Set penalty (OK, +2, DNF) |
| DELETE | `/api/solves/<id>` | Delete a solve |
| GET | `/api/sessions/<id>/times` | Effective times for the stats service |
| GET | `/api/sessions/<id>/stats` | Current averages, personal bests, new PBs (stats service) |

## Deployment on Azure
Live: https://agokuldasieu2024ui.z28.web.core.windows.net/

`.github/workflows/cd.yml` runs on every push to `main`. It runs CI (`ci.yml` through `workflow_call`), then points both Container Apps at the images tagged with the commit SHA, writes `ui/config.js` with the services' Azure addresses, uploads `ui/` to the storage static website and waits for `/health` on both services to return 200. It signs in as the managed identity `agokuldas-ieu2024-github` with OIDC, so no Azure password is stored anywhere. Nothing is created or changed by hand after the one-time setup below.

| Resource | Name |
|---|---|
| Resource group | `rg-agokuldas-ieu2024` (France Central) |
| UI (storage static website) | `agokuldasieu2024ui` |
| Pipeline identity | `agokuldas-ieu2024-github` (Contributor on the resource group only) |
| SQL server | `agokuldas-ieu2024-sql` |
| Databases (serverless, free offer) | `agokuldas-ieu2024-solves-db`, `agokuldas-ieu2024-stats-db` |
| Container Apps environment and logs | `agokuldas-ieu2024-env`, `agokuldas-ieu2024-logs` |
| Container Apps | `agokuldas-ieu2024-solves`, `agokuldas-ieu2024-stats` |

### One-time setup (Azure Cloud Shell, Bash)
Passwords were generated in the shell and never written down; `<...>` marks where they go.

```bash
# 1. Subscription, region and names. The region is one from the policy "Allowed resource deployment regions".
az account set --subscription "<Azure for Students subscription id>"
az policy assignment list --query "[?contains(displayName, 'region')].parameters" --output json
PREFIX=agokuldas-ieu2024; RG=rg-$PREFIX; LOCATION=francecentral
UI_STORAGE=agokuldasieu2024ui; SQL_SERVER=$PREFIX-sql; SQL_HOST=$SQL_SERVER.database.windows.net
UI_ORIGIN=https://agokuldasieu2024ui.z28.web.core.windows.net

# 2. Providers and resource group
for p in Microsoft.App Microsoft.OperationalInsights Microsoft.Sql Microsoft.Storage Microsoft.ManagedIdentity; do
  az provider register --namespace "$p"
done
az group create --name "$RG" --location "$LOCATION"

# 3. UI: storage static website
az storage account create --name "$UI_STORAGE" --resource-group "$RG" --location "$LOCATION" --kind StorageV2 --sku Standard_LRS
az storage blob service-properties update --account-name "$UI_STORAGE" --auth-mode key --static-website --index-document index.html

# 4. SQL server, two free serverless databases, one contained user per database
az sql server create --name "$SQL_SERVER" --resource-group "$RG" --location "$LOCATION" \
  --admin-user sqladmin --admin-password "<random admin password>"
az sql server firewall-rule create --resource-group "$RG" --server "$SQL_SERVER" \
  --name AllowAzureServices --start-ip-address 0.0.0.0 --end-ip-address 0.0.0.0
for svc in solves stats; do
  az sql db create --resource-group "$RG" --server "$SQL_SERVER" --name "$PREFIX-$svc-db" \
    --edition GeneralPurpose --compute-model Serverless --family Gen5 --min-capacity 0.5 --capacity 1 \
    --backup-storage-redundancy Local --use-free-limit true --free-limit-exhaustion-behavior AutoPause
done
# The users are created from Cloud Shell, so its IP is allowed only for that and removed straight after.
az sql server firewall-rule create --resource-group "$RG" --server "$SQL_SERVER" --name cloudshell-setup \
  --start-ip-address "<cloud shell ip>" --end-ip-address "<cloud shell ip>"
sqlcmd -S "$SQL_HOST" -d "$PREFIX-solves-db" -U sqladmin -P "<admin password>" -Q \
  "CREATE USER solves_user WITH PASSWORD = '<solves password>'; ALTER ROLE db_ddladmin ADD MEMBER solves_user; ALTER ROLE db_datareader ADD MEMBER solves_user; ALTER ROLE db_datawriter ADD MEMBER solves_user;"
sqlcmd -S "$SQL_HOST" -d "$PREFIX-stats-db" -U sqladmin -P "<admin password>" -Q \
  "CREATE USER stats_user WITH PASSWORD = '<stats password>'; ALTER ROLE db_ddladmin ADD MEMBER stats_user; ALTER ROLE db_datareader ADD MEMBER stats_user; ALTER ROLE db_datawriter ADD MEMBER stats_user;"
az sql server firewall-rule delete --resource-group "$RG" --server "$SQL_SERVER" --name cloudshell-setup

# 5. Container Apps environment (with a logs workspace named with the prefix) and the two apps
az monitor log-analytics workspace create --resource-group "$RG" --workspace-name "$PREFIX-logs" --location "$LOCATION"
az containerapp env create --name "$PREFIX-env" --resource-group "$RG" --location "$LOCATION" \
  --logs-workspace-id "<workspace customer id>" --logs-workspace-key "<workspace key>"
az containerapp create --name "$PREFIX-solves" --resource-group "$RG" --environment "$PREFIX-env" \
  --image mcr.microsoft.com/k8se/quickstart:latest --ingress external --target-port 8000 \
  --min-replicas 0 --max-replicas 1 --cpu 0.25 --memory 0.5Gi \
  --secrets "db-url=mssql://solves_user:<solves password>@$SQL_HOST:1433/$PREFIX-solves-db" \
  --env-vars DATABASE_URL=secretref:db-url CORS_ORIGINS="$UI_ORIGIN"
az containerapp create --name "$PREFIX-stats" --resource-group "$RG" --environment "$PREFIX-env" \
  --image mcr.microsoft.com/k8se/quickstart:latest --ingress external --target-port 8000 \
  --min-replicas 0 --max-replicas 1 --cpu 0.25 --memory 0.5Gi \
  --secrets "db-url=mssql://stats_user:<stats password>@$SQL_HOST:1433/$PREFIX-stats-db" \
  --env-vars DATABASE_URL=secretref:db-url CORS_ORIGINS="$UI_ORIGIN" SOLVES_URL="https://<solves app fqdn>"

# 6. Pipeline identity: Contributor on the resource group only, trusted for runs on main of this repository
az identity create --name "$PREFIX-github" --resource-group "$RG" --location "$LOCATION"
az role assignment create --assignee-object-id "<identity principal id>" --assignee-principal-type ServicePrincipal \
  --role Contributor --scope "<resource group id>"
az identity federated-credential create --name github-main --identity-name "$PREFIX-github" --resource-group "$RG" \
  --issuer https://token.actions.githubusercontent.com --audiences api://AzureADTokenExchange \
  --subject "repo:athulgokuldas22/speedcubing-tracker:ref:refs/heads/main"
az identity federated-credential create --name github-main-ids --identity-name "$PREFIX-github" --resource-group "$RG" \
  --issuer https://token.actions.githubusercontent.com --audiences api://AzureADTokenExchange \
  --subject "repo:athulgokuldas22@232575926/speedcubing-tracker@1407628672:ref:refs/heads/main"

# 7. GitHub secrets and variables (values never written in the repository)
gh secret set AZURE_CLIENT_ID --body "<identity client id>"
gh secret set AZURE_TENANT_ID --body "<tenant id>"
gh secret set AZURE_SUBSCRIPTION_ID --body "<subscription id>"
gh secret set SOLVES_DB_PASSWORD --body "<solves password>"
gh secret set STATS_DB_PASSWORD --body "<stats password>"
gh variable set PREFIX --body "$PREFIX"
gh variable set RESOURCE_GROUP --body "$RG"
gh variable set UI_STORAGE --body "$UI_STORAGE"

# 8. Read access for the professors
for prof in amartini@faculty.ie.edu bserra@faculty.ie.edu; do
  az role assignment create --assignee "$prof" --role Reader --scope "<resource group id>"
done
```

After the first push to `main`, the packages `ghcr.io/athulgokuldas22/speedcubing-solves` and `speedcubing-stats` were made public, so Container Apps can pull them without credentials.

## Tests and coverage
Run in each service folder (`services/solves` or `services/stats`):

    pip install -r requirements-dev.txt
    python -m pytest --cov=app --cov-report=term-missing

The database tests need a SQL Server. CI starts a throwaway one for every run and fails if a service's coverage is under 70%. Locally, without one, the database tests are skipped and the rest still run. To include them, start a SQL Server and point `TEST_DATABASE_URL` at its `master` database:

    docker run -d -p 1433:1433 -e ACCEPT_EULA=Y -e MSSQL_SA_PASSWORD='<a strong password>' mcr.microsoft.com/mssql/server:2022-latest
    export TEST_DATABASE_URL='mssql://sa:<the same password>@localhost:1433/master'

## Project layout
    services/solves/   service 1: sessions, solves, scrambles (Dockerfile, openapi.yaml, app/, migrations/, tests/)
    services/stats/    service 2: averages and personal bests (Dockerfile, openapi.yaml, app/, migrations/, tests/)
    ui/                static timer page, served by nginx
    db/init.sql        creates one database and one login per service
    docker-compose.yml starts SQL Server, db-init, both services and the UI
    system.yaml        every service, its settings, its call across the seam and its Azure resources
    system.schema.json the format system.yaml must follow, provided by the professor (CI validates against it on every push)
    ADR.md  AI_USAGE.md  docs/
