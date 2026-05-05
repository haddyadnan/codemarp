# CodeMarp

**Static code maps for Python, TypeScript, and JavaScript**

CodeMarp builds three views of a codebase from static analysis:

| Level | What you get |
|---|---|
| High | Module and package architecture |
| Mid | Function call relationships |
| Low | Control flow inside one function |

It exports Mermaid graphs, JSON data, and standalone browser views with Mermaid or Cytoscape.

## Install

### Homebrew

```bash
brew tap haddyadnan/forge
brew install codemarp
```

### uv

Install the CLI as a tool:

```bash
uv tool install codemarp
```

Install a specific release from source:

```bash
uv tool install git+https://github.com/haddyadnan/codemarp.git@v0.5.0
```

### Development

```bash
uv sync --extra dev
```

## Supported languages

| Language | Support |
|---|---|
| Python | Tree-sitter by default, AST available with `--parser-engine ast` |
| TypeScript | Tree-sitter for `.ts` and `.tsx` |
| JavaScript | Tree-sitter for `.js` |

Low-level CFG is currently Python-only.

## Quickstart

Analyze a repo and write graph files:

```bash
codemarp analyze src --out out
```

Open an interactive browser view:

```bash
codemarp view src --mode full --renderer cytoscape
```

Use Mermaid instead:

```bash
codemarp view src --mode full --renderer mermaid
```

Trace from one function:

```bash
codemarp analyze src \
  --mode trace \
  --focus codemarp.cli.main:analyze_command \
  --out out
```

Inspect low-level control flow for one Python function:

```bash
codemarp analyze src \
  --mode low \
  --focus codemarp.cli.main:analyze_command \
  --out out
```

Point CodeMarp at the folder that contains your top-level package:

```bash
# flat layout
codemarp analyze .

# src layout
codemarp analyze src
```

`--focus` and `--module` must match module IDs relative to the root you analyze.

## Modes

- `full`: architecture + full function graph
- `trace`: follow calls forward from one function
- `reverse`: find what reaches one function
- `module`: show functions and relationships inside one module
- `low`: build a control-flow graph for one Python function

Requirements:

- `--focus` is required for `trace`, `reverse`, and `low`
- `--module` is required for `module`

`--debug-resolution` prints why mid-level call edges were resolved:

- `same_module`
- `imported_symbol`
- `imported_module`
- `unique_global`

Example:

```bash
codemarp analyze path/to/repo --out out --debug-resolution > debug.txt
```

## Output

`full`, `trace`, `reverse`, and `module` modes produce:

```text
out/
  high_level.mmd
  mid_level.mmd
  mid_level.json
  graph.json
```

`low` mode produces:

```text
out/
  high_level.mmd
  low_level.mmd
  low_level.json
  graph.json
```

`view --out` writes standalone HTML:

```bash
codemarp view src \
  --mode trace \
  --focus codemarp.cli.main:analyze_command \
  --renderer cytoscape \
  --out codemarp_trace.html
```

Mermaid output renders well in GitHub, Mermaid Live Editor, and VS Code Mermaid preview extensions.

## Sample outputs

Sample outputs generated from this repo are included under [`samples/`](samples):

- [`samples/codemarp_full_out/README.md`](samples/codemarp_full_out/README.md)
- [`samples/codemarp_trace_out/README.md`](samples/codemarp_trace_out/README.md)
- [`samples/codemarp_low_out/README.md`](samples/codemarp_low_out/README.md)

## Guarantees and limitations

### High-level

- Built from imports and grouping
- Best-effort architecture view
- Can be sparse depending on project layout

### Mid-level

- Conservative call graph
- Resolves:
  - same-module functions
  - imported symbols (`from x import y`)
  - imported modules (`import x; x.y()`)
  - unique module-level functions
- Prefers precision over recall
- Avoids speculative resolution for dynamic dispatch and unresolved method calls

### Low-level

- Structural CFG only
- No runtime modeling
- Python-only for now

Known limitations:

| Limitation | Workaround |
|---|---|
| Relative imports can produce sparse high-level graphs | Use `module`, `trace`, or `reverse` |
| Method calls such as `self.method()` are handled conservatively | Some real edges may be omitted |
| Dynamic dispatch is not tracked | Treat results as static structure only |
| TypeScript and JavaScript support are conservative | Common function/import/call facts are covered, some forms are still omitted |
| Large full graphs can be noisy | Use focused modes instead of `full` |

## Status

- Python, TypeScript, and JavaScript support
- Tree-sitter default parser
- Python AST fallback available with `--parser-engine ast`
- Mermaid and Cytoscape browser renderers
- `v0.5.x` release line

## Roadmap

- Better call resolution and symbol handling
- Broader multi-language support
- Language-neutral low-level CFG
- Richer interactive viewer workflows
- More filtering and graph navigation controls

## Philosophy

- Useful before perfect
- Readable before complete
- Static first

## Name

**CodeMarp** sounds like "code map", which is what it produces.
