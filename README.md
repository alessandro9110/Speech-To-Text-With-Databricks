# Speech-To-Text con Databricks

## 📝 Descrizione del Progetto

Questo progetto implementa una soluzione avanzata di **Speech-to-Text** (trascrizione vocale automatica) utilizzando Databricks come piattaforma di elaborazione dati. La soluzione sfrutta modelli di machine learning open source, in particolare quelli disponibili tramite Hugging Face, per trasformare file audio in testo con alta precisione e scalabilità.

### Obiettivi

La soluzione tecnologica ha l'obiettivo di:
- Fornire una pipeline scalabile per la trascrizione automatica di file audio
- Utilizzare modelli open source all'avanguardia per il riconoscimento vocale
- Integrare facilmente con l'ecosistema Databricks per elaborazioni su larga scala
- Supportare diverse lingue e formati audio
- Offrire un'architettura modulare e facilmente estensibile

## 🏗️ Architettura

Il progetto è strutturato come **Databricks Asset Bundle**, che fornisce un modo standardizzato per organizzare e distribuire risorse Databricks.

### Componenti Principali

- **Databricks**: Piattaforma unificata di analytics e AI per l'elaborazione distribuita
- **Hugging Face Transformers**: Libreria di modelli pre-addestrati per Speech-to-Text
- **Delta Live Tables (DLT)**: Per la gestione di pipeline ETL affidabili e scalabili
- **Unity Catalog**: Per la gestione centralizzata di dati e governance

### Stack Tecnologico

- **Python 3.10+**: Linguaggio principale per lo sviluppo
- **PySpark**: Per l'elaborazione distribuita dei dati
- **Modelli Open Source**: Whisper, Wav2Vec2, e altri modelli da Hugging Face
- **Databricks Asset Bundles**: Per il deployment e la gestione delle risorse

## ✨ Caratteristiche Principali

- ✅ **Elaborazione distribuita**: Sfrutta la potenza di Spark per processare grandi volumi di audio
- ✅ **Modelli pre-addestrati**: Utilizzo di modelli all'avanguardia da Hugging Face
- ✅ **Pipeline modulari**: Architettura basata su Delta Live Tables per pipeline affidabili
- ✅ **Multi-formato**: Supporto per diversi formati audio (WAV, MP3, FLAC, etc.)
- ✅ **Multi-lingua**: Capacità di trascrivere audio in diverse lingue
- ✅ **Scalabilità**: Elaborazione parallela di migliaia di file audio
- ✅ **Monitoring e governance**: Integrazione con Unity Catalog per tracciabilità completa

## 📋 Prerequisiti

Prima di iniziare, assicurati di avere:

- **Databricks Workspace**: Account Databricks con accesso a workspace
- **Python 3.10 o superiore**: Per lo sviluppo locale
- **Databricks CLI**: Per il deployment degli asset bundle
- **UV Package Manager**: (opzionale) Per la gestione delle dipendenze Python
- **Git**: Per il controllo versione del codice

### Permessi Richiesti

- Permessi di creazione di cluster su Databricks
- Accesso a Unity Catalog per la gestione di cataloghi e schemi
- Permessi di scrittura nello workspace Databricks

## 🚀 Installazione e Setup

### 1. Clonare il Repository

```bash
git clone https://github.com/alessandro9110/Speech-To-Text-With-Databricks.git
cd Speech-To-Text-With-Databricks/speech_to_text_asset_bundle
```

### 2. Installare le Dipendenze

```bash
# Usando uv (consigliato)
pip install uv
uv sync

# Oppure usando pip
pip install -e ".[dev]"
```

### 3. Configurare Databricks CLI

```bash
databricks configure
```

Inserisci i dettagli del tuo workspace Databricks quando richiesto.

### 4. Personalizzare la Configurazione

Modifica il file `databricks.yml` per adattarlo al tuo ambiente:

```yaml
variables:
  catalog: <tuo_catalog>
  schema: <tuo_schema>

workspace:
  host: <tuo_workspace_url>
```

## 📦 Deployment

### Ambiente di Sviluppo

Per deployare nell'ambiente di sviluppo:

```bash
databricks bundle deploy -t dev
```

### Ambiente di Produzione

Per deployare in produzione:

```bash
databricks bundle deploy -t prod
```

