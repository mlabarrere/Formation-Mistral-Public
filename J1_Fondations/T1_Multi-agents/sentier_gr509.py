"""Module partagé T2 — GR509 Crêt de la Neige (Massif du Jura).

**But : fournir les briques métier communes à NB_T1a et NB_T1b**, sans dépendance Mistral.
Le décor est une randonnée réelle — le GR509 depuis le col de Menthières jusqu'au Crêt de
la Neige (1 718 m, point culminant du Massif du Jura) — pour illustrer les patterns
multi-agents sur un cas concret et motivant.

Ce module est le **cœur partagé** du diptyque T2. Les deux notebooks l'importent tel quel :

- ``NB_T1a_multiagents_mistral`` — patterns Agents API Mistral, tools branchés sur l'API ;
- ``NB_T1b_multiagents_langgraph`` — mêmes tools branchés sur LangGraph.

Idées mises en scène
--------------------
- **Calcul GPS déterministe** : ``calculer_distance_km`` alias pédagogique de
  ``gpxpy.length_3d()`` ; le résultat est fixe pour une trace donnée.
- **Formule de Naismith** : ``estimation_naismith`` — une ligne, référence académique connue.
- **Météo dual-mode** : ``get_meteo_prevision`` appelle Open-Meteo si réseau disponible,
  retourne un dict offline si ``requests`` échoue — indispensable pour les démos en salle.
- **Fallback GPX** : si la trace n'est pas présente dans ``atelier/``, les fonctions
  utilisent des valeurs hardcodées calibrées sur la trace réelle.

Garanties techniques
--------------------
- **Zéro dépendance Mistral** : pur Python + ``gpxpy`` + ``requests`` (tous déjà dans le
  ``.venv`` racine).
- **Importable partout** : pas d'état global mutable, pas d'effet de bord à l'import.
- **Dual-mode** : toutes les fonctions « réseau » ont un fallback offline déterministe.

Convention de retour
--------------------
``get_meteo_prevision`` retourne toujours un ``dict`` (jamais une exception propagée) :
``{"location", "temperature_c", "wind_kmh", "condition", "source"}`` avec ``source``
valant ``"open-meteo"`` (réseau) ou ``"offline-fallback"`` (hors-ligne).
"""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Optional


# ─────────────────────────────────────────────────────────────────────────────
# Constantes de la trace réelle (calibrées sur les données GPX GR509 Jura)
# ─────────────────────────────────────────────────────────────────────────────
# Utilisées en fallback si le fichier GPX n'est pas présent.
_DISTANCE_KM_FALLBACK: float = 8.4       # km — Col de Menthières → Crêt de la Neige
_DENIV_POS_M_FALLBACK: int   = 680       # m D+ cumulé sur la montée

# Météo offline : dict renvoyé lorsque Open-Meteo est inaccessible (réseau coupé, salle).
_METEO_OFFLINE: dict = {
    "location":      "Crêt de la Neige (offline)",
    "latitude":      46.373,
    "longitude":     5.780,
    "temperature_c": 8.0,
    "wind_kmh":      25.0,
    "condition":     "Partiellement nuageux",
    "source":        "offline-fallback",
}


# ─────────────────────────────────────────────────────────────────────────────
# Dataclass — contrat de données d'un itinéraire
# ─────────────────────────────────────────────────────────────────────────────
@dataclass
class Itineraire:
    """Descripteur d'un itinéraire GR.

    Attributes
    ----------
    id : str
        Identifiant court (ex. ``"GR509-CRET"``).
    nom : str
        Nom lisible (ex. ``"Col de Menthières → Crêt de la Neige"``).
    fichier_gpx : str
        Chemin relatif (depuis ``T2_Multi-agents/``) vers le fichier GPX de la trace.
    depart : str
        Nom du point de départ (lieu-dit ou commune).
    arrivee : str
        Nom du point d'arrivée.
    altitude_max_m : int
        Altitude du point culminant en mètres (sommet ou col).
    """

    id: str
    nom: str
    fichier_gpx: str
    depart: str
    arrivee: str
    altitude_max_m: int


# Itinéraire « golden » utilisé dans les deux notebooks.
ITINERAIRE_GR509 = Itineraire(
    id="GR509-CRET",
    nom="Col de Menthières → Crêt de la Neige",
    fichier_gpx="atelier/trace_gps.gpx",
    depart="Col de Menthières",
    arrivee="Crêt de la Neige",
    altitude_max_m=1718,
)


# ─────────────────────────────────────────────────────────────────────────────
# Fonctions de calcul GPS
# ─────────────────────────────────────────────────────────────────────────────
def charger_trace_gpx(chemin: str):
    """Charge une trace GPX depuis un fichier et retourne l'objet ``gpxpy.GPX``.

    Parameters
    ----------
    chemin : str
        Chemin vers le fichier ``.gpx`` (absolu ou relatif au CWD).

    Returns
    -------
    gpxpy.gpx.GPX or None
        L'objet GPX parsé, ou ``None`` si le fichier est absent ou illisible.

    Notes
    -----
    Retourne ``None`` silencieusement si le fichier est manquant — les fonctions
    ``calculer_distance_km`` et ``denivele_positif_m`` gèrent ce cas par fallback.
    """
    try:
        import gpxpy  # noqa: PLC0415

        p = Path(chemin)
        if not p.exists():
            return None
        with p.open(encoding="utf-8") as f:
            return gpxpy.parse(f)
    except Exception:
        return None


