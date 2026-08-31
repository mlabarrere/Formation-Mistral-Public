"""Simulation d'une petite usine (habillage : manufacture de lunettes du Jura) — thème T1.

**But : servir de décor à l'orchestration, rien de plus.** On imagine une usine simple — recevoir une
commande, s'approvisionner, fabriquer, assembler, contrôler, expédier — pour illustrer *comment on
orchestre* un enchaînement d'étapes fiable. **Aucune connaissance métier n'est requise** : les stations
sont des fonctions génériques ; ce qui compte, c'est le flux (séquence, branche, reprise, validation
humaine), pas la fabrication réelle.

Ce module est le **cœur partagé** du diptyque T1. Les deux notebooks l'importent tel quel :

- `NB_T1a_workflow_mistral`   enveloppe chaque station dans une **activité Mistral Workflows** (`@wf.activity`) ;
- `NB_T1b_workflow_langgraph` enveloppe chaque station dans un **nœud / tool LangGraph**.

La **logique est identique** des deux côtés ; seul le **moteur d'orchestration** change.

Idées mises en scène (indépendantes du métier)
----------------------------------------------
- **Branche** : une commande *Standard* et une *Premium* ne suivent pas le même chemin (la Premium
  passe par une étape de **finition** supplémentaire).
- **Reprise (cycle)** : un défaut *réparable* renvoie la commande en fabrication (une reprise), puis
  elle repasse au contrôle.
- **Rebut (scrap)** : un défaut *irrécupérable* (une pièce cassée) met la commande au rebut, sans reprise.
- **Validation humaine (HITL)** : si le délai d'appro dépasse l'échéance client, un humain doit trancher.
- **Métriques évidentes** : taux de succès, nombre de reprises, coût, livré à temps (oui/non).

Garanties techniques
--------------------
- **Pur Python, zéro dépendance** (importable partout, y compris dans une activité).
- **Reproductible** : l'aléa de chaque station est *seedé* par ``(id_commande, station, tentative)``
  (:func:`_rng`) — un même run rejoué donne le même résultat (indispensable pour illustrer le *replay*).
- **Scénarios** : le champ ``profil`` d'une commande force une trajectoire nette (``reprise``, ``casse``,
  ``urgent``) pour que les commandes « golden » racontent chacune une histoire claire.

Convention de retour
--------------------
Chaque station renvoie un ``dict`` avec au moins ``ok: bool`` et ``defaut: str | None`` (``None`` si
conforme, sinon un nom de défaut lisible : ``"defaut_fabrication"``, ``"piece_cassee"``…). Le contrôle
qualité (:func:`controler_qualite`) lit ces défauts pour décider ``accept`` / ``rework`` / ``scrap``.
"""
from __future__ import annotations

import random
import textwrap
from dataclasses import dataclass, field
from typing import Literal, Optional

# Deux gammes de produit : elles suivront deux chemins de production différents (la branche).
Gamme = Literal["standard", "premium"]
# Verdict du contrôle qualité : accepté / à reprendre / mis au rebut.
Verdict = Literal["accept", "rework", "scrap"]

# ─────────────────────────────────────────────────────────────────────────────
# Constantes (coûts et durées indicatifs, choisis pour la lisibilité — pas des vraies valeurs métier)
# ─────────────────────────────────────────────────────────────────────────────
# Coût (€/commande) et temps de cycle (minutes/commande) par station.
STATIONS = {
    "commande":   {"cout": 0.2, "minutes": 2.0},
    "appro":      {"cout": 2.0, "minutes": 1.0},   # coût matière moyen ramené à la commande
    "fabrication": {"cout": 1.5, "minutes": 10.0},
    "finition":   {"cout": 1.2, "minutes": 8.0},   # étape supplémentaire, uniquement en gamme Premium
    "assemblage": {"cout": 1.0, "minutes": 6.0},
    "controle":   {"cout": 0.5, "minutes": 4.0},
    "expedition": {"cout": 0.4, "minutes": 3.0},
}

# Délai d'approvisionnement (jours) selon la gamme — la Premium met plus longtemps à sourcer.
# Ce délai est comparé à l'échéance client : s'il la dépasse, on déclenche une validation humaine.
DELAI_APPRO_JOURS = {"standard": 20, "premium": 40}

# Défauts qu'on ne peut PAS réparer : ils envoient la commande au rebut (pas de reprise possible).
DEFAUTS_IRRECUPERABLES = {"piece_cassee"}


