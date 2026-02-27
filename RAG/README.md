# RAG Project — Setup and Run Guide

## Prerequisites

The following must be installed and available on the host machine before proceeding.

| Dependency | Minimum Version | Verification Command |
|---|---|---|
| Python | 3.12 | `python3 --version` |
| uv | latest | `uv --version` |
| Ollama | latest | `ollama --version` |
| Git | any | `git --version` |

Do not proceed if any prerequisite is missing or below the required version.

---

## 1. Clone the Repository

```bash
git clone <repository-url>
cd RAG
```

---

## 2. Create the Virtual Environment

```bash
uv venv --python 3.12
```

This creates a `.venv/` directory at the project root. The `.python-version` file pins the interpreter to 3.12.

---

## 3. Install Dependencies

```bash
uv sync
```

This reads `pyproject.toml` and `uv.lock`, then installs all pinned dependencies into `.venv/`. Do not use `pip install` directly — the lock file ensures reproducible builds.

### Core Dependencies

| Package | Purpose |
|---|---|
| `chromadb` | Vector database for embedding storage and retrieval |
| `ollama` | Python client for the Ollama local LLM service |
| `python-dotenv` | Loads environment variables from `.env` files |

---

## 4. Start the Ollama Service

Ollama must be running before the application can make inference calls.

```bash
ollama serve
```

Default endpoint: `http://localhost:11434`

Pull the required models:

```bash
ollama pull llama3.2
ollama pull nomic-embed-text
```

Verify the models are available:

```bash
ollama list
```

---

## 5. Configure Environment Variables

Create a `.env` file at the project root. This file is not checked into version control.

```bash
touch .env
```

Populate it with any required configuration. Example:

```
OLLAMA_HOST=http://localhost:11434
```

Refer to the application source (`main.py`) for the definitive list of expected variables.

---

## 6. Run the Application

```bash
uv run python main.py <folder_path> [overwrite]
```

Arguments:
- `folder_path` — Path to a folder containing C/C++ source files (`.cpp`, `.h`, `.hpp`, `.cc`, `.cxx`, `.hxx`).
- `overwrite` — Optional. Pass `overwrite` to force re-indexing even if a saved index exists.

Example:

```bash
uv run python main.py ~/my-cpp-project
uv run python main.py ~/my-cpp-project overwrite
```

On first run the tool indexes all source files into a local vector database, then opens an interactive chat where you can ask questions about the code.

---

## Project Structure

```
RAG/
├── .venv/              # Virtual environment (not in version control)
├── .chroma_db/         # Persisted vector database (not in version control)
├── main.py             # Application entry point
├── pyproject.toml      # Project metadata and dependencies
├── uv.lock             # Pinned dependency lock file
├── .python-version     # Python version pin (3.12)
├── .gitignore          # Git ignore rules
├── .env                # Environment variables (not in version control)
└── README.md           # This file
```

---

## Troubleshooting

| Problem | Cause | Fix |
|---|---|---|
| `uv: command not found` | uv is not installed | Install via `curl -LsSf https://astral.sh/uv/install.sh \| sh` |
| `ollama: command not found` | Ollama is not installed | Install from https://ollama.com |
| `ConnectionRefusedError` on Ollama calls | Ollama service is not running | Run `ollama serve` in a separate terminal |
| `ModuleNotFoundError` | Dependencies not installed | Run `uv sync` |
| Wrong Python version | System default is below 3.12 | Install Python 3.12 and re-run `uv venv --python 3.12` |

---

## Rules

- Always use `uv sync` to install dependencies. Never use `pip install` in this project.
- Never commit `.env` or `.venv/` to version control.
- Keep `uv.lock` in version control. It guarantees deterministic installs.
- Run the Ollama service before starting the application.
- Use Python 3.12 or higher. Lower versions are not supported.
