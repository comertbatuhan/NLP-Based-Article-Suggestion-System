# Semantic Search & Reranking Engine for Academic Literature

![Status](https://img.shields.io/badge/Status-Ongoing-orange)
![Context](https://img.shields.io/badge/Context-M.S._Graduation_Project-blue)
![University](https://img.shields.io/badge/University-Boğaziçi_University-purple)
![Python](https://img.shields.io/badge/Python-3.9%2B-yellow)

> **Note:** This project is currently **under active development**. Architecture and logic are subject to change as research progresses.

## 📖 About The Project

This repository hosts the implementation of a search via OpenAlex API and reranking engine designed to improve information retrieval for academic literature. Unlike traditional keyword-based search, this system utilizes **Vector Space Models** and **Cross-Encoders** to understand the contextual relationship between a user's query and scientific works.

The core objective is to mitigate the "vocabulary mismatch problem" in specific domains (e.g., Molecular Communication, Nanonetworking) by leveraging state-of-the-art NLP techniques.

### 🎓 Academic Context
This work is being developed as the **Graduation Project** for the **Master of Science in Software Engineering** program at **Boğaziçi University**.

**Author:** Batuhan Cömert  
**Expected Completion:** January 2026

---

## Architecture & Logic

The system follows a two-stage retrieval process:

1.  **Retrieval (Broad Search):** Fetches a candidate set of "Works" based on metadata and keywords (via OpenAlex).
2.  **Reranking (Deep Search):** Re-orders the candidate set by calculating the semantic similarity between the query and the work's title/abstract.

### Key Features
* **Semantic Reranking:** utilizes `sentence-transformers` (Bi-Encoders and Cross-Encoders) to score relevance.
* **Abstract Handling:** Intelligent parsing of keywords/abstracts to generate query and search spaces.
* **Pydantic Integration:** Strongly typed data validation for Requests and Responses.

---

## 🛠 Tech Stack

* **Language:** Python
* **ML Frameworks:** PyTorch, SentenceTransformers (Hugging Face)
* **Models:** * `all-MiniLM-L6-v2` (Bi-Encoder)
    * `cross-encoder/ms-marco-MiniLM-L-6-v2` (Cross-Encoder)
* **Data Validation:** Pydantic
* **Performance:** LRU Caching for model loading

---

## Current Progress & Roadmap

As this is an ongoing academic project, the following modules are currently in development or refinement:

- [x] **Basic Retrieval Pipeline:** Fetching works and parsing metadata.
- [x] **Bi-Encoder Implementation:** Cosine similarity calculation using embedding vectors.
- [x] **Cross-Encoder Upgrade:** Moving to `ms-marco` for higher accuracy on small candidate sets.
- [x] **Evaluation Metrics:** Implementing nDCG and MAP to benchmark reranking performance.
- [x] **API Layer:** Exposing the reranker via FastAPI endpoints.

---

## 💻 Quick Start

**Backend:**
```bash
cd backend
pip install -r requirements.txt
uvicorn app.main:app --reload
```

**Frontend:**
```bash
cd frontend
python3 -m http.server 3000
```

Then open `http://localhost:3000` in your browser.

## Frontend Features

- Interactive search form with keyword and abstract inputs
- Side-by-side comparison of three ranking methods
- Expandable result cards showing full abstracts
- Voting system to track user preferences
- Real-time bar chart visualization of votes


