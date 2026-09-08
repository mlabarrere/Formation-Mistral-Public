# T4 : RAG & GraphRAG · Jour 2 (Fondations)

> Donner à un modèle une connaissance qu'il n'a pas, d'abord en indexant les **mots**
> (RAG vectoriel et hybride), puis en indexant les **relations** (GraphRAG).

**Support de cours** : [`Présentations/J2-T4_GraphRAG.pptx`](../../Présentations/J2-T4_GraphRAG.pptx)
**Notebook** : [`NB_T4_rag_graphrag.ipynb`](NB_T4_rag_graphrag.ipynb), 65 cellules, ~120 min,
exécuté avec ses sorties. **LangChain seul** : aucun LangGraph, aucune base graphe à installer.

Ce README est le document de référence du thème : il contient tout ce qui ne se déroule pas
en salle : grilles de décision, écarts jouet→production, panorama des outils et
bibliographie. Le notebook, lui, ne contient que ce qu'on exécute.

---

## Déroulé du notebook

| Chapitre | Contenu | Tasks |
|---|---|---|
| **1 · Indexer** | chunking (512/64 → 700 car.), `mistral-embed`, cosinus calculé à la main en NumPy, puis Chroma. Encart **ChromaDB vs Qdrant** | 3 + encart |
| **2 · Retrouver** | le `retriever` LangChain, BM25 pour les termes rares, fusion **RRF** (k=60) | 2 + exercice |
| **3 · Générer** | chaîne LCEL `prompt \| llm \| parser`, ancrage et refus, puis **le mur** | 2 |
| **4 · Traduire la question** | Multi-Query et HyDE : pourquoi ils ne suffisent pas | 1 |
| **5 · GraphRAG** | extraction de triplets par `with_structured_output`, graphe NetworkX, *entity linking*, traversée k-hop, chaîne GraphRAG | 4 |
| **6 · Mesurer et décider** | juge LLM sur 3 pipelines × 10 questions, coût d'indexation et d'interrogation | exercice final |

### Les deux moments qui portent tout le thème

**Le mur** (Task 3.2) : trois questions dont la réponse n'est écrite dans aucun passage. Le
RAG vectoriel y échoue de trois façons différentes :

1. un **refus honnête** : le cas sain, détectable ;
2. un **décompte faux** sans signal d'incertitude : sur une agrégation, le vectoriel répond
   sur ce qu'il a vu, jamais « je n'ai pas tout vu » ;
3. une **recombinaison erronée de fragments authentiques** : le modèle attribue aux domaines
   de Château-Chalon la liste des cépages autorisés par l'AOC Crémant du Jura, trouvée dans
   une autre fiche. Chaque mot de la réponse est dans le contexte ; le lien entre eux est
   inventé. C'est le vrai risque du RAG, pas l'invention pure.

**Le tableau d'évaluation** (chapitre 6) : le graphe fait 3/3 sur le multi-sauts, mais **perd
2 des 4 questions simples**. Le volume du clavelin et la durée d'élevage ne sont pas des
relations du schéma : le graphe refuse proprement, alors que le corpus contenait la réponse.
C'est l'argument central du réflexe « gardez les deux ».

---

## Contenu du dossier

| Fichier | Rôle |
|---|---|
| `NB_T4_rag_graphrag.ipynb` | Le notebook de cours |
| `vins_jura.py` | Module partagé : corpus, 3 familles de questions, graphe de référence, `rrf`, `cosinus` |
| `corpus_vins/` | 7 fiches markdown : le corpus indexé |

### `vins_jura.py` : API publique

| Symbole | Rôle |
|---|---|
| `CORPUS_DIR`, `charger_corpus()` | Chemin et chargement des fiches (`fichier`, `titre`, `texte`) |
| `QUESTIONS_SIMPLES` (4) | Répondables avec un seul passage : le vectoriel y excelle |
| `QUESTIONS_MULTIHOP` (3) | Deux sauts ou une agrégation : le vectoriel échoue par construction |
| `QUESTIONS_HORS_SCOPE` (3) | Hors corpus : la bonne réponse est de refuser |
| `TRIPLETS_REFERENCE` (48) | Le graphe « gold », écrit à la main : sert de vérité terrain |
| `RELATIONS` (7) | Les types de relations autorisés |
| `rrf(classements, k=60)` | Reciprocal Rank Fusion |
| `cosinus(a, b)` | Similarité cosinus en NumPy |

Aucune dépendance LangChain ni Mistral, aucun effet de bord à l'import, aucun appel réseau.
Le module a un smoke test : `uv run python J2_Fondations/T4_GraphRAG/vins_jura.py`.

---

## Le corpus

