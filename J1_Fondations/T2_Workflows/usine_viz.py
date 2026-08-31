"""Visualisations matplotlib / networkx du thème T1 (style aligné sur J2/T4b).

Trois vues, partagées par les deux notebooks (NB_T1a Mistral Workflows, NB_T1b LangGraph) pour qu'on
voie *la même usine, deux moteurs* :

1. :func:`dessiner_topologie` — le graphe d'orchestration (stations, branche acétate/métal, cycle de
   reprise). NB_T1a lui passe le **schéma** du workflow ; NB_T1b lui passe le **vrai graphe** extrait
   de LangGraph via ``compiled.get_graph()``.
2. :func:`dessiner_trajectoires` — le chemin réel de chaque ordre dans l'atelier (un point par étape,
   vert = conforme, rouge = défaut) : la boucle de reprise et le scrap se lisent d'un coup d'œil.
3. :func:`dessiner_kpis` — taux de succès par commande (couleur = verdict, annotation = reprises).

Palette (identique à T4b) : rouge ``#d64550``, bleu ``#6b8fb5``, orange ``#f2a900``, vert ``#2e8b57``.

Format d'entrée commun (``resultats``)
-------------------------------------
:func:`dessiner_trajectoires` et :func:`dessiner_kpis` attendent une **liste de dicts**, un par commande ::

    {
      "id":       str,             # identifiant (le préfixe "CMD-2026-" est retiré à l'affichage)
      "gamme":    "standard"|"premium",
      "verdict":  "accept"|"scrap"|"rework",
      "reprises": int,             # nombre de reprises (0 = passé du premier coup)
      "hitl":     bool,            # un point de validation humaine a-t-il été déclenché ?
      "a_temps":  bool | None,     # livré à temps ? (None si non expédiée)
      "kpis":     {"taux_succes": float, "cout_eur": float, ...},   # cf. usine_lunettes.calcul_metriques
      "parcours": [{"station": str, "ok": bool}, ...],              # une entrée par étape franchie
    }

Toutes les fonctions renvoient l'``Axes`` matplotlib (pour composition/tests) et laissent le notebook
faire ``plt.show()``.
"""
import collections

import matplotlib.pyplot as plt
import networkx as nx

# Palette T4b (réutilisée pour l'unité visuelle entre thèmes).
ROUGE, BLEU, ORANGE, VERT, GRIS = "#d64550", "#6b8fb5", "#f2a900", "#2e8b57", "#9aa0a6"


def _couches(G, source):
    """Assigne à chaque nœud une **couche** (profondeur) pour un rendu gauche→droite en colonnes.

    La couche = distance BFS depuis ``source`` en **ignorant les arcs retour** (ceux d'un cycle, comme
    ``qc → usinage`` pour la reprise) : sans cette précaution, un cycle rendrait le layering ambigu.
    Les nœuds atteignables uniquement par un arc retour sont placés une couche après le maximum.

    Parameters
    ----------
    G : networkx.DiGraph
        Graphe orienté à disposer.
    source : hashable
        Nœud de départ (ex. ``"appro"`` pour Mistral, ``"__start__"`` pour LangGraph).

    Returns
    -------
    dict
        ``{nœud: index_de_couche (int)}``.
    """
    couche = {source: 0}
    dq = collections.deque([source])
    while dq:
        u = dq.popleft()
        for v in G.successors(u):
            if v not in couche:                     # 1re visite = arc avant → fixe la couche
                couche[v] = couche[u] + 1
                dq.append(v)
    m = max(couche.values(), default=0)
    for n in G.nodes:                               # nœuds vus seulement via un arc retour
        couche.setdefault(n, m + 1)
    return couche


