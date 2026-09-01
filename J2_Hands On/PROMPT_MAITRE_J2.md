# Prompt maître — moderniser et rendre ultra pédagogiques les notebooks J2

> Copie-colle le bloc ci-dessous dans Codex depuis la racine du dépôt.

```text
Tu travailles dans le dépôt de formation courant. Ta mission est de moderniser et de
réécrire en place uniquement les notebooks `J2_Hands On/L4_tools.ipynb` à
`J2_Hands On/L9_HITL.ipynb`, ainsi que les fichiers de support J2 explicitement
autorisés ci-dessous. Le résultat doit être exécutable, reproductible et ultra
pédagogique pour des adultes débutants.

## Résultat attendu

- Six notebooks en français, prévus pour 30 à 45 minutes chacun.
- Les scénarios du cours LangChain Essentials restent reconnaissables.
- Le code utilise `mistral-large-latest`, `temperature=0`, `MISTRAL_API_KEY` et
  `MISTRAL_SERVER_URL`.
- Chaque notion est expliquée avant le code, prédite avant l’exécution, puis relue
  après le résultat.
- Les sorties sont nettoyées dans les fichiers livrés.
- L’environnement J2 est isolé, verrouillé et reconstruit avec Python 3.13.

## Périmètre et sécurité

Tu peux modifier uniquement :

- `J2_Hands On/L4_tools.ipynb`
- `J2_Hands On/L5_tools_with_mcp.ipynb`
- `J2_Hands On/L6_memory.ipynb`
- `J2_Hands On/L7_structuredOutput.ipynb`
- `J2_Hands On/L8_dynamic.ipynb`
- `J2_Hands On/L9_HITL.ipynb`
- `J2_Hands On/pyproject.toml`
- `J2_Hands On/uv.lock`
- `J2_Hands On/.python-version`
- `J2_Hands On/example.env`
- `J2_Hands On/README.md`
- les métadonnées kernel des six notebooks.

Ne modifie jamais L1–L3, `studio/`, `.env`, le `.venv` racine ni le
`requirements.txt` racine. Ne lis et n’affiche jamais `.env` ou une valeur secrète.
Utilise uniquement les variables déjà présentes dans le processus d’exécution.
Préserve toutes les modifications utilisateur hors périmètre.

## Orchestration multi-agents obligatoire

Commence par inspecter le dépôt, l’état Git, les six notebooks, leurs sources amont,
les dépendances et la documentation officielle. Ne rédige rien avant d’avoir publié
un contrat partagé.

Lance en parallèle trois sous-agents d’analyse :

1. un architecte pédagogique pour la progression L4→L9, les analogies ELI5, les
   exercices et la cohérence des emojis ;
2. un expert versions et APIs pour les versions stables, les migrations LangChain,
   Mistral et MCP, et les contraintes Windows ;
3. un responsable QA et documentation pour les oracles, les liens officiels et les
   critères d’acceptation.

Synthétise leurs conclusions et modernise d’abord l’environnement. Lance ensuite
deux vagues de trois auteurs indépendants : L4/L5/L6, puis L7/L8/L9. Un seul auteur
possède un notebook donné. Chaque auteur rend les changements, les pages officielles
consultées, ses tests et ses limites Mistral. Termine par trois relectures croisées
L4–L5, L6–L7 et L8–L9. Classe les constats en bloquant, important ou cosmétique et
limite les retours aux auteurs à deux tours.

Pendant toute l’opération, publie des points d’avancement courts et concrets. Ne
laisse pas une commande lente masquer le travail parallèle.

## Environnement J2

- Conserve le `.venv` racine intact.
- Crée `J2_Hands On/.venv` avec Python 3.13.
- Écris `3.13` dans `.python-version` et
  `requires-python = ">=3.13,<3.14"` dans `pyproject.toml`.
- Si un `.venv` J2 incompatible existe, renomme-le avec un suffixe de sauvegarde
  daté avant d’en recréer un.
- Recherche au moment de l’exécution les dernières versions stables, non retirées et
  sans préversion. Laisse `uv` résoudre leur compatibilité et fige tout dans
  `uv.lock`.
- Dépendances directes : `langchain`, `langchain-core`, `langgraph`,
  `langchain-mistralai`, `langchain-mcp-adapters`, `sqlalchemy`, `python-dotenv`,
  `packaging`, `pydantic`, `jupyter`, `ipykernel`, `nbclient`, `nbformat`.
- Dépendances de développement : `ruff`, `nbdime`.
- Retire `langchain-openai`, `langchain-anthropic` et `langgraph-cli[inmem]`.

Commandes de référence, lancées depuis `J2_Hands On` :

    uv python install 3.13
    uv lock --upgrade --resolution highest --prerelease disallow --python 3.13
    uv sync --frozen --extra dev --python 3.13
    uv lock --check
    uv pip check --python .venv/Scripts/python.exe
    uv run --frozen jupyter lab

Ajoute au README ces commandes exactes et un tableau des versions directes réellement
résolues. Vérifie par smoke test chaque import direct et confirme que l’interpréteur
est celui de `J2_Hands On/.venv`.

Pour L5, utilise la dernière version stable de `mcp-server-time` via `uvx`. Respecte
sa contrainte déclarée `mcp>=1.29.0,<2` et n’ajoute pas de contournement redondant.
Teste le lancement Windows avant de conserver un bloc de compatibilité.

## Contrat pédagogique commun

Adopte un ELI5 pour adultes : phrases courtes, une idée à la fois, analogies simples
et définition du vocabulaire technique à la première apparition. Utilise cette
signalétique sans décoration gratuite :

- 🎯 objectif ; 🧠 intuition ou prédiction ; 🗺️ schéma mental ;
- 🛠️ construction ; ▶️ exécution ; 👀 résultat attendu ;
- 🔍 lecture de la sortie ; ⚠️ piège ; 🧪 exercice ;
- ✅ correction ; 🧭 acquis et transition ; 📚 documentation ;
- ⚙️ spécificité Windows ; ⏱️ durée.

Avant chaque cellule importante, demande ce que l’apprenant prévoit. Après son
exécution, indique précisément ce qu’il doit observer et pourquoi. Distingue toujours
ce que fait LangChain, ce que décide Mistral et ce qu’exécute Python ou le système
externe.

Chaque notebook contient au moins un micro-exercice avec cellule `TODO`, consigne,
critères de réussite et correction dans `<details>`. Il se termine par trois à cinq
acquis et une transition explicite vers la leçon suivante.

Chaque API importante reçoit deux niveaux de documentation :

1. un lien officiel précis dans le Markdown au premier usage ;
2. un commentaire de code proche de l’appel important, puis une section finale
   `## 📚 Documentation officielle`.