Sept cuvées d'un petit vignoble jurassien. **Une fiche = une cuvée**, pas un domaine : un
domaine qui produit deux cuvées est donc décrit dans deux fiches, et rien dans une fiche ne
dit ce que contient l'autre. Cette fragmentation est délibérée : c'est elle qui rend les
questions multi-sauts insolubles en RAG vectoriel. C'est aussi la situation normale d'un
fonds documentaire réel.

Le graphe de référence compte **48 triplets, 35 entités et 7 relations** :

```text
Vigneron -[DIRIGE]->     Domaine
Domaine  -[SIEGE_A]->    Commune        (siège social et caves du domaine)
Domaine  -[PRODUIT]->    Cuvée
Cuvée    -[VINIFIE_A]->  Commune        (commune où se trouve la parcelle)
Cuvée    -[ISSU_DE]->    Cépage
Cuvée    -[RELEVE_DE]->  Appellation
Cuvée    -[EST_UN]->     TypeDeVin
```

**La distinction `SIEGE_A` / `VINIFIE_A` porte toute la difficulté** : le siège du Domaine de
la Roche Percée est à Château-Chalon, mais la parcelle de son crémant est à Voiteur. Les
confondre casse la première question multi-sauts.

Ambiguïté volontaire : « Château-Chalon » et « L'Étoile » sont à la fois des communes et des
appellations. C'est le cas dans la réalité, et le typage des relations est ce qui lève
l'ambiguïté.

> **Note honnête.** Les domaines, vignerons, cuvées et lieux-dits sont **fictifs**. Les
> appellations, cépages, communes et règles d'élevage (durée sous voile, clavelin de 62 cl,
> méthode traditionnelle, minimum de neuf mois sur lattes) sont réels et vérifiables.
> Inventer les producteurs évite d'attribuer à de vraies exploitations des caractéristiques
> qu'elles n'ont pas. L'annexe du support T4 documente précisément ce type d'erreur.

---

## Vectoriel vs Hybride vs GraphRAG : grille de décision

| Critère | RAG vectoriel | RAG hybride | GraphRAG |
|---|---|---|---|
| **Mise en œuvre** | une après-midi | +1 heure (BM25 + RRF) | plusieurs jours (schéma, extraction, normalisation) |
| **Coût d'indexation** | 1 embedding / chunk | idem | **1 appel LLM / document** |
| **Coût par question** | faible | faible | faible à modéré (contexte compact) |
| **Paraphrase, synonymes** | ✅ excellent | ✅ excellent | ❌ perd le texte |
| **Termes rares, identifiants** | ❌ faible | ✅ **c'est son apport** | ➖ selon le schéma |
| **Multi-sauts, jointures** | ❌ impossible | ❌ impossible | ✅ **c'est son apport** |
| **Comptage, agrégation** | ❌ faux avec assurance | ❌ idem | ✅ exact si le graphe est complet |
| **Citations, nuance, style** | ✅ conservés | ✅ conservés | ❌ le triplet oublie la phrase |
| **Maintenance** | faible | faible | **élevée** (le graphe dérive avec le corpus) |
| **Choisir si...** | questions factuelles sur du texte | idem + jargon ou références | questions relationnelles sur un domaine stable et typé |

### Les trois réflexes à emporter

1. **Commencez hybride, pas vectoriel.** Dense + BM25 + RRF coûte une heure de plus et
   ferme la moitié des angles morts. C'est le vrai point de départ, et le système qu'il faut
   battre avant d'invoquer autre chose.
2. **Le GraphRAG ne se justifie que par les questions.** Écrivez d'abord dix questions
   réelles. Si aucune n'exige de joindre deux documents, le graphe est un coût sans
   contrepartie. Et **le schéma se conçoit à partir des questions**, pas des documents :
   c'est la leçon du 2/4 sur les questions simples.
3. **Gardez les deux.** En production on interroge le vectoriel *et* le graphe, puis on
   fusionne, par RRF encore. Le graphe apporte la structure, le texte apporte la nuance et
   les citations.

---

## Jouet → Production : les écarts à combler

| Dimension | Le notebook (jouet) | Production |
|---|---|---|
| **Index vectoriel** | Chroma en mémoire, reconstruit à chaque exécution | base persistante, réindexation incrémentale sur événement |
| **Normalisation d'entités** | une fonction de 6 lignes | *entity resolution* : dictionnaire d'alias, sigles, seuils de fusion, revue humaine |
| **Qualité du graphe** | précision/rappel mesurés une fois | test de non-régression à chaque réindexation, alerte sur dérive |
| **Chunking** | 700 caractères pour tout | par type de document, en respectant titres et tableaux |
| **Fraîcheur** | corpus figé | suppression et mise à jour propagées jusqu'au graphe |
| **RGPD** | données fictives | pseudonymisation **avant** vectorisation, droit à l'effacement jusque dans l'index |
| **Habilitations** | aucune | filtre par périmètre appliqué **dans** la requête, jamais dans le prompt |
| **Observabilité** | `print()` | traces LangSmith, journal des contextes servis, retour utilisateur |
| **Évaluation** | 10 questions, exécution manuelle | plusieurs centaines de cas en CI, seuils bloquants |
| **Coût** | mesuré une fois | budget par question, plafond, cache d'embeddings |