def dessiner_topologie(edges, titre, source, couleurs_noeuds=None, ax=None):
    """Dessine un graphe d'orchestration orienté, disposé en couches (gauche→droite).

    Les **arcs avant** (progression) sont gris pleins ; les **arcs retour** (cycle de reprise) sont
    rouges pointillés et incurvés — la boucle de rework saute ainsi aux yeux.

    Parameters
    ----------
    edges : list of tuple
        Arêtes ``(source, cible)`` ou ``(source, cible, label)``. Le label (ex. ``"acétate"``,
        ``"accept"``) est affiché sur l'arête s'il est non vide.
    titre : str
        Titre de la figure.
    source : hashable
        Nœud d'entrée, passé à :func:`_couches` pour le layering.
    couleurs_noeuds : dict, optional
        ``{nœud: couleur}`` pour surligner certains nœuds (par défaut : bleu). Convention du thème :
        orange = décision/HITL, vert = expédition, gris = terminal/technique.
    ax : matplotlib.axes.Axes, optional
        Axes cible ; créé si absent.

    Returns
    -------
    matplotlib.axes.Axes
        L'axes dessiné.
    """
    couleurs_noeuds = couleurs_noeuds or {}
    G = nx.DiGraph()
    for e in edges:
        G.add_edge(e[0], e[1], label=(e[2] if len(e) > 2 else ""))
    couche = _couches(G, source)
    for n in G.nodes:
        G.nodes[n]["subset"] = couche[n]            # 'subset' = clé attendue par multipartite_layout
    pos = nx.multipartite_layout(G, subset_key="subset")
    if ax is None:
        _, ax = plt.subplots(figsize=(11, 4.6))
    cols = [couleurs_noeuds.get(n, BLEU) for n in G.nodes]
    # Sépare arcs avant / retour d'après les couches (un arc retour va vers une couche <=).
    avant = [(u, v) for u, v in G.edges if couche[v] > couche[u]]
    retour = [(u, v) for u, v in G.edges if couche[v] <= couche[u]]   # = cycle de reprise
    nx.draw_networkx_nodes(G, pos, node_color=cols, node_size=1600, edgecolors="white", ax=ax)
    nx.draw_networkx_labels(G, pos, font_size=7.5, font_color="white", ax=ax)
    nx.draw_networkx_edges(G, pos, edgelist=avant, edge_color="#888", arrows=True,
                           node_size=1600, ax=ax)
    nx.draw_networkx_edges(G, pos, edgelist=retour, edge_color=ROUGE, arrows=True, style="dashed",
                           connectionstyle="arc3,rad=0.35", node_size=1600, ax=ax)  # incurvé = lisible
    lbls = {(u, v): d["label"] for u, v, d in G.edges(data=True) if d["label"]}
    nx.draw_networkx_edge_labels(G, pos, edge_labels=lbls, font_size=7, ax=ax,
                                 bbox=dict(boxstyle="round,pad=0.15", fc="white", ec="none", alpha=0.8))
    ax.set_title(titre, fontsize=11, fontweight="bold")
    ax.axis("off")
    plt.tight_layout()
    return ax


def dessiner_trajectoires(resultats, ax=None):
    """Trace le chemin de chaque ordre : une ligne par ordre, un point coloré par étape franchie.

    Vert = étape conforme, rouge = défaut. Un ordre repris apparaît **plus long** (il repasse par
    l'usinage/QC) ; un scrap s'arrête tôt. La longueur des lignes diffère donc volontairement.

    Parameters
    ----------
    resultats : list of dict
        Voir le format ``resultats`` documenté au niveau module (clés lues : ``id``, ``matiere``,
        ``verdict``, ``hitl``, ``parcours``).
    ax : matplotlib.axes.Axes, optional
        Axes cible ; créé (hauteur adaptée au nombre d'ordres) si absent.

    Returns
    -------
    matplotlib.axes.Axes
    """
    if ax is None:
        _, ax = plt.subplots(figsize=(11, 0.75 * len(resultats) + 1.6))
    longest = max(resultats, key=lambda r: len(r["parcours"]))["parcours"]  # axe x = plus long parcours
    for i, r in enumerate(resultats):
        y = len(resultats) - 1 - i                  # 1er ordre en haut
        parcours = r["parcours"]
        ax.plot(range(len(parcours)), [y] * len(parcours), color="#ccc", zorder=1)
        for x, etape in enumerate(parcours):
            ax.scatter(x, y, s=150, zorder=3, edgecolors="white",
                       color=(VERT if etape.get("ok", True) else ROUGE))
        etiq = f"{r['id'].replace('CMD-2026-', '')} [{r['gamme']}] → {r['verdict']}"
        if r.get("hitl"):
            etiq += " (HITL)"
        ax.text(-0.5, y, etiq, ha="right", va="center", fontsize=8)
    ax.set_xticks(range(len(longest)))
    ax.set_xticklabels([e["station"] for e in longest], rotation=45, ha="right", fontsize=7)
    ax.set_yticks([])
    ax.set_xlim(-3.2, len(longest) - 0.5)           # marge gauche pour les étiquettes d'ordres
    ax.set_title("Trajectoire des ordres dans l'atelier (vert = étape OK, rouge = défaut)",
                 fontsize=11, fontweight="bold")
    plt.tight_layout()
    return ax


