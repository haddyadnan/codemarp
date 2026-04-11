```markdown
# Codemap

Codemap is a tool for exploring Python codebases at three levels:

- **High level** → how modules/packages interact  
- **Mid level** → how functions call each other  
- **Low level** → how control flows inside a function  

It helps you answer:

- *“How is this codebase structured?”*
- *“What calls this function?”*
- *“What actually happens inside this function?”*

---

## Why Codemap?

Understanding unfamiliar code is hard because information is scattered:

- architecture lives across files
- function relationships are implicit
- control flow is hidden in code

Codemap turns that into **visual graphs**.

---

## The 3 Levels

### High Level — Architecture

Shows how modules/packages depend on each other.

```

codemap.cli → codemap.pipeline → codemap.views

```

Use this to understand structure and layering.

---

### Mid Level — Function Graph

Shows how functions call each other.

```

main.run → worker.process → db.save

````

Use this to trace behavior across the codebase.

---

### Low Level — Control Flow

Shows what happens *inside* a function.

- branches
- loops
- returns
- execution paths

Use this to understand logic in detail.

---

## Installation

```bash
uv venv
uv pip install -e .
````

---

## Usage

### Analyze a codebase

```bash
codemap analyze src
```

---

### View types

#### Full (default)

```bash
codemap analyze src --view full
```

Outputs:

* full graph
* high-level + mid-level views

---

#### Trace (forward)

```bash
codemap analyze src --view trace --focus module:function
```

Example:

```bash
codemap analyze src --view trace --focus codemap.cli.main:analyze_command
```

---

#### Reverse (callers)

```bash
codemap analyze src --view reverse --focus module:function
```

---

#### Module view

```bash
codemap analyze src --view module --module module_id
```

---

#### Low-level (control flow)

```bash
codemap analyze src --view low --focus module:function
```

Example:

```bash
codemap analyze src --view low --focus codemap.cli.main:analyze_command
```

---

## Output

Codemap writes to `./codemap_out` by default:

* `graph.json` — full graph data
* `high_level.mmd` — architecture view
* `mid_level.mmd` — function graph
* `low_level.mmd` — control flow (when using `--view low`)

You can view `.mmd` files using:

* Mermaid preview tools
* editors like Zed / VSCode with Mermaid support

---

## Focus format

Low-level and trace views require a focus:

```
module:function_name
module:ClassName.method_name
```

Examples:

```
app.main:run
app.service:Service.process
```

---

## Limitations

Codemap is **not a full semantic analyzer**.

It uses static heuristics, which means:

### Mid-level limitations

* cannot fully resolve:

  * `obj.method()` when type is unknown
  * dynamic dispatch
  * runtime-generated calls

### Low-level limitations

* only supports functions and methods
* does not support:

  * module-level executable code
  * full `try/except` control flow
  * `break` / `continue` / `match`

### General

* resolution is best-effort, not guaranteed exact

---

## Design philosophy

Codemap is built to be:

* **Useful** → gives real insight into code structure
* **Simple** → avoids unnecessary complexity
* **Honest** → does not pretend to fully understand runtime behavior

---

## Roadmap

Current focus:

* improving visualization and readability
* better documentation
* real-world validation

Future directions:

* richer resolution
* UI / interactive exploration
* support for other languages

---

## Status

Early-stage but functional.

Feedback and experimentation encouraged.
