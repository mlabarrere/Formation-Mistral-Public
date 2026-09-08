# 🚀 Jour 3 — LangChain Avancé avec Mistral AI

Trois thèmes approfondissent les patterns vus en J2 et introduisent les architectures
de production : workflows contrôlés par l'humain (dont un agent email multi-étapes),
recherche augmentée par récupération (RAG) et fine-tuning des modèles (niveau théorique).

🎯 **Public** : participants ayant suivi J1 et J2 (ou équivalent), à l'aise avec les
bases de LangChain/LangGraph et Mistral. Chaque thème dure **60 à 90 minutes**.

---

## 🗺️ Parcours

| Thème | Dossier | Question centrale |
|---|---|---|
| T1 — Workflows & HITL | `T1_Workflows_HITL/` | Comment concevoir un graphe LangGraph fiable avec interruption humaine ? |
| T2 — RAG avec LangChain | `T2_RAG/` | Comment ancrer les réponses du LLM dans des documents réels ? |
| T3 — Fine-tuning (théorie) | `T3_FineTuning/` | Quand et comment adapter un modèle à son domaine ? |

---

## 📁 Structure du dossier

```
J3_Avancé/
├── T1_Workflows_HITL/      ← graphe d'état, interrupt, checkpointer durable, agent email
│   ├── atelier/
│   └── NB_T1a_workflows_hitl.ipynb
├── T2_RAG/                 ← ingestion, retrieval, query translation, évaluation
│   ├── atelier/
│   ├── data/               ← documents de démonstration
│   └── NB_T2a_rag_langchain.ipynb
├── T3_FineTuning/          ← panorama théorique, LoRA, SFT, RLHF
│   ├── atelier/
│   └── NB_T3a_finetuning_theorie.ipynb
├── assets/                 ← images affichées dans les notebooks
├── data/                   ← données partagées entre thèmes
└── util/                   ← utilitaires communs (env, loaders…)
```

---

## 🛠️ Prérequis

- Environnement J2 fonctionnel (`J2_Hands On/.venv`) ; J3 peut réutiliser le même
  `.venv` ou en créer un dédié selon les nouvelles dépendances (ex. `chromadb`,
  `sentence-transformers`).
- Une clé **Mistral** et l'URL du serveur compatible avec l'API Mistral.
- Un compte **LangSmith** (gratuit) — fortement recommandé pour tracer les runs RAG.

---

## 🔐 Variables d'environnement

Copiez `example.env` vers `.env` et renseignez vos valeurs :

```bash
cp example.env .env
```

| Variable | Rôle |
|---|---|
| `MISTRAL_API_KEY` | **obligatoire** — clé d'accès au serveur Mistral. |
| `MISTRAL_SERVER_URL` | **obligatoire** — URL de base du serveur Mistral ; les notebooks ajoutent `/v1` automatiquement. |
| `LANGSMITH_API_KEY` | traçabilité LangSmith. |
| `LANGSMITH_TRACING` | `true` pour envoyer les traces à LangSmith. |
| `LANGSMITH_PROJECT` | nom du projet LangSmith pour J3. |
| `HUGGINGFACE_API_KEY` | *(T3 optionnel)* — accès aux modèles HuggingFace pour le fine-tuning. |

---

## 📚 Documentation officielle

- [LangGraph — Workflows & Agents](https://docs.langchain.com/oss/python/langgraph/workflows-agents)
- [LangGraph — Interrupts & HITL](https://langchain-ai.github.io/langgraph/concepts/human_in_the_loop/)
- [LangChain — RAG](https://docs.langchain.com/docs/concepts/rag/)
- [Mistral — Fine-tuning](https://docs.mistral.ai/capabilities/finetuning/)
- [LoRA — paper](https://arxiv.org/abs/2106.09685)