@dataclass
class Commande:
    """Commande qui traverse l'usine — le « contrat » d'état passé de station en station.

    C'est l'équivalent métier du *state* d'un workflow durable (NB_T1a) ou du *state* d'un graphe
    LangGraph (NB_T1b) : chaque station lit les champs d'entrée et enrichit l'état.

    Attributes
    ----------
    id : str
        Identifiant unique (sert aussi de graine d'aléa via :func:`_rng`).
    modele : str
        Nom du produit (pur habillage : « Lunettes Morez … »).
    gamme : {"standard", "premium"}
        Détermine le **chemin de production** (la Premium passe par la finition).
    quantite : int
        Nombre d'unités commandées (comparé au MOQ à l'approvisionnement).
    echeance_jours : int, default 40
        Délai promis au client. Comparé au délai d'appro pour la validation humaine et le « livré à temps ».
    profil : str, default "nominal"
        Scénario : ``nominal`` (aléa pur), ``reprise`` (force un défaut réparable), ``casse`` (force un
        défaut irrécupérable), ``urgent`` (échéance très courte).
    etape : str, default "recue"
        Dernière station franchie (mise à jour par :func:`_journaliser`).
    defauts : list of str
        Défauts constatés, au format ``"station:defaut"`` (alimenté par :func:`_journaliser`).
    historique : list of dict
        Une entrée par station exécutée — **source des métriques** (voir :func:`calcul_metriques`).
    tentative_qc : int, default 0
        Numéro de passe qualité (0 = première ; 1 = après une reprise). Pilote la boucle de reprise.
    """
    id: str
    modele: str
    gamme: Gamme
    quantite: int
    echeance_jours: int = 40
    profil: str = "nominal"              # nominal | reprise | casse | urgent
    etape: str = "recue"
    defauts: list = field(default_factory=list)
    historique: list = field(default_factory=list)  # 1 entrée / station exécutée → métriques
    tentative_qc: int = 0


# ─────────────────────────────────────────────────────────────────────────────
# Helpers internes
# ─────────────────────────────────────────────────────────────────────────────
def _rng(id_commande: str, station: str, tentative: int = 0) -> random.Random:
    """Générateur aléatoire **reproductible** propre à un (commande, station, tentative).

    Deux appels identiques produisent la même séquence : c'est ce qui permet de « rejouer » une
    station à l'identique (démonstration du *replay*). Une reprise (``tentative`` différent) re-tire
    un aléa neuf — un défaut réparable peut donc disparaître à la 2ᵉ passe.

    Parameters
    ----------
    id_commande, station : str
        Composantes de la graine (découplent l'aléa entre commandes et entre stations).
    tentative : int, default 0
        Numéro de passe.

    Returns
    -------
    random.Random
        Instance seedée à utiliser localement.
    """
    return random.Random(f"{id_commande}|{station}|{tentative}")


def _journaliser(cmd: Commande, station: str, ok: bool,
                 defaut: Optional[str], metriques: dict) -> dict:
    """Enregistre le passage d'une commande à une station dans son ``historique`` (source des métriques).

    Mute ``cmd`` : ajoute une entrée d'historique, empile le défaut éventuel (préfixé du nom de
    station), met à jour ``cmd.etape``.

    Parameters
    ----------
    cmd : Commande
        Commande mise à jour en place.
    station : str
        Nom de la station (doit exister dans :data:`STATIONS`).
    ok : bool
        Étape conforme ou non.
    defaut : str or None
        Nom du défaut si non conforme, sinon ``None``.
    metriques : dict
        Métriques additionnelles (fusionnées dans l'entrée).

    Returns
    -------
    dict
        L'entrée créée : ``{"station", "ok", "defaut", "cout_eur", "minutes", **metriques}``.
    """
    entree = {
        "station": station,
        "ok": ok,
        "defaut": defaut,
        "cout_eur": STATIONS[station]["cout"],
        "minutes": STATIONS[station]["minutes"],
        **metriques,
    }
    cmd.historique.append(entree)
    if defaut:
        cmd.defauts.append(f"{station}:{defaut}")   # provenance conservée pour l'audit
    cmd.etape = station
    return entree


def router_gamme(gamme: Gamme) -> str:
    """Aiguille une commande selon sa gamme (la **branche** de production).

    Sert de règle de routage aux deux moteurs (handoff Mistral / arête conditionnelle LangGraph).

    Parameters
    ----------
    gamme : {"standard", "premium"}

    Returns
    -------
    str
        ``"finition"`` pour la Premium (étape supplémentaire), ``"assemblage"`` pour la Standard.
    """
    return "finition" if gamme == "premium" else "assemblage"


