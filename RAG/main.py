#!/usr/bin/env python3
"""
Code RAG system using Ollama + Llama over C++/H files.

Usage:
    uv run python main.py <folder_path> [overwrite]

Arguments:
    folder_path  - Path to folder containing .cpp and .h files to index.
    overwrite    - Optional. If provided, re-indexes even if a saved collection exists.
"""

import sys
import os
import glob
import chromadb
import ollama

COLLECTION_NAME = "code_rag"
CHROMA_PERSIST_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), ".chroma_db")
EMBED_MODEL = "nomic-embed-text"
CHAT_MODEL = "llama3.2"
CHUNK_SIZE = 1500
CHUNK_OVERLAP = 200


def find_source_files(folder_path: str) -> list[str]:
    """Recursively find all .cpp and .h files in the given folder."""
    patterns = ["**/*.cpp", "**/*.h", "**/*.hpp", "**/*.cc", "**/*.cxx", "**/*.hxx"]
    files = []
    for pattern in patterns:
        files.extend(glob.glob(os.path.join(folder_path, pattern), recursive=True))
    return sorted(set(files))


def chunk_file(filepath: str) -> list[dict]:
    """Read a file and split it into overlapping chunks with metadata."""
    try:
        with open(filepath, "r", encoding="utf-8", errors="replace") as f:
            content = f.read()
    except OSError as e:
        print(f"  Warning: Could not read {filepath}: {e}")
        return []

    if not content.strip():
        return []

    chunks = []
    lines = content.splitlines(keepends=True)
    current_chunk = []
    current_len = 0
    chunk_start_line = 1

    for i, line in enumerate(lines, start=1):
        current_chunk.append(line)
        current_len += len(line)

        if current_len >= CHUNK_SIZE:
            chunk_text = "".join(current_chunk)
            chunks.append({
                "text": chunk_text,
                "file": filepath,
                "start_line": chunk_start_line,
                "end_line": i,
            })

            # Calculate overlap: keep the last CHUNK_OVERLAP characters worth of lines
            overlap_lines = []
            overlap_len = 0
            for ol in reversed(current_chunk):
                if overlap_len + len(ol) > CHUNK_OVERLAP:
                    break
                overlap_lines.insert(0, ol)
                overlap_len += len(ol)

            current_chunk = overlap_lines
            current_len = overlap_len
            chunk_start_line = i - len(overlap_lines) + 1

    # Remaining content
    if current_chunk:
        chunk_text = "".join(current_chunk)
        if chunk_text.strip():
            chunks.append({
                "text": chunk_text,
                "file": filepath,
                "start_line": chunk_start_line,
                "end_line": len(lines),
            })

    return chunks


def build_index(folder_path: str, client: chromadb.ClientAPI) -> chromadb.Collection:
    """Index all source files into ChromaDB."""
    # Delete existing collection if present
    try:
        client.delete_collection(COLLECTION_NAME)
    except Exception:
        pass

    collection = client.get_or_create_collection(
        name=COLLECTION_NAME,
        metadata={"hnsw:space": "cosine"},
    )

    files = find_source_files(folder_path)
    if not files:
        print(f"No C/C++ source files found in: {folder_path}")
        sys.exit(1)

    print(f"Found {len(files)} source file(s). Indexing...")

    all_chunks = []
    for filepath in files:
        rel = os.path.relpath(filepath, folder_path)
        chunks = chunk_file(filepath)
        all_chunks.extend(chunks)
        print(f"  {rel}: {len(chunks)} chunk(s)")

    if not all_chunks:
        print("No content to index.")
        sys.exit(1)

    print(f"\nTotal chunks: {len(all_chunks)}")
    print(f"Generating embeddings with {EMBED_MODEL}...")

    # Process in batches to avoid overwhelming Ollama
    batch_size = 50
    for i in range(0, len(all_chunks), batch_size):
        batch = all_chunks[i:i + batch_size]
        texts = [c["text"] for c in batch]
        ids = [f"chunk_{i + j}" for j in range(len(batch))]
        metadatas = [{"file": c["file"], "start_line": c["start_line"], "end_line": c["end_line"]} for c in batch]

        # Get embeddings from Ollama
        embeddings = []
        for text in texts:
            resp = ollama.embed(model=EMBED_MODEL, input=text)
            embeddings.append(resp["embeddings"][0])

        collection.add(
            ids=ids,
            embeddings=embeddings,
            documents=texts,
            metadatas=metadatas,
        )
        done = min(i + batch_size, len(all_chunks))
        print(f"  Indexed {done}/{len(all_chunks)} chunks")

    # Save indexed folder path as metadata marker
    meta_collection = client.get_or_create_collection(name="__rag_meta__")
    try:
        meta_collection.delete(ids=["source_folder"])
    except Exception:
        pass
    meta_collection.add(
        ids=["source_folder"],
        documents=[os.path.abspath(folder_path)],
    )

    print("Indexing complete.\n")
    return collection


