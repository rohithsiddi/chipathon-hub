FROM python:3.11-slim

WORKDIR /app

# Install build backend first (cached layer)
RUN pip install --no-cache-dir hatchling

# Copy dependency manifest and source package together
# (hatchling needs chatbot/ present to build the package)
COPY pyproject.toml README.md ./
COPY chatbot/ ./chatbot/

# Install all project dependencies
RUN pip install --no-cache-dir .

# Copy the pre-built vector store (33 MB, committed to repo)
COPY data/vectorstore/ ./data/vectorstore/

# HF Spaces runs as a non-root user — ensure the vectorstore is readable/writable
# (ChromaDB writes WAL files on open)
RUN chmod -R 777 /app/data

ENV CHROMA_PERSIST_DIR=/app/data/vectorstore
ENV CHROMA_COLLECTION_NAME=chipathon_docs
ENV PORT=7860

EXPOSE 7860

CMD ["python", "chatbot/api.py"]
