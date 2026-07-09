# src/data_loader.py
# pulls bio data from the private HF 

from huggingface_hub import HfApi, hf_hub_download
import config
from config import DOC_REPO_ID          # constant — eager is fine

def load_documents():
    api = HfApi(token=config.HF_TOKEN)
    filenames = [
        f for f in api.list_repo_files(DOC_REPO_ID, repo_type="dataset")
        if f.endswith(".md")
    ]
    documents = []
    for filename in filenames:
        path = hf_hub_download(
            repo_id=DOC_REPO_ID,
            filename=filename,
            repo_type="dataset",
            token=config.HF_TOKEN,
        )
        with open(path, "r", encoding="utf-8") as f:
            text = f.read()
        documents.append({"text": text, "source": filename})
        print(f"Loaded: {filename}")
    return documents