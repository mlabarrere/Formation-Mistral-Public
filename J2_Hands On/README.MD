# 🧪 Jour 2 — LangChain Hands On avec Mistral AI

Neuf ateliers guidés mènent d'un premier agent jusqu'à l'interaction humaine, en
français et pas à pas. On y passe d'une simple fonction Python à un agent capable
d'utiliser des outils, de mémoriser un fil, de structurer sa réponse, d'adapter son
contexte et de demander une validation humaine.

🎯 **Public** : adultes débutants en LangChain, déjà à l'aise avec les bases de
Python. Chaque atelier dure **30 à 45 minutes** et utilise Mistral AI via les APIs
LangChain actuelles.

## 🗺️ Parcours

| Notebook | Question à laquelle il répond |
|---|---|
| `Atelier 1 - Premier agent SQL.ipynb` | Comment construire un premier agent en quelques lignes ? |
| `Atelier 2 - Messages.ipynb` | Comment LangChain représente-t-il une conversation ? |
| `Atelier 3 - Streaming.ipynb` | Comment afficher une réponse au fil de l'eau ? |
| `Atelier 4 - Tools.ipynb` | Comment un modèle choisit-il puis appelle-t-il une fonction Python ? |
| `Atelier 5 - Tools MCP.ipynb` | Comment découvrir des outils fournis par un serveur MCP ? |
| `Atelier 6 - Memoire.ipynb` | Comment conserver l'état d'un fil sans mélanger deux utilisateurs ? |
| `Atelier 7 - Sortie structuree.ipynb` | Comment obtenir une réponse validée plutôt qu'un texte libre ? |
| `Atelier 8 - Prompt dynamique.ipynb` | Comment adapter le prompt au contexte de l'utilisateur ? |
| `Atelier 9 - Human-in-the-loop.ipynb` | Comment interrompre une action et attendre une décision humaine ? |

## 📁 Structure du dossier

- `data/` — la base de démonstration `Chinook.db` (SQLite, lecture seule).
- `util/` — utilitaires importés par les notebooks (`env_utils.py`, `sql_db.py`).
- `assets/` — images affichées dans les notebooks.
- `studio/` — agent SQL prêt pour **LangGraph Studio** (débogueur visuel, bonus).

## 🛠️ Prérequis

