# T1 — Multi-agents · Jour 1 (Fondations)

> Faire travailler ensemble **plusieurs agents spécialisés**, chacun avec son rôle, son prompt et
> ses outils — coordonnés par un superviseur.

**Plan de référence** : [`Checklist_Mistral_CD39.md` → T1](../../Checklist_Mistral_CD39.md#t1-multi-agents)

## Déroulé

- **Concept** — le multi-agents est d'abord un choix d'**ingénierie de contexte** ; patterns séquentiel / fan-out / hiérarchique ; superviseur-as-tools ; scoper vs superviseur.
- **Démonstration Mistral** (`NB_T1a`) — agents spécialisés via la **Agents API** (`client.agents`) ; délégation / handoff typé ; évaluation LLM-as-a-Judge.
- **Démonstration LangGraph** (`NB_T1b`) — mêmes agents sur le même scénario GR509, orchestrés avec LangGraph + ToolNode.
- **Atelier CD39** — répartir un dossier sur plusieurs agents → [`atelier/`](atelier/).

## Contenu du dossier

| Fichier | Rôle |
|---|---|
| `NB_T1a_multiagents_mistral.ipynb` | Notebook principal — Agents API Mistral |
| `NB_T1b_multiagents_langgraph.ipynb` | Pendant LangGraph |
| `react_agent_mistral.ipynb` | Démo autonome ReAct (LangGraph + outils génériques) |
| `sentier_gr509.py` | Module partagé GR509 — GPS, Naismith, météo dual-mode |
| `atelier/` | Trace GPS réelle + `.env` |

## 🌐 Page site

[`site/src/pages/jour-1.astro`](../../site/src/pages/jour-1.astro)