def dessiner_kpis(resultats, ax=None):
    """Taux de succès par commande : barres colorées par verdict, annotées du nb de reprises.

    Métriques volontairement **évidentes** (pas de jargon industriel) : la hauteur = taux de succès
    (part d'étapes réussies du 1er coup) ; la couleur = verdict (vert accepté / rouge rebut) ;
    l'annotation = nombre de reprises et retard éventuel.

    Parameters
    ----------
    resultats : list of dict
        Voir le format ``resultats`` au niveau module (clés lues : ``id``, ``verdict``, ``reprises``,
        ``a_temps``, ``kpis.taux_succes``).
    ax : matplotlib.axes.Axes, optional
        Axes cible ; créé si absent.

    Returns
    -------
    matplotlib.axes.Axes
    """
    import numpy as np
    from matplotlib.patches import Patch
    ids = [r["id"].replace("CMD-2026-", "") for r in resultats]
    succes = [r["kpis"]["taux_succes"] for r in resultats]
    x = np.arange(len(ids))
    if ax is None:
        _, ax = plt.subplots(figsize=(10, 4))
    couleurs = [VERT if r["verdict"] == "accept" else ROUGE for r in resultats]
    ax.bar(x, succes, 0.6, color=couleurs, edgecolor="white")
    for xi, r, s in zip(x, resultats, succes):       # annotation au-dessus de chaque barre
        note = f"{r.get('reprises', 0)} reprise(s)"
        if r.get("a_temps") is False:
            note += "\nen retard"
        ax.text(xi, s + 0.02, note, ha="center", va="bottom", fontsize=7)
    ax.set_xticks(x)
    ax.set_xticklabels(ids, fontsize=8)
    ax.set_ylim(0, 1.2)
    ax.set_ylabel("taux de succès (part d'étapes OK du 1er coup)")
    ax.legend(handles=[Patch(color=VERT, label="accepté"), Patch(color=ROUGE, label="rebut")],
              fontsize=8, loc="lower right")
    ax.set_title("Résultat par commande", fontsize=11, fontweight="bold")
    plt.tight_layout()
    return ax


def _stations_ordonnees(resultats):
    """Renvoie la liste ordonnée (1re apparition) de toutes les stations dans resultats."""
    seen, out = set(), []
    for r in resultats:
        for e in r["parcours"]:
            s = e["station"]
            if s not in seen:
                seen.add(s)
                out.append(s)
    return out


_PALETTE_STATIONS = [BLEU, ORANGE, "#c084fc", "#34d399", GRIS, "#fb923c", "#60a5fa", "#f472b6"]


def dessiner_couts(resultats, ax=None):
    """Décomposition du coût par station (barres empilées horizontales, une ligne par commande).

    Chaque segment = coût d'une station ; le total est annoté à droite. Permet d'identifier la
    station la plus coûteuse et l'impact des reprises (la station fabrication apparaît deux fois
    pour une commande reprise).

    Parameters
    ----------
    resultats : list of dict
        Voir le format ``resultats`` au niveau module (clés lues : ``id``, ``parcours.cout_eur``,
        ``kpis.cout_eur``).
    ax : matplotlib.axes.Axes, optional
        Axes cible ; créé si absent.

    Returns
    -------
    matplotlib.axes.Axes
    """
    import numpy as np
    stations = _stations_ordonnees(resultats)
    coul = {s: _PALETTE_STATIONS[i % len(_PALETTE_STATIONS)] for i, s in enumerate(stations)}
    ids = [r["id"].replace("CMD-2026-", "") for r in resultats]
    y = np.arange(len(ids))
    if ax is None:
        _, ax = plt.subplots(figsize=(11, 0.7 * len(resultats) + 2.2))
    lefts = np.zeros(len(resultats))
    for s in stations:
        vals = np.array([
            sum(e["cout_eur"] for e in r["parcours"] if e["station"] == s)
            for r in resultats
        ])
        ax.barh(y, vals, left=lefts, color=coul[s], label=s, edgecolor="white", height=0.55)
        lefts += vals
    for i, r in enumerate(resultats):
        ax.text(lefts[i] + 0.05, y[i], f"{r['kpis']['cout_eur']:.1f} €",
                va="center", fontsize=8)
    ax.set_yticks(y)
    ax.set_yticklabels(ids, fontsize=8)
    ax.set_xlabel("coût (€)")
    ax.set_title("Décomposition du coût par station", fontsize=11, fontweight="bold")
    ax.legend(fontsize=7, loc="lower right")
    plt.tight_layout()
    return ax