> **Deux lignes ne sont pas des améliorations mais des prérequis** : les habilitations et le
> RGPD. Un système qui sert à un agent un passage qu'il n'a pas le droit de lire est un
> incident, pas une imperfection, et « le prompt lui dit de ne pas le montrer » n'est pas un
> contrôle d'accès. Le filtre doit être dans la requête à l'index. Même leçon que
> l'Atelier 8 du J2.

---

## GraphRAG en production : le panorama des outils

Le graphe du notebook est écrit à la main pour être lisible. Voici ce que font les outils
dédiés, et ce que ça change.

**Microsoft GraphRAG** (Edge et al. 2024) ajoute la couche que nous n'avons pas : la
**détection de communautés**. L'algorithme de Leiden regroupe les nœuds densément connectés,
puis un LLM rédige un **résumé par communauté**, hiérarchiquement. Ça débloque les questions
globales, « quels sont les grands thèmes de ce corpus ? », auxquelles ni le vectoriel ni
notre traversée ne savent répondre. On parle alors de *local search* (notre approche : ancrer
puis traverser) et de *global search* (interroger les résumés). Le coût d'indexation est en
revanche considérable : plusieurs appels LLM par document, plus les résumés.

**LightRAG** (Guo et al. 2024) vise le même objectif pour bien moins cher, en supprimant les
résumés de communautés au profit d'un double niveau de retrieval (entités précises et thèmes
larges) sur un index unique. Paquet `lightrag-hku`, SDK autonome, **pas d'intégration
LangChain**.

**Les bases graphe intégrées à LangChain**, quand le graphe ne tient plus en mémoire :

| Paquet | Base | Infrastructure | Apport |
|---|---|---|---|
| `langchain-neo4j` | Neo4j | serveur (Docker ou Aura) | l'écosystème le plus riche : `GraphCypherQAChain` génère le Cypher, `Neo4jVector` fait l'hybride texte+graphe, GDS fournit Leiden |
| `langchain-kuzu` | Kùzu | **embarqué**, aucun serveur | Cypher complet sans infrastructure ; `KuzuQAChain` pour le text-to-Cypher |
| `langchain-memgraph` | Memgraph | serveur | orienté temps réel, compatible Cypher |

**Et l'extraction ?** `LLMGraphTransformer` (dans `langchain-experimental`, aussi exposé par
`langchain-neo4j`) fait en un appel ce que le Task 5.1 écrit à la main, avec `allowed_nodes`
et `allowed_relationships` en garde-fous. Le notebook l'écrit à la main pour une raison :
quand l'extraction déraille, et elle déraille, il faut pouvoir regarder dedans.

> **Le passage à l'échelle change l'outillage, pas le raisonnement.** Ancrer, traverser,
> sérialiser reste la boucle. Et la normalisation des entités reste le travail réel, quel que
> soit l'outil.

---

## Prérequis

Depuis la racine du dépôt :

```bash
uv python install 3.13
uv sync --python 3.13
uv run jupyter lab
```

