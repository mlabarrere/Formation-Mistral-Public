# T3 — Fine-tuning des modèles · Jour 3 (Avancé — Théorique)

> Comprendre **quand et comment** adapter un LLM à son domaine — de la théorie des
> paramètres jusqu'au choix entre fine-tuning, RAG et prompt engineering.

## ⚠️ Niveau de ce thème

Ce thème est **principalement théorique et analytique**. Il n'y a pas de code à exécuter
en production (le fine-tuning réel d'un modèle demande des GPU dédiés et des heures de calcul).
Le notebook contient des illustrations, des exemples de configuration et des démonstrations
de l'impact avec de petits modèles locaux (optionnel).

## Objectifs pédagogiques

À la fin de T3, un profil Tech/DSI sait :

1. expliquer la différence entre **pré-entraînement**, **fine-tuning supervisé (SFT)**,
   **RLHF** et **alignement par préférence (DPO)** ;
2. comprendre **LoRA / QLoRA** : adapter seulement des matrices de rang faible, pas tous
   les poids — réduire de 1 000× les paramètres entraînables ;
3. **décider** quand fine-tuner (vs RAG, vs prompt engineering) avec un arbre de décision ;
4. lire et interpréter une **courbe de perte** d'entraînement et identifier overfitting ;
5. estimer le **coût** d'un fine-tuning (GPU-heures, tokens, stockage) et le comparer au
   coût opérationnel d'un RAG ;
6. citer les offres **Mistral Fine-tuning** et **HuggingFace AutoTrain** pour un premier
   fine-tuning sans infrastructure propre.

## Plan du notebook (NB_T3a)

### Partie 1 — Fondations (30 min)

| Section | Contenu |
|---|---|
| 1.1 | Anatomie d'un LLM : poids, couches, têtes d'attention |
| 1.2 | Pré-entraînement vs fine-tuning : ce qu'on touche, ce qu'on ne touche pas |
| 1.3 | SFT (Supervised Fine-Tuning) : format des données, paires `(instruction, réponse)` |
| 1.4 | RLHF & DPO : apprendre depuis les préférences humaines |

### Partie 2 — LoRA et ses variantes (30 min)

| Section | Contenu |
|---|---|
| 2.1 | Le problème de l'adaptation complète : trop de paramètres |
| 2.2 | LoRA : décomposition de rang faible, `r`, `alpha`, `target_modules` |
| 2.3 | QLoRA : quantification 4-bit + LoRA — fine-tuning sur un seul GPU |
| 2.4 | Paramètres clés : rank `r`, dropout, learning rate, epochs |
| 2.5 | Lecture d'une courbe de perte : convergence, overfitting, plateaux |

### Partie 3 — Décision et mise en œuvre (30 min)

| Section | Contenu |
|---|---|
| 3.1 | Arbre de décision : prompt engineering → RAG → SFT → pré-entraînement |
| 3.2 | Format des données : JSONL, structure `messages`, tokenisation |
| 3.3 | Mistral Fine-tuning API — démo de configuration (sans exécution longue) |
| 3.4 | HuggingFace AutoTrain — alternative no-code |
| 3.5 | Estimation de coût : GPU-heures, tokens, stockage du modèle affiné |
| 3.6 | Évaluation du modèle affiné : benchmarks, LLM-as-a-Judge, tests de régression |

## L'arbre de décision

```
Problème métier à résoudre
        │
        ▼
Le LLM de base répond déjà bien avec un bon prompt ?
  ├── OUI ──► Prompt Engineering (le moins cher)
  └── NON
        │
        ▼
Les données manquantes sont dans des documents existants ?
  ├── OUI ──► RAG (données fraîches, pas de réentraînement)
  └── NON — le modèle doit apprendre un style/format/domaine spécifique
        │
        ▼
Volume de données labellisées disponibles ?
  ├── < 1 000 exemples ──► Few-shot + évaluation rigoureuse
  ├── 1 000 – 100 000  ──► SFT avec LoRA / QLoRA
  └── > 100 000        ──► SFT complet ou pré-entraînement partiel
```

## Glossaire express

- **SFT** — Supervised Fine-Tuning : entraînement supervisé sur des paires `(instruction, réponse)`.
- **RLHF** — Reinforcement Learning from Human Feedback : optimisation via des classements humains.
- **DPO** — Direct Preference Optimization : alternative RLHF sans modèle de récompense séparé.
- **LoRA** — Low-Rank Adaptation : modifier seulement des matrices de rang faible (`r` petit).
- **QLoRA** — LoRA + quantification 4-bit : réduit la mémoire GPU de ~4×.
- **rank `r`** — dimension de la décomposition LoRA ; plus grand = plus expressif mais plus lourd.
- **Overfitting** — le modèle mémorise les exemples d'entraînement au lieu de généraliser.
- **Perplexité** — métrique de qualité d'un LLM : plus basse = mieux (sur son domaine).

## Contenu du dossier

| Fichier | Rôle |
|---|---|
| `NB_T3a_finetuning_theorie.ipynb` | Notebook principal — théorie + illustrations interactives |
| `atelier/` | Discussion guidée : cas d'usage fine-tuning vs RAG |

## 📚 Ressources

- [Mistral — Fine-tuning](https://docs.mistral.ai/capabilities/finetuning/)
- [LoRA — paper original](https://arxiv.org/abs/2106.09685)
- [QLoRA — paper](https://arxiv.org/abs/2305.14314)
- [HuggingFace — PEFT (LoRA)](https://huggingface.co/docs/peft/conceptual_guides/lora)
- [HuggingFace — TRL (SFT, DPO)](https://huggingface.co/docs/trl/)
- [DPO — paper](https://arxiv.org/abs/2305.18290)
- [Présentation J3-T5](../../Présentations/J3-T5_FineTuning.pptx) — slides de référence
- [Présentation J3-T6](../../Présentations/J3-T6_LoRA.pptx) — slides LoRA détaillées
