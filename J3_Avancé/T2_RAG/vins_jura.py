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
#: Extensions reconnues par :func:`charger_corpus`, dans l'ordre de priorité.
#: Un même document livré en plusieurs formats (``arbois.html`` et ``arbois.pdf``)
#: n'est chargé qu'une fois, via le premier format disponible de cette liste.
EXTENSIONS = (".md", ".html", ".htm")


def _texte_html(chemin: Path) -> tuple[str, str]:
    """Extrait (titre, texte) d'un cahier des charges HTML.

    Le balisage de navigation est retiré : ce qui reste est le texte réglementaire,
    seul contenu utile à l'indexation.
    """
    from bs4 import BeautifulSoup

    soup = BeautifulSoup(chemin.read_text(encoding="utf-8", errors="replace"), "html.parser")
    for balise in soup(["script", "style", "nav", "header", "footer"]):
        balise.decompose()

    titre = ""
    if soup.title and soup.title.string:
        titre = soup.title.string.strip()
    elif soup.h1:
        titre = soup.h1.get_text(" ", strip=True)

    lignes, precedente = [], None
    for ligne in soup.get_text("\n", strip=True).splitlines():
        # Les exports INAO répètent le titre en en-tête de page : on déduplique
        # les lignes consécutives identiques, sinon chaque chunk commence pareil.
        if ligne and ligne != precedente:
            lignes.append(ligne)
        precedente = ligne
    return titre or chemin.stem, "\n".join(lignes)


def _texte_markdown(chemin: Path) -> tuple[str, str]:
    """Extrait (titre, texte) d'une fiche markdown, le titre venant du premier ``# ...``."""
    texte = chemin.read_text(encoding="utf-8")
    premiere = texte.lstrip().splitlines()[0] if texte.strip() else ""
    return premiere.lstrip("# ").strip() or chemin.stem, texte


def charger_corpus(dossier: Path | str | None = None) -> list[dict]:
    """Charge le corpus, trié par nom de fichier.

    Accepte le markdown et le HTML. Les cahiers des charges de l'INAO sont livrés en
    HTML et en PDF ; seul le HTML est lu, le PDF étant la même chose en moins
    exploitable. Un document présent dans deux formats n'est donc chargé qu'une fois.

    Parameters
    ----------
    dossier : Path or str or None
        Dossier contenant les documents. Si ``None``, utilise ``CORPUS_DIR``.

    Returns
    -------
    list of dict
        Un dict par document : ``{"fichier", "titre", "texte"}``.

    Raises
    ------
    FileNotFoundError
        Si le dossier est absent ou ne contient aucun document exploitable.

    Examples
    --------
    >>> fiches = charger_corpus()
    >>> len(fiches)
    7
    """
    base = Path(dossier) if dossier is not None else CORPUS_DIR
    if not base.is_dir():
        raise FileNotFoundError(f"Corpus introuvable : {base}")

    lecteurs = {".md": _texte_markdown, ".html": _texte_html, ".htm": _texte_html}

    # Un document = un nom de fichier sans extension. Si arbois.html et arbois.pdf
    # coexistent, on garde le premier format listé dans EXTENSIONS.
    par_document: dict[str, Path] = {}
    for extension in EXTENSIONS:
        for chemin in base.glob(f"*{extension}"):
            par_document.setdefault(chemin.stem, chemin)

    fiches = []
    for stem in sorted(par_document):
        chemin = par_document[stem]
        titre, texte = lecteurs[chemin.suffix.lower()](chemin)
        fiches.append({"fichier": chemin.name, "titre": titre, "texte": texte})

    if not fiches:
        attendues = ", ".join(EXTENSIONS)
        raise FileNotFoundError(f"Aucun document ({attendues}) dans {base}")
    return fiches