def w(texte: str, etiquette: str = "", largeur: int = 96) -> str:
    """Replie une chaîne pour l'affichage console (évite le scroll horizontal dans les notebooks).

    Parameters
    ----------
    texte : str
        Texte à afficher.
    etiquette : str, default ""
        Préfixe court (ex. ``"✅"``, ``"•"``) aligné avec les lignes de continuation.
    largeur : int, default 96
        Largeur cible en colonnes.

    Returns
    -------
    str
        Le texte replié, prêt pour ``print``.
    """
    prefixe = f"{etiquette} " if etiquette else ""
    corps = textwrap.fill(str(texte), width=largeur - len(prefixe),
                          subsequent_indent=" " * len(prefixe))
    return f"{prefixe}{corps}"


# ─────────────────────────────────────────────────────────────────────────────
# Stations (tools fakés) — fonctions pures, seedées. Génériques : aucune connaissance métier requise.
# ─────────────────────────────────────────────────────────────────────────────
def recevoir_commande(id_commande: str, gamme: str, quantite: int) -> dict:
    """Station 1 — Réception : valide la commande (quantité positive, gamme connue).

    Parameters
    ----------
    id_commande : str
        Identifiant.
    gamme : str
        Doit valoir ``"standard"`` ou ``"premium"``.
    quantite : int
        Doit être strictement positive.

    Returns
    -------
    dict
        ``{"ok": bool, "issues": list[str]}`` — ``issues`` liste les problèmes de saisie.
    """
    issues = []
    if quantite <= 0:
        issues.append("quantité invalide")
    if gamme not in ("standard", "premium"):
        issues.append(f"gamme inconnue: {gamme}")
    return {"ok": len(issues) == 0, "issues": issues}


def approvisionner(id_commande: str, gamme: str, quantite: int) -> dict:
    """Station 2 — Approvisionnement : réconcilie la quantité avec le **MOQ** et calcule le **délai**.

    Parameters
    ----------
    id_commande : str
        Identifiant.
    gamme : {"standard", "premium"}
        Fixe le MOQ (300 standard / 150 premium) et le délai d'appro (voir :data:`DELAI_APPRO_JOURS`).
    quantite : int
        Quantité demandée.

    Returns
    -------
    dict
        ``{"ok": bool, "moq": int, "extra_needed": int, "delai_jours": int, "cout_matiere_eur": float}``
        — ``extra_needed`` = surplus imposé si la quantité est sous le MOQ (MOQ = minimum de commande).
    """
    moq = 300 if gamme == "standard" else 150
    extra = max(0, moq - quantite)                          # surplus si commande sous le MOQ
    delai = DELAI_APPRO_JOURS[gamme]
    cout = round(STATIONS["appro"]["cout"] * max(quantite, moq), 2)
    return {"ok": True, "moq": moq, "extra_needed": extra,
            "delai_jours": delai, "cout_matiere_eur": cout}


def fabriquer(id_commande: str, quantite: int, tentative: int = 0, profil: str = "nominal") -> dict:
    """Station 3 — Fabrication : produit le lot. Peut générer un défaut (réparable ou non).

    Parameters
    ----------
    id_commande : str
        Identifiant (graine d'aléa).
    quantite : int
        Taille du lot (informative).
    tentative : int, default 0
        Numéro de passe. Le scénario ``reprise`` force un défaut **réparable** à la passe 0 seulement
        (la reprise le corrige).
    profil : str, default "nominal"
        ``reprise`` → ``"defaut_fabrication"`` (réparable) à la passe 0 ; ``casse`` → ``"piece_cassee"``
        (irrécupérable) ; sinon aléa faible.

    Returns
    -------
    dict
        ``{"ok": bool, "taux_rebut_pct": float, "defaut": str | None}`` ; ``defaut`` ∈
        ``{"defaut_fabrication", "piece_cassee", None}``.
    """
    rng = _rng(id_commande, "fabrication", tentative)
    rebut = round(rng.uniform(2.0, 8.0), 1)                 # % de pièces perdues (métrique, pas un défaut)
    defaut = None
    if profil == "casse":
        defaut = "piece_cassee"                             # irrécupérable → rebut au contrôle
    elif profil == "reprise" and tentative == 0:
        defaut = "defaut_fabrication"                       # réparable → corrigé à la reprise
    elif rng.random() < 0.06:                               # aléa faible pour les commandes nominales
        defaut = "defaut_fabrication"
    return {"ok": defaut is None, "taux_rebut_pct": rebut, "defaut": defaut}


