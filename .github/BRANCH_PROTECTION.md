# Protezione del Branch Main

Questo file contiene le istruzioni per configurare la protezione del branch `main` del repository.

## 🔒 Regole di Protezione del Branch

Il branch `main` è protetto e **non può essere modificato direttamente**. Tutte le modifiche devono passare attraverso **Pull Request** da altri branch.

## ⚙️ Configurazione su GitHub

Per applicare completamente queste regole, un amministratore del repository deve configurare le seguenti impostazioni su GitHub:

### Passaggi per Configurare la Branch Protection:

1. Vai su **Settings** → **Branches** nel repository GitHub
2. Clicca su **Add branch protection rule**
3. Nel campo "Branch name pattern" inserisci: `main`
4. Abilita le seguenti opzioni:

   ✅ **Require a pull request before merging**
   - ✅ Require approvals (consigliato: almeno 1)
   - ✅ Dismiss stale pull request approvals when new commits are pushed
   
   ✅ **Require status checks to pass before merging**
   - ✅ Require branches to be up to date before merging
   
   ✅ **Require conversation resolution before merging**
   
   ✅ **Do not allow bypassing the above settings**
   
   ✅ **Restrict who can push to matching branches**
   - Lascia vuoto per bloccare tutti i push diretti

5. Clicca su **Create** o **Save changes**

## 📋 Workflow di Sviluppo

### Per contribuire al progetto:

1. **Crea un nuovo branch dal main aggiornato:**
   ```bash
   git checkout main
   git pull origin main
   git checkout -b feature/tua-feature
   ```

2. **Effettua le modifiche e committa:**
   ```bash
   git add .
   git commit -m "Descrizione delle modifiche"
   ```

3. **Pusha il branch:**
   ```bash
   git push origin feature/tua-feature
   ```

4. **Crea una Pull Request su GitHub:**
   - Vai su GitHub
   - Clicca su "Pull requests" → "New pull request"
   - Seleziona il tuo branch come source e `main` come target
   - Compila la descrizione e crea la PR

5. **Attendi la review e l'approvazione:**
   - Un altro membro del team revisionerà le modifiche
   - Risolvi eventuali commenti
   - Una volta approvata, la PR può essere mergiata in `main`

## 🚫 Cosa NON fare

❌ **Non eseguire:**
```bash
git checkout main
git commit -m "modifiche dirette"
git push origin main  # Questo verrà BLOCCATO
```

## ✅ Naming Convention per i Branch

Usa nomi descrittivi per i tuoi branch:

- `feature/nome-feature` - Per nuove funzionalità
- `fix/descrizione-fix` - Per correzioni di bug
- `hotfix/issue-critico` - Per fix urgenti
- `docs/aggiornamento-docs` - Per modifiche alla documentazione
- `refactor/nome-refactor` - Per refactoring del codice

## 🔄 Branch Esistenti

- `main` - Branch principale protetto (produzione)
- `dev` - Branch di sviluppo (se presente)

## 📞 Supporto

Per domande sulla branch protection o problemi con le PR, contatta:
- Alessandro Armillotta - a.armillotta91@gmail.com

---

**Nota:** Questa protezione aiuta a mantenere la stabilità del codice in produzione e garantisce che tutte le modifiche siano revisionate prima di essere integrate nel branch principale.
