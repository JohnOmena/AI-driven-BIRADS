# Plan 0: Project Setup — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Initialize the project with Git, folder structure, dependencies, updated question table, and base configs.

**Architecture:** Scaffolding plan — creates the directory structure, initializes Git with remote, installs dependencies, and prepares all config files needed by subsequent plans.

**Tech Stack:** Git, Python 3.10+, pip, YAML/JSON configs

**Spec:** `docs/superpowers/specs/2026-04-13-birads-classification-pipeline-design.md`

---

## File Structure

```
AI-driven-BIRADS/
├── .gitignore                          (create)
├── requirements.txt                    (create)
├── configs/
│   ├── question_table/
│   │   └── qt_mass_calc.json           (modify — 13 questions, PT + ES)
│   └── models.yaml                     (create)
├── src/
│   ├── __init__.py                     (create)
│   ├── translation/__init__.py         (create)
│   ├── preprocessing/__init__.py       (create)
│   ├── embedding/__init__.py           (create)
│   ├── qa/__init__.py                  (create)
│   ├── postprocessing/__init__.py      (create)
│   ├── classification/__init__.py      (create)
│   └── evaluation/__init__.py          (create)
├── results/                            (create — empty with .gitkeep)
├── notebooks/                          (create — empty with .gitkeep)
└── tests/
    └── __init__.py                     (create)
```

---

### Task 1: Initialize Git and link remote

**Files:**
- Create: `.gitignore`

- [ ] **Step 1: Initialize Git repository**

Run:
```bash
cd D:/AI-driven-BIRADS
git init
```
Expected: `Initialized empty Git repository`

- [ ] **Step 2: Add remote**

Run:
```bash
git remote add origin https://github.com/JohnOmena/AI-driven-BIRADS.git
```

- [ ] **Step 3: Create .gitignore**

```gitignore
# Python
__pycache__/
*.py[cod]
*$py.class
*.egg-info/
dist/
build/
*.egg
.eggs/

# Virtual environments
venv/
.venv/
env/

# IDE
.vscode/
.idea/
*.swp
*.swo

# OS
.DS_Store
Thumbs.db

# Project specific
results/**/*.npy
results/**/*.pkl
*.env

# Jupyter
.ipynb_checkpoints/

# Large data (keep CSVs tracked)
*.npy
*.pkl
```

- [ ] **Step 4: Stage and commit**

Run:
```bash
git add .gitignore
git commit -m "chore: initialize repo with .gitignore"
```

---

### Task 2: Create project directory structure

**Files:**
- Create: all `__init__.py` files and `.gitkeep` files

- [ ] **Step 1: Create source directories with __init__.py**

Run:
```bash
mkdir -p src/translation src/preprocessing src/embedding src/qa src/postprocessing src/classification src/evaluation
touch src/__init__.py src/translation/__init__.py src/preprocessing/__init__.py src/embedding/__init__.py src/qa/__init__.py src/postprocessing/__init__.py src/classification/__init__.py src/evaluation/__init__.py
```

- [ ] **Step 2: Create tests directory**

Run:
```bash
mkdir -p tests
touch tests/__init__.py
```

- [ ] **Step 3: Create results and notebooks directories with .gitkeep**

Run:
```bash
mkdir -p results notebooks
touch results/.gitkeep notebooks/.gitkeep
```

- [ ] **Step 4: Create configs subdirectories**

Run:
```bash
mkdir -p configs/lexicon configs/classification configs/prompts
```

- [ ] **Step 5: Commit**

Run:
```bash
git add src/ tests/ results/.gitkeep notebooks/.gitkeep configs/lexicon configs/classification configs/prompts
git commit -m "chore: create project directory structure"
```

---

### Task 3: Create requirements.txt

**Files:**
- Create: `requirements.txt`

- [ ] **Step 1: Write requirements.txt**

