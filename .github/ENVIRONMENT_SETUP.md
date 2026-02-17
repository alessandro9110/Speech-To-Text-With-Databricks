# GitHub Actions Environment Setup

Questo documento spiega come configurare le variabili e i secret necessari per il workflow `sync_git_folder_dev.yml`.

## Prerequisiti

1. Un service principal Databricks configurato con workload identity federation per GitHub Actions
2. Accesso amministrativo al repository GitHub per configurare gli ambienti

## Configurazione dell'Ambiente "Dev"

Il workflow `sync_git_folder_dev.yml` richiede le seguenti variabili e secret configurati nell'ambiente GitHub chiamato **"Dev"**.

### Passo 1: Creare l'Ambiente

Se l'ambiente "Dev" non esiste già:

1. Vai alle impostazioni del repository GitHub
2. Naviga a **Settings** > **Environments**
3. Clicca su **New environment**
4. Nomina l'ambiente: `Dev`
5. Clicca su **Configure environment**

### Passo 2: Configurare le Variabili

Nell'ambiente "Dev", aggiungi le seguenti **Environment variables**:

| Nome Variabile | Descrizione | Esempio |
|----------------|-------------|---------|
| `DATABRICKS_HOST` | L'URL del workspace Databricks | `https://dbc-3cceb672-6c68.cloud.databricks.com` |

**Come aggiungere:**
1. Nella pagina di configurazione dell'ambiente "Dev"
2. Scorri fino alla sezione **Environment variables**
3. Clicca su **Add variable**
4. Inserisci il nome e il valore
5. Clicca su **Add variable**

### Passo 3: Configurare i Secret

Nell'ambiente "Dev", aggiungi i seguenti **Environment secrets**:

| Nome Secret | Descrizione | Come ottenerlo |
|-------------|-------------|----------------|
| `DATABRICKS_CLIENT_ID` | Il client ID (UUID) del service principal configurato per l'autenticazione OIDC | Ottienilo dalla configurazione del service principal in Databricks |

**Come aggiungere:**
1. Nella pagina di configurazione dell'ambiente "Dev"
2. Scorri fino alla sezione **Environment secrets**
3. Clicca su **Add secret**
4. Inserisci il nome e il valore
5. Clicca su **Add secret**

## Autenticazione OIDC con Databricks

Il workflow utilizza GitHub OIDC (OpenID Connect) per autenticarsi con Databricks, che è un metodo più sicuro rispetto all'uso di token a lungo termine.

### Requisiti per OIDC:

1. **Service Principal in Databricks**: Devi avere un service principal configurato nel tuo account Databricks
2. **Federation Policy**: Il service principal deve avere una policy di federazione che permette l'accesso da GitHub Actions

### Configurazione del Service Principal (se non già fatto):

```bash
# Crea una federation policy per il service principal
databricks account service-principal-federation-policy create <SERVICE_PRINCIPAL_ID> --json '{
  "oidc_policy": {
    "issuer": "https://token.actions.githubusercontent.com",
    "audiences": [ "<DATABRICKS_ACCOUNT_ID>" ],
    "subject": "repo:<GITHUB_ORG>/<GITHUB_REPO>:environment:Dev"
  }
}'
```

**Nota**: Sostituisci `<GITHUB_ORG>/<GITHUB_REPO>` con `alessandro9110/Speech-To-Text-With-Databricks` per questo repository.

## Verifica della Configurazione

Dopo aver configurato le variabili e i secret:

1. Vai alla tab **Actions** nel repository
2. Trova il workflow "Sync Git Folder Dev"
3. Se necessario, esegui manualmente il workflow per testare la configurazione
4. Verifica che il workflow completi con successo

## Risoluzione dei Problemi

### Errore: "DATABRICKS_HOST is not set"
- Verifica che la variabile `DATABRICKS_HOST` sia configurata nell'ambiente "Dev"
- Assicurati che il nome dell'ambiente nel workflow corrisponda esattamente a quello configurato

### Errore: "DATABRICKS_CLIENT_ID is not set"
- Verifica che il secret `DATABRICKS_CLIENT_ID` sia configurato nell'ambiente "Dev"
- Assicurati che il valore sia corretto

### Errore di autenticazione OIDC
- Verifica che il service principal abbia la federation policy configurata correttamente
- Verifica che il `subject` nella policy corrisponda al pattern del repository e dell'ambiente
- Assicurati che le permission `id-token: write` siano impostate nel workflow (già presente)

## Riferimenti

- [Databricks - Enable workload identity federation for GitHub Actions](https://docs.databricks.com/dev-tools/auth/provider-github)
- [GitHub Docs - Using environments for deployment](https://docs.github.com/en/actions/deployment/targeting-different-environments/using-environments-for-deployment)
- [GitHub Docs - Configuring OpenID Connect in cloud providers](https://docs.github.com/en/actions/deployment/security-hardening-your-deployments/configuring-openid-connect-in-cloud-providers)