# ─────────────────────────────────────────────────────────────────────────────
# Jeux de questions : le cœur de la démonstration
# ─────────────────────────────────────────────────────────────────────────────
# Chaque question porte une réponse de référence `ref` : c'est la clé de correction
# utilisée par le juge LLM du chapitre 6.

# Répondables avec un seul passage du corpus : le RAG vectoriel y excelle.
QUESTIONS_SIMPLES: list[dict] = [
    {
        "question": "Quel est le rendement autorisé en AOC Château-Chalon ?",
        "ref": (
            "30 hectolitres par hectare. Le rendement butoir est fixé à "
            "50 hectolitres à l'hectare."
        ),
    },
    {
        "question": (
            "Combien de temps une eau-de-vie « Marc du Jura » destinée à la "
            "consommation doit-elle vieillir sous bois, et dans quels contenants ?"
        ),
        "ref": (
            "Au moins 24 mois sous bois, dans des logements d'une capacité "
            "unitaire maximale de 600 litres, sans interruption."
        ),
    },
    {
        "question": (
            "Quelle bouteille est réservée au conditionnement des vins de "
            "l'appellation Château-Chalon, et quelle est sa contenance ?"
        ),
        "ref": (
            "La bouteille dite « Clavelin », ou « bouteille à vin jaune », d'une "
            "contenance de 62 centilitres environ. Elle porte le cachet moulé au nom "
            "de l'appellation et lui est exclusivement réservée."
        ),
    },
    {
        "question": "Sur quelles communes s'étend l'aire géographique de l'AOC L'Étoile ?",
        "ref": (
            "Quatre communes du Jura : L'Étoile, Plainoiseau, Quintigny et Saint-Didier. "
            "La récolte, la vinification, l'élaboration et l'élevage y sont assurés."
        ),
    },
]

#: Questions dont la réponse n'est écrite dans **aucun** document pris isolément.
#: Elles exigent de croiser plusieurs cahiers des charges, ou d'agréger sur les sept.
#: C'est le pivot du notebook : le RAG vectoriel échoue ici par construction, quel que
#: soit le réglage du retrieval, et c'est le GraphRAG qui les résout.
QUESTIONS_MULTIHOP: list[dict] = [
    {
        "question": (
            "Combien d'appellations du corpus peuvent produire un « vin jaune », "
            "lesquelles, et laquelle y est entièrement consacrée ?"
        ),
        "ref": (
            "Quatre. Arbois, Côtes du Jura et L'Étoile peuvent compléter leur nom par "
            "la mention facultative « vin jaune » ; Château-Chalon est réservée aux "
            "vins blancs tranquilles dits « vins jaunes » et n'a donc aucune mention "
            "complémentaire à ajouter. Le Crémant du Jura, le Macvin du Jura et le "
            "Marc du Jura n'en produisent pas. Les quatre imposent la même règle : "
            "élevage en fût de chêne sans ouillage jusqu'au 15 décembre de la 6e année "
            "suivant la récolte, dont 60 mois au moins sous voile."
        ),
        "pourquoi": (
            "Agrégation sur les sept cahiers des charges. Le piège : marc-du-jura.html "
            "est le seul document qui contienne à la fois « vin jaune » et la liste des "
            "six autres appellations, mais c'est pour en INTERDIRE la mention sur "
            "l'étiquette. C'est donc lui que le retrieval remonte, et il ne permet pas "
            "de répondre."
        ),
    },
    {
        "question": (
            "Parmi les sept cahiers des charges, quelle appellation impose le "
            "rendement le plus bas et laquelle le plus élevé ?"
        ),
        "ref": (
            "Le plus bas est celui de Château-Chalon : 30 hectolitres par hectare "
            "(butoir 50). Le plus élevé est celui du Crémant du Jura : 78 hectolitres "
            "par hectare pour les parcelles dont l'écartement moyen entre rangs est "
            "inférieur ou égal à 1,6 mètre. Entre les deux, Arbois, Côtes du Jura, "
            "L'Étoile et Macvin du Jura sont à 60 hl/ha en blanc et 55 hl/ha en rouge "
            "et rosé. Le Marc du Jura ne fixe pas de rendement à l'hectare mais un "
            "rendement en alcool."
        ),
        "pourquoi": (
            "Comparaison chiffrée sur six documents : chaque article VIII ne donne que "
            "le rendement de son appellation, aucun ne cite celui d'une autre. Il faut "
            "les lire tous puis les ordonner."
        ),
    },
    {
        "question": (
            "Quel cépage est autorisé par les sept appellations du corpus, et lequel "
            "l'est par six d'entre elles seulement ? Quelle appellation fait exception ?"
        ),
        "ref": (
            "Le savagnin est autorisé par les sept appellations. Le chardonnay l'est "
            "par six : Château-Chalon fait exception, ses vins étant issus "
            "exclusivement du seul cépage savagnin."
        ),
        "pourquoi": (
            "Agrégation sur les sept documents, doublée d'une détection d'ABSENCE. "
            "Répondre suppose d'avoir lu les sept articles V et remarqué que l'un "
            "d'eux ne mentionne pas le chardonnay. Un retrieval qui rate un seul "
            "document donne une réponse fausse sans aucun signal."
        ),
    },
]

