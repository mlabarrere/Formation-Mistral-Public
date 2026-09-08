# Atelier T1 — Workflows HITL (Jour 3)

> **Objectif :** adapter le pipeline HITL du notebook à un cas métier réel apporté
> par les participants. Durée : ~45 min.

## Scénario proposé

Construire un **workflow de validation de document** avec :

1. Un agent qui analyse le document et propose une action.
2. Un nœud HITL qui demande la validation humaine (approve / reject / modify).
3. Des branches conditionnelles selon la décision.
4. Un checkpointer persistant pour survivre à une interruption.

## Ce que le participant apporte

| Quoi | Format | Pourquoi |
|---|---|---|
| Un document ou demande à traiter | Texte / PDF | Matière du pipeline |
| Les critères de validation métier | Oral / texte | Configurer les conditions HITL |
| Le seuil de confiance pour auto-approuver | Nombre (0–1) | Paramétrer la branche automatique |

## Ce qu'on produit pendant la session

```
atelier/
├── pipeline_hitl.py          # StateGraph avec checkpointer + branches
├── document_entree.txt       # Document apporté par le participant
├── decisions.jsonl           # Journal des interventions humaines (qui, quand, quoi)
└── mesures.md                # Nb d'interruptions, temps de réponse humain, taux auto-approuvé
```

## Déroulé

1. **Modéliser** le flux : quelles étapes ? où placer les `interrupt` ?
2. **Coder** le graphe avec `StateGraph` + `SqliteSaver` (`langgraph-checkpoint-sqlite`)
3. **Tester** la reprise : tuer le processus pendant le HITL, relancer, vérifier la continuité
4. **Mesurer** : taux d'auto-approbation, délai moyen de validation humaine
