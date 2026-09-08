# Atelier T3 — Fine-tuning : discussion guidée (Jour 3)

> **Objectif :** À partir d'un cas métier réel, décider collectivement de la stratégie
> d'adaptation (prompt engineering / RAG / fine-tuning) et esquisser un plan de mise
> en œuvre. Durée : ~30 min (format discussion + tableau blanc).

## Format

Cet atelier est une **discussion structurée**, pas un coding session — le fine-tuning
réel demande des GPU et plusieurs heures. On s'appuie sur le notebook pour illustrer.

## Déroulé

### Étape 1 — Présenter le cas (5 min)

Chaque groupe présente son cas métier :
- Quel domaine ? (juridique, médical, technique, service public…)
- Quel problème le LLM résout-il mal aujourd'hui ?
- Quelles données sont disponibles (et en quelle quantité) ?

### Étape 2 — Appliquer l'arbre de décision (10 min)

Parcourir collectivement l'arbre (cf. README T3) :
1. Un bon prompt suffit-il ? → tester en live si possible
2. Les données manquantes sont-elles dans des documents ? → RAG
3. Le style/format/domaine est-il trop spécifique ? → SFT

### Étape 3 — Estimer le coût (10 min)

| Stratégie | Coût estimé | Délai | Maintenance |
|---|---|---|---|
| Prompt engineering | ~ 0 € | 1 jour | Faible |
| RAG | 10–200 €/mois (hosting) | 1 semaine | Moyen (docs à jour) |
| SFT LoRA (Mistral API) | 5–50 € selon volume | 2–5 jours (données + entraînement) | Fort (réentraîner si données évoluent) |

### Étape 4 — Plan d'action (5 min)

Chaque groupe repart avec :
- La stratégie choisie et pourquoi
- Le format de données nécessaire (si SFT)
- Les 3 prochaines étapes concrètes
