# Team Name: [Insert Team Name]

## 👥 Team Members
* Member 1: [Name] - [GitHub Profile]
* Member 2: [Name] - [GitHub Profile]
* Member 3: [Name] - [GitHub Profile]
* Member 4: [Name] - [GitHub Profile]

## 🔗 Project Links
* **Demo Video:** [Link to YouTube/Loom (3-5 mins)]
* **Hosted Demo:** [Optional: Link to live app]

## 🤖 Technical Implementation

### 1. Data Pipeline (Scraping)
* **Tools Used:** (e.g., Scrapy, Beautiful Soup, Selenium)
* **Strategy:** Briefly explain how you scraped `wiki.metakgp.org`. How did you handle cleaning and indexing?
* **Indexing:** (e.g., ChromaDB, FAISS, Pinecone)

### 2. Graph of Thoughts (GoT)
* **Reasoning Model:** Explain how your nodes and edges are structured.
* **Graph Logic:** How do you connect different MetaKGP pages? (e.g., connecting a "Society" page to a "Student" page).

### 3. Mixture of Experts (MoE)
* **Expert 1 (Source Matcher):** How do you verify the text exists in the scraped data?
* **Expert 2 (Hallucination Hunter):** How do you detect fabricated info?
* **Expert 3 (Logic Expert):** How do you ensure logical consistency?

## 📊 Setup Instructions
* **Prerequisites:** (e.g., Python 3.10, Neo4j)
* **Environment Variables:** List required `.env` keys (do not share actual keys).
* **How to Run Scraper:** `python scrape.py`
* **How to Run Bot:** `streamlit run app.py`

## 📸 Screenshots
* 

[Image of Graph Visualization]

* 

[Image of Chat Interface]
