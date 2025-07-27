# 🇫🇷 INSEE RAG Agent – Streamlit Prototype

## 🔑 INSEE API Access – Essential Setup

This project uses the **INSEE BDM API**, which provides over 150,000 time series on French macroeconomic and regional indicators.

To access the data, you must:

1. Create an account on [https://api.insee.fr](https://api.insee.fr)
2. Subscribe to the API you want to use (e.g. “BDM – Base de données macroéconomiques”)
3. Obtain your `client_id` and `client_secret`
4. Generate an access token via `https://api.insee.fr/token`

These credentials are entered directly in the Streamlit interface.  
If you want to use the RAG (Retrieval-Augmented Generation) functionality, you can also provide an OpenAI API key.

- INSEE API documentation: https://api.insee.fr/catalogue/
- Python wrapper (optional): https://pynsee.readthedocs.io

---

## 🧠 What is this?

This repository provides a simple **RAG agent** prototype that connects to the INSEE API, retrieves datasets, and lets you:

- 🧭 Search and explore INSEE time series (e.g. employment, unemployment)
- 📊 Display and interact with the data frame
- 💬 Ask questions in natural language based on the data
- ⚙️ Use OpenAI’s GPT to generate summaries or insights

Built with **Streamlit** and minimal Python dependencies.

---

## 🚀 How to Run

1. Clone the repo
2. Install dependencies:

```bash
pip install -r requirements.txt
