"""Module partagé T2 : vins du Jura (RAG et GraphRAG).

**But : fournir le corpus, les jeux de questions et les briques de calcul communes au
notebook NB_T2a**, sans aucune dépendance LangChain ni Mistral. Le décor est un petit
vignoble jurassien de sept cuvées, choisi parce qu'un corpus viticole est naturellement
*relationnel* : un domaine est dirigé par une personne, situé dans une commune, et
produit des cuvées issues de cépages relevant d'appellations.

C'est cette structure qui permet de montrer, sur le même corpus, ce que le RAG vectoriel
sait faire et ce qu'il ne sait pas faire.

Idées mises en scène
--------------------
- **Corpus délibérément fragmenté** : l'information nécessaire aux questions multi-sauts
  est répartie entre plusieurs fiches. Aucun chunk ne contient à lui seul la réponse.
- **Trois familles de questions** : ``QUESTIONS_SIMPLES`` (un seul chunk suffit),
  ``QUESTIONS_MULTIHOP`` (deux sauts ou une agrégation, cas où le RAG vectoriel échoue),
  ``QUESTIONS_HORS_SCOPE`` (le système doit refuser de répondre).
- **Graphe de référence** : ``TRIPLETS_REFERENCE`` est le graphe « gold » écrit à la main.
  Il sert à mesurer la précision et le rappel de l'extraction faite par le LLM.
- **Ambiguïté volontaire** : « Château-Chalon » et « L'Étoile » sont à la fois des
  communes et des appellations. C'est le cas dans la réalité, et c'est exactement ce qui
  rend le typage des entités indispensable dans un graphe de connaissances.

Garanties techniques
--------------------
- **Zéro dépendance LangChain / Mistral** : pur Python + ``numpy`` (déjà dans le ``.venv``
  racine). Importable depuis n'importe quel notebook de la formation.
- **Aucun effet de bord à l'import** : le corpus n'est lu que lors de l'appel explicite à
  ``charger_corpus()``.
- **Déterministe** : aucun appel réseau, aucun tirage aléatoire.

Note honnête
------------
Les **domaines, vignerons, cuvées et lieux-dits sont fictifs**. En revanche les
appellations, les cépages, les communes et les règles d'élevage (durée sous voile,
clavelin de 62 cl, méthode traditionnelle, mentions autorisées) sont réels et
vérifiables. Inventer les producteurs évite d'attribuer à de vraies exploitations des
caractéristiques qu'elles n'ont pas.
"""
from __future__ import annotations

from pathlib import Path

# ─────────────────────────────────────────────────────────────────────────────
# Localisation du corpus
# ─────────────────────────────────────────────────────────────────────────────
# Résolu par rapport à ce fichier, pas au répertoire courant : le notebook
# fonctionne donc quel que soit le dossier depuis lequel Jupyter a été lancé.
CORPUS_DIR: Path = Path(__file__).parent / "corpus_vins"


# ─────────────────────────────────────────────────────────────────────────────
# Chargement du corpus
# ─────────────────────────────────────────────────────────────────────────────
def charger_corpus(dossier: Path | str | None = None) -> list[dict]:
    """Charge les fiches markdown du corpus, triées par nom de fichier.

    Parameters
    ----------
    dossier : Path or str or None
        Dossier contenant les fiches ``.md``. Si ``None``, utilise ``CORPUS_DIR``.

    Returns
    -------
    list of dict
        Un dict par fiche : ``{"fichier", "titre", "texte"}``. ``titre`` est extrait
        de la première ligne ``# ...`` du markdown.

    Raises
    ------
    FileNotFoundError
        Si le dossier est absent ou ne contient aucun fichier ``.md``.

    Examples
    --------
    >>> fiches = charger_corpus()
    >>> len(fiches)
    7
    """
    base = Path(dossier) if dossier is not None else CORPUS_DIR
    if not base.is_dir():
        raise FileNotFoundError(f"Corpus introuvable : {base}")

    fiches = []
    for chemin in sorted(base.glob("*.md")):
        texte = chemin.read_text(encoding="utf-8")
        premiere = texte.lstrip().splitlines()[0] if texte.strip() else ""
        titre = premiere.lstrip("# ").strip() or chemin.stem
        fiches.append({"fichier": chemin.name, "titre": titre, "texte": texte})

    if not fiches:
        raise FileNotFoundError(f"Aucune fiche .md dans {base}")
    return fiches