## 💻 Utilizzo

### Eseguire una Pipeline

1. **Tramite UI Databricks**:
   - Naviga alla sezione Workflows nel tuo workspace
   - Trova la pipeline `speech_to_text_asset_bundle_etl`
   - Clicca su "Run"

2. **Tramite CLI**:
   ```bash
   databricks bundle run speech_to_text_asset_bundle_etl -t dev
   ```

### Eseguire un Job

```bash
databricks bundle run sample_job -t dev
```

### Notebook di Esempio

Il progetto include un notebook di esempio (`sample_notebook.ipynb`) che mostra come utilizzare le funzionalità della libreria.

## 📁 Struttura del Progetto

```
speech_to_text_asset_bundle/
├── databricks.yml                    # Configurazione principale dell'asset bundle
├── pyproject.toml                    # Dipendenze Python e configurazione del progetto
├── resources/                        # Definizioni delle risorse Databricks
│   ├── sample_job.job.yml           # Definizione job di esempio
│   └── speech_to_text_asset_bundle_etl.pipeline.yml  # Definizione pipeline DLT
├── src/
│   ├── sample_notebook.ipynb        # Notebook di esempio
│   ├── speech_to_text_asset_bundle/ # Package Python principale
│   │   ├── __init__.py
│   │   ├── main.py                  # Entry point principale
│   │   └── taxis.py                 # Moduli di esempio
│   └── speech_to_text_asset_bundle_etl/  # Pipeline ETL
│       ├── README.md
│       └── transformations/         # Trasformazioni DLT
│           ├── sample_trips_speech_to_text_asset_bundle.py
│           └── sample_zones_speech_to_text_asset_bundle.py
└── tests/                           # Test suite
    ├── conftest.py
    └── sample_taxis_test.py
```

## 🔧 Sviluppo

### Eseguire i Test

```bash
pytest tests/
```

### Linting del Codice

```bash
ruff check .
```

### Formattazione del Codice

```bash
ruff format .
```

## 🤝 Contribuire

I contributi sono benvenuti! Per contribuire:

⚠️ **Importante**: Il branch `main` è protetto e non accetta push diretti. Tutte le modifiche devono passare attraverso Pull Request.

1. Fai un fork del repository
2. Crea un branch per la tua feature (`git checkout -b feature/AmazingFeature`)
3. Committa le tue modifiche (`git commit -m 'Add some AmazingFeature'`)
4. Pusha il branch (`git push origin feature/AmazingFeature`)
5. Apri una Pull Request verso il branch `main`
6. Attendi la review e l'approvazione prima del merge

📖 Per maggiori dettagli sulla protezione del branch e il workflow di sviluppo, consulta [Branch Protection Guidelines](.github/BRANCH_PROTECTION.md).

## 📚 Risorse e Riferimenti

### Databricks
- [Documentazione Databricks Asset Bundles](https://docs.databricks.com/dev-tools/bundles/index.html)
- [Delta Live Tables](https://docs.databricks.com/delta-live-tables/index.html)
- [Unity Catalog](https://docs.databricks.com/data-governance/unity-catalog/index.html)

### Hugging Face
- [Hugging Face Transformers](https://huggingface.co/docs/transformers/index)
- [Modelli Speech-to-Text](https://huggingface.co/models?pipeline_tag=automatic-speech-recognition)
- [Whisper by OpenAI](https://huggingface.co/openai/whisper-large-v3)

### Machine Learning per Speech-to-Text
- [Wav2Vec 2.0](https://ai.facebook.com/blog/wav2vec-20-learning-the-structure-of-speech-from-raw-audio/)
- [Documentazione Whisper](https://github.com/openai/whisper)

## 📄 Licenza

Questo progetto è distribuito sotto licenza MIT. Vedi il file `LICENSE` per maggiori dettagli.

## 👥 Autori

- Alessandro Armillotta - [a.armillotta91@gmail.com](mailto:a.armillotta91@gmail.com)

## 🐛 Segnalazione Bug e Feature Request

Per segnalare bug o richiedere nuove funzionalità, apri una issue su GitHub:
https://github.com/alessandro9110/Speech-To-Text-With-Databricks/issues

---

**Nota**: Questo progetto è in fase di sviluppo attivo. Le funzionalità e l'API potrebbero cambiare nelle versioni future.