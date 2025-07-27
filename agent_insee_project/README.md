# Agent RAG pour les données INSEE

Ce dépôt propose un prototype d'**agent de recherche augmentée par récupération** (RAG) qui s'interface avec l’API de l’INSEE pour interroger des séries chronologiques (BDM) et exploiter des données géographiques ou macro‑économiques.  L’interface est bâtie avec **Streamlit** et permet à la fois d’extraire des données via l’API, de les explorer interactivement par colonne et de poser des questions en langage naturel grâce à un grand modèle de langage.

## Contexte

L’API BDM de l’INSEE regroupe plusieurs centaines de milliers de séries économiques et sociales.  Une librairie comme `pynsee` donne accès à plus de 150 000 séries macro‑économiques et à plusieurs jeux de données locaux, ainsi qu’à des métadonnées essentielles et à la base SIRENE【326924110483048†L29-L35】.  Pour utiliser certaines API, notamment celles de la base SIRENE, il est nécessaire d’obtenir des identifiants et un jeton d’accès, mais les modules relatifs aux séries macro‑économiques ou aux données locales sont généralement accessibles sans authentification【326924110483048†L38-L41】.  L’INSEE recommande cependant de se créer un compte, de souscrire à l’API voulue et de générer un jeton d’accès via le portail des API【973880206466863†L39-L56】.  Un jeton d’accès est une chaîne de caractères fournie par le catalogue des API ; il doit être transmis dans chaque appel pour vous identifier et est valable par défaut une semaine【973880206466863†L97-L104】.

## Fonctionnalités du prototype

* **Authentification à l’API INSEE :** l’application gère la récupération d’un jeton d’accès via le flux OAuth2 `client_credentials` à l’aide de votre `client_id` et `client_secret`.
* **Interrogation de séries BDM :** renseignez un ou plusieurs identifiants `idbank` et des paramètres (période de début, nombre d’observations, etc.).  Les données récupérées sont converties en `pandas.DataFrame` et affichées de manière interactive.
* **Exploration par colonne :** après chargement des données, vous pouvez sélectionner une colonne (par exemple `date` ou `value`) pour en afficher un résumé statistique.  Les colonnes numériques sont illustrées par un graphique et un descriptif, tandis que les colonnes catégorielles sont synthétisées par les effectifs.
* **Agent RAG :** un champ de texte permet de poser une question en français sur le jeu de données chargé.  Une fonction combine les premières lignes du DataFrame avec votre question pour formuler un prompt et interroge un modèle `OpenAI` afin de générer une réponse.  Cette approche illustre comment combiner récupération de données et génération de texte.

## Installation

1. Clonez ou téléchargez ce dépôt dans votre environnement de travail.
2. Créez un environnement virtuel Python et installez les dépendances :

   ```bash
   python -m venv venv
   source venv/bin/activate
   pip install -r requirements.txt
   ```

3. Renseignez les variables d’environnement nécessaires :

   * `INSEE_CLIENT_ID` et `INSEE_CLIENT_SECRET` : identifiants de votre application INSEE.  Vous devez vous inscrire sur le portail des API, vous abonner à l’API « BDM » et générer un jeton pour obtenir ces clés【973880206466863†L39-L56】.
   * `OPENAI_API_KEY` : clé d’API OpenAI, facultative mais nécessaire pour activer le module RAG.

   Vous pouvez définir ces variables dans votre shell ou directement dans Streamlit via la barre latérale.

## Lancer l’application

Exécutez la commande suivante à la racine du projet :

```bash
streamlit run streamlit_app.py
```

Une interface web s’ouvrira dans votre navigateur.  Renseignez vos identifiants INSEE et, si vous souhaitez poser des questions en langage naturel, votre clé OpenAI.  Choisissez ensuite les identifiants `idbank` des séries à interroger (séparés par des virgules) et cliquez sur **« Récupérer les données »**.  Une fois les données chargées, vous pourrez :

* consulter et trier le tableau interactif ;
* sélectionner une colonne et afficher des statistiques ou un graphique associé ;
* poser une question et lire la réponse générée.

## Remarques

* Ce prototype se base sur les points d’extrémité de l’API BDM.  Les paramètres pris en charge (`startPeriod`, `lastNObservations`, `detail`, etc.) correspondent à ceux décrits dans la documentation officielle de l’INSEE.
* L’INSEE impose une limite de 30 appels par minute et par adresse IP【162473825327686†L83-L89】.  Adaptez votre cadence de requêtes en conséquence.
* Les modules d’exploration des colonnes s’inspirent d’EXA : ils offrent la possibilité d’inspecter chaque colonne individuellement, de visualiser des statistiques et de générer des graphiques simples.

## Structure du dépôt

```
agent_insee/
├── README.md              # Ce fichier
├── requirements.txt       # Dépendances Python
├── insee_api.py           # Module de connexion et de récupération des données INSEE
├── rag_agent.py           # Fonctions RAG utilisant OpenAI pour répondre à des questions
└── streamlit_app.py       # Application Streamlit
```

## Avertissement sur les quotas et les droits d’usage

Avant de déployer ce prototype en production, veuillez consulter les conditions d’utilisation des API de l’INSEE.  Certaines API nécessitent une habilitation explicite ou imposent des limites strictes d’usage.  Le jeton d’accès généré est personnel et ne doit pas être partagé publiquement.  Enfin, n’oubliez pas de renouveler régulièrement vos jetons, ceux‑ci ayant une durée de validité limitée【973880206466863†L97-L106】.