# ─────────────────────────────────────────────────────────────────────────────
# Jeux de questions : le cœur de la démonstration
# ─────────────────────────────────────────────────────────────────────────────
# Chaque question porte une réponse de référence `ref` : c'est la clé de correction
# utilisée par le juge LLM du chapitre 6.

# Répondables avec un seul passage du corpus : le RAG vectoriel y excelle.
QUESTIONS_SIMPLES: list[dict] = [
    {
        "question": "Quel est le volume d'un clavelin ?",
        "ref": "62 centilitres.",
    },
    {
        "question": "Quel cépage entre dans la cuvée Ploussard des Curons ?",
        "ref": "Le poulsard, écrit et prononcé ploussard à Pupillin.",
    },
    {
        "question": "Combien de temps un vin de l'appellation Château-Chalon doit-il vieillir ?",
        "ref": "Au moins six ans et trois mois, dont soixante mois sous voile.",
    },
    {
        "question": "Qui dirige le Domaine de la Combe Grise ?",
        "ref": "Louise Perrenot, qui a créé le domaine en 2009.",
    },
]

# Deux sauts de relation, ou une agrégation sur tout le corpus.
# Aucun chunk ne contient la réponse : le RAG vectoriel échoue par construction.
QUESTIONS_MULTIHOP: list[dict] = [
    {
        "question": (
            "Quels cépages sont travaillés par les domaines dont le siège est à "
            "Château-Chalon ?"
        ),
        "ref": (
            "Savagnin, chardonnay et pinot noir. Le Domaine des Clavelins travaille le "
            "savagnin ; le Domaine de la Roche Percée travaille le savagnin (Sous Voile) "
            "ainsi que le chardonnay et le pinot noir (Bulles de Voiteur)."
        ),
        "pourquoi": "2 sauts : commune -> domaines -> cuvées -> cépages, réparti sur 3 fiches.",
    },
    {
        "question": "Quel vigneron dirige un domaine qui produit à la fois un vin jaune et un crémant ?",
        "ref": (
            "Salomé Vuillod, du Domaine de la Roche Percée : Sous Voile est un vin jaune, "
            "Bulles de Voiteur est un crémant."
        ),
        "pourquoi": "Intersection de deux ensembles décrits dans deux fiches distinctes.",
    },
    {
        "question": (
            "Combien de cuvées du corpus utilisent le savagnin, et dans quelles "
            "appellations ?"
        ),
        "ref": (
            "Quatre cuvées : Clavelin d'Automne et Sous Voile en Château-Chalon, "
            "Les Marnes Bleues en Côtes du Jura, Étoile Filante en L'Étoile. "
            "Soit trois appellations."
        ),
        "pourquoi": "Agrégation : il faut avoir vu les 7 fiches pour compter juste.",
    },
]

# Hors du corpus : la bonne réponse est de refuser.
QUESTIONS_HORS_SCOPE: list[dict] = [
    {
        "question": "Quel est le prix d'une bouteille de Bulles de Voiteur ?",
        "ref": "Information absente du corpus : le système doit refuser de répondre.",
    },
    {
        "question": "Quel est le rendement maximal autorisé en AOC Arbois ?",
        "ref": "Information absente du corpus : le système doit refuser de répondre.",
    },
    {
        "question": "Quel temps fera-t-il demain à Arbois ?",
        "ref": "Hors sujet : le système doit refuser de répondre.",
    },
]


# ─────────────────────────────────────────────────────────────────────────────
# Graphe de référence, écrit à la main : il sert de vérité terrain
# ─────────────────────────────────────────────────────────────────────────────
# Sept types de relations. Noter la distinction SIEGE_A / VINIFIE_A : c'est elle qui
# rend la première question multi-sauts insoluble en RAG vectoriel, puisque le siège
# du Domaine de la Roche Percée (Château-Chalon) et la parcelle de sa cuvée
# effervescente (Voiteur) ne sont pas dans la même commune.
RELATIONS: tuple[str, ...] = (
    "DIRIGE",     # Vigneron  -> Domaine
    "SIEGE_A",    # Domaine   -> Commune  (siège social et caves)
    "PRODUIT",    # Domaine   -> Cuvee
    "VINIFIE_A",  # Cuvee     -> Commune  (commune de la parcelle)
    "ISSU_DE",    # Cuvee     -> Cepage
    "RELEVE_DE",  # Cuvee     -> Appellation
    "EST_UN",     # Cuvee     -> TypeDeVin
)

