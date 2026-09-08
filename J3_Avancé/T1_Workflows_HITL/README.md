# T1 — Workflows & Human-in-the-Loop · Jour 3 (Avancé)

> Reprendre là où l'**Atelier 9 - Human-in-the-loop** (J2) s'est arrêté : passer d'un
> `interrupt` simple à un **graphe de production** fiable — avec checkpointing durable,
> branches conditionnelles et validation humaine sélective.

## Objectifs pédagogiques

À la fin de T1, un profil Tech/DSI sait :

1. distinguer **interrupt simple** (pause jusqu'à input) et **HITL structuré** (approbation,
   corrections partielles, audit trail) ;
2. concevoir un `StateGraph` avec **checkpointer persistant** (SQLite / Redis) permettant
   la reprise après plantage ou timeout humain ;
3. implémenter des **branches conditionnelles** déclenchées par la décision humaine
   (approve / reject / modify) ;
4. **tracer** chaque intervention humaine (qui, quand, quoi) pour conformité et audit ;
5. choisir entre `MemorySaver` (développement) et un checkpointer durable (production).

## Prérequis

- Avoir exécuté **Atelier 9 - Human-in-the-loop** (J2) et **J1 · T2 Workflows**.
- Connaître `StateGraph`, `interrupt`, `Command`, `thread_id` (notions vues en J1/J2).

## 📦 Dépendances (nouveauté vs J2)

`langgraph` et `langchain-mistralai` viennent du Jour 2. Ce thème ajoute **un seul** paquet,
pour le checkpointer durable sur disque :

```powershell
uv pip install langgraph-checkpoint-sqlite
```

## Déroulé (NB_T1a)

Contrairement à J2·A9 (HITL « haut niveau » via `create_agent` + `HumanInTheLoopMiddleware`),
ce notebook construit le **graphe d'état à la main** (`StateGraph` + `interrupt()` brut) —
une approche bas niveau qui donne le contrôle total d'un workflow de production.

| Partie | Concept | Code |
|---|---|---|
| 1 | Rappel `interrupt()` minimal | `interrupt` + `InMemorySaver` + `Command(resume=...)` |
| 2 | Router après décision | `Command(goto=..., update=...)` — approuver / éditer / rejeter |
| 3 | Checkpointer **durable** | `SqliteSaver` — état reconstruit depuis le disque après redémarrage |
| 4 | Capstone : agent email | classify → fan-out (doc + bug) → write → **HITL sélectif** → send |
| 5 | Audit & rejeu | champ `audit` (reducer `operator.add`) + `get_state_history` |

## Contenu du dossier

| Fichier | Rôle |
|---|---|
| `NB_T1a_workflows_hitl.ipynb` | Notebook principal — Workflows avancés & HITL |
| `atelier/` | Exercice : adapter le pipeline à un cas métier apporté par le participant |

## Connexion avec J2

Ce thème est la suite directe de :
- **Atelier 8 - Prompt dynamique** — contexte dynamique injecté avant le HITL
- **Atelier 9 - Human-in-the-loop** — le `interrupt` de base

```python
# J2·A9 : HITL haut niveau (middleware sur un agent)
agent = create_agent(..., middleware=[HumanInTheLoopMiddleware(...)], checkpointer=InMemorySaver())

# T1·J3 : graphe bas niveau + checkpointer DURABLE
import sqlite3
from langgraph.checkpoint.sqlite import SqliteSaver

conn = sqlite3.connect("checkpoints.db", check_same_thread=False)
app = builder.compile(checkpointer=SqliteSaver(conn))   # survit à l'arrêt du processus
```

## ✅ Statut

Notebook validé de bout en bout : la logique LangGraph (interrupt/resume, `Command(goto)`,
fan-in, reprise durable depuis disque, `get_state_history`) est **testée** avec un LLM stubbé ;
seuls les appels Mistral réels nécessitent une clé.

## 📚 Ressources

- [LangGraph — Workflows & Agents](https://docs.langchain.com/oss/python/langgraph/workflows-agents)
- [LangGraph — Human-in-the-loop](https://langchain-ai.github.io/langgraph/concepts/human_in_the_loop/)
- [LangGraph — Persistence](https://langchain-ai.github.io/langgraph/concepts/persistence/)
- [LangGraph — Checkpointers](https://langchain-ai.github.io/langgraph/reference/checkpoints/)