def dessiner_gantt(resultats, ax=None):
    """Diagramme de Gantt des commandes : une ligne par ordre, un segment coloré par station.

    La largeur de chaque segment = durée de la station (minutes). Les étapes en défaut sont
    coloriées en rouge, les reprises se lisent comme une répétition de la même station sur la ligne.

    Parameters
    ----------
    resultats : list of dict
        Voir le format ``resultats`` au niveau module (clés lues : ``id``, ``parcours.minutes``,
        ``parcours.station``, ``parcours.ok``).
    ax : matplotlib.axes.Axes, optional
        Axes cible ; créé si absent.

    Returns
    -------
    matplotlib.axes.Axes
    """
    import numpy as np
    stations = _stations_ordonnees(resultats)
    coul = {s: _PALETTE_STATIONS[i % len(_PALETTE_STATIONS)] for i, s in enumerate(stations)}
    ids = [r["id"].replace("CMD-2026-", "") for r in resultats]
    y = np.arange(len(ids))
    if ax is None:
        _, ax = plt.subplots(figsize=(11, 0.7 * len(resultats) + 2.2))
    for i, r in enumerate(resultats):
        t = 0.0
        for e in r["parcours"]:
            duree = e.get("minutes", 0.0)
            col = ROUGE if not e.get("ok", True) else coul.get(e["station"], BLEU)
            ax.barh(y[i], duree, left=t, color=col, edgecolor="white", height=0.55, alpha=0.88)
            if duree >= 3:
                ax.text(t + duree / 2, y[i], e["station"],
                        ha="center", va="center", fontsize=6, color="white")
            t += duree
    ax.set_yticks(y)
    ax.set_yticklabels(ids, fontsize=8)
    ax.set_xlabel("minutes cumulées")
    ax.set_title("Gantt des commandes (rouge = étape en défaut, reprise visible par répétition)",
                 fontsize=11, fontweight="bold")
    plt.tight_layout()
    return ax


def dessiner_entonnoir(resultats, ax=None):
    """Entonnoir qualité : nb de commandes sans défaut à chaque étape (goulot d'étranglement).

    Pour chaque station, la hauteur = nombre d'ordres qui ont traversé cette station avec ``ok=True``.
    La ligne pointillée grise = total des commandes. Permet d'identifier la station qui génère le
    plus de défauts.

    Parameters
    ----------
    resultats : list of dict
        Voir le format ``resultats`` au niveau module (clés lues : ``parcours.station``,
        ``parcours.ok``).
    ax : matplotlib.axes.Axes, optional
        Axes cible ; créé si absent.

    Returns
    -------
    matplotlib.axes.Axes
    """
    import numpy as np
    stations = _stations_ordonnees(resultats)
    n_total = len(resultats)
    counts = [
        sum(1 for r in resultats
            if any(e["station"] == s and e.get("ok", True) for e in r["parcours"]))
        for s in stations
    ]
    x = np.arange(len(stations))
    if ax is None:
        _, ax = plt.subplots(figsize=(11, 4))
    couleurs = [VERT if c == n_total else ORANGE if c >= n_total * 0.75 else ROUGE
                for c in counts]
    ax.bar(x, counts, color=couleurs, edgecolor="white", width=0.6)
    ax.axhline(n_total, linestyle="--", color=GRIS, linewidth=1,
               label=f"total ({n_total} commandes)")
    for xi, c in zip(x, counts):
        ax.text(xi, c + 0.05, str(c), ha="center", va="bottom", fontsize=9, fontweight="bold")
    ax.set_xticks(x)
    ax.set_xticklabels(stations, rotation=30, ha="right", fontsize=8)
    ax.set_ylim(0, n_total + 1)
    ax.set_ylabel("commandes sans défaut à cette étape")
    ax.set_title("Entonnoir qualité — ordres passant chaque étape sans défaut",
                 fontsize=11, fontweight="bold")
    ax.legend(fontsize=8)
    plt.tight_layout()
    return ax