TRIPLETS_REFERENCE: list[tuple[str, str, str]] = [
    # ── Qui dirige quoi ──────────────────────────────────────────────────────
    ("Adèle Renaud",           "DIRIGE",    "Domaine des Clavelins"),
    ("Salomé Vuillod",         "DIRIGE",    "Domaine de la Roche Percée"),
    ("Marc Vasseur",           "DIRIGE",    "Domaine du Bief Rouge"),
    ("Louise Perrenot",        "DIRIGE",    "Domaine de la Combe Grise"),
    ("Jean-Baptiste Chapuis",  "DIRIGE",    "Domaine Chapuis"),
    # ── Où sont les sièges ───────────────────────────────────────────────────
    ("Domaine des Clavelins",      "SIEGE_A", "Château-Chalon"),
    ("Domaine de la Roche Percée", "SIEGE_A", "Château-Chalon"),
    ("Domaine du Bief Rouge",      "SIEGE_A", "Pupillin"),
    ("Domaine de la Combe Grise",  "SIEGE_A", "L'Étoile"),
    ("Domaine Chapuis",            "SIEGE_A", "Montigny-lès-Arsures"),
    # ── Qui produit quelle cuvée ─────────────────────────────────────────────
    ("Domaine des Clavelins",      "PRODUIT", "Clavelin d'Automne"),
    ("Domaine de la Roche Percée", "PRODUIT", "Sous Voile"),
    ("Domaine de la Roche Percée", "PRODUIT", "Bulles de Voiteur"),
    ("Domaine du Bief Rouge",      "PRODUIT", "Les Marnes Bleues"),
    ("Domaine du Bief Rouge",      "PRODUIT", "Ploussard des Curons"),
    ("Domaine de la Combe Grise",  "PRODUIT", "Étoile Filante"),
    ("Domaine Chapuis",            "PRODUIT", "Rosée des Corvées"),
    # ── Où est la parcelle de chaque cuvée ───────────────────────────────────
    ("Clavelin d'Automne",   "VINIFIE_A", "Château-Chalon"),
    ("Sous Voile",           "VINIFIE_A", "Château-Chalon"),
    ("Les Marnes Bleues",    "VINIFIE_A", "Pupillin"),
    ("Ploussard des Curons", "VINIFIE_A", "Pupillin"),
    ("Étoile Filante",       "VINIFIE_A", "L'Étoile"),
    ("Bulles de Voiteur",    "VINIFIE_A", "Voiteur"),
    ("Rosée des Corvées",    "VINIFIE_A", "Montigny-lès-Arsures"),
    # ── Quel cépage dans quelle cuvée ────────────────────────────────────────
    ("Clavelin d'Automne",   "ISSU_DE", "savagnin"),
    ("Sous Voile",           "ISSU_DE", "savagnin"),
    ("Les Marnes Bleues",    "ISSU_DE", "savagnin"),
    ("Ploussard des Curons", "ISSU_DE", "poulsard"),
    ("Étoile Filante",       "ISSU_DE", "chardonnay"),
    ("Étoile Filante",       "ISSU_DE", "savagnin"),
    ("Bulles de Voiteur",    "ISSU_DE", "chardonnay"),
    ("Bulles de Voiteur",    "ISSU_DE", "pinot noir"),
    ("Rosée des Corvées",    "ISSU_DE", "poulsard"),
    ("Rosée des Corvées",    "ISSU_DE", "trousseau"),
    # ── Quelle appellation ───────────────────────────────────────────────────
    ("Clavelin d'Automne",   "RELEVE_DE", "Château-Chalon"),
    ("Sous Voile",           "RELEVE_DE", "Château-Chalon"),
    ("Les Marnes Bleues",    "RELEVE_DE", "Côtes du Jura"),
    ("Ploussard des Curons", "RELEVE_DE", "Arbois"),
    ("Étoile Filante",       "RELEVE_DE", "L'Étoile"),
    ("Bulles de Voiteur",    "RELEVE_DE", "Crémant du Jura"),
    ("Rosée des Corvées",    "RELEVE_DE", "Crémant du Jura"),
    # ── Quel type de vin ─────────────────────────────────────────────────────
    ("Clavelin d'Automne",   "EST_UN", "vin jaune"),
    ("Sous Voile",           "EST_UN", "vin jaune"),
    ("Les Marnes Bleues",    "EST_UN", "blanc ouillé"),
    ("Ploussard des Curons", "EST_UN", "rouge"),
    ("Étoile Filante",       "EST_UN", "blanc sec"),
    ("Bulles de Voiteur",    "EST_UN", "crémant"),
    ("Rosée des Corvées",    "EST_UN", "crémant"),
]