def calculer_distance_km(gpx=None) -> float:
    """Distance 3D totale de l'itinéraire en kilomètres.

    Alias pédagogique de ``gpxpy.GPX.length_3d()``.  Le fait d'exposer une
    fonction nommée ``calculer_distance_km`` (plutôt que d'appeler ``length_3d``
    directement) permet de brancher un schéma JSON minimal sur l'Agents API
    sans exposer l'API gpxpy au LLM.

    Parameters
    ----------
    gpx : gpxpy.gpx.GPX or None
        Objet GPX chargé par ``charger_trace_gpx``.  Si ``None``, retourne la
        valeur fallback calibrée sur la trace GR509.

    Returns
    -------
    float
        Distance en km, arrondie à 1 décimale.
    """
    if gpx is None:
        return _DISTANCE_KM_FALLBACK
    try:
        return round(gpx.length_3d() / 1000, 1)
    except Exception:
        return _DISTANCE_KM_FALLBACK


def denivele_positif_m(gpx=None) -> int:
    """Dénivelé positif cumulé de l'itinéraire en mètres.

    Parameters
    ----------
    gpx : gpxpy.gpx.GPX or None
        Objet GPX chargé par ``charger_trace_gpx``.  Si ``None``, retourne la
        valeur fallback calibrée sur la trace GR509.

    Returns
    -------
    int
        Dénivelé positif cumulé en mètres.
    """
    if gpx is None:
        return _DENIV_POS_M_FALLBACK
    try:
        return round(gpx.get_uphill_downhill().uphill)
    except Exception:
        return _DENIV_POS_M_FALLBACK


def estimation_naismith(dist_km: float, deniv_pos_m: int) -> float:
    """Durée de marche estimée selon la règle de Naismith.

    Règle : 5 km/h en terrain plat + 10 minutes pour chaque 100 m de dénivelé
    positif (soit 600 m/h en montée).

    Référence : W. W. Naismith, *Scottish Mountaineering Club Journal*, 1892.
    Wikipedia : https://en.wikipedia.org/wiki/Naismith%27s_rule

    Parameters
    ----------
    dist_km : float
        Distance de l'itinéraire en kilomètres.
    deniv_pos_m : int
        Dénivelé positif cumulé en mètres.

    Returns
    -------
    float
        Durée estimée en heures, arrondie à 2 décimales.

    Examples
    --------
    >>> estimation_naismith(8.4, 680)
    2.81
    """
    return round(dist_km / 5.0 + deniv_pos_m / 600.0, 2)


# ─────────────────────────────────────────────────────────────────────────────
# Météo dual-mode — Open-Meteo avec fallback offline
# ─────────────────────────────────────────────────────────────────────────────
def get_meteo_prevision(lieu: str) -> dict:
    """Prévision météo actuelle pour un lieu donné via Open-Meteo.

    Géocode ``lieu`` (API gratuite Open-Meteo geocoding), puis interroge le
    point de prévision horaire courant.  Retourne un fallback offline si le
    réseau est indisponible ou si le lieu est introuvable.

    Open-Meteo API : https://open-meteo.com/en/docs

    Parameters
    ----------
    lieu : str
        Nom d'un lieu (ville, sommet, col, commune…).

    Returns
    -------
    dict
        ``{"location", "latitude", "longitude", "temperature_c", "wind_kmh",
        "condition", "source"}`` — ``source`` vaut ``"open-meteo"`` si l'appel
        réseau a réussi, ``"offline-fallback"`` sinon.

    Notes
    -----
    Ne lève jamais d'exception : tout échec réseau retourne le dict offline.
    C'est intentionnel — le WeatherAgent doit toujours recevoir un dict JSON
    valide, même en salle sans internet.
    """
    try:
        import requests  # noqa: PLC0415

        geo = requests.get(
            "https://geocoding-api.open-meteo.com/v1/search",
            params={"name": lieu, "count": 1, "language": "fr", "format": "json"},
            timeout=8,
        )
        geo.raise_for_status()
        results = geo.json().get("results")
        if not results:
            fallback = dict(_METEO_OFFLINE)
            fallback["location"] = f"{lieu} (introuvable — offline-fallback)"
            return fallback

        place = results[0]
        meteo = requests.get(
            "https://api.open-meteo.com/v1/forecast",
            params={
                "latitude":        place["latitude"],
                "longitude":       place["longitude"],
                "current_weather": True,
                "windspeed_unit":  "kmh",
            },
            timeout=8,
        )
        meteo.raise_for_status()
        now = meteo.json()["current_weather"]

        return {
            "location":      place["name"],
            "latitude":      place["latitude"],
            "longitude":     place["longitude"],
            "temperature_c": now["temperature"],
            "wind_kmh":      now["windspeed"],
            "condition":     "Données météo réelles Open-Meteo",
            "source":        "open-meteo",
        }

    except Exception:
        fallback = dict(_METEO_OFFLINE)
        fallback["location"] = f"{lieu} (offline-fallback)"
        return fallback


# ─────────────────────────────────────────────────────────────────────────────
# Smoke test local
# ─────────────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    it = ITINERAIRE_GR509
    gpx = charger_trace_gpx(it.fichier_gpx)
    dist = calculer_distance_km(gpx)
    deniv = denivele_positif_m(gpx)
    duree = estimation_naismith(dist, deniv)

    print(f"Itinéraire : {it.nom}")
    print(f"  Distance  : {dist} km  (source : {'GPX' if gpx else 'fallback'})")
    print(f"  D+        : {deniv} m")
    print(f"  Durée     : {duree} h (Naismith)")

    meteo = get_meteo_prevision(it.arrivee)
    print(f"\nMétéo {meteo['location']} ({meteo['source']}) :")
    print(f"  {meteo['temperature_c']} °C  |  {meteo['wind_kmh']} km/h vent")
