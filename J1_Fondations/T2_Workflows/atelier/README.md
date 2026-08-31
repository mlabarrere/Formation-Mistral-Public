# Atelier T1 — Workflows CD39

> **Objectif :** automatiser un traitement récurrent du Département en un pipeline
> traçable, rejouable et mesurable. Durée : ~60 min (J1 après-midi).

## Ce que le CD39 apporte en amont

| Quoi | Format | Pourquoi |
|------|--------|---------|
| Un lot de 10–20 courriers ou comptes rendus récurrents | PDF ou texte brut | Matière de l'atelier |
| Description du traitement actuel (qui fait quoi, à quelle fréquence) | Oral / note | Caler les étapes du workflow |
| Critères de tri ou de résumé attendus | Oral / document | Définir les sorties de chaque étape |

> Les documents doivent être **anonymisés** (pas de noms réels, pas de données personnelles
> identifiables) avant transmission. Un lot fictif réaliste suffit si les vrais docs ne sont
> pas encore disponibles.

## Ce qu'on produit pendant la session

```
atelier/
├── workflow_cd39.py          # Pipeline Python : étapes nommées, sortie JSON par étape
├── lot_entree/               # Courriers / CR apportés par le CD39
│   └── exemple_01.txt
│   └── ...
├── lot_sortie/               # Résultats produits par le workflow
│   └── exemple_01_sortie.json
│   └── ...
├── journal_run.jsonl         # Log entrée→sortie par document (horodaté)
└── mesures.md                # Fiabilité des étapes + coût/latence par étape
```

## Déroulé de la session

1. **Découper** le traitement en étapes nommées à responsabilité unique (≤ 3 étapes)
2. **Coder** le pipeline avec sorties JSON typées entre étapes
3. **Rejouer** le lot complet, journaliser chaque entrée→sortie
4. **Mesurer** : taux de succès par étape, latence, coût estimé (tokens × tarif)
5. **Discuter** : quand rejouer ? Comment gérer une étape qui échoue ?
