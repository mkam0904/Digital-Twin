# Pushover: A service/API that sends push notifications from your apps or scripts 
#   directly to your phone or desktop.
# Gradio: fn|ML/AI model -> shareable web app (chatbot, demo, tool)
# Hugging face: AI Platform: https://huggingface.co/

#### Step 1: Import Libraries and load the env
#### Step 2: Load OpenAI API key and create client\
#### Clean document
#### Step 4: Chunk the document
Generated chunk_text with ChatGPT from this prompt:
Create a Python function chunk_text(text, chunk_size=500, overlap=50, min_chunk=250).

Hard requirements:
- Every chunk MUST start at the beginning of a sentence whenever one exists.
- Every chunk MUST end at a paragraph boundary, sentence boundary, or word boundary, in that priority order.
- Do not split inside a sentence unless unavoidable because a single sentence exceeds chunk_size.
- Preserve all text; do not drop any characters.
- Use ~50 chars overlap between chunks.
- Minimum chunk length 250 chars unless end of document or a single sentence exceeds limits.

Priority order:
1. preserve all text and target around 500 chars per chunk, plus or minus around 10. 
2. start at sentence boundary
3. end at paragraph > sentence > word boundary
4. maintain overlap

 ### Step 5: Create Embeddings for each chunk - each embedding is a vector
 -----------------------
 RAG: Embed (Embeddings: dense numerical vector representations of data)
 -----------------------

### Step 6: Store vectors in ChromaDB

### Step 6: Visualize the embeddings in 2D space by using dimensionality reduction with t-SNE

### Step 3: Define dynamic context for Simple RAG (Retrieval-Augmented Generation) implementation

#### Step 4: Load Pushover API keys from environment and initiate tools list

#### Define Pushover as an LLM Tool and add it to tools list

#### Define Dice Roll as an LLM Tool and add it to tools list

#### Handle Tool Calls

### Call the LLM

### Function to process conversation turn

#### Launch Gradio