#: Questions plausibles dans le domaine mais dont la réponse n'est nulle part.
#: Un cahier des charges ne fixe ni prix, ni hiérarchie de millésimes, ni accords
#: mets-vins. La bonne réponse du système est le refus.
QUESTIONS_HORS_SCOPE: list[dict] = [
    {
        "question": "Quel est le prix de vente d'un clavelin de Château-Chalon ?",
        "ref": (
            "Information absente du corpus : le système doit refuser de répondre. "
            "Un cahier des charges de l'INAO ne fixe aucun prix ni tarif."
        ),
    },
    {
        "question": "Quels millésimes de vin jaune du Jura sont considérés comme les plus grands ?",
        "ref": (
            "Information absente du corpus : le système doit refuser de répondre. "
            "Les cahiers des charges ne hiérarchisent pas les millésimes ; ils "
            "n'imposent l'indication du millésime que sur les étiquettes des « vins de "
            "paille »."
        ),
    },
    {
        "question": (
            "Avec quels plats accompagner un Macvin du Jura, et à quelle température "
            "le servir ?"
        ),
        "ref": (
            "Information absente du corpus : le système doit refuser de répondre. "
            "Les cahiers des charges décrivent les caractéristiques organoleptiques du "
            "produit mais ne donnent ni accord mets-vins ni température de service."
        ),
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
    "PRODUIT_TYPE",   # AOC              -> TypeDeVin  (blanc tranquille, mousseux, eau-de-vie...)
    "ADMET_MENTION",  # AOC              -> Mention    (vin jaune, vin de paille, vieux, tres vieux)
    "AUTORISE",       # AOC              -> Cepage     (cépages principaux uniquement)
    "RECOLTEE_SUR",   # AOC              -> Commune    (seulement les aires de <= 5 communes)
    "RENDEMENT_MAX",  # AOC              -> Valeur     (rendement de base, en hl/ha)
    "ELEVAGE_MIN",    # AOC ou Mention   -> Duree      (durée minimale réglementaire)
)

#: Graphe « gold » extrait à la main des sept cahiers des charges de ``corpus_vins/``.
#: Chaque triplet est littéralement vérifiable dans le texte source ; c'est la vérité
#: terrain contre laquelle le notebook mesure la précision et le rappel de l'extraction
#: automatique. Un graphe de référence faux invaliderait toute la mesure.
#:
#: Conventions retenues, et elles ne sont pas neutres :
#: - seuls les **cépages principaux** figurent ici. Les variétés accessoires et celles
#:   soumises à convention INAO (aligoté, gringet, sacy...) sont ignorées.
#: - ``RECOLTEE_SUR`` n'est émis que pour Château-Chalon et L'Étoile, dont l'aire de
#:   récolte tient en quatre communes. Arbois en compte douze, les autres davantage.
#: - Château-Chalon ``ADMET_MENTION`` « vin jaune » : son article III dit que l'appellation
#:   est réservée aux « vins blancs tranquilles dits vins jaunes ». Son article II précise
#:   pourtant « pas de disposition particulière » sur les mentions : les deux lectures se
#:   défendent, on retient la plus littérale.
#: - les couleurs ne sont émises que pour les AOC de vins tranquilles : parler de
#:   « rouge » pour un vin de liqueur ou une eau-de-vie induirait en erreur.
TRIPLETS_REFERENCE: list[tuple[str, str, str]] = [
    # ── Arbois ────────────────────────────────────────────────── arbois.html
    ("Arbois",          "ADMET_MENTION", "vin de paille"),
    ("Arbois",          "ADMET_MENTION", "vin jaune"),
    ("Arbois",          "AUTORISE",      "chardonnay"),
    ("Arbois",          "AUTORISE",      "pinot noir"),
    ("Arbois",          "AUTORISE",      "poulsard"),
    ("Arbois",          "AUTORISE",      "savagnin"),
    ("Arbois",          "AUTORISE",      "trousseau"),
    ("Arbois",          "PRODUIT_TYPE",  "blanc tranquille"),
    ("Arbois",          "PRODUIT_TYPE",  "rosé"),
    ("Arbois",          "PRODUIT_TYPE",  "rouge"),
    ("Arbois",          "RENDEMENT_MAX", "55 hl/ha"),
    ("Arbois",          "RENDEMENT_MAX", "60 hl/ha"),
    # ── Château-Chalon ──────────────────────────────────── chateau-chalon.html
    ("Château-Chalon",  "ADMET_MENTION", "vin jaune"),
    ("Château-Chalon",  "AUTORISE",      "savagnin"),
    ("Château-Chalon",  "ELEVAGE_MIN",   "60 mois sous voile"),
    ("Château-Chalon",  "PRODUIT_TYPE",  "blanc tranquille"),
    ("Château-Chalon",  "RECOLTEE_SUR",  "Château-Chalon"),
    ("Château-Chalon",  "RECOLTEE_SUR",  "Domblans"),
    ("Château-Chalon",  "RECOLTEE_SUR",  "Menetru-le-Vignoble"),
    ("Château-Chalon",  "RECOLTEE_SUR",  "Nevy-sur-Seille"),
    ("Château-Chalon",  "RENDEMENT_MAX", "30 hl/ha"),
    # ── Côtes du Jura ────────────────────────────────────── cotes-du-jura.html
    ("Côtes du Jura",   "ADMET_MENTION", "vin de paille"),
    ("Côtes du Jura",   "ADMET_MENTION", "vin jaune"),
    ("Côtes du Jura",   "AUTORISE",      "chardonnay"),
    ("Côtes du Jura",   "AUTORISE",      "pinot noir"),
    ("Côtes du Jura",   "AUTORISE",      "poulsard"),
    ("Côtes du Jura",   "AUTORISE",      "savagnin"),
    ("Côtes du Jura",   "AUTORISE",      "trousseau"),
    ("Côtes du Jura",   "PRODUIT_TYPE",  "blanc tranquille"),
    ("Côtes du Jura",   "PRODUIT_TYPE",  "rosé"),
    ("Côtes du Jura",   "PRODUIT_TYPE",  "rouge"),
    ("Côtes du Jura",   "RENDEMENT_MAX", "55 hl/ha"),
    ("Côtes du Jura",   "RENDEMENT_MAX", "60 hl/ha"),
    # ── Crémant du Jura ──────────────────────────────────── cremant-du-jura.html
    ("Crémant du Jura", "AUTORISE",      "chardonnay"),
    ("Crémant du Jura", "AUTORISE",      "pinot gris"),
    ("Crémant du Jura", "AUTORISE",      "pinot noir"),
    ("Crémant du Jura", "AUTORISE",      "poulsard"),
    ("Crémant du Jura", "AUTORISE",      "savagnin"),
    ("Crémant du Jura", "AUTORISE",      "trousseau"),
    ("Crémant du Jura", "ELEVAGE_MIN",   "12 mois à compter du tirage"),
    ("Crémant du Jura", "PRODUIT_TYPE",  "mousseux"),
    ("Crémant du Jura", "RENDEMENT_MAX", "78 hl/ha"),
    # ── L'Étoile ─────────────────────────────────────────────── letoile.html
    ("L'Étoile",        "ADMET_MENTION", "vin de paille"),
    ("L'Étoile",        "ADMET_MENTION", "vin jaune"),
    ("L'Étoile",        "AUTORISE",      "chardonnay"),
    ("L'Étoile",        "AUTORISE",      "savagnin"),
    ("L'Étoile",        "PRODUIT_TYPE",  "blanc tranquille"),
    ("L'Étoile",        "RECOLTEE_SUR",  "L'Étoile"),
    ("L'Étoile",        "RECOLTEE_SUR",  "Plainoiseau"),
    ("L'Étoile",        "RECOLTEE_SUR",  "Quintigny"),
    ("L'Étoile",        "RECOLTEE_SUR",  "Saint-Didier"),
    ("L'Étoile",        "RENDEMENT_MAX", "60 hl/ha"),
    # ── Macvin du Jura ───────────────────────────────────── macvin-du-jura.html
    ("Macvin du Jura",  "AUTORISE",      "chardonnay"),
    ("Macvin du Jura",  "AUTORISE",      "pinot noir"),
    ("Macvin du Jura",  "AUTORISE",      "poulsard"),
    ("Macvin du Jura",  "AUTORISE",      "savagnin"),
    ("Macvin du Jura",  "AUTORISE",      "trousseau"),
    ("Macvin du Jura",  "ELEVAGE_MIN",   "10 mois sous bois"),
    ("Macvin du Jura",  "PRODUIT_TYPE",  "vin de liqueur"),
    ("Macvin du Jura",  "RENDEMENT_MAX", "55 hl/ha"),
    ("Macvin du Jura",  "RENDEMENT_MAX", "60 hl/ha"),
    # ── Marc du Jura ───────────────────────────────────────── marc-du-jura.html
    # Pas de RENDEMENT_MAX : son rendement est un rendement de distillation
    # (litres d'alcool pur pour 100 kg de marcs), inexprimable en hl/ha.
    ("Marc du Jura",    "ADMET_MENTION", "très vieux"),
    ("Marc du Jura",    "ADMET_MENTION", "vieux"),
    ("Marc du Jura",    "AUTORISE",      "chardonnay"),
    ("Marc du Jura",    "AUTORISE",      "pinot gris"),
    ("Marc du Jura",    "AUTORISE",      "pinot noir"),
    ("Marc du Jura",    "AUTORISE",      "poulsard"),
    ("Marc du Jura",    "AUTORISE",      "savagnin"),
    ("Marc du Jura",    "AUTORISE",      "trousseau"),
    ("Marc du Jura",    "ELEVAGE_MIN",   "24 mois sous bois"),
    ("Marc du Jura",    "PRODUIT_TYPE",  "eau-de-vie"),
    # ── Règles portant sur la mention, pas sur l'appellation ───────────────
    ("très vieux",      "ELEVAGE_MIN",   "8 ans sous bois"),
    ("vieux",           "ELEVAGE_MIN",   "5 ans sous bois"),
    ("vin de paille",   "ELEVAGE_MIN",   "18 mois sous bois"),
    ("vin jaune",       "ELEVAGE_MIN",   "60 mois sous voile"),
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
