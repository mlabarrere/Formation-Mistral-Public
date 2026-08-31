# T1 — Workflows · Jour 1 (Fondations)

> Orchestrer une chaîne d'étapes **fiable, traçable et reprenable** — l'inverse d'un agent libre.
> Fil rouge : **une petite usine imaginaire** (décor : une manufacture de lunettes du Jura, clin d'œil
> à **Morez**), traitée **deux fois** — d'abord avec **Mistral Workflows** (exécution durable), puis
> avec **LangChain/LangGraph**. Même usine, deux moteurs → on *sent* la différence d'orchestration.
> **Aucune connaissance métier n'est requise** : les stations sont de simples fonctions.

**Plan de référence** : [`Checklist_Mistral_CD39.md → T1`](../../Checklist_Mistral_CD39.md#t1-workflows)

## Objectifs pédagogiques
À la fin de T1, un profil Tech/DSI sait :
1. distinguer **workflow déterministe** et **agent libre**, et défendre le choix (traçabilité, reprise) ;
2. expliquer l'**exécution durable** (event log, rejeu sans ré-exécution, sandbox de déterminisme) ;
3. modéliser un process en **activités + orchestrateur** (Mistral) *ou* en **graphe d'état** (LangGraph) ;
4. mettre en œuvre **branche conditionnelle**, **cycle de reprise**, **retries/timeouts** et **human-in-the-loop** ;
5. mesurer un pipeline avec des **métriques simples** (taux de succès, reprises, coût, livré à temps) ;
6. arbitrer **Mistral Workflows vs LangGraph** (souveraineté, lock-in, maturité) et savoir les **composer**.

## L'arc en 2 notebooks (générés — éditer [`outils/generate_notebooks.py`](../../outils/generate_notebooks.py), jamais les `.ipynb`)
- **`NB_T1a_workflow_mistral.ipynb`** — **Mistral Workflows d'abord** (l'intro « comment ça marche ») :
  activités durables (`@wf.activity`, retry/timeout/heartbeat), orchestrateur (`@wf.workflow.define`/
  `entrypoint`), branche **Standard/Premium**, boucle de reprise, HITL (`wait_for_input`), métriques.
  Les activités **s'exécutent en local pour de vrai** ; `execute_workflow` tourne aussi localement.
- **`NB_T1b_workflow_langgraph.ipynb`** — **puis LangGraph** (le vrai apprentissage) : la **même usine**
  en `StateGraph` (nœuds/arêtes), branche conditionnelle, **cycle** de reprise, `interrupt` +
  `MemorySaver`, `create_react_agent`, `RetryPolicy`. **Exécuté en live** sur modèles Mistral (`ChatMistralAI`).

Chaque notebook ouvre sur un **glossaire** et suit le rythme *Pourquoi (concept défini) → code → À retenir*,
avec des encadrés `> **Piège.**` / `> **Note honnête.**` et trois visualisations (topologie, trajectoires, résultats).

## Modules partagés
- [`usine_lunettes.py`](usine_lunettes.py) — la simulation d'usine (stations = fonctions génériques,
  seedées/reproductibles ; 4 commandes golden). **Logique identique** pour les deux notebooks ; seul le
  moteur d'orchestration change. Cœur de la démo honnête.
- [`usine_viz.py`](usine_viz.py) — visualisations matplotlib/networkx (style J2/T4b) : topologie
  d'orchestration, trajectoire des commandes, résultats par commande.

### La chaîne de production (stations génériques)
| # | Station (fonction) | Entrée | Action | Sortie clé |
|---|---|---|---|---|
| 1 | `recevoir_commande` | gamme, quantité | valide la commande | `ok`, `issues` |
| 2 | `approvisionner` | gamme, quantité | réconcilie MOQ + délai | `delai_jours`, `extra_needed` |
| 3 | `fabriquer` | lot | produit le lot | `taux_rebut_pct`, `defaut` |
| 4 | `finition_premium` *(Premium)* | lot fabriqué | étape supplémentaire haut de gamme | `defaut` |
| 5 | `assembler` | pièces | assemble | `defaut` |
| 6 | `controler_qualite` | défauts constatés | décide du sort de la commande | `verdict` (accept/rework/scrap) |
| 7 | `expedier` | commande acceptée | livraison | `livre_a_temps` |

**Branche** : gamme `premium` → passe par la finition ; `standard` → assemblage direct.
**Cycle** : contrôle `rework` → retour fabrication (une reprise). **Rebut** : défaut irrécupérable
(`piece_cassee`) → `scrap`. **HITL** : délai d'appro > échéance → validation humaine.

## 📖 Glossaire express
- **Exécution durable / event log** — chaque étape journalisée ; après panne, rejeu **sans** ré-exécuter.
- **Workflow vs Activity** — orchestrateur déterministe vs unité de travail à effet de bord (retriable).
- **Sandbox de déterminisme** — pas d'horloge/hasard/I/O dans le corps du workflow (sinon rejeu divergent).
- **StateGraph / nœud / arête / reducer** — graphe d'état LangGraph ; reducer = fusion d'un champ (ex. `+`).
- **Checkpointer / thread** — persistance de l'état par `thread_id` (reprise).
- **interrupt / wait_for_input (HITL)** — suspend le run jusqu'à une décision humaine.
- **Métriques** — taux de succès (étapes OK du 1er coup), reprises, coût, livré à temps (oui/non).

## Dépendances
`langgraph==0.6.11`, `langchain-mistralai==0.2.12`, `mistralai-workflows==3.11.0` (cf. [`requirements.txt`](../../requirements.txt) à la racine).
⚠️ Lignes **pré-1.0** obligatoires (les 1.x exigent `langchain-core>=1.4.7` → cassent `ragas`/T4).
Piège serveur dédié : `ChatMistralAI(..., endpoint=MISTRAL_SERVER_URL.rstrip("/") + "/v1")`.

## Exécuter
```bash
python3.12 -m venv .venv && .venv/bin/pip install -r requirements.txt   # depuis la racine du dépôt
# .env à la racine du dépôt : MISTRAL_API_KEY=... et (optionnel) MISTRAL_SERVER_URL=...
python outils/generate_notebooks.py      # (re)génère les .ipynb depuis la source de vérité
jupyter notebook J1_Fondations/T1_Workflows/NB_T1a_workflow_mistral.ipynb
```
NB_T1a tourne sans clé (activités locales + simulation) ; NB_T1b exige `MISTRAL_API_KEY` (appels LLM live).

## 📚 Ressource Titanium
- **`↻ T-09`** orchestrateur / cycle de vie → [`09_Multi_Agent_Systems`](../../ressources/titanium/09_Multi_Agent_Systems/)
- Résolution complète : [`ressources/MAP_Titanium.md`](../../ressources/MAP_Titanium.md)

## 🌐 Page site
[`site/src/pages/jour-1.astro`](../../site/src/pages/jour-1.astro)

## 📁 atelier/
Artefacts CD39 du thème (données anonymisées, mesures de coût/latence).