def finition_premium(id_commande: str, tentative: int = 0, profil: str = "nominal") -> dict:
    """Station 4 (Premium uniquement) — Finition : l'étape supplémentaire des produits haut de gamme.

    Parameters
    ----------
    id_commande : str
        Identifiant (graine d'aléa).
    tentative : int, default 0
        Numéro de passe.
    profil : str, default "nominal"
        Non utilisé pour forcer un défaut ici (aléa faible), mais gardé pour cohérence de signature.

    Returns
    -------
    dict
        ``{"ok": bool, "defaut": str | None}`` ; ``defaut`` = ``"finition_ratee"`` (réparable) ou ``None``.
    """
    rng = _rng(id_commande, "finition", tentative)
    defaut = "finition_ratee" if rng.random() < 0.05 else None
    return {"ok": defaut is None, "defaut": defaut}


def assembler(id_commande: str, tentative: int = 0, profil: str = "nominal") -> dict:
    """Station 5 — Assemblage : monte les pièces. Défaut d'assemblage réparable, rare.

    Parameters
    ----------
    id_commande : str
        Identifiant (graine d'aléa).
    tentative : int, default 0
        Numéro de passe.
    profil : str, default "nominal"
        Gardé pour cohérence de signature.

    Returns
    -------
    dict
        ``{"ok": bool, "defaut": str | None}`` ; ``defaut`` = ``"assemblage_defectueux"`` ou ``None``.
    """
    rng = _rng(id_commande, "assemblage", tentative)
    defaut = "assemblage_defectueux" if rng.random() < 0.04 else None
    return {"ok": defaut is None, "defaut": defaut}


def controler_qualite(id_commande: str, defauts: list, tentative_qc: int) -> dict:
    """Station 6 — Contrôle qualité : décide du sort de la commande.

    Règle de décision (le cœur de la boucle de reprise) :

    - aucun défaut → ``accept`` ;
    - défaut **irrécupérable** (:data:`DEFAUTS_IRRECUPERABLES`) → ``scrap`` immédiat ;
    - sinon, défaut réparable en 1re passe (``tentative_qc == 0``) → ``rework`` ;
    - défaut réparable encore présent après reprise → ``scrap``.

    Parameters
    ----------
    id_commande : str
        Identifiant (décision déterministe, pas d'aléa).
    defauts : list of str
        Défauts actifs, bruts (``"defaut_fabrication"``) ou préfixés (``"fabrication:defaut_fabrication"``).
    tentative_qc : int
        Numéro de passe qualité (0 = première ; ≥1 = après une reprise).

    Returns
    -------
    dict
        ``{"verdict": {"accept","rework","scrap"}, "defauts": list[str], "irrecuperables": list[str]}``.
    """
    actifs = [d.split(":", 1)[-1] for d in defauts]         # tolère "station:defaut" comme "defaut"
    if not actifs:
        verdict: Verdict = "accept"
    elif any(d in DEFAUTS_IRRECUPERABLES for d in actifs):
        verdict = "scrap"
    elif tentative_qc == 0:
        verdict = "rework"                                  # une reprise autorisée
    else:
        verdict = "scrap"                                   # la reprise n'a pas suffi
    return {"verdict": verdict, "defauts": actifs,
            "irrecuperables": [d for d in actifs if d in DEFAUTS_IRRECUPERABLES]}


def expedier(id_commande: str, quantite: int, delai_jours: int, echeance_jours: int) -> dict:
    """Station 7 — Expédition : la commande est-elle **livrée à temps** ?

    Parameters
    ----------
    id_commande : str
        Identifiant.
    quantite : int
        Quantité (supposée complète ici).
    delai_jours : int
        Délai réel (dominé par l'appro).
    echeance_jours : int
        Échéance promise au client.

    Returns
    -------
    dict
        ``{"ok", "livre_a_temps", "delai_jours", "echeance_jours"}`` ; ``livre_a_temps`` = délai ≤ échéance.
    """
    a_temps = delai_jours <= echeance_jours
    return {"ok": a_temps, "livre_a_temps": a_temps,
            "delai_jours": delai_jours, "echeance_jours": echeance_jours}


