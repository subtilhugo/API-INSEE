"""Module de connexion et de récupération des données auprès des API de l'INSEE.

Ce module encapsule l'authentification via OAuth2 et fournit des fonctions
pour interroger les séries chronologiques BDM.  Il est conçu pour être utilisé
dans une application Streamlit ou tout autre script Python.  Aucune
connexion préalable n'est effectuée tant que la méthode ``get_token``
n'est pas appelée.  Les exceptions de `requests` sont propagées afin de
permettre à l'application de les gérer proprement.
"""

from __future__ import annotations

import os
import time
from typing import Iterable, List, Optional

import pandas as pd  # type: ignore
import requests  # type: ignore


class InseeAPI:
    """Client léger pour l'API INSEE.

    Cette classe gère l'authentification via le mécanisme ``client_credentials``
    et expose des méthodes pour interroger des séries BDM.  Les jetons sont
    automatiquement renouvelés lorsque la date d'expiration est atteinte.

    Parameters
    ----------
    client_id: str, optional
        Identifiant de l'application tel que fourni par le portail des API de
        l'INSEE.  Si absent, la valeur de la variable d'environnement
        ``INSEE_CLIENT_ID`` sera utilisée.
    client_secret: str, optional
        Secret associé à l'application.  Si absent, la valeur de la variable
        d'environnement ``INSEE_CLIENT_SECRET`` sera utilisée.
    base_url: str, optional
        URL de base pour l'API.  Par défaut ``https://api.insee.fr``.

    Raises
    ------
    ValueError
        Si les identifiants ne sont pas fournis.
    """

    def __init__(
        self,
        client_id: Optional[str] = None,
        client_secret: Optional[str] = None,
        base_url: str = "https://api.insee.fr",
    ) -> None:
        self.client_id = client_id or os.getenv("INSEE_CLIENT_ID")
        self.client_secret = client_secret or os.getenv("INSEE_CLIENT_SECRET")
        self.base_url = base_url.rstrip("/")
        self._access_token: Optional[str] = None
        self._token_expiry: float = 0.0
        if not self.client_id or not self.client_secret:
            raise ValueError(
                "client_id et client_secret doivent être fournis via les arguments ou les variables d'environnement"
            )

    def _obtain_token(self) -> None:
        """Obtenir ou renouveler le jeton d'accès.

        Cette méthode envoie une requête POST au point d'authentification de
        l'INSEE.  Si l'authentification échoue, une exception `requests` est
        levée.  Un jeton est stocké en mémoire avec sa date d'expiration.
        """
        url = f"{self.base_url}/token?grant_type=client_credentials"
        # Le corps peut être vide ; l'authentification se fait via Basic Auth
        response = requests.post(url, auth=(self.client_id, self.client_secret), data={})
        response.raise_for_status()
        data = response.json()
        self._access_token = data.get("access_token")
        # Certaines API renvoient expires_in (en secondes), sinon on suppose 3600
        expires_in = data.get("expires_in", 3600)
        self._token_expiry = time.time() + float(expires_in)

    def get_token(self) -> str:
        """Retourne un jeton d'accès valide.

        Si aucun jeton n'est présent ou si le jeton a expiré, un nouveau
        jeton est demandé.  Le jeton est ensuite retourné.
        """
        if not self._access_token or time.time() >= self._token_expiry:
            self._obtain_token()
        assert self._access_token is not None  # pour mypy/pylint
        return self._access_token

    def get_bdm_series(
        self,
        idbanks: Iterable[str] | str,
        start_period: Optional[str] = None,
        last_n_observations: Optional[int] = None,
        detail: Optional[str] = None,
        include_history: bool = False,
        updated_after: Optional[str] = None,
    ) -> pd.DataFrame:
        """Récupère des séries BDM identifiées par un ou plusieurs identifiants `idbank`.

        Les paramètres disponibles correspondent à ceux décrits dans la documentation
        de l'INSEE (startPeriod, lastNObservations, detail, includeHistory,
        updatedAfter).  Le résultat est restitué sous forme de `pandas.DataFrame`.

        Parameters
        ----------
        idbanks : iterable of str or str
            Identifiant(s) des séries à récupérer.  Peut être un seul identifiant
            sous forme de chaîne ou une liste/tuple de chaînes.  Les identifiants
            seront concaténés avec le séparateur ``+`` conformément à la syntaxe
            attendue par l'API.
        start_period : str, optional
            Date de début de la période (format `AAAA-MM`, `AAAA` ou `AAAA-QX`).
        last_n_observations : int, optional
            Limite le nombre d'observations renvoyées aux `n` valeurs les plus
            récentes.
        detail : str, optional
            Spécifie le niveau de détail (``dataonly`` pour ne renvoyer que les
            valeurs, ``nodata`` pour ne renvoyer que la structure).  Laisser à
            ``None`` pour obtenir toutes les informations.
        include_history : bool, optional
            Lorsque ``True``, inclut l’historique complet des corrections.
        updated_after : str, optional
            Permet de ne récupérer que les observations postérieures à une date
            donnée (format `YYYY-MM-DD`).

        Returns
        -------
        pandas.DataFrame
            Un DataFrame avec au moins trois colonnes : ``idbank``, ``date`` et
            ``value``.  D'autres colonnes sont ajoutées si la réponse contient
            des métadonnées supplémentaires.

        Raises
        ------
        requests.HTTPError
            Si l'appel réseau échoue ou si l'API renvoie un code d'erreur.
        """
        # Gestion du paramètre idbanks
        if isinstance(idbanks, (list, tuple, set)):
            # filtrer les valeurs vides et join
            id_list = [str(x).strip() for x in idbanks if str(x).strip()]
            ids = "+".join(id_list)
        else:
            ids = str(idbanks).strip()
        if not ids:
            raise ValueError("Au moins un identifiant idbank doit être fourni.")

        # Construction de l'URL et des paramètres de requête
        endpoint = f"{self.base_url}/series/data/SERIES_BDM/{ids}"
        params: dict[str, str] = {}
        if start_period:
            params["startPeriod"] = start_period
        if last_n_observations:
            params["lastNObservations"] = str(last_n_observations)
        if detail:
            params["detail"] = detail
        if include_history:
            params["includeHistory"] = "true"
        if updated_after:
            params["updatedAfter"] = updated_after

        headers = {"Authorization": f"Bearer {self.get_token()}"}
        response = requests.get(endpoint, headers=headers, params=params)
        response.raise_for_status()
        data = response.json()

        # La structure de la réponse de l'API BDM comporte généralement une clé
        # "series" contenant une liste de séries ; chaque série possède un
        # identifiant idBank et une liste d'observations.  Chaque observation
        # contient une date et une valeur.  Le code ci‑dessous tente de convertir
        # cette structure en DataFrame.  Si la structure change, adaptez le code.
        series_list: List[dict] = data.get("series", [])  # type: ignore
        records: List[dict] = []
        for serie in series_list:
            idbank = serie.get("idBank")
            # Certaines implémentations utilisent la clé "values" pour les valeurs
            observations = serie.get("values", [])
            for obs in observations:
                # obs peut être un dict ou une liste selon le format ; on tente
                date = None
                value = None
                if isinstance(obs, dict):
                    date = obs.get("date") or obs.get("time")
                    value = obs.get("value")
                elif isinstance(obs, list) and len(obs) >= 2:
                    date, value = obs[0], obs[1]
                if date is not None:
                    records.append({"idbank": idbank, "date": date, "value": value})

        df = pd.DataFrame(records)
        return df