# ⏳ TimeLoop — Python Time-Travel Debugger

**TimeLoop** is a web-based time-travel debugger for Python. It lets you write Python code in the browser, execute it on a sandboxed backend, and then step forward and backward through every state change your program made — inspecting variables, call stacks, and execution flow at any point in time.

> _"Where elite developers master execution timelines."_

---

## Table of Contents

- [Features](#features)
- [Architecture Overview](#architecture-overview)
- [Tech Stack](#tech-stack)
- [Project Structure](#project-structure)
- [Getting Started](#getting-started)
  - [Prerequisites](#prerequisites)
  - [Backend Setup](#backend-setup)
  - [Frontend Setup](#frontend-setup)
- [API Reference](#api-reference)
  - [POST /execute](#post-execute)
  - [GET /state](#get-state)
  - [GET /variable-history](#get-variable-history)
  - [GET /function-calls](#get-function-calls)
  - [GET /line](#get-line)
  - [GET /exceptions](#get-exceptions)
- [Backend Modules](#backend-modules)
  - [Engine](#engine)
    - [Tracer](#tracer)
    - [Executor](#executor)
    - [Worker](#worker)
    - [Sandbox](#sandbox)
    - [Serializer](#serializer)
    - [Reconstruction](#reconstruction)
    - [Limits](#limits)
  - [Models](#models)
  - [Routes](#routes)
  - [Utils](#utils)
- [Frontend Components](#frontend-components)
- [Execution Modes](#execution-modes)
- [Security & Sandboxing](#security--sandboxing)
- [Configuration](#configuration)
- [Contributing](#contributing)
- [License](#license)

---

## Features

- 🔄 **Time-Travel Debugging** — Step forward and backward through your Python program's execution history.
- ⚡ **Dual Execution Modes** — *Fast* mode for quick results, *Detailed* mode for full line-by-line tracing.
- 🔍 **Variable Inspector** — View the value of every variable at any point in execution.
- 📊 **Variable History** — Track how a variable changes over the entire run.
- 🧱 **Call Stack Reconstruction** — See the full call stack at every traced step.
- 🛡️ **Sandboxed Execution** — User code runs in a restricted sandbox with whitelisted builtins and modules.
- 🗂️ **Session Persistence** — Execution sessions are saved to disk as JSON for later retrieval.
- 🏗️ **Delta-Based Snapshots** — Efficient storage using periodic full checkpoints + incremental deltas.
- 🐛 **Exception Tracking** — Automatically captures and indexes all exceptions.
- 📍 **Line Index** — Look up which execution steps visited a given source line.

---

## Architecture Overview

```
┌─────────────────────────────────────────────────────────┐
│                     Frontend (React + Vite)             │
│  ┌──────────┐  ┌──────────┐  ┌────────────────────┐    │
│  │ Landing  │  │   Auth   │  │     Dashboard      │    │
│  │  Page    │→ │   Page   │→ │  (Timeline, Code,  │    │
│  │          │  │          │  │  Variables, Sessions)│   │
│  └──────────┘  └──────────┘  └────────────────────┘    │
└────────────────────────┬────────────────────────────────┘
                         │ HTTP (REST API)
                         ▼
┌─────────────────────────────────────────────────────────┐
│                  Backend (FastAPI + Python)              │
│                                                         │
│  ┌──────────┐    ┌──────────────────────────────────┐   │
│  │  Routes  │───→│           Engine                  │  │
│  │ /execute │    │  ┌────────┐  ┌────────────────┐  │  │
│  │ /state   │    │  │Executor│→ │ Worker Process │  │  │
│  │ /line    │    │  └────────┘  │  ┌──────────┐  │  │  │
│  │ ...      │    │              │  │  Tracer   │  │  │  │
│  └──────────┘    │              │  │  Sandbox  │  │  │  │
│                  │              │  │ Serializer│  │  │  │
│  ┌──────────┐    │              │  └──────────┘  │  │  │
│  │  Models  │    │              └────────────────┘  │  │
│  │(Pydantic)│    │  ┌────────────────┐             │  │
│  └──────────┘    │  │ Reconstruction │             │  │
│                  │  └────────────────┘             │  │
│  ┌──────────┐    └──────────────────────────────────┘  │
│  │  Utils   │                                          │
│  │(Storage) │     sessions/  ← JSON session files      │
│  └──────────┘                                          │
└─────────────────────────────────────────────────────────┘
```

---

## Tech Stack

### Backend
| Technology | Purpose |
|---|---|
| **Python 3.8+** | Core language |
| **FastAPI** | REST API framework |
| **Pydantic** | Request/response validation |
| **multiprocessing** | Isolated code execution in child processes |
| **sys.settrace** | Python's built-in trace hook for line-level debugging |

### Frontend
| Technology | Purpose |
|---|---|
| **React 18** | UI framework |
| **Vite 5** | Dev server & bundler |
| **Framer Motion** | Animations & transitions |
| **Lucide React** | Icon library |
| **TailwindCSS (CDN)** | Utility-first CSS |

---

## Project Structure

```
TIMELOOP1/
├── backend/
│   ├── app/
│   │   ├── __init__.py
│   │   ├── main.py                 # FastAPI app entry point
│   │   ├── engine/
│   │   │   ├── __init__.py
│   │   │   ├── executor.py         # Orchestrates execution in a subprocess
│   │   │   ├── worker.py           # Subprocess entry — runs user code + tracer
│   │   │   ├── tracer.py           # Core tracing engine (sys.settrace callback)
│   │   │   ├── sandbox.py          # Sandbox globals & safe import restrictions
│   │   │   ├── serializer.py       # Safe serialization of arbitrary Python values
│   │   │   ├── reconstruction.py   # Reconstruct full state from checkpoint + deltas
│   │   │   └── limits.py           # Execution limits (timeout, depth, steps)
│   │   ├── models/
│   │   │   ├── __init__.py
│   │   │   └── execution.py        # Pydantic models for request/response
│   │   ├── routes/
│   │   │   ├── __init__.py
│   │   │   └── execute.py          # All API route handlers
│   │   └── utils/
│   │       └── storage.py          # Session save/load (JSON files)
│   ├── sessions/                   # Runtime directory for session JSON files
│   └── venv/                       # Python virtual environment
│
├── frontend/
│   ├── index.html                  # HTML entry point
│   ├── package.json                # Node dependencies & scripts
│   ├── vite.config.js              # Vite configuration
│   └── src/
│       ├── main.jsx                # React DOM mount
│       ├── App.jsx                 # Root component & page router
│       └── components/
│           ├── LandingPage.jsx     # Marketing / hero landing page
│           ├── AuthPage.jsx        # Login & signup form
│           └── Dashboard.jsx       # Main debugger interface
│
└── .gitignore
```

---

## Getting Started

### Prerequisites

- **Python 3.8+** with `pip`
- **Node.js 18+** with `npm`
- **Git**

### Backend Setup

```bash
# Navigate to the backend directory
cd backend

# Create and activate a virtual environment
python -m venv venv
venv\Scripts\activate        # Windows
# source venv/bin/activate   # macOS/Linux

# Install dependencies
pip install fastapi uvicorn pydantic

# Start the API server
uvicorn app.main:app --reload --port 8000
```

The backend will be available at `http://localhost:8000`. Visit `http://localhost:8000/docs` for the interactive Swagger UI.

### Frontend Setup

```bash
# Navigate to the frontend directory
cd frontend

# Install dependencies
npm install

# Start the dev server
npm run dev
```

The frontend will be available at `http://localhost:3000`.

---

## API Reference

### `POST /execute`

Execute Python code and return the full trace.

**Request Body:**

```json
{
  "code": "x = 10\ny = x * 2\nprint(y)",
  "mode": "fast"          // "fast" (default) or "detailed"
}
```

**Response:**

```json
{
  "session_id": "uuid-string",
  "snapshots": [
    {
      "step": 1,
      "event": "line",
      "line_no": 1,
      "function": "global",
      "stack": ["global"],
      "locals": { "x": 10 },
      "delta": null,
      "is_full": true
    }
  ],
  "variable_history": {
    "x": [[1, 10]],
    "y": [[2, 20]]
  },
  "line_index": {
    "1": [1],
    "2": [2]
  },
  "truncated": false,
  "error": null
}
```

---

### `GET /state`

Reconstruct the full variable state at a specific step.

| Parameter | Type | Description |
|---|---|---|
| `session_id` | `string` | Session UUID from `/execute` |
| `step` | `int` | Target step number |

**Response:**

```json
{
  "step": 5,
  "state": {
    "x": 10,
    "y": 20
  }
}
```

---

### `GET /variable-history`

Get the change history of a single variable across the entire execution.

| Parameter | Type | Description |
|---|---|---|
| `session_id` | `string` | Session UUID |
| `name` | `string` | Variable name |

**Response:**

```json
{
  "variable": "x",
  "history": [
    { "step": 1, "value": 0 },
    { "step": 5, "value": 10 },
    { "step": 12, "value": 42 }
  ]
}
```

---

### `GET /function-calls`

List all execution steps where a given function was called. **Requires detailed mode.**

| Parameter | Type | Description |
|---|---|---|
| `session_id` | `string` | Session UUID |
| `name` | `string` | Function name |

**Response:**

```json
{
  "function": "my_func",
  "calls": [3, 7, 15]
}
```

---

### `GET /line`

List all execution steps that visited a specific source line. **Not available in fast mode.**

| Parameter | Type | Description |
|---|---|---|
| `session_id` | `string` | Session UUID |
| `line_no` | `int` | Source line number |

**Response:**

```json
{
  "line": 5,
  "steps": [3, 12, 25]
}
```

---

### `GET /exceptions`

List all exceptions that occurred during execution.

| Parameter | Type | Description |
|---|---|---|
| `session_id` | `string` | Session UUID |

**Response:**

```json
{
  "exceptions": [
    {
      "step": 8,
      "line_no": 15,
      "error": "ZeroDivisionError: division by zero"
    }
  ]
}
```

---

### `POST /explain`  _(Phase 7 — AI Explainer)_

Analyze the program at the user's current point in the replay timeline and
return a structured complexity analysis + optimization. Secrets stay
server-side — **no API key is ever sent to or stored in the frontend.**

**Request Body:**

```json
{
  "code": "for i in range(n):\n    for j in range(n):\n        pass",
  "current_line": 2,
  "snapshot": { "step": 5, "function": "global", "stack": ["global"] },
  "variables": { "n": 10 },
  "stack": ["global"],
  "mode": "smart"
}
```

**Response:**

```json
{
  "timeComplexity": "O(n²)",
  "spaceComplexity": "O(1)",
  "expectedComplexity": "O(n) time, O(n) space",
  "issue": "2-level nested iteration detected...",
  "optimization": "Replace inner scans with a hash set / dict lookup...",
  "optimizedCode": "...",
  "activeLineInfo": "Line 2: for j in range(n):",
  "contextSummary": "Step 5 in global with 1 active variable(s).",
  "source": "llm",
  "model": "claude-opus-5",
  "error": null
}
```

**How it degrades:** the endpoint always returns a complete analysis.
- With `ANTHROPIC_API_KEY` set → `source: "llm"` (Claude), with the
  deterministic analysis back-filling any field the model omits.
- Without a key (or if the LLM call fails) → `source: "static-analysis"`,
  produced by a deterministic **AST** analyzer (real loop-nesting depth,
  recursion, backtracking detection) — no network required.

Enable the LLM path by copying `backend/.env.example` to `backend/.env` and
setting `ANTHROPIC_API_KEY`. Check the active mode at `GET /health`.

---

## Backend Modules

### Engine

The engine is the core of TimeLoop — it handles code execution, tracing, and state reconstruction.

#### Tracer

**File:** `backend/app/engine/tracer.py`

The `Tracer` class implements a `sys.settrace` callback that records execution snapshots. Key behaviors:

- **Dual-mode tracing:**
  - `fast` mode — Traces only the global scope and caps at 2,000 steps. Skips function internals.
  - `detailed` mode — Traces all `line`, `call`, `return`, and `exception` events at every scope.
- **Delta compression** — Only the first snapshot (and every Nth snapshot at `checkpoint_interval=50`) stores the full `locals` dict. All intermediate snapshots store only the changed variables (`delta`).
- **Duplicate filtering** — Consecutive snapshots with the same line number, function, and delta are deduplicated.
- **Variable history** — Tracks every value change of global-scope variables as `(step, value)` tuples.
- **Line index** — Maps each `line_no` → list of steps that executed that line.
- **Safety limits** — Enforces `max_steps` (default 20,000) and `max_depth` (default 1,000).

#### Executor

**File:** `backend/app/engine/executor.py`

The `ExecutionEngine` class orchestrates code execution:

1. Creates a `multiprocessing.Pipe` for communication.
2. Spawns a child `Process` running `worker_main`.
3. Waits up to `EXECUTION_TIMEOUT` seconds.
4. If the process doesn't finish in time, it terminates the child and returns a timeout error.
5. Otherwise, reads the trace results from the pipe.

#### Worker

**File:** `backend/app/engine/worker.py`

The `worker_main` function runs inside the child process:

- **Detailed mode:** Installs `sys.settrace(tracer.trace)`, then `exec()`s the user code in the sandbox globals. The tracer captures every execution event.
- **Fast mode:** Runs `exec()` **without** tracing. After completion, it creates a single snapshot from the final `sandbox_globals`, builds a basic variable history, and returns it.
- Always sends results back through the `Pipe` connection and closes it, even on error.

#### Sandbox

**File:** `backend/app/engine/sandbox.py`

Provides a restricted execution environment:

- **Whitelisted builtins:** `print`, `range`, `len`, `int`, `float`, `str`, `bool`, `list`, `dict`, `set`, `tuple`, `abs`, `min`, `max`, `sum`.
- **Safe import:** Only `math` and `random` modules are allowed. All other imports raise `ImportError`.
- `get_sandbox_globals()` returns a globals dict with `__builtins__` replaced by the whitelist.

#### Serializer

**File:** `backend/app/engine/serializer.py`

`safe_serialize(value)` converts arbitrary Python objects into JSON-safe representations:

- Primitives (`int`, `float`, `bool`, `None`) pass through unchanged.
- Strings are truncated at 200 characters.
- Lists/tuples are capped at 50 items, recursively serialized to `max_depth=3`.
- Dicts are capped at 50 entries.
- Functions are serialized as `"<function name>"`.
- Everything else falls back to `str(value)`.

#### Reconstruction

**File:** `backend/app/engine/reconstruction.py`

`reconstruct_state(snapshots, target_step)` rebuilds the full variable state at any step:

1. Binary searches (`bisect`) for the closest snapshot ≤ `target_step`.
2. Walks backward to the nearest full checkpoint (`is_full=True`).
3. Starts from the checkpoint's `locals` dict.
4. Applies all subsequent `delta` dicts forward up to `target_step`.
5. Handles `"__deleted__"` markers by removing variables from the state.

#### Limits

**File:** `backend/app/engine/limits.py`

| Constant | Value | Description |
|---|---|---|
| `MAX_STEPS` | 20,000 | Maximum number of traced steps |
| `MAX_DEPTH` | 1,000 | Maximum call stack depth |
| `MAX_CONTAINER_ITEMS` | 50 | Maximum items serialized from a list/dict |
| `MAX_SERIALIZATION_DEPTH` | 4 | Maximum nesting depth for serialization |
| `EXECUTION_TIMEOUT` | 8 seconds | Maximum wall-clock time for code execution |

### Models

**File:** `backend/app/models/execution.py`

Pydantic models for request/response validation:

| Model | Fields | Purpose |
|---|---|---|
| `ExecutionRequest` | `code: str`, `mode: Optional[str] = "fast"` | Incoming execution request |
| `Snapshot` | `step`, `event`, `line_no`, `function`, `stack`, `locals`, `delta`, `is_full` | A single execution snapshot |
| `ExecutionResponse` | `session_id`, `snapshots`, `variable_history`, `line_index`, `truncated`, `error` | Full execution result |

### Routes

**File:** `backend/app/routes/execute.py`

All API endpoints are defined here using FastAPI's `APIRouter`. See the [API Reference](#api-reference) section for full details.

### Utils

**File:** `backend/app/utils/storage.py`

Simple file-based session persistence:

- `save_session(session_id, data)` — Writes session data as JSON to `sessions/{session_id}.json`.
- `load_session(session_id)` — Reads and returns session data from disk, or `None` if not found.

---

## Frontend Components

| Component | File | Description |
|---|---|---|
| **App** | `src/App.jsx` | Root component. Manages page state (`landing` → `auth` → `dashboard`). Renders animated background effects. |
| **LandingPage** | `src/components/LandingPage.jsx` | Hero page with project branding, tagline, and "Get Early Access" CTA. Uses Framer Motion for staggered fade-in animations. |
| **AuthPage** | `src/components/AuthPage.jsx` | Sign-up / sign-in form with glassmorphism card design. Supports toggling between modes. |
| **Dashboard** | `src/components/Dashboard.jsx` | The main debugger interface. Features a sidebar navigation, execution timeline with playback controls, code viewer with line highlighting, variable inspector, and session history panel. |

### Dashboard Sub-Components

| Component | Description |
|---|---|
| `NavItem` | Sidebar navigation button with icon + label |
| `CodeViewer` | Displays source code with line numbers and error highlighting |
| `VariableItem` | Individual variable display with name, type, and value |
| `StatCard` | Small statistics card (e.g., "Total: 128") |
| `StatusBadge` | Colored badge showing session status (completed / failed / running) |

---

## Execution Modes

### Fast Mode (Default)

- **No `sys.settrace` hook** — code runs at full speed.
- After execution, a single snapshot is created from the final global state.
- Variable history has only one entry (the final value).
- **Line tracking and function call tracking are NOT available.**
- Step limit: **2,000** (if tracing is attempted).
- Best for: Quick runs where you only need the final result.

### Detailed Mode

- `sys.settrace` is installed before execution.
- Every `line`, `call`, `return`, and `exception` event is captured.
- Full delta-based snapshot stream with checkpoints every 50 steps.
- Variable history tracks every change.
- Line index and function call tracking are fully available.
- Step limit: **20,000**.
- Best for: Deep debugging where you need to step through execution.

---

## Security & Sandboxing

TimeLoop executes arbitrary user-submitted Python code. The following safeguards are in place:

1. **Restricted builtins** — Only a handful of safe builtins (`print`, `range`, `len`, type constructors, aggregation functions) are available. Dangerous functions like `open`, `eval`, `exec`, `__import__` (direct) are removed.
2. **Controlled imports** — Custom `safe_import` only allows `math` and `random`. All other modules are blocked.
3. **Process isolation** — User code runs in a `multiprocessing.Process`, isolating it from the main API server.
4. **Execution timeout** — A hard timeout of 8 seconds kills runaway processes.
5. **Step limits** — The tracer aborts after 20,000 steps (detailed) or 2,000 steps (fast).
6. **Depth limits** — Call stack depth is limited to 1,000 frames.
7. **Serialization limits** — Containers are capped at 50 items, strings at 200 chars, nesting at 3 levels.

> **⚠️ Note:** This sandbox is NOT production-hardened. It is designed for educational/demo purposes. For production use, consider running user code in a containerized environment (e.g., Docker with restricted capabilities, seccomp profiles, and network isolation).

---

## Configuration

Key configuration values are centralized in `backend/app/engine/limits.py`:

```python
MAX_STEPS = 20000               # Max traced steps before abort
MAX_DEPTH = 1000                # Max call stack depth
MAX_CONTAINER_ITEMS = 50        # Max items serialized per list/dict
MAX_SERIALIZATION_DEPTH = 4     # Max nesting depth
EXECUTION_TIMEOUT = 8           # Seconds before process is killed
```

The Tracer also has an internal `checkpoint_interval = 50`, controlling how often full state checkpoints are stored vs. deltas.

CORS is configured in `backend/app/main.py` to allow all origins (`*`) for development convenience. **Restrict this in production.**

---

## Smart Mode Advanced Construct Guarantees (Phase 5)

These guarantees define what Smart Mode currently commits to for advanced Python constructs. The goal is replay integrity, not fake visibility.

### 1) Generators / `yield`
- Classification: partially supported
- Guaranteed:
  - Native generator semantics execute correctly.
  - `next(gen)` call ordering is deterministic.
  - Top-level state deltas around generator consumption are deterministic.
- Not guaranteed:
  - Generator-frame ownership across suspension/resume is not replay-faithful.
  - `yield` is not a first-class replay event.
  - `yield from` attribution can collapse onto caller-visible line events.
- Replay integrity risk: medium

### 2) `async` / `await`
- Classification: partially supported
- Guaranteed:
  - Native coroutine objects and await execution are preserved by Python runtime.
  - Deterministic replay ordering is possible for simple direct coroutine stepping.
- Not guaranteed:
  - Event-loop scheduling semantics are not represented.
  - Suspension/resume boundaries are not modeled as replay-owned events.
  - Async stack ownership is not a formal guarantee.
- Replay integrity risk: high

### 3) Decorators
- Classification: partially supported
- Guaranteed:
  - Wrapper execution is visible when wrapper calls are instrumented.
  - Native decorated-call behavior is preserved.
- Not guaranteed:
  - Wrapped-function identity attribution is not stable (wrapper/local names may appear instead of original callable identity).
  - Nested decorators can produce attribution ambiguity between wrapper layers.
- Replay integrity risk: medium

### 4) Closures / nested functions
- Classification: partially supported
- Guaranteed:
  - Lexical capture and `nonlocal` mutation execute natively and deterministically.
  - Nested function calls are visible.
- Not guaranteed:
  - Captured-variable ownership is not explicitly modeled as closure-cell events.
  - Attribution may flatten closure mutations to inner-frame line events only.
- Replay integrity risk: medium

### 5) Lambda execution
- Classification: transparent / intentionally uninstrumented (fine-grain)
- Guaranteed:
  - Lambda execution semantics are native Python semantics.
  - Lambda invocation can appear as normal callable events.
- Not guaranteed:
  - Lambda internals are not expanded into dedicated semantic event families.
  - No special lambda-level ownership model beyond generic call/line handling.
- Replay integrity risk: low

### 6) Comprehensions
- Classification: transparent / intentionally uninstrumented (loop-internal detail)
- Guaranteed:
  - Native comprehension results are deterministic and preserved.
  - Assignment of comprehension result is replay-visible at statement level.
- Not guaranteed:
  - Per-iteration comprehension body/branch visibility is not provided.
  - Generator-expression internal stepping is not modeled.
- Replay integrity risk: low

### 7) Context managers (`with`)
- Classification: partially supported
- Guaranteed:
  - Native `__enter__`/body/`__exit__` ordering executes correctly.
  - Nested `with` execution order is deterministic.
- Not guaranteed:
  - Replay attribution for dunder calls can be ambiguous (for example, `__exit__` may appear without robust frame ownership metadata).
  - Exception-interaction semantics are not fully normalized as dedicated context-manager semantic events.
- Replay integrity risk: medium

---

## Smart Mode Replay Invariants (Phase 5)

These are the formal replay invariants validated for Smart Mode. They define the replay contract used by Phase 6 checkpoint reconstruction planning.

### 1) Timeline determinism
- Classification: stable
- Guarantee:
  - Re-running identical code produces identical replay event structure (event type order, step order, branch chronology, stack chronology), excluding volatile object-address text in repr fallbacks.

### 2) Stack invariants
- Classification: stable
- Guarantee:
  - Stack depth transitions are consistent and bounded by call/unwind semantics.
  - Completed timelines end with `['global']` stack ownership.
  - Exception paths preserve unwind visibility without leaked frames in validated cases.

### 3) Event ordering invariants
- Classification: stable
- Guarantee:
  - Normal paths preserve call/line/control/return chronology.
  - Exception paths preserve exception and unwind sequencing in deterministic order.
  - Loop/control-flow events remain chronologically stable under nested interactions.

### 4) Replay reconstruction consistency
- Classification: partially stable
- Guarantee:
  - Delta stream, variable history, and snapshot ordering reconstruct semantically consistent final replay state in validated domains.
- Limitation:
  - Under timeout-truncated executions, reconstruction is only valid for the retained prefix timeline.

### 5) Replay index integrity
- Classification: stable
- Guarantee:
  - `step` is strictly monotonic.
  - `line_index` points to valid steps and matching `line_no`.
  - `variable_history` step references align with snapshot deltas.

### 6) Cross-domain interactions
- Classification: partially stable
- Guarantee:
  - Invariants remain stable for validated combinations:
    - recursion + exceptions
    - loops + branches + exceptions
    - nested mutable state + recursion (bounded depth)
    - decorators + closures + branches
- Limitation:
  - High-stress inputs may hit execution timeout; this is a scalability boundary, not a replay-ordering contract change.

### Phase 6 dependency notes
- Phase 6 depends directly on:
  - deterministic step/event chronology
  - valid stack ownership transitions
  - stable index mappings (`line_index`, `variable_history`)
  - canonical delta-driven reconstruction semantics
- Must remain unchanged before Phase 6 architecture work:
  - replay-state ownership model
  - stack/event ownership boundaries
  - AST/runtime/transport separation

---

## Contributing

1. Fork the repository.
2. Create a feature branch: `git checkout -b feature/my-feature`.
3. Commit your changes: `git commit -m "Add my feature"`.
4. Push to the branch: `git push origin feature/my-feature`.
5. Open a Pull Request.

---

## License

This project is currently unlicensed. Contact the maintainers for usage terms.

---

<p align="center">
  Built with ❤️ by the <strong>TimeLoop Labs</strong> team
</p>
