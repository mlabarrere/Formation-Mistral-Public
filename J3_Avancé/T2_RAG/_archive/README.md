# T2 — RAG avec LangChain · Jour 3 (Avancé)

> **Retrieval-Augmented Generation** : ancrer les réponses du LLM dans des documents
> réels — ingestion, découpage, embedding, retrieval, reranking, génération et évaluation.

## Objectifs pédagogiques

À la fin de T2, un profil Tech/DSI sait :

1. expliquer le **cycle RAG complet** (index → retrieve → augment → generate) et ses
   limites (hallucination résiduelle, couverture, fraîcheur) ;
2. **ingérer** des documents (PDF, texte, web) avec les loaders LangChain et les découper
   en chunks avec `RecursiveCharacterTextSplitter` ;
3. **créer un index vectoriel** (ChromaDB / FAISS) avec des embeddings Mistral ou
   sentence-transformers ;
4. implémenter la **chaîne RAG** (`retriever | prompt | llm | parser`) et un **reranker** ;
5. **évaluer** la qualité RAG (fidélité, pertinence, couverture) avec RAGAS ou LLM-as-a-Judge ;
6. choisir entre **RAG naïf**, **RAG hybride** (dense + sparse / BM25) et **GraphRAG**.

## Déroulé (NB_T2a)

Le corpus de démonstration est un billet de blog public sur les agents LLM (Lilian Weng),
choisi car dense et bien structuré ; il se remplace par vos propres documents dans l'atelier.

| Partie | Concept | Code |
|---|---|---|
| 1 | Indexing | `WebBaseLoader` + `RecursiveCharacterTextSplitter` + `MistralAIEmbeddings` + `Chroma` |
| 2 | Retrieval | `retriever.invoke` — similarité sémantique, k chunks |
| 3 | Generation | chaîne LCEL `{context, question} \| prompt \| llm \| parser` |
| 4a | Multi-Query | reformulations multiples + union des chunks (`retriever.map()`) |
| 4b | RAG-Fusion | Reciprocal Rank Fusion (RRF, `k=60`) |
| 4c | HyDE | document hypothétique → embedding → retrieval |
| 5 | Comparaison | mêmes questions sur les 4 chaînes, quand utiliser quoi |

### Pour aller plus loin (atelier & suite)

Reranking (`CohereRerank`), RAG hybride (BM25 + dense via `EnsembleRetriever`), évaluation
**RAGAS** (faithfulness, answer_relevancy, context_precision) et traçage **LangSmith** sont
traités dans l'[`atelier/`](atelier/), aux côtés de techniques avancées de RAG (routing,
query construction, RAPTOR, ColBERT, CRAG, Self-RAG).

## Architecture RAG

```
Documents sources
      │
      ▼
   Loader ──► Splitter ──► Embedder ──► VectorStore (Chroma/FAISS)
                                              │
Question utilisateur ──► Retriever ◄──────────┘
      │                      │
      │                      ▼
      │              Reranker (optionnel)
      │                      │
      └──────────────► Prompt augmenté
                             │
                             ▼
                          LLM (Mistral)
                             │
                             ▼
                       Réponse + sources
```

## Contenu du dossier

| Fichier / Dossier | Rôle |
|---|---|
| `NB_T2a_rag_langchain.ipynb` | Notebook principal — RAG complet avec LangChain |
| `data/` | Documents de démonstration (PDF, textes) |
| `atelier/` | Exercice : RAG sur les documents apportés par les participants |

## 📦 Dépendances (nouveautés vs J2)

`langchain-mistralai` est déjà présent depuis le Jour 2. Ce thème ajoute :

```powershell
uv pip install langchain-community langchain-chroma chromadb beautifulsoup4
```

| Paquet | Usage |
|---|---|
| `langchain-community` | `WebBaseLoader` (chargement web) |
| `langchain-chroma` + `chromadb` | index vectoriel Chroma (en mémoire) |
| `beautifulsoup4` | parsing HTML du corpus |

> **Piège.** Le notebook utilise `mistral-embed`. Vérifiez que votre serveur expose la
> route `/v1/embeddings` — certains déploiements ne servent que la complétion.

## 📖 Glossaire express

- **Chunk** — fragment de document ; taille et chevauchement sont les deux leviers clés.
- **Embedding** — vecteur dense représentant le sens sémantique d'un texte.
- **VectorStore** — base de données optimisée pour la recherche par similarité cosinus.
- **MMR (Maximal Marginal Relevance)** — diversifier les chunks retournés pour éviter la redondance.
- **RAGAS** — framework d'évaluation RAG : fidélité, pertinence, précision du contexte.
- **RAG hybride** — combine recherche dense (embeddings) + sparse (BM25/TF-IDF).

## 📚 Ressources

- [LangChain — RAG](https://python.langchain.com/docs/tutorials/rag/)
- [LangChain — VectorStores](https://python.langchain.com/docs/concepts/vectorstores/)
- [LangChain — Retrievers](https://python.langchain.com/docs/concepts/retrievers/)
- [ChromaDB](https://docs.trychroma.com/)
- [RAGAS — Évaluation RAG](https://docs.ragas.io/)
- [Mistral Embeddings](https://docs.mistral.ai/capabilities/embeddings/)
- [RRF — article d'origine (Cormack et al.)](https://plg.uwaterloo.ca/~gvcormas/cormacksigir09-rrf.pdf)
- [HyDE — Precise Zero-Shot Dense Retrieval](https://arxiv.org/abs/2212.10496)
