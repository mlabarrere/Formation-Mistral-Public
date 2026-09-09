# Archive — ancienne version du thème T2

Ce dossier conserve la **première version** du thème T2 (RAG), remplacée le 9 septembre 2026
par le notebook `NB_T2a_rag_graphrag.ipynb` (corpus « vins du Jura »), promu depuis
`J2_Fondations/T4_GraphRAG/`.

| Fichier | Ce que c'était |
|---|---|
| `NB_T2a_rag_langchain.ipynb` | RAG LangChain sur un billet de blog public (Lilian Weng), chargé par `WebBaseLoader`. 36 cellules, **jamais exécutées** : aucune sortie. |
| `README.md` | Le README du thème dans cette version |
| `atelier/` | L'énoncé d'atelier associé (RAG + RAGAS sur documents apportés) |

## Pourquoi le remplacement

Le notebook des vins du Jura couvre tout ce que celui-ci couvrait, et va plus loin :

| Sujet | Ancienne version | Version retenue |
|---|---|---|
| Chunking, embeddings, Chroma | ✅ | ✅ + cosinus recalculé à la main en NumPy |
| Comparaison de bases vectorielles | ❌ | ✅ encart **ChromaDB vs Qdrant**, même corpus rejoué sur les deux |
| Retrieval lexical (BM25) et hybride | ❌ | ✅ fusion par RRF |
| Multi-Query, RAG-Fusion, HyDE | ✅ | ✅ (Multi-Query fusionné par RRF = RAG-Fusion) |
| GraphRAG | ❌ | ✅ extraction de triplets, graphe NetworkX, traversée k-hop |
| Évaluation chiffrée | énoncée, non implémentée | ✅ juge LLM sur 10 questions × 3 pipelines, + coût en tokens |
| Sorties exécutées | ❌ aucune | ✅ toutes |

## Ce qui reste à récupérer ici, éventuellement

- **`WebBaseLoader`** : la version retenue lit des fichiers markdown locaux. Si un atelier
  doit démontrer l'ingestion depuis le web, le code est dans la cellule 07.
- **L'énoncé d'atelier `atelier/README.md`** : il porte sur les documents apportés par les
  participants et reste valable tel quel, indépendamment du corpus de démonstration.
