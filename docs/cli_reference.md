# CLI Reference

The `adapter-cli` provides a command-line interface for managing contracts, inspecting state, analyzing performance, and debugging violations in the Polyglot FFI Contract Verifier.

## Installation

The CLI can be run directly from the source or installed as part of the package.

```bash
# Direct execution
python cli/adapter_cli.py --help
```

## Global Options

- `--format {text,json,table}`: Set the output format (default: `text`).

## Commands

### `contract`
Manage and inspect FFI contracts.

#### `validate <file>`
Validate the format and structure of a contract JSON file.
```bash
adapter-cli contract validate my_contract.json
```

#### `inspect <file>`
Inspect contract metadata and function signatures.
```bash
adapter-cli contract inspect my_contract.json
```

### `state`
Inspect and manage adapter state snapshots.

#### `snapshot <output>`
Create a snapshot of the current adapter state and save it to a file.
```bash
adapter-cli state snapshot current_state.json
```

#### `query <file> <path>`
Query specific attributes within a state snapshot using dot-notation.
```bash
adapter-cli state query state.json statistics.loaded_functions
```

### `perf`
Analyze performance metrics.

#### `report [--metrics <file>]`
Generate a performance report either from a running instance or a metrics file.
```bash
adapter-cli perf report --format table
```

### `debug`
Debugging and troubleshooting utilities.

#### `violations [--filter <string>]`
Show recent contract violations, optionally filtered by function or clause.
```bash
adapter-cli debug violations --filter "process_buffer"
```

## Output Formats

1.  **Text (Default)**: Optimized for human readability in the terminal.
2.  **JSON**: Machine-readable format suitable for piping to other tools like `jq`.
3.  **Table**: Tabular representation for lists of data (e.g., function lists or violations).

## Examples

### Validating a Contract
```bash
$ adapter-cli contract validate examples/contracts/image_proc.json
✓ Contract is valid
  Contract ID: image_processing
  Functions: 2
```

### Querying Statistics via JSON
```bash
$ adapter-cli --format json state query state.json statistics
{
  "loaded_functions": 5,
  "ffi_mode": "ctypes",
  "diagnostics_enabled": true
}
```

### Viewing Violations in a Table
```bash
$ adapter-cli debug violations --format table
function       | clause       | timestamp
-------------- | ------------ | --------------------
process_buffer | range_check  | 2024-01-15T10:30:00Z
allocate       | nullability | 2024-01-15T10:31:00Z
```