# ─────────────────────────────────────────────────────────────────────────────
# Briques de calcul réutilisées dans le notebook
# ─────────────────────────────────────────────────────────────────────────────
def cosinus(a, b) -> float:
    """Similarité cosinus entre deux vecteurs.

    Implémentation directe de la formule de Salton, Wong & Yang (1975) :
    ``cos(a, b) = (a . b) / (||a|| * ||b||)``. Exposée ici pour que le notebook
    puisse montrer le calcul « à la main » avant d'utiliser un index vectoriel.

    Parameters
    ----------
    a, b : array_like
        Deux vecteurs de même dimension.

    Returns
    -------
    float
        Valeur dans ``[-1, 1]``. Vaut ``0.0`` si l'un des vecteurs est nul.

    Examples
    --------
    >>> round(cosinus([1, 0], [1, 0]), 6)
    1.0
    >>> round(cosinus([1, 0], [0, 1]), 6)
    0.0
    """
    import numpy as np  # noqa: PLC0415

    va, vb = np.asarray(a, dtype=float), np.asarray(b, dtype=float)
    denom = float(np.linalg.norm(va) * np.linalg.norm(vb))
    return 0.0 if denom == 0.0 else float(va @ vb / denom)


def rrf(classements: list[list[str]], k: int = 60) -> list[tuple[str, float]]:
    """Fusionne plusieurs classements par Reciprocal Rank Fusion.

    Chaque document reçoit ``1 / (k + rang)`` pour chaque classement où il apparaît,
    le rang commençant à 1. Les scores sont sommés, puis les documents triés par score
    décroissant. RRF n'utilise que les **rangs**, jamais les scores d'origine : c'est ce
    qui lui permet de fusionner un classement dense (cosinus, entre 0 et 1) et un
    classement lexical (BM25, non borné) sans aucune normalisation.

    Référence : Cormack, Clarke & Buettcher, *Reciprocal Rank Fusion outperforms Condorcet
    and individual Rank Learning Methods*, SIGIR 2009. La valeur ``k = 60`` est celle de
    l'article ; elle amortit le poids des toutes premières positions.

    Parameters
    ----------
    classements : list of list of str
        Une liste par système de recherche, contenant des identifiants de documents
        ordonnés du plus au moins pertinent.
    k : int
        Constante d'amortissement. 60 par défaut.

    Returns
    -------
    list of tuple
        ``[(identifiant, score), ...]`` trié par score décroissant.

    Examples
    --------
    >>> rrf([["a", "b"], ["b", "a"]])  # doctest: +ELLIPSIS
    [('a', 0.032...), ('b', 0.032...)]
    """
    scores: dict[str, float] = {}
    for classement in classements:
        for rang, doc_id in enumerate(classement, start=1):
            scores[doc_id] = scores.get(doc_id, 0.0) + 1.0 / (k + rang)
    return sorted(scores.items(), key=lambda kv: kv[1], reverse=True)


# ─────────────────────────────────────────────────────────────────────────────
# Smoke test local
# ─────────────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    fiches = charger_corpus()
    print(f"Corpus : {len(fiches)} fiches dans {CORPUS_DIR.name}/")
    for f in fiches:
        print(f"  {f['fichier']:28s} {len(f['texte']):5d} car.  {f['titre']}")

    total = sum(len(f["texte"]) for f in fiches)
    print(f"\nTotal : {total} caractères")

    print(
        f"\nQuestions : {len(QUESTIONS_SIMPLES)} simples, "
        f"{len(QUESTIONS_MULTIHOP)} multi-sauts, "
        f"{len(QUESTIONS_HORS_SCOPE)} hors-scope"
    )

    entites = {t[0] for t in TRIPLETS_REFERENCE} | {t[2] for t in TRIPLETS_REFERENCE}
    print(
        f"Graphe de référence : {len(TRIPLETS_REFERENCE)} triplets, "
        f"{len(entites)} entités, {len(RELATIONS)} types de relations"
    )

    print(f"\nRRF (démo)  : {rrf([['a', 'b', 'c'], ['c', 'a']])}")
    print(f"Cosinus 1/1 : {cosinus([1, 0, 0], [1, 0, 0])}")
    print(f"Cosinus 1/0 : {cosinus([1, 0, 0], [0, 1, 0])}")
