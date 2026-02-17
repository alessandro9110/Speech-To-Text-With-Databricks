# 🔧 Guida alla Configurazione della Protezione del Branch Main

Questa guida fornisce istruzioni passo-passo per l'amministratore del repository per attivare completamente la protezione del branch `main`.

## 📋 Prerequisiti

- Permessi di amministratore sul repository GitHub
- Accesso alle impostazioni del repository

---

## ⚙️ Configurazione Branch Protection su GitHub

### Passo 1: Accedere alle Impostazioni del Branch

1. Vai al repository su GitHub: https://github.com/alessandro9110/Speech-To-Text-With-Databricks
2. Clicca sulla tab **Settings** (Impostazioni)
3. Nel menu laterale sinistro, clicca su **Branches** sotto "Code and automation"

### Passo 2: Aggiungere una Regola di Protezione

1. Nella sezione "Branch protection rules", clicca su **Add branch protection rule**
2. Nel campo **Branch name pattern**, inserisci: `main`

### Passo 3: Configurare le Regole di Protezione

Abilita le seguenti opzioni (seleziona le checkbox):

#### ✅ Require a pull request before merging
Questa è l'impostazione principale che blocca i push diretti.

- **Require approvals**: Seleziona questa opzione
  - Imposta **Required number of approvals before merging** a `1` (o più se preferisci)
- **Dismiss stale pull request approvals when new commits are pushed**: ✅ Abilitato
- **Require review from Code Owners**: ✅ Abilitato (utilizzerà il file `.github/CODEOWNERS`)

#### ✅ Require status checks to pass before merging
Richiede che i test e i controlli automatici passino prima del merge.

- **Require branches to be up to date before merging**: ✅ Abilitato

#### ✅ Require conversation resolution before merging
Tutti i commenti della review devono essere risolti prima del merge.

#### ✅ Require signed commits (Opzionale)
Se vuoi richiedere commit GPG firmati, abilita questa opzione.

#### ✅ Require linear history (Opzionale)
Previene merge commits, richiedendo rebase o squash merge.

#### ✅ Include administrators
**IMPORTANTE**: Abilita questa opzione per applicare le regole anche agli amministratori.
Questo garantisce che nessuno, nemmeno gli admin, possa bypassare la protezione.

#### ❌ Allow force pushes
Lascia **DISABILITATO** per prevenire force push al branch main.

#### ❌ Allow deletions
Lascia **DISABILITATO** per prevenire l'eliminazione del branch main.

### Passo 4: Salvare la Configurazione

1. Scorri fino in fondo alla pagina
2. Clicca su **Create** (o **Save changes** se stai modificando una regola esistente)

---

## 🔐 Configurazione CODEOWNERS (già completato)

Il file `.github/CODEOWNERS` è già stato creato e configurato. Questo file:
- Specifica chi è responsabile per il codice
- Richiede automaticamente review dai code owners quando viene creata una PR
- Funziona automaticamente una volta che la branch protection è attivata

---

## 🤖 GitHub Actions (già configurato)

È stato creato un workflow GitHub Actions (`.github/workflows/enforce-branch-protection.yml`) che:
- Si attiva su ogni push diretto al branch `main`
- Blocca il push con un messaggio di errore chiaro
- Fornisce istruzioni su come procedere correttamente

Questo workflow fornisce un ulteriore livello di protezione.

---

## ✅ Verifica della Configurazione

Dopo aver completato la configurazione, verifica che funzioni:

### Test 1: Tentativo di Push Diretto (dovrebbe fallire)
```bash
git checkout main
echo "test" >> test.txt
git add test.txt
git commit -m "Test direct push"
git push origin main
```
**Risultato atteso**: Il push dovrebbe essere bloccato con un messaggio di errore.

### Test 2: Pull Request (dovrebbe funzionare)
```bash
git checkout -b test-branch
echo "test" >> test.txt
git add test.txt
git commit -m "Test via PR"
git push origin test-branch
# Crea una PR su GitHub
```
**Risultato atteso**: Il push funziona e puoi creare una PR.

---

## 📊 Riepilogo delle Protezioni Implementate

| Protezione | Stato | Descrizione |
|------------|-------|-------------|
| Branch Protection Rules | ⚙️ Da configurare | Regole su GitHub Settings |
| CODEOWNERS | ✅ Configurato | File `.github/CODEOWNERS` |
| GitHub Actions Workflow | ✅ Configurato | Workflow che blocca push diretti |
| PR Template | ✅ Configurato | Template per le Pull Request |
| Documentazione | ✅ Configurato | File `BRANCH_PROTECTION.md` |
| README aggiornato | ✅ Configurato | Sezione "Contribuire" aggiornata |

---

## 🆘 Troubleshooting

### Problema: Gli amministratori possono ancora pushare direttamente
**Soluzione**: Verifica che l'opzione "Include administrators" sia abilitata nelle branch protection rules.

### Problema: Le PR non richiedono review
**Soluzione**: Verifica che "Require approvals" sia abilitato e impostato a 1 o più.

### Problema: CODEOWNERS non funziona
**Soluzione**: Verifica che:
1. Il file `.github/CODEOWNERS` sia presente
2. L'opzione "Require review from Code Owners" sia abilitata
3. Gli username nel file CODEOWNERS siano corretti

---

## 📚 Risorse Utili

- [Documentazione GitHub - Branch Protection](https://docs.github.com/en/repositories/configuring-branches-and-merges-in-your-repository/managing-protected-branches/about-protected-branches)
- [Documentazione GitHub - CODEOWNERS](https://docs.github.com/en/repositories/managing-your-repositorys-settings-and-features/customizing-your-repository/about-code-owners)
- [Documentazione GitHub Actions - Workflow Syntax](https://docs.github.com/en/actions/using-workflows/workflow-syntax-for-github-actions)

---

## ✉️ Supporto

Per assistenza o domande sulla configurazione:
- Email: a.armillotta91@gmail.com
- Apri una issue: https://github.com/alessandro9110/Speech-To-Text-With-Databricks/issues

---

**Ultimo aggiornamento**: 2026-02-17