def query_rag(collection: chromadb.Collection, question: str, n_results: int = 5) -> str:
    """Query the RAG collection and return context string."""
    # Embed the question
    resp = ollama.embed(model=EMBED_MODEL, input=question)
    query_embedding = resp["embeddings"][0]

    results = collection.query(
        query_embeddings=[query_embedding],
        n_results=n_results,
    )

    if not results["documents"] or not results["documents"][0]:
        return ""

    context_parts = []
    for doc, meta in zip(results["documents"][0], results["metadatas"][0]):
        file_info = f"{meta['file']}:{meta['start_line']}-{meta['end_line']}"
        context_parts.append(f"--- {file_info} ---\n{doc}")

    return "\n\n".join(context_parts)


SYSTEM_PROMPT = """You are a helpful C/C++ code assistant. You answer questions about a codebase using the provided source code context.

Rules:
- Base your answers on the provided code context.
- Reference specific files and line numbers when relevant.
- If the context doesn't contain enough information, say so honestly.
- Keep answers focused and technical."""


def chat_loop(collection: chromadb.Collection):
    """Interactive chat loop with RAG-augmented responses."""
    print(f"Chat ready (model: {CHAT_MODEL}). Type 'quit' or 'exit' to stop.\n")

    conversation: list[dict] = []

    while True:
        try:
            user_input = input("You: ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\nBye.")
            break

        if not user_input:
            continue
        if user_input.lower() in ("quit", "exit"):
            print("Bye.")
            break

        # Retrieve relevant context
        context = query_rag(collection, user_input)

        # Build the augmented user message
        if context:
            augmented = f"Code context:\n{context}\n\nQuestion: {user_input}"
        else:
            augmented = user_input

        conversation.append({"role": "user", "content": augmented})

        messages = [{"role": "system", "content": SYSTEM_PROMPT}] + conversation

        # Stream the response
        print("Assistant: ", end="", flush=True)
        response_text = ""
        stream = ollama.chat(model=CHAT_MODEL, messages=messages, stream=True)
        for chunk in stream:
            token = chunk["message"]["content"]
            print(token, end="", flush=True)
            response_text += token
        print()

        conversation.append({"role": "assistant", "content": response_text})


def main():
    if len(sys.argv) < 2:
        print("Usage: uv run python main.py <folder_path> [overwrite]")
        sys.exit(1)

    folder_path = sys.argv[1]
    do_overwrite = len(sys.argv) >= 3 and sys.argv[2].lower() == "overwrite"

    if not os.path.isdir(folder_path):
        print(f"Error: '{folder_path}' is not a valid directory.")
        sys.exit(1)

    # Persistent ChromaDB client
    client = chromadb.PersistentClient(path=CHROMA_PERSIST_DIR)

    # Check if collection already exists
    existing_collections = [c.name for c in client.list_collections()]
    has_existing = COLLECTION_NAME in existing_collections

    if has_existing and not do_overwrite:
        print(f"Found existing RAG index at {CHROMA_PERSIST_DIR}")
        print("Using saved index. Pass 'overwrite' as second argument to rebuild.\n")
        collection = client.get_collection(name=COLLECTION_NAME)
    else:
        if has_existing and do_overwrite:
            print("Overwrite requested. Rebuilding index...\n")
        collection = build_index(folder_path, client)

    chat_loop(collection)


if __name__ == "__main__":
    main()
