# Atelier T2 — Multi-agents CD39

> **Objectif :** répartir un dossier CD39 complexe sur plusieurs agents spécialisés
> et mesurer la trajectoire complète (pas seulement la réponse finale). Durée : ~45 min (J1).

## Ce que le CD39 apporte en amont

| Quoi | Format | Pourquoi |
|------|--------|---------|
| Un dossier ou une question transverse impliquant plusieurs services | PDF / texte | Matière du fan-out |
| Description des rôles impliqués (ex. accueil, instruction, validation) | Oral | Mapper les agents |
| Exemples de réponses attendues par service | Document | Calibrer chaque worker |

> Idéal : une demande composite (ex. APA + FSL logement simultanés) qui nécessite
> de consulter deux services distincts.

## Ce qu'on produit pendant la session

```
atelier/
├── orchestrateur_cd39.py     # Scoper → Superviseur → Workers
├── agents/
│   ├── agent_solidarites.py  # Worker solidarités (APA, RSA, FSL)
│   └── agent_logement.py     # Worker logement
├── dossier_entree.txt        # Demande CD39 apportée par le participant
├── trajectoire.jsonl         # Journal complet : agent, question, sources, ms
└── mesures.md                # Nb agents, nb appels, tokens estimés, latence, refus
```

## Déroulé de la session

1. **Mapper** la demande CD39 → agents (qui cherche, qui vérifie, qui rédige)
2. **Coder** le Scoper (plan JSON) + les 2–3 workers spécialisés
3. **Brancher** sur l'Agents API Mistral (ou stub si réseau limité)
4. **Journaliser** la trajectoire complète avec `class Trajectoire` (NB_T2b)
5. **Mesurer** : `mesurer_trajectoire()` → rapport → comparer agent unique vs multi-agents