# ─────────────────────────────────────────────────────────────────────────────
# Métriques agrégées (volontairement simples et lisibles)
# ─────────────────────────────────────────────────────────────────────────────
def calcul_metriques(historique: list, quantite: int = 100) -> dict:
    """Agrège des **métriques évidentes** à partir de l'historique des stations d'une commande.

    Parameters
    ----------
    historique : list of dict
        Entrées produites par les stations ; clés lues : ``"ok"``, ``"minutes"``, ``"cout_eur"``.
    quantite : int, default 100
        Taille du lot (non utilisée dans les métriques actuelles ; gardée pour extension).

    Returns
    -------
    dict
        ``{"taux_succes", "cout_eur", "delai_min", "n_etapes"}`` :

        - **taux_succes** — part d'étapes réussies du premier coup (0–1) ;
        - **cout_eur** — coût cumulé des étapes ;
        - **delai_min** — temps de cycle cumulé (minutes) ;
        - **n_etapes** — nombre d'étapes exécutées (reprises comprises).
    """
    if not historique:
        return {"taux_succes": 0.0, "cout_eur": 0.0, "delai_min": 0.0, "n_etapes": 0}
    n = len(historique)
    ok = sum(1 for e in historique if e["ok"])
    return {
        "taux_succes": round(ok / n, 3),
        # .get(...) : tolère un historique minimal ({station, ok}) — coût/délai valent alors 0.
        "cout_eur": round(sum(e.get("cout_eur", 0.0) for e in historique), 2),
        "delai_min": round(sum(e.get("minutes", 0.0) for e in historique), 1),
        "n_etapes": n,
    }


def noter_etape(station: str, res: dict) -> dict:
    """Dict d'historique pour un nœud LangGraph (retourné dans la mise à jour partielle).

    Pendant fonctionnel de ``enregistrer_etape`` : même logique, mais renvoie un dict
    au lieu de muter une liste (compatible avec les reducers LangGraph).
    Utilisé par les nœuds de NB_T1b ; ``enregistrer_etape`` délègue ici.

    Parameters
    ----------
    station : str
        Nom de la station (clé de STATIONS).
    res : dict
        Résultat de la station (doit contenir au moins ``ok``).
    """
    s = STATIONS.get(station, {})              # récupère coût et durée de la station
    return {
        "station":  station,
        "ok":       bool(res.get("ok", True)), # True si l'étape s'est bien passée
        "cout_eur": s.get("cout", 0.0),        # coût unitaire de la station (€)
        "minutes":  s.get("minutes", 0.0),     # durée typique de la station (min)
    }


def enregistrer_etape(hist: list, station: str, res: dict) -> None:
    """Ajoute une entrée dans l'historique d'une commande (coût + durée issus de STATIONS).

    Utilisé par ``piloter()`` dans NB_T1a pour construire le ``parcours`` à visualiser.

    Parameters
    ----------
    hist : list
        Liste mutable qui accumule les étapes (modifiée en place).
    station : str
        Nom de la station (clé de STATIONS).
    res : dict
        Résultat de la station (doit contenir au moins ``ok``).
    """
    hist.append(noter_etape(station, res))


# ─────────────────────────────────────────────────────────────────────────────
# Commandes « golden » — une histoire claire par commande (séquence, branche, reprise, rebut, HITL)
# ─────────────────────────────────────────────────────────────────────────────
COMMANDES_GOLDEN = [
    # Standard nominale : passe tout du premier coup, livrée à temps (le « happy path »).
    Commande(id="CMD-2026-001", modele="Lunettes Morez Classic",
             gamme="standard", quantite=300, echeance_jours=40, profil="nominal"),
    # Premium avec défaut réparable : contrôle → reprise (passe 0) → accept (passe 1). Démontre le CYCLE
    # (et la branche Premium : passe par la finition).
    Commande(id="CMD-2026-002", modele="Lunettes Morez Prestige",
             gamme="premium", quantite=150, echeance_jours=60, profil="reprise"),
    # Premium avec pièce cassée : défaut irrécupérable → REBUT (et échéance 30 < délai appro 40 → HITL).
    Commande(id="CMD-2026-003", modele="Lunettes Morez Signature",
             gamme="premium", quantite=150, echeance_jours=30, profil="casse"),
    # Standard urgente : conforme, mais échéance 10 < délai appro 20 → livrée en retard + HITL.
    Commande(id="CMD-2026-004", modele="Lunettes Morez Express",
             gamme="standard", quantite=200, echeance_jours=10, profil="urgent"),
]


if __name__ == "__main__":
    # Smoke local : exécute la chaîne (sans orchestrateur) sur la commande standard golden.
    c = COMMANDES_GOLDEN[0]
    print(w(f"Commande {c.id} — {c.modele} [{c.gamme}] x{c.quantite}", "▶"))
    print(" réception :", recevoir_commande(c.id, c.gamme, c.quantite))
    print(" appro     :", approvisionner(c.id, c.gamme, c.quantite))
    print(" fabrication:", fabriquer(c.id, c.quantite, profil=c.profil))
    print(" assemblage:", assembler(c.id))
    print(" route     :", router_gamme(c.gamme))
