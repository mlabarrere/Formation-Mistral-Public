# 🧪 Jour 2 — LangChain Hands On avec Mistral AI

Neuf notebooks guidés mènent d’un premier agent jusqu’à l’interaction humaine :
trois **Ateliers d’introduction** (créer un agent, comprendre les messages, streamer
les réponses) puis six **leçons** (tools, MCP, mémoire, sortie structurée, prompt
dynamique, human-in-the-loop).

🎯 **Public** : adultes débutants en LangChain, déjà à l’aise avec les bases de
Python. Chaque leçon est prévue pour **30 à 45 minutes**.

Les exemples restent proches du
[cours LangChain Essentials original](https://github.com/langchain-ai/lca-langchainV1-essentials/tree/main/python),
mais ils utilisent Mistral AI et les APIs LangChain actuelles.

## 🗺️ Parcours

| Notebook | Question à laquelle il répond |
|---|---|
| `Atelier1_fast_agent.ipynb` | Comment construire un premier agent (SQL) en quelques lignes ? |
| `Atelier2_messages.ipynb` | Comment LangChain représente-t-il une conversation (messages) ? |
| `Atelier3_streaming.ipynb` | Comment afficher une réponse au fil de l’eau (streaming) ? |
| `L4_tools.ipynb` | Comment un modèle choisit-il puis appelle-t-il une fonction Python ? |
| `L5_tools_with_mcp.ipynb` | Comment découvrir des tools fournis par un serveur MCP ? |
| `L6_memory.ipynb` | Comment conserver l’état d’un même fil sans mélanger deux utilisateurs ? |
| `L7_structuredOutput.ipynb` | Comment obtenir une réponse validée plutôt qu’un texte libre ? |
| `L8_dynamic.ipynb` | Comment adapter le prompt au contexte de l’utilisateur ? |
| `L9_HITL.ipynb` | Comment interrompre une action et attendre une décision humaine ? |

## 🛠️ Prérequis

- [Git](https://git-scm.com/install/) ;
- [uv](https://docs.astral.sh/uv/getting-started/installation/), qui fournit aussi
  `uvx` pour L5 ;
- une clé Mistral et l’URL du serveur compatible avec l’API Mistral ;
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

`uv.lock` fige également les dépendances transitives : deux participants obtiennent
ainsi la même combinaison de bibliothèques. Après une première installation, ne
relancez `uv lock --upgrade` que lorsque vous souhaitez volontairement mettre le
cours à niveau.

### 🔐 Variables d’environnement

Deux variables suffisent : `MISTRAL_API_KEY` et `MISTRAL_SERVER_URL`. Le moyen le
plus simple, valable pour **les neuf notebooks**, est de les exporter dans le shell
avant de lancer Jupyter (voir ci-dessous). Les trois Ateliers d’introduction chargent
en plus, si présent, un fichier `.env` via `python-dotenv` ; les leçons L4–L9 lisent
uniquement les variables du **processus courant**. Dans tous les cas, **aucune valeur
secrète n’est affichée** et `.env` ne doit jamais être versionné.

PowerShell :

```powershell
$env:MISTRAL_API_KEY = Read-Host -Prompt "Clé Mistral" -MaskInput
$env:MISTRAL_SERVER_URL = "https://votre-serveur.example/v1"
```

Bash ou zsh :

```bash
read -rsp "Clé Mistral : " MISTRAL_API_KEY && export MISTRAL_API_KEY
export MISTRAL_SERVER_URL="https://votre-serveur.example/v1"
```

LangSmith est facultatif. Les noms de variables optionnelles figurent dans
`example.env`, sans secret réel.

### ▶️ Lancer Jupyter

Depuis `J2_Hands On` :

```powershell
uv run jupyter lab
```

Lancé ainsi depuis ce dossier, le kernel **Python 3 (J2 Hands On)** par défaut est
déjà celui du `.venv` J2 (Python 3.13) : les notebooks s’ouvrent prêts à l’emploi.

## 🧾 Environnement testé

Les versions ci-dessous sont celles réellement résolues dans `uv.lock` le
1er septembre 2026. Le lock reste la source de vérité.

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

L5 lance séparément `mcp-server-time==2026.8.18` avec `uvx`. Cette version déclare
la contrainte `mcp>=1.29.0,<2` ; voir la
[page PyPI officielle de mcp-server-time](https://pypi.org/project/mcp-server-time/).

## 🧪 Vérifications utiles

Vérifier les imports directs sans lancer un notebook :

```powershell
uv run --frozen python -c "import langchain, langchain_core, langgraph, langchain_mistralai, langchain_mcp_adapters, sqlalchemy, dotenv, packaging, pydantic, jupyter, ipykernel, nbclient, nbformat; print('✅ Imports J2 OK')"
```

Vérifier l’interpréteur réellement utilisé :

```powershell
uv run --frozen python -c "import sys; print(sys.executable); print(sys.version)"
```

Le chemin affiché doit se terminer par `J2_Hands On\.venv\Scripts\python.exe` sous
Windows.

## ⚙️ Particularité MCP sous Windows

Le notebook L5 vérifie d’abord que `uvx` est disponible. Il lance ensuite le serveur
time par le transport `stdio`. Un message actionnable remplace une erreur obscure si
`uvx` manque. Aucun contournement MCP supplémentaire n’est nécessaire tant que le
serveur déclare correctement sa contrainte SDK.

## 📚 Documentation officielle

- [Agents LangChain](https://docs.langchain.com/oss/python/langchain/agents)
- [Tools LangChain](https://docs.langchain.com/oss/python/langchain/tools)
- [Model Context Protocol](https://docs.langchain.com/oss/python/langchain/mcp)
- [Mémoire à court terme](https://docs.langchain.com/oss/python/langchain/short-term-memory)
- [Sortie structurée](https://docs.langchain.com/oss/python/langchain/structured-output)
- [Context engineering](https://docs.langchain.com/oss/python/langchain/context-engineering)
- [Middleware](https://docs.langchain.com/oss/python/langchain/middleware/overview)
- [Human-in-the-loop](https://docs.langchain.com/oss/python/langchain/human-in-the-loop)
- [Intégration ChatMistralAI](https://docs.langchain.com/oss/python/integrations/chat/mistralai)
- [Function calling Mistral](https://docs.mistral.ai/studio/conversations/function-calling)

Le fichier `PROMPT_MAITRE_J2.md` décrit l’orchestration multi-agents utilisée pour
maintenir ou reproduire cette version du cours. 🧭