Références minimales :

- L4 : https://docs.langchain.com/oss/python/langchain/tools et
  https://docs.langchain.com/oss/python/langchain/agents
- L5 : https://docs.langchain.com/oss/python/langchain/mcp
- L6 : https://docs.langchain.com/oss/python/langchain/short-term-memory
- L7 : https://docs.langchain.com/oss/python/langchain/structured-output
- L8 : https://docs.langchain.com/oss/python/langchain/context-engineering et
  https://docs.langchain.com/oss/python/langchain/middleware/overview
- L9 : https://docs.langchain.com/oss/python/langchain/human-in-the-loop
- Commun : https://docs.langchain.com/oss/python/integrations/chat/mistralai
- Function calling Mistral, si pertinent :
  https://docs.mistral.ai/studio/conversations/function-calling

Vérifie réellement les liens et n’utilise pas de billet tiers lorsqu’une page
officielle répond directement au besoin.

## Attendus propres à chaque leçon

- L4 — Tools : fonction Python → `@tool` → description et schéma → décision Mistral
  → exécution Python → `ToolMessage` → réponse finale. Affiche `tool_calls`.
- L5 — MCP : compare tool local et MCP, explique serveur/adapter/transport, affiche
  les tools découverts et isole Windows dans un encadré ⚙️.
- L6 — Memory : compare sans mémoire, même `thread_id` et nouveau thread. Dis
  explicitement que le modèle n’apprend pas : LangChain/LangGraph persistent l’état.
- L7 — Structured output : compare texte libre, `TypedDict` et Pydantic. Inspecte
  `structured_response` et sa validation. Utilise `ToolStrategy` si la stratégie
  automatique du proxy Mistral n’est pas fiable.
- L8 — Dynamic prompt : compare prompt statique et `@dynamic_prompt` avec deux
  contextes. Précise qu’un prompt n’est pas un contrôle d’accès de production.
- L9 — HITL : montre proposition → interruption → décision → reprise, avec rejet et
  approbation dans deux scénarios distincts.

Pour les exemples SQL, ouvre une copie temporaire de Chinook en lecture seule et
fournis au modèle le schéma nécessaire : aucune table ne doit être inventée.

## Validation et définition de terminé

Valide le JSON des notebooks et leurs métadonnées Python 3.13. Exécute chaque
notebook depuis un kernel propre sur une copie temporaire, en laissant les originaux
intacts. N’invente jamais un succès réseau : si les variables du processus manquent,
exécute les validations hors ligne et rapporte précisément le test bloqué.

Contrôle notamment : tool visible en L4 ; découverte MCP et absence de `uvx` en L5 ;
isolation des threads en L6 ; schéma en L7 ; variation contextuelle en L8 ;
interruption, rejet et approbation en L9. Répète les scénarios sensibles au tool
calling. Vérifie la base SQL sur une copie temporaire et son intégrité après test.

Enfin, lance `uv lock --check`, `uv sync --frozen`, `uv pip check`, les smoke tests,
la vérification des liens, et une recherche de secrets, dépendances OpenAI inutiles,
Markdown anglais résiduel, outputs et compteurs d’exécution. Nettoie tous les outputs
des notebooks livrés. Ne déclare le travail terminé que lorsque tous les critères
vérifiables sont satisfaits et liste honnêtement les validations éventuellement
bloquées par des identifiants externes.
```
