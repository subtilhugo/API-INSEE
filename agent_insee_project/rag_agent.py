"""Fonctions d'agent de génération augmentée par récupération (RAG).

Ce module fournit des utilitaires pour transformer un jeu de données en contexte
et interroger un modèle de langage afin d'obtenir une réponse en utilisant
ce contexte.  Les fonctions sont volontairement simples pour s'intégrer
facilement à une application Streamlit.
"""

from __future__ import annotations

import os
from typing import Optional

import pandas as pd  # type: ignore

try:
    import openai  # type: ignore
except ImportError:
    # L'import d'OpenAI échouera si le package n'est pas installé.  Dans ce
    # cas, les fonctions dépendantes renverront un message d'erreur.
    openai = None  # type: ignore


def dataframe_to_context(df: pd.DataFrame, max_rows: int = 5) -> str:
    """Convertit les premières lignes d'un DataFrame en chaîne de caractères.

    Cela permet de fournir un aperçu du jeu de données au modèle de
    génération.  Par défaut, seules les 5 premières lignes sont utilisées.

    Parameters
    ----------
    df : pandas.DataFrame
        Le DataFrame à résumer.
    max_rows : int
        Nombre maximum de lignes à inclure dans le contexte.

    Returns
    -------
    str
        Une chaîne représentant les premières lignes du DataFrame.
    """
    if df.empty:
        return "Le jeu de données est vide."
    try:
        context = df.head(max_rows).to_string(index=False)
    except Exception:
        context = str(df.head(max_rows))
    return context


def ask_question(
    df: pd.DataFrame,
    question: str,
    model: str = "gpt-3.5-turbo",
    temperature: float = 0.2,
) -> str:
    """Pose une question à un modèle OpenAI en utilisant un DataFrame comme contexte.

    La fonction assemble un prompt en français contenant un extrait du jeu de
    données ainsi que la question de l'utilisateur.  Elle appelle ensuite
    l'API OpenAI pour obtenir une réponse.  Si la clé API n'est pas définie ou
    si le package `openai` n'est pas installé, un message d'erreur est renvoyé.

    Parameters
    ----------
    df : pandas.DataFrame
        Le jeu de données servant de base au contexte.
    question : str
        La question posée par l'utilisateur.
    model : str, optional
        Nom du modèle OpenAI à utiliser.  Par défaut ``gpt-3.5-turbo``.
    temperature : float, optional
        Température du modèle pour ajuster la créativité.

    Returns
    -------
    str
        La réponse générée ou un message d'erreur en cas de problème.
    """
    if openai is None:
        return "Le package openai n'est pas installé. Veuillez l'ajouter aux dépendances."
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        return "Aucune clé OPENAI_API_KEY trouvée. Définissez cette variable d'environnement dans votre système ou dans Streamlit."
    openai.api_key = api_key
    # Construire le contexte
    context = dataframe_to_context(df)
    messages = [
        {
            "role": "system",
            "content": "Tu es un assistant qui répond aux questions sur des données de l'INSEE en utilisant les informations fournies dans le contexte. Réponds en français de façon concise et claire."
        },
        {
            "role": "user",
            "content": f"Contexte des données:\n{context}\n\nQuestion:\n{question}"
        },
    ]
    try:
        response = openai.ChatCompletion.create(
            model=model,
            messages=messages,
            temperature=temperature,
            max_tokens=256,
        )
        return response.choices[0].message.get("content", "").strip()
    except Exception as exc:
        return f"Erreur lors de l'appel à l'API OpenAI : {exc}"