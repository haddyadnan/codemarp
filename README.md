# CodeMarp

**Multi-level code architecture and relationship mapping**

> Understand a codebase like a map — zoom in, zoom out, follow the flow.

---

## The problem

Large codebases are hard to navigate. You open a file and you're already lost. You don't know what calls what, where things live, or what actually happens inside a function.

Documentation is outdated. Diagrams don't exist. The only way to understand the code is to read all of it.

CodeMarp is a different approach.

---

## What CodeMarp does

Given a Python repository, CodeMarp gives you three zoom levels:

| Level | What you see |
|-------|-------------|
| **High** | Module and package architecture — how things are organised |
| **Mid** | Function relationships — who calls what |
| **Low** | Control flow inside a function — what actually happens |

Think of it as **Google Maps for your codebase**.

Zoom out to see the city. Zoom in to see the streets. Zoom in further to see the building layout.

---

## Output

Every analysis produces:

```
out/
  high_level.mmd    # architecture graph
  mid_level.mmd     # function call graph
  low_level.mmd     # control flow (when using --view low)
  graph.json        # full graph data for tooling
```

- **Mermaid** (`.mmd`) — renders in GitHub, VS Code, Mermaid Live Editor
- **JSON** — for tooling, integrations, and future UI

---

## Install

```bash
pip install codemarp
```

Or for development:

```bash
pip install -e .
```

---

## Usage

### Analyse a repo

```bash
codemarp analyze path/to/repo --out out
```

Point at the folder that **contains your top-level package**:

```bash
# flat layout: mypackage/ is at root
codemarp analyze .

# src layout: mypackage/ is inside src/
codemarp analyze src
```

---

### Views

#### Full (default)
See the entire graph — architecture + all function relationships.

```bash
codemarp analyze path/to/repo --view full --out out
```

#### Trace — what does this function call?
Follow a function forward through the call graph.

```bash
codemarp analyze path/to/repo \
  --view trace \
  --focus package.module:function_name \
  --max-depth 3 \
  --out out
```

#### Reverse — what calls this function?
Find every path that leads to a function.

```bash
codemarp analyze path/to/repo \
  --view reverse \
  --focus package.module:function_name \
  --out out
```

#### Module — what lives in this module?
Scope the graph to a single module.

```bash
codemarp analyze path/to/repo \
  --view module \
  --module package.module \
  --out out
```

#### Low — what happens inside this function?
Render the control flow graph for a single function.

```bash
codemarp analyze path/to/repo \
  --view low \
  --focus package.module:function_name \
  --out out
```

---

## Typical workflow

```
1. codemarp analyze src --view full
   → understand the overall structure

2. codemarp analyze src --view module --module mypackage.core
   → inspect one area

3. codemarp analyze src --view trace --focus mypackage.core:run --max-depth 3
   → follow a specific entrypoint

4. codemarp analyze src --view low --focus mypackage.core:run
   → zoom into the logic
```

---

## Viewing the output

Mermaid files render automatically in:

- **GitHub** — paste into any `.md` file inside a ` ```mermaid ` block
- **[Mermaid Live Editor](https://mermaid.live)** — paste and share
- **VS Code** — with the Mermaid Preview extension

---

## Known limitations

CodeMarp is static analysis — it reads your code without running it.

| Limitation | Workaround |
|-----------|------------|
| Relative imports may produce sparse high-level graphs | Use `--view module` or `--view trace` instead |
| Method calls (`self.method()`) are best-effort resolved | False positive edges are possible |
| Dynamic dispatch is not tracked | Results reflect static structure only |
| Large full graphs can be hard to read | Use focused views — `trace`, `module`, `reverse` |

These are honest limitations, not bugs. Focused views exist precisely because full graphs on real codebases get noisy.

---

## Roadmap

- Better call resolution (method dispatch, aliases)
- Graph filtering and noise reduction
- Tree-sitter migration → multi-language support
- JavaScript / TypeScript support
- Interactive web UI

---

## Philosophy

**Useful before perfect.**
CodeMarp v0.1 is not exhaustive. It is correct for common cases and honest about where it isn't.

**Readable before complete.**
A graph you can understand is more valuable than a graph that shows everything.

**Static first.**
No runtime instrumentation. No code execution. Analysis runs anywhere.

---

## Status

- Python only (AST-based)
- CLI-first
- v0.1.0 — early but usable on real codebases

---

## Name

**CodeMarp** — sounds like "code map", because that's what it produces.

Expanded if you need it: *Code Mapping, Architecture, Relationships, and Paths*

---

*Built to answer the question every developer asks when they open an unfamiliar codebase: where do I even start?*codemarpcodemarpcodemarpcodemarp
