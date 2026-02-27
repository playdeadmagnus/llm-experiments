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

Pull at least one model:

```bash
ollama pull llama3
```

Verify the model is available:

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
OLLAMA_MODEL=llama3
```

Refer to the application source (`main.py`) for the definitive list of expected variables.

---

## 6. Run the Application

```bash
uv run python main.py
```

Alternatively, activate the virtual environment first:

```bash
source .venv/bin/activate
python main.py
```

Expected output on a fresh install:

```
Hello from rag!
```

---

## Project Structure

```
RAG/
├── .venv/              # Virtual environment (not in version control)
├── main.py             # Application entry point
├── pyproject.toml      # Project metadata and dependencies
├── uv.lock             # Pinned dependency lock file
├── .python-version     # Python version pin (3.12)
├── .gitignore          # Git ignore rules
├── .env                # Environment variables (not in version control)
├── README.md           # Project description
└── howto.md            # This file
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