Un `.env` à la racine avec `MISTRAL_API_KEY` et `MISTRAL_SERVER_URL` (**sans** `/v1`, les
notebooks l'ajoutent).

Modèles utilisés, tous exposés par le serveur de formation : `mistral-medium-latest` pour le
chat et le juge, `mistral-embed` (1 024 dimensions) pour les embeddings.

> **Poids de l'installation.** Ce thème ajoute `langchain-chroma`, `langchain-qdrant`,
> `rank-bm25` et `numpy` au `pyproject.toml`, soit **24 paquets** avec les dépendances
> transitives. `chromadb` tire à lui seul `onnxruntime`, `kubernetes` et `bcrypt` : comptez
> ~100 Mo et quelques minutes de `uv sync`. À faire **avant** la session, pas pendant.

Chroma est la base vectorielle de référence du notebook (chapitres 1 à 3) ; Qdrant n'apparaît
que dans l'encart comparatif. Si l'installation de `chromadb` est bloquée sur votre parc,
l'index NumPy écrit à la main au Task 1.2 rend les mêmes services : il faut alors remplacer
`recherche_dense` et le `retriever` du chapitre 2, les deux seuls points d'appui sur Chroma.

---

## Trois pièges vérifiés sur ce serveur

- **`/v1` obligatoire pour les embeddings aussi.** `MistralAIEmbeddings` poste sur
  `{endpoint}/embeddings` : sans le suffixe `/v1`, on obtient un `404`. Même gotcha que
  `ChatMistralAI`, documenté pour les 9 ateliers du J2.
- **`MistralAIEmbeddings` télécharge un tokenizer HuggingFace** au premier appel
  (`mistralai/Mixtral-8x7B-v0.1`) pour découper les lots par nombre de tokens. Derrière un
  proxy qui bloque `huggingface.co`, il émet un avertissement et repart sur un découpage
  approximatif : ça fonctionne, mais prévoyez la surprise en salle.
- **`ragas` ne s'importe plus** dans l'environnement unifié : sa dépendance `litellm` réclame
  `langchain_community.chat_models.vertexai`, module supprimé de `langchain-community 0.4`.
  C'est l'incompatibilité annoncée dans le
  [README de T2_Workflows](../../J1_Fondations/T2_Workflows/README.md). Le juge du chapitre 6
  est donc écrit en LangChain pur, avec le même protocole et les mêmes métriques.
  ⚠️ Conséquence au-delà de T4 : le bloc d'évaluation de `NB_T1a` est sous `try/except` et
  échoue donc **silencieusement** aujourd'hui.

---

## Ce que le notebook n'aborde pas

- **Détection de communautés** (Leiden) et *global search* : traité en référence ci-dessus.
- **Bases graphe serveur** (`langchain-neo4j`, `langchain-kuzu`) : mentionnées, non installées.
- **Re-ranking par cross-encoder** : exige un modèle local (`sentence-transformers`), hors
  périmètre du serveur de formation. RRF couvre le besoin en formation.
- **Ingestion multimodale** : `mistral-ocr-latest` est disponible sur le serveur, mais
  `mistral-voxtral` **ne l'est pas** : la partie audio annoncée par le support n'est pas
  démontrable.
- **RAPTOR, ColBERT, CRAG, Self-RAG** (parties 12-18 de `rag-from-scratch`) : CRAG et Self-RAG
  sont par nature du LangGraph, exclu du périmètre de ce thème.

---

## Références académiques

Les 13 sources citées dans le notebook, dans l'ordre d'apparition.

| Référence | Apport |
|---|---|
| **Lewis et al. (2020)** « Retrieval-Augmented Generation for Knowledge-Intensive NLP Tasks » [arXiv:2005.11401](https://arxiv.org/abs/2005.11401) | l'article fondateur du RAG |
| **Salton, Wong & Yang (1975)** « A Vector Space Model for Automatic Indexing » | la similarité cosinus |
| **Robertson & Walker (1994)** « Some Simple Effective Approximations to the 2-Poisson Model » SIGIR | BM25, avec k₁ ≈ 1,5 et b ≈ 0,75 |
| **Cormack, Clarke & Buettcher (2009)** « Reciprocal Rank Fusion outperforms Condorcet and individual Rank Learning Methods » SIGIR | RRF, et la constante k = 60 |
| **Gao et al. (2022)** « Precise Zero-Shot Dense Retrieval without Relevance Labels » [arXiv:2212.10496](https://arxiv.org/abs/2212.10496) | HyDE |
| **Liu et al. (2023)** « Lost in the Middle » [arXiv:2307.03172](https://arxiv.org/abs/2307.03172) | la dégradation sur contextes longs, d'où le choix de `k` |
| **Edge et al. (2024)** « From Local to Global: A Graph RAG Approach to Query-Focused Summarization » [arXiv:2404.16130](https://arxiv.org/abs/2404.16130) | Microsoft GraphRAG, local vs global search |
| **Guo et al. (2024)** « LightRAG: Simple and Fast Retrieval-Augmented Generation » [arXiv:2410.05779](https://arxiv.org/abs/2410.05779) | l'alternative légère à GraphRAG |
| **Es et al. (2023)** « RAGAS: Automated Evaluation of Retrieval Augmented Generation » [arXiv:2309.15217](https://arxiv.org/abs/2309.15217) | le protocole d'évaluation dont s'inspire le chapitre 6 |
| **Yao et al. (2022)** « ReAct » [arXiv:2210.03629](https://arxiv.org/abs/2210.03629) | rappel de T1, pour situer T4 |
| **Naismith (1892)**, *Scottish Mountaineering Club Journal* | cité pour mémoire : le fil rouge de T1 |
| **rag-from-scratch** (LangChain) : https://github.com/langchain-ai/rag-from-scratch | le dépôt dont ce thème reprend la progression (parties 1-9 et 15) |
| **Documentation LangChain** : https://docs.langchain.com/oss/python/langchain/rag | RAG, retrievers, vector stores, LCEL, structured output |