- [Git](https://git-scm.com/install/) ;
- [uv](https://docs.astral.sh/uv/getting-started/installation/), qui fournit aussi
  `uvx` (utilisé par l'Atelier 5) ;
- une clé **Mistral** et l'URL du serveur compatible avec l'API Mistral ;
- un compte **LangSmith** (gratuit) pour la traçabilité — voir plus bas ;
- aucune installation Python manuelle : `uv` installe Python 3.13 si nécessaire.

Le Jour 2 possède son propre environnement `J2_Hands On/.venv`. Il ne modifie pas
le `.venv` racine utilisé par les autres journées. 🛡️

## 🚀 Installation reproductible

Placez-vous dans ce dossier, puis exécutez exactement :

```powershell
uv python install 3.13
uv lock --upgrade --resolution highest --prerelease disallow --python 3.13
uv sync --frozen --python 3.13
uv lock --check
uv pip check --python ".venv\Scripts\python.exe"
```

`uv.lock` fige aussi les dépendances transitives : deux participants obtiennent la
même combinaison de bibliothèques.

## 🔐 Variables d'environnement (dont LangSmith)

Copiez `example.env` vers `.env` et renseignez vos valeurs (le `.env` ne doit jamais
être versionné) :

```bash
cp example.env .env
```

| Variable | Rôle |
|---|---|
| `MISTRAL_API_KEY` | **obligatoire** — clé d'accès au serveur Mistral. |
| `MISTRAL_SERVER_URL` | **obligatoire** — URL du serveur Mistral (se termine par `/v1`). |
| `LANGSMITH_API_KEY` | traçabilité LangSmith (voir ci-dessous). |
| `LANGSMITH_TRACING` | `true` pour envoyer les traces à LangSmith. |
| `LANGSMITH_PROJECT` | nom du projet où regrouper les traces. |

Le moyen le plus simple, valable pour les neuf notebooks, est d'exporter ces
variables dans le shell avant de lancer Jupyter. Les Ateliers 1 à 3 chargent en plus
un `.env` s'il existe (via `python-dotenv`). Aucune valeur secrète n'est jamais
affichée.

PowerShell :

```powershell
$env:MISTRAL_API_KEY = Read-Host -Prompt "Cle Mistral" -MaskInput
$env:MISTRAL_SERVER_URL = "https://votre-serveur.example/v1"
$env:LANGSMITH_API_KEY = Read-Host -Prompt "Cle LangSmith" -MaskInput
$env:LANGSMITH_TRACING = "true"
$env:LANGSMITH_PROJECT = "formation-mistral-j2"
```

### 🔎 Créer un compte LangSmith

1. Créez un compte gratuit sur [smith.langchain.com](https://smith.langchain.com/).
2. Générez une **API key** (menu *Settings → API Keys*).
3. Renseignez `LANGSMITH_API_KEY`, mettez `LANGSMITH_TRACING=true`, puis relancez le
   kernel. Vos exécutions apparaissent dans le projet `LANGSMITH_PROJECT` : vous y
   voyez chaque appel d'outil, chaque message et le détail des tokens.

## ▶️ Lancer Jupyter

Depuis `J2_Hands On` :

```powershell
uv run jupyter lab
```

Lancé ainsi, le kernel **Python 3 (J2 Hands On)** par défaut est déjà celui du
`.venv` J2 (Python 3.13) : les notebooks s'ouvrent prêts à l'emploi.

## 🎛️ LangGraph Studio en local (bonus)

Le dossier `studio/` contient un agent SQL prêt pour **LangGraph Studio**, un
débogueur visuel qui affiche le graphe de l'agent et chaque étape de raisonnement.

Depuis `J2_Hands On` :

```powershell
# 1) Fournir les variables au studio (créez studio/.env avec vos clés)
Copy-Item .env studio\.env   # si vous utilisez un fichier .env

# 2) Lancer le serveur de dev (langgraph-cli est déjà installé)
cd studio
uv run --project .. langgraph dev
```

Une page s'ouvre dans le navigateur : choisissez le graphe `agent2`, posez une
question sur la base musicale, et observez l'agent décider puis interroger la base.

## 🧾 Environnement testé

Versions réellement résolues dans `uv.lock` le 1er septembre 2026. Le lock reste la
source de vérité.

| Composant direct | Version résolue |
|---|---:|
| Python | 3.13.13 |
| `langchain` | 1.3.18 |
| `langchain-core` | 1.6.1 |
| `langgraph` | 1.2.11 |
| `langgraph-cli[inmem]` | 0.4.31 |
| `langchain-mistralai` | 1.1.6 |
| `langchain-mcp-adapters` | 0.3.2 |
| `sqlalchemy` | 2.0.52 |
| `python-dotenv` | 1.2.3 |
| `packaging` | 26.3 |
| `pydantic` | 2.13.5 |
| `jupyter` | 1.1.1 |
| `ipykernel` | 7.3.0 |
| `nbclient` | 0.11.0 |
| `nbformat` | 5.11.1 |
| `ruff` *(développement)* | 0.16.5 |
| `nbdime` *(développement)* | 4.0.4 |

L'Atelier 5 lance séparément `mcp-server-time==2026.8.18` avec `uvx`. Cette version
déclare la contrainte `mcp>=1.29.0,<2` ; voir la
[page PyPI de mcp-server-time](https://pypi.org/project/mcp-server-time/).

## 🧪 Vérifications utiles

Vérifier les imports directs sans lancer un notebook :

```powershell
uv run --frozen python -c "import langchain, langchain_core, langgraph, langchain_mistralai, langchain_mcp_adapters, sqlalchemy, dotenv, packaging, pydantic, jupyter, ipykernel, nbclient, nbformat; print('Imports J2 OK')"
```

Vérifier l'interpréteur réellement utilisé (doit finir par `J2_Hands On\.venv\Scripts\python.exe`) :

```powershell
uv run --frozen python -c "import sys; print(sys.executable)"
```

## ⚙️ Particularité MCP sous Windows

L'Atelier 5 vérifie d'abord que `uvx` est disponible, puis lance le serveur time par
le transport `stdio`. Un message clair remplace une erreur obscure si `uvx` manque.
Aucun contournement MCP supplémentaire n'est nécessaire.

## 📚 Documentation officielle

- [Agents LangChain](https://docs.langchain.com/oss/python/langchain/agents)
- [Tools LangChain](https://docs.langchain.com/oss/python/langchain/tools)
- [Messages](https://docs.langchain.com/oss/python/langchain/messages)
- [Streaming](https://docs.langchain.com/oss/python/langchain/streaming)
- [Model Context Protocol](https://docs.langchain.com/oss/python/langchain/mcp)
- [Mémoire à court terme](https://docs.langchain.com/oss/python/langchain/short-term-memory)
- [Sortie structurée](https://docs.langchain.com/oss/python/langchain/structured-output)
- [Context engineering](https://docs.langchain.com/oss/python/langchain/context-engineering)
- [Middleware](https://docs.langchain.com/oss/python/langchain/middleware/overview)
- [Human-in-the-loop](https://docs.langchain.com/oss/python/langchain/human-in-the-loop)
- [Intégration ChatMistralAI](https://docs.langchain.com/oss/python/integrations/chat/mistralai)
- [Function calling Mistral](https://docs.mistral.ai/studio/conversations/function-calling)
- [LangGraph Studio](https://docs.langchain.com/oss/python/langchain/studio)