```txt
# LLM APIs
openai>=1.30.0
google-generativeai>=0.7.0

# Embeddings and NLP
sentence-transformers>=3.0.0
torch>=2.2.0
transformers>=4.40.0

# Data processing
pandas>=2.2.0
numpy>=1.26.0

# Statistical tests
scipy>=1.13.0
scikit-posthocs>=0.9.0

# Classification
scikit-learn>=1.5.0
pgmpy>=0.1.25

# Visualization
matplotlib>=3.9.0
seaborn>=0.13.0

# Notebooks
jupyter>=1.0.0
ipykernel>=6.29.0

# Utilities
pyyaml>=6.0.0
tqdm>=4.66.0
python-dotenv>=1.0.0
```

- [ ] **Step 2: Commit**

Run:
```bash
git add requirements.txt
git commit -m "chore: add requirements.txt with project dependencies"
```

- [ ] **Step 3: Install dependencies**

Run:
```bash
pip install -r requirements.txt
```

Note: This may take several minutes. Verify no errors at the end.

---

### Task 4: Update question table (13 questions, bilingual)

**Files:**
- Modify: `configs/question_table/qt_mass_calc.json`

- [ ] **Step 1: Rewrite qt_mass_calc.json with 13 questions**

Replace the entire file with:

```json
{
  "questions": [
    {
      "id": 1,
      "field": "single_nodule",
      "question_pt": "Temos apenas um nódulo sendo descrito no exame atual?",
      "question_es": "¿Se describe solo un nódulo en el examen actual?",
      "answer_type": "boolean"
    },
    {
      "id": 2,
      "field": "has_calcifications",
      "question_pt": "Há calcificações descritas no exame atual?",
      "question_es": "¿Se describen calcificaciones en el examen actual?",
      "answer_type": "boolean"
    },
    {
      "id": 3,
      "field": "has_mass",
      "question_pt": "Há massa ou nódulo descrito no exame atual?",
      "question_es": "¿Se describe una masa o nódulo en el examen actual?",
      "answer_type": "boolean"
    },
    {
      "id": 4,
      "field": "calc_morph_fine_linear_branching",
      "question_pt": "A morfologia das calcificações é fine linear ou fine-linear branching?",
      "question_es": "¿La morfología de las calcificaciones es fine linear o fine-linear branching?",
      "answer_type": "boolean"
    },
    {
      "id": 5,
      "field": "calc_morph_fine_pleomorphic",
      "question_pt": "A morfologia das calcificações é fine pleomorphic?",
      "question_es": "¿La morfología de las calcificaciones es fine pleomorphic?",
      "answer_type": "boolean"
    },
    {
      "id": 6,
      "field": "calc_morph_typically_benign",
      "question_pt": "As calcificações têm morfologia tipicamente benigna?",
      "question_es": "¿Las calcificaciones tienen morfología típicamente benigna?",
      "answer_type": "boolean"
    },
    {
      "id": 7,
      "field": "calc_dist_segmental",
      "question_pt": "A distribuição das calcificações é segmentar?",
      "question_es": "¿La distribución de las calcificaciones es segmentaria?",
      "answer_type": "boolean"
    },
    {
      "id": 8,
      "field": "calc_dist_linear",
      "question_pt": "A distribuição das calcificações é linear/ductal?",
      "question_es": "¿La distribución de las calcificaciones es lineal/ductal?",
      "answer_type": "boolean"
    },
    {
      "id": 9,
      "field": "calc_dist_grouped",
      "question_pt": "A distribuição das calcificações é agrupada/clustered?",
      "question_es": "¿La distribución de las calcificaciones es agrupada/clustered?",
      "answer_type": "boolean"
    },
    {
      "id": 10,
      "field": "mass_margin_spiculated",
      "question_pt": "A margem da massa ou nódulo é espiculada?",
      "question_es": "¿El margen de la masa o nódulo es espiculado?",
      "answer_type": "boolean"
    },
    {
      "id": 11,
      "field": "mass_shape_irregular",
      "question_pt": "A forma da massa ou nódulo é irregular?",
      "question_es": "¿La forma de la masa o nódulo es irregular?",
      "answer_type": "boolean"
    },
    {
      "id": 12,
      "field": "mass_size_mm",
      "question_pt": "Qual é o tamanho da massa ou nódulo em milímetros?",
      "question_es": "¿Cuál es el tamaño de la masa o nódulo en milímetros?",
      "answer_type": "number"
    },
    {
      "id": 13,
      "field": "nodule_location",
      "question_pt": "Qual a localização do nódulo ou massa na mama?",
      "question_es": "¿Cuál es la ubicación del nódulo o masa en la mama?",
      "answer_type": "categorical"
    }
  ]
}
```

