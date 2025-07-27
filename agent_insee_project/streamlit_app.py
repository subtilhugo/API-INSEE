"""Application Streamlit pour interroger et explorer les données INSEE.

Ce module définit une interface web interactive permettant :

1. De saisir les identifiants d'authentification de l'API INSEE (client_id et
   client_secret) ainsi qu'une clé OpenAI facultative.
2. D'interroger l'API BDM avec un ou plusieurs idbanks et divers paramètres
   (période de début, nombre d'observations, niveau de détail, etc.).
3. D'afficher les résultats dans un tableau interactif et de sélectionner des
   colonnes pour obtenir des statistiques ou des graphiques simples.
4. De poser une question en langage naturel et d'obtenir une réponse grâce au
   module RAG alimenté par OpenAI.
"""

from __future__ import annotations

import os
from typing import List

import pandas as pd  # type: ignore
import streamlit as st  # type: ignore

from insee_api import InseeAPI
from rag_agent import ask_question


def main() -> None:
    st.set_page_config(page_title="Agent INSEE RAG", layout="wide")
    st.title("Agent RAG pour les données INSEE")

    st.write(
        "Utilisez cette application pour interroger l'API BDM de l'INSEE, explorer les données obtenues et poser des questions en langage naturel."
    )

    # --- Barre latérale pour les paramètres et les identifiants ---
    with st.sidebar:
        st.header("Authentification et paramètres")
        client_id = st.text_input(
            "INSEE client_id",
            value=os.getenv("INSEE_CLIENT_ID", ""),
            type="password",
            help="Identifiant de votre application INSEE (obtenu via le portail).",
        )
        client_secret = st.text_input(
            "INSEE client_secret",
            value=os.getenv("INSEE_CLIENT_SECRET", ""),
            type="password",
            help="Secret associé à votre application INSEE.",
        )
        openai_key = st.text_input(
            "OpenAI API key",
            value=os.getenv("OPENAI_API_KEY", ""),
            type="password",
            help="Clé API OpenAI, nécessaire pour générer des réponses via le module RAG.",
        )
        # Mise à jour de l'environnement pour l'appel OpenAI
        if openai_key:
            os.environ["OPENAI_API_KEY"] = openai_key

        st.subheader("Paramètres de la requête BDM")
        idbanks_input = st.text_input(
            "Identifiants idbank (séparés par des virgules)",
            value="001688406",
            help="Entrez un ou plusieurs identifiants idbank, séparés par des virgules."
        )
        start_period = st.text_input(
            "startPeriod (AAAA, AAAA-MM ou AAAA-QX)",
            value="",
            help="Date de début de la série. Laissez vide pour ne pas filtrer."
        )
        last_n_observations = st.number_input(
            "lastNObservations",
            min_value=0,
            max_value=400,
            value=0,
            step=1,
            help="Limite le nombre d'observations renvoyées aux n valeurs les plus récentes. 0 signifie aucune limite."
        )
        detail = st.selectbox(
            "detail",
            options=["", "dataonly", "nodata"],
            index=0,
            help="Niveau de détail de la réponse. Laisser vide pour obtenir toutes les informations."
        )
        include_history = st.checkbox(
            "includeHistory",
            value=False,
            help="Inclut l'historique complet des corrections si coché."
        )
        updated_after = st.text_input(
            "updatedAfter (YYYY-MM-DD)",
            value="",
            help="Permet de ne récupérer que les observations postérieures à une date donnée."
        )

        fetch_button = st.button("Récupérer les données")

    # --- Création du client API si les identifiants sont fournis ---
    api_client = None
    if client_id and client_secret:
        try:
            api_client = InseeAPI(client_id=client_id, client_secret=client_secret)
        except ValueError as e:
            st.error(str(e))

    # --- Gestion de la récupération des données ---
    if fetch_button:
        if not api_client:
            st.error("Veuillez saisir votre client_id et client_secret dans la barre latérale.")
        else:
            with st.spinner("Appel de l'API INSEE en cours..."):
                idbanks: List[str] = [x.strip() for x in idbanks_input.split(",") if x.strip()]
                try:
                    df = api_client.get_bdm_series(
                        idbanks=idbanks,
                        start_period=start_period if start_period else None,
                        last_n_observations=int(last_n_observations) if last_n_observations else None,
                        detail=detail if detail else None,
                        include_history=include_history,
                        updated_after=updated_after if updated_after else None,
                    )
                    if df.empty:
                        st.warning("Aucune observation trouvée pour ces paramètres.")
                    else:
                        st.session_state["df"] = df
                        st.success(f"{len(df)} observations chargées.")
                except Exception as exc:
                    st.exception(exc)

    # --- Affichage des données et exploration ---
    if "df" in st.session_state:
        df: pd.DataFrame = st.session_state["df"]
        st.markdown("## Jeu de données chargé")
        st.dataframe(df, use_container_width=True)

        # Sélection de colonne pour exploration
        if not df.empty:
            st.markdown("### Analyse par colonne")
            selected_column = st.selectbox("Choisissez une colonne à explorer", options=df.columns.tolist())
            if selected_column:
                col_data = df[selected_column]
                # Afficher statistiques selon le type
                if pd.api.types.is_numeric_dtype(col_data):
                    st.write("Statistiques descriptives :")
                    st.write(col_data.describe())
                    # Si une colonne 'date' existe, utiliser comme index pour un graphique de série
                    if "date" in df.columns and pd.api.types.is_datetime64_any_dtype(pd.to_datetime(df["date"], errors="coerce")):
                        # Conversion de la colonne date
                        tmp_df = df.copy()
                        tmp_df["date"] = pd.to_datetime(tmp_df["date"], errors="coerce")
                        chart_df = tmp_df[["date", selected_column]].dropna().set_index("date").sort_index()
                        st.line_chart(chart_df)
                    else:
                        st.line_chart(col_data.dropna())
                else:
                    # Colonnes non numériques : afficher les effectifs des valeurs
                    st.write("Effectifs des modalités :")
                    counts = col_data.value_counts().reset_index()
                    counts.columns = [selected_column, "Effectif"]
                    st.dataframe(counts)

        # Section RAG pour poser des questions
        st.markdown("### Posez une question sur ce jeu de données")
        question = st.text_input(
            "Votre question", value="", help="Exemple : Quel est la moyenne de la variable value ?"
        )
        if st.button("Interroger l'agent"):
            if not question.strip():
                st.warning("Veuillez entrer une question avant de cliquer sur le bouton.")
            else:
                with st.spinner("Génération de la réponse..."):
                    answer = ask_question(df, question)
                    st.markdown("**Réponse de l'agent :**")
                    st.write(answer)


if __name__ == "__main__":
    main()