  ---
  title: My Digital Twin
  emoji: 🧑‍💻
  sdk: gradio
  sdk_version: "4.44.0"
  app_file: app.py
  pinned: false
  ---

# Digital-Twin
AI-Powered Digital Twin: 
Under the hood:  
- Prompt engineering (system vs user prompts) 
- Tokenization and API Cost management
- Conversation history &amp; context management
- Building chat UIs with Gradio
- RAG (chunking, embeddings, vector stores)
- LLM tool calling (parallel &amp; sequential calls)
- Deploying to Hugging Face Spaces

## Deployment Architecture

This repository uses a GitHub Actions CI/CD pipeline to automatically sync code to Hugging Face on every push to the `main` branch. GitHub acts as the single source of truth.

* **Workflow File:** `.github/workflows/sync_to_hf.yml`
* **Target Space:** `mkam0904/my-Digital-Twin`
* **Mechanism:** Uses a forced push (`git push --force`) to ensure GitHub code strictly overwrites any conflicting files on Hugging Face.
* **Authentication:** Secured via a Fine-Grained Hugging Face Write Token, stored as a GitHub Repository Secret (`GITHUB_HF_TOKEN`).