- [ ] **Step 2: Validate JSON**

Run:
```bash
python -c "import json; json.load(open('configs/question_table/qt_mass_calc.json', encoding='utf-8')); print('Valid JSON with', len(json.load(open('configs/question_table/qt_mass_calc.json', encoding='utf-8'))['questions']), 'questions')"
```
Expected: `Valid JSON with 13 questions`

- [ ] **Step 3: Commit**

Run:
```bash
git add configs/question_table/qt_mass_calc.json
git commit -m "feat: update question table to 13 bilingual questions (PT/ES)"
```

---

### Task 5: Create models.yaml config

**Files:**
- Create: `configs/models.yaml`

- [ ] **Step 1: Write models.yaml**

```yaml
models:
  gpt-4o:
    provider: openai
    model_id: gpt-4o-mini-2024-07-18
    api_base: https://api.openai.com/v1
    env_key: OPENAI_API_KEY
    cost_per_1m_input: 0.075
    cost_per_1m_output: 0.60
    cost_limit_usd: 50.00

  gemini-2.0-flash:
    provider: google
    model_id: gemini-2.0-flash
    env_key: GOOGLE_API_KEY
    cost_per_1m_input: 0.0
    cost_per_1m_output: 0.0
    cost_limit_usd: 50.00

  llama-3.3-70b:
    provider: together
    model_id: meta-llama/Llama-3.3-70B-Instruct-Turbo
    api_base: https://api.together.xyz/v1
    env_key: TOGETHER_API_KEY
    cost_per_1m_input: 0.0
    cost_per_1m_output: 0.0
    cost_limit_usd: 50.00

  deepseek-v3:
    provider: openai_compatible
    model_id: deepseek-chat
    api_base: https://api.deepseek.com/v1
    env_key: DEEPSEEK_API_KEY
    cost_per_1m_input: 0.07
    cost_per_1m_output: 1.10
    cost_limit_usd: 50.00

defaults:
  temperature: 0
  num_repetitions: 3
```

- [ ] **Step 2: Create .env.example**

```env
OPENAI_API_KEY=your-key-here
GOOGLE_API_KEY=your-key-here
TOGETHER_API_KEY=your-key-here
DEEPSEEK_API_KEY=your-key-here
```

- [ ] **Step 3: Commit**

Run:
```bash
git add configs/models.yaml .env.example
git commit -m "chore: add models config and .env.example"
```

---

### Task 6: Commit existing data and docs

**Files:**
- Existing: `data/reports_raw_canonical.csv`, `doc/`, `docs/`

- [ ] **Step 1: Stage existing project files**

Run:
```bash
git add data/reports_raw_canonical.csv doc/ docs/
```

- [ ] **Step 2: Commit**

Run:
```bash
git commit -m "chore: add dataset, reference paper, and design spec"
```

- [ ] **Step 3: Push to remote**

Run:
```bash
git branch -M main
git push -u origin main
```

---

### Task 7: Verify setup

- [ ] **Step 1: Verify project structure**

Run:
```bash
find . -type f -not -path './.git/*' -not -path './.claude/*' -not -path './.serena/*' | sort
```

Verify all expected files exist.

- [ ] **Step 2: Verify Python imports work**

Run:
```bash
python -c "import torch; import sentence_transformers; import openai; import google.generativeai; import pandas; import sklearn; import pgmpy; import yaml; print('All imports OK')"
```
Expected: `All imports OK`

- [ ] **Step 3: Verify Git status is clean**

Run:
```bash
git status
git log --oneline
```

Expected: clean working tree, 5-6 commits.
