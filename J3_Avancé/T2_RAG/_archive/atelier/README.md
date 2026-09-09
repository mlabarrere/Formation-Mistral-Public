# Atelier T2 — RAG (Jour 3)

> **Objectif :** construire un système RAG sur des documents réels apportés par les
> participants, évaluer la qualité avec RAGAS, et identifier les axes d'amélioration.
> Durée : ~60 min.

## Ce que le participant apporte

| Quoi | Format | Pourquoi |
|---|---|---|
| 2–5 documents métier | PDF ou texte | Corpus de l'index |
| 5–10 questions types (avec réponse attendue) | Texte | Évaluation RAGAS |
| Contexte métier (domaine, public cible) | Oral | Calibrer le prompt système |

## Ce qu'on produit

```
atelier/
├── documents/                # Documents apportés par le participant
├── index/                    # VectorStore persisté (Chroma)
├── rag_pipeline.py           # Chaîne RAG : loader → splitter → embed → retrieve → génération
├── eval_dataset.json         # Questions + réponses attendues (gold)
├── eval_results.json         # Scores RAGAS : faithfulness, relevancy, precision
└── rapport.md                # Analyse : quels chunks manquent ? trop de bruit ?
```

## Déroulé

1. **Ingérer** les documents participants (`PyPDFLoader` / `TextLoader`)
2. **Chunker** : tester chunk_size 256 vs 512 — observer l'impact sur la précision
3. **Indexer** dans ChromaDB avec embeddings Mistral
4. **Interroger** : les 5–10 questions du participant
5. **Évaluer** avec RAGAS — identifier les questions mal couvertes
6. **Améliorer** : ajuster chunk_size, ajouter un reranker, ou enrichir les métadonnées
