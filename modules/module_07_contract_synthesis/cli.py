# ==============================================================================
# Polyglot FFI Contract Verifier
# Copyright (c) 2025 Darshit Lagdhir and Team LOGLORE. All Rights Reserved.
#
# This file is part of the Polyglot FFI Contract Verifier ecosystem.
# It is licensed under the Antigravity Source-Available and Technical
# Protection License (ASTPL).
#
# PROHIBITED USES: Commercial Use, Network Access Provision, and Machine
# Training Use are strictly prohibited absent explicit written authorization.
#
# Removal or alteration of this header may constitute a violation of the
# repository's governing agreements.
#
# File Integrity Identifier: 2f95ac040241fc16
# ==============================================================================

"""
Module 07: CLI Interface (Prompt 6/15)

Command-line interface for synthesis operations.

Provides user-friendly commands for:
- Contract synthesis
- Validation
- Batch processing
- Regression detection
- Reporting
"""

import sys
import json
import logging
import glob
from pathlib import Path
from typing import Optional, List, Tuple
from concurrent.futures import ThreadPoolExecutor, as_completed

import click
from rich.console import Console
from rich.table import Table
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn
from rich import print as rprint

# Internal imports deferred to avoid circularity/startup cost
# but we need some at module level if used in type hints or decorators.
# CLI functions use them.

# We will move them inside commands or keep them if no circularity found.
# Let's try to keeping standard library imports and `click`, `rich`.
# And defer application imports.

console = Console()

# ============================================================================
# CLI MAIN GROUP
# ============================================================================

@click.group()
@click.version_option(version="1.0.0", prog_name="pfcv-synth")
@click.option('--verbose', '-v', is_flag=True, help='Verbose output')
@click.option('--quiet', '-q', is_flag=True, help='Minimal output')
@click.pass_context
def cli(ctx, verbose, quiet):
    """
    PFCV Contract Synthesis CLI

    Generate, validate, and manage FFI contracts from IR artifacts.
    """
    # Setup context
    ctx.ensure_object(dict)
    ctx.obj['verbose'] = verbose
    ctx.obj['quiet'] = quiet

    # Configure logging
    if verbose:
        logging.basicConfig(level=logging.DEBUG, format='%(levelname)s: %(message)s')
    elif quiet:
        logging.basicConfig(level=logging.ERROR, format='%(levelname)s: %(message)s')
    else:
        logging.basicConfig(level=logging.INFO, format='%(message)s')

# ============================================================================
# SYNTHESIZE COMMAND
# ============================================================================

@cli.command()
@click.argument('ir_file', type=click.Path(exists=True, path_type=Path))
@click.option('--output', '-o', type=click.Path(path_type=Path), help='Output file')
@click.option('--format', '-f', type=click.Choice(['json', 'yaml', 'text']), default='text', help='Output format')
@click.option('--synthesis-version', default='1.0.0', help='Synthesis version')
@click.option('--strict/--no-strict', default=True, help='Strict validation')
@click.pass_context
def synthesize(ctx, ir_file, output, format, synthesis_version, strict):
    """
    Synthesize contract from IR artifact.

    Example:
        pfcv-synth synthesize input.json -o contract.json --format json
    """
    verbose = ctx.obj.get('verbose', False)
    quiet = ctx.obj.get('quiet', False)

    if not quiet:
        console.print(f"[blue]Synthesizing contract from:[/blue] {ir_file}")

    try:
        # Defer imports
        from module_05_ir_normalization.ir_serialization import IRSerializer
        from module_07_contract_synthesis.synthesis_engine import SynthesisEngine, SynthesisConfig
        from module_06_contract_schema.contract_serialization import ContractSerializer
        from module_07_contract_synthesis.contract_bridge import ContractBridge

        # Load IR
        if verbose:
            console.print("[dim]Loading IR...[/dim]")
        
        try:
            ir_serializer = IRSerializer()
            ir_content = ir_file.read_text(encoding='utf-8')
            ir_unit = ir_serializer.deserialize(ir_content)
        except Exception as e:
            console.print(f"[red]Failed to load IR:[/red] {e}")
            sys.exit(1)
        
        # Setup synthesis
        config = SynthesisConfig(
            synthesis_version=synthesis_version,
            strict_mode=strict
        )
        engine = SynthesisEngine(config)
        
        # Synthesize with progress
        if not quiet:
            with Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                console=console,
                transient=True
            ) as progress:
                task = progress.add_task("Synthesizing...", total=None)
                result = engine.synthesize(ir_unit, ir_file.stem)
                progress.update(task, completed=True)
        else:
            result = engine.synthesize(ir_unit, ir_file.stem)
        
        # Check result
        if not result.success:
            console.print("[red]✗ Synthesis failed[/red]")
            for error in result.errors:
                console.print(f"  [red]Error:[/red] {error}")
            sys.exit(1)
        
        # Output
        if output:
            _write_contract(result.contract, output, format)
            if not quiet:
                console.print(f"[green]✓ Contract written to:[/green] {output}")
        else:
            _print_contract(result, format)
        
        if not quiet:
            console.print(f"\n[green]✓ Success:[/green] {result.clauses_generated} clauses generated")

    except Exception as e:
        console.print(f"[red]✗ Error:[/red] {str(e)}")
        if verbose:
            console.print_exception()
        sys.exit(1)

# ============================================================================
# VALIDATE COMMAND
# ============================================================================

@cli.command()
@click.argument('contract_file', type=click.Path(exists=True, path_type=Path))
@click.pass_context
def validate(ctx, contract_file):
    """
    Validate contract file.

    Example:
        pfcv-synth validate contract.json
    """
    quiet = ctx.obj.get('quiet', False)

    if not quiet:
        console.print(f"[blue]Validating contract:[/blue] {contract_file}")

    try:
        from module_06_contract_schema.contract_serialization import ContractSerializer
        from module_06_contract_schema.contract_validation import ContractValidator

        # Load contract
        serializer = ContractSerializer()
        content = contract_file.read_text(encoding='utf-8')
        contract = serializer.deserialize(content)
        
        # Validate
        validator = ContractValidator()
        result = validator.validate(contract)
        
        if result.passed: # Assuming result has 'passed' property based on Prompt 4/5 logic
            console.print("[green]✓ Contract is valid[/green]")
            if not quiet:
                console.print(f"  Clauses: {len(contract.clauses)}")
                console.print(f"  Interface: {contract.header.target_interface_id}")
        else:
            console.print("[red]✗ Contract is invalid[/red]")
            # Assuming result has errors list
            for error in result.get_all_errors():
                console.print(f"  [red]Error:[/red] {error}")
            sys.exit(1)

    except Exception as e:
        console.print(f"[red]✗ Error:[/red] {str(e)}")
        sys.exit(1)

# ============================================================================
# DIFF COMMAND
# ============================================================================

@cli.command()
@click.argument('contract_a', type=click.Path(exists=True, path_type=Path))
@click.argument('contract_b', type=click.Path(exists=True, path_type=Path))
@click.pass_context
def diff(ctx, contract_a, contract_b):
    """
    Compare two contract files.

    Example:
        pfcv-synth diff old_contract.json new_contract.json
    """
    try:
        from module_06_contract_schema.contract_serialization import ContractSerializer, ContractDeserializer
        serializer = ContractSerializer()
        deserializer = ContractDeserializer()

        # Load contracts
        cA = deserializer.deserialize(contract_a.read_text(encoding='utf-8'))
        cB = deserializer.deserialize(contract_b.read_text(encoding='utf-8'))

        console.print(f"[blue]Comparing contracts:[/blue]")
        console.print(f"  A: {contract_a}")
        console.print(f"  B: {contract_b}")

        # Basic diff logic
        # Compare clause counts
        lenA = len(cA.clauses)
        lenB = len(cB.clauses)

        table = Table(title="Contract Diff Summary")
        table.add_column("Property", style="cyan")
        table.add_column("Contract A", style="magenta")
        table.add_column("Contract B", style="magenta")
        table.add_column("Status", style="bold")

        table.add_row(
            "Target Interface",
            cA.header.target_interface_id,
            cB.header.target_interface_id,
            "Match" if cA.header.target_interface_id == cB.header.target_interface_id else "[red]Mismatch[/red]"
        )
        table.add_row(
            "Clause Count",
            str(lenA),
            str(lenB),
            "Match" if lenA == lenB else f"[yellow]{lenB - lenA:+}[/yellow]"
        )

        console.print(table)

        # More detailed diff could compare clause IDs
        idsA = {c.clause_id for c in cA.clauses}
        idsB = {c.clause_id for c in cB.clauses}

        added = idsB - idsA
        removed = idsA - idsB
        common = idsA & idsB

        if added:
            console.print(f"\n[green]Added clauses ({len(added)}):[/green]")
            for aid in sorted(added):
                console.print(f"  + {aid}")
        
        if removed:
            console.print(f"\n[red]Removed clauses ({len(removed)}):[/red]")
            for rid in sorted(removed):
                console.print(f"  - {rid}")

        # Check for changes in common clauses
        changed = 0
        for cid in common:
            cA_clause = next(c for c in cA.clauses if c.clause_id == cid)
            cB_clause = next(c for c in cB.clauses if c.clause_id == cid)
            
            # Compare JSON representation
            a_json = json.dumps(cA_clause.to_dict(), sort_keys=True)
            b_json = json.dumps(cB_clause.to_dict(), sort_keys=True)
            if a_json != b_json:
                changed += 1

        if changed:
            console.print(f"\n[yellow]Changed clauses ({changed}):[/yellow] (Identical IDs, different content)")

        if not added and not removed and changed == 0:
            console.print("\n[green]✓ Contracts are identical[/green]")

    except Exception as e:
        console.print(f"[red]✗ Error:[/red] {str(e)}")
        sys.exit(1)

# ============================================================================
# BATCH COMMAND
# ============================================================================

@cli.command()
@click.argument('pattern', type=str)
@click.option('--output-dir', '-o', type=click.Path(path_type=Path), required=True, help='Output directory')
@click.option('--parallel/--no-parallel', default=True, help='Parallel processing')
@click.option('--max-workers', type=int, default=4, help='Max parallel workers')
@click.pass_context
def batch(ctx, pattern, output_dir, parallel, max_workers):
    """
    Batch synthesize multiple IR files.

    Example:
        pfcv-synth batch "interfaces/*.json" --output-dir contracts/
    """
    quiet = ctx.obj.get('quiet', False)

    # Find files
    ir_files = [Path(f) for f in glob.glob(pattern)]

    if not ir_files:
        console.print(f"[yellow]No files matching pattern:[/yellow] {pattern}")
        sys.exit(0)

    if not quiet:
        console.print(f"[blue]Found {len(ir_files)} files[/blue]")

    # Create output directory
    output_dir.mkdir(parents=True, exist_ok=True)

    # Process files
    results = []

    if parallel:
        with Progress(
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
            console=console,
            transient=quiet
        ) as progress:
            task = progress.add_task("Processing...", total=len(ir_files))
            
            with ThreadPoolExecutor(max_workers=max_workers) as executor:
                futures = {
                    executor.submit(_synthesize_single, f, output_dir): f
                    for f in ir_files
                }
                
                for future in as_completed(futures):
                    ir_file = futures[future]
                    try:
                        result = future.result()
                        results.append((ir_file, result, None))
                    except Exception as e:
                        results.append((ir_file, None, str(e)))
                    
                    progress.update(task, advance=1)
    else:
        for ir_file in ir_files:
            try:
                result = _synthesize_single(ir_file, output_dir)
                results.append((ir_file, result, None))
            except Exception as e:
                results.append((ir_file, None, str(e)))

    # Report
    _print_batch_report(results)

# ============================================================================
# VERIFY-DETERMINISM COMMAND
# ============================================================================

@cli.command()
@click.argument('ir_file', type=click.Path(exists=True, path_type=Path))
@click.option('--iterations', type=int, default=10, help='Number of iterations')
@click.pass_context
def verify_determinism(ctx, ir_file, iterations):
    """
    Verify synthesis determinism.

    Example:
        pfcv-synth verify-determinism input.json --iterations 10
    """
    console.print(f"[blue]Verifying determinism:[/blue] {ir_file}")
    console.print(f"Iterations: {iterations}")

    try:
        from module_05_ir_normalization.ir_serialization import IRSerializer
        from module_07_contract_synthesis.versioning import DeterminismVerifier

        # Load IR
        ir_serializer = IRSerializer()
        ir_unit = ir_serializer.deserialize(ir_file.read_text(encoding='utf-8'))
        
        # Verify
        verifier = DeterminismVerifier()
        
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console
        ) as progress:
            task = progress.add_task(f"Running {iterations} iterations...", total=None)
            report = verifier.verify_determinism(ir_unit, "1.0.0", iterations)
            progress.update(task, completed=True)
        
        # Report
        if report.deterministic:
            console.print(f"[green]✓ Deterministic[/green]")
            console.print(f"  All {report.iterations_tested} runs produced identical output")
            if report.fingerprint:
                console.print(f"  Fingerprint: {report.fingerprint[:16]}...")
        else:
            console.print(f"[red]✗ Non-deterministic[/red]")
            console.print(f"  Reason: {report.reason}")
            console.print(f"  Unique fingerprints: {report.unique_fingerprints}")
            sys.exit(1)

    except Exception as e:
        console.print(f"[red]✗ Error:[/red] {str(e)}")
        sys.exit(1)

# ============================================================================
# RECORD-BASELINE COMMAND
# ============================================================================

@cli.command()
@click.argument('ir_file', type=click.Path(exists=True, path_type=Path))
@click.pass_context
def record_baseline(ctx, ir_file):
    """
    Record synthesis baseline for CI regression detection.

    Example:
        pfcv-synth record-baseline input.json
    """
    console.print(f"[blue]Recording baseline:[/blue] {ir_file}")

    try:
        from module_05_ir_normalization.ir_serialization import IRSerializer
        from module_07_contract_synthesis.synthesis_engine import SynthesisEngine, SynthesisConfig
        from module_07_contract_synthesis.versioning import FingerprintComputer, RegressionDetector

        # Load and synthesize
        ir_serializer = IRSerializer()
        ir_unit = ir_serializer.deserialize(ir_file.read_text(encoding='utf-8'))
        
        config = SynthesisConfig()
        engine = SynthesisEngine(config)
        result = engine.synthesize(ir_unit, ir_file.stem)
        
        if not result.success:
            console.print("[red]✗ Synthesis failed, cannot record baseline[/red]")
            sys.exit(1)
        
        # Compute fingerprint
        computer = FingerprintComputer()
        fingerprint = computer.compute_full_fingerprint(
            ir_unit, config, result.contract
        )
        
        # Record
        detector = RegressionDetector()
        detector.record_baseline(ir_file.stem, fingerprint)
        
        console.print(f"[green]✓ Baseline recorded[/green]")
        console.print(f"  Synthesis version: {config.synthesis_version}")
        console.print(f"  Fingerprint: {fingerprint.compute_composite_hash()[:16]}...")

    except Exception as e:
        console.print(f"[red]✗ Error:[/red] {str(e)}")
        sys.exit(1)

# ============================================================================
# CHECK-REGRESSION COMMAND
# ============================================================================

@cli.command()
@click.argument('ir_file', type=click.Path(exists=True, path_type=Path))
@click.pass_context
def check_regression(ctx, ir_file):
    """
    Check for synthesis regression against baseline.

    Example:
        pfcv-synth check-regression input.json
    """
    console.print(f"[blue]Checking regression:[/blue] {ir_file}")

    try:
        from module_05_ir_normalization.ir_serialization import IRSerializer
        from module_07_contract_synthesis.synthesis_engine import SynthesisEngine, SynthesisConfig
        from module_07_contract_synthesis.versioning import FingerprintComputer, RegressionDetector

        # Synthesize current
        ir_serializer = IRSerializer()
        ir_unit = ir_serializer.deserialize(ir_file.read_text(encoding='utf-8'))
        
        config = SynthesisConfig()
        engine = SynthesisEngine(config)
        result = engine.synthesize(ir_unit, ir_file.stem)
        
        if not result.success:
            console.print("[red]✗ Synthesis failed[/red]")
            sys.exit(1)
        
        # Compute fingerprint
        computer = FingerprintComputer()
        fingerprint = computer.compute_full_fingerprint(
            ir_unit, config, result.contract
        )
        
        # Check regression
        detector = RegressionDetector()
        report = detector.check_for_regression(ir_file.stem, fingerprint)
        
        if report is None:
            console.print("[green]✓ No regression detected[/green]")
        elif report.severity == "info":
            console.print(f"[blue]ℹ {report.message}[/blue]")
        elif report.severity == "warning":
            console.print(f"[yellow]⚠ {report.message}[/yellow]")
        elif report.severity == "error":
            console.print(f"[red]✗ Regression detected:[/red]")
            console.print(f"  {report.message}")
            sys.exit(1)

    except Exception as e:
        console.print(f"[red]✗ Error:[/red] {str(e)}")
        sys.exit(1)

# ============================================================================
# INFO COMMAND
# ============================================================================

@cli.command()
@click.argument('file', type=click.Path(exists=True, path_type=Path))
@click.pass_context
def info(ctx, file):
    """
    Show information about IR or contract file.

    Example:
        pfcv-synth info contract.json
    """
    try:
        content = file.read_text(encoding='utf-8')
        data = json.loads(content)
        
        # Determine file type
        if 'header' in data and 'clauses' in data: # Generic JSON structure likely
             # However, it might be wrapped in envelope. 
             # Check serialization format.
             if 'contract' in data and 'schema_version' in data:
                 data = data['contract']
             _print_contract_info(data)

        elif 'unit_id' in data:
            _print_ir_info(data)
        elif 'contract' in data: # Envelope
            _print_contract_info(data['contract'])
        else:
            console.print("[yellow]Unknown file format[/yellow]")

    except Exception as e:
        console.print(f"[red]✗ Error:[/red] {str(e)}")
        sys.exit(1)

# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def _synthesize_single(ir_file: Path, output_dir: Path):
    """Synthesize single IR file."""
    # Defer imports
    from module_05_ir_normalization.ir_serialization import IRSerializer
    from module_07_contract_synthesis.synthesis_engine import SynthesisEngine, SynthesisConfig

    ir_serializer = IRSerializer()
    ir_unit = ir_serializer.deserialize(ir_file.read_text(encoding='utf-8'))

    config = SynthesisConfig()
    engine = SynthesisEngine(config)
    result = engine.synthesize(ir_unit, ir_file.stem)

    if result.success:
        output_file = output_dir / f"{ir_file.stem}_contract.json"
        _write_contract(result.contract, output_file, 'json')
        return result
    else:
        raise Exception(", ".join(result.errors))

def _write_contract(contract, output_file: Path, format: str):
    """Write contract to file."""
    from module_06_contract_schema.contract_serialization import ContractSerializer
    serializer = ContractSerializer()

    if format == 'json':
        content = serializer.serialize(contract)
        output_file.write_text(content, encoding='utf-8')
    elif format == 'yaml':
        try:
            import yaml
            data = json.loads(serializer.serialize(contract))
            output_file.write_text(yaml.dump(data), encoding='utf-8')
        except ImportError:
            console.print("[yellow]PyYAML not installed, falling back to JSON[/yellow]")
            content = serializer.serialize(contract)
            output_file.write_text(content, encoding='utf-8')
    elif format == 'text':
        content = _format_contract_text(contract)
        output_file.write_text(content, encoding='utf-8')

def _print_contract(result, format: str):
    """Print contract to stdout."""
    if format == 'json':
        from module_06_contract_schema.contract_serialization import ContractSerializer
        serializer = ContractSerializer()
        console.print(serializer.serialize(result.contract))
    elif format == 'text':
        _print_synthesis_report(result)
    elif format == 'yaml':
        from module_06_contract_schema.contract_serialization import ContractSerializer
        # Simple YAML console output
        serializer = ContractSerializer()
        try:
             import yaml
             data = json.loads(serializer.serialize(result.contract))
             console.print(yaml.dump(data))
        except ImportError:
             console.print(serializer.serialize(result.contract))

def _print_synthesis_report(result):
    """Print human-readable synthesis report."""
    console.print("\n[bold]Synthesis Report[/bold]")
    console.print("═" * 60)

    # Summary
    table = Table(show_header=False, box=None)
    table.add_column("Metric", style="cyan")
    table.add_column("Value", style="green")

    table.add_row("Total clauses", str(result.clauses_generated))
    table.add_row("Layout clauses", str(result.layout_clauses))
    table.add_row("Nullability clauses", str(result.nullability_clauses))
    table.add_row("Ownership clauses", str(result.ownership_clauses))

    console.print(table)

    # Contextual analysis logic from Prompt 3
    # Check if metadata stores analysis results
    if result.metadata and "contextual_analysis" in result.metadata:
        analysis = result.metadata["contextual_analysis"]
        console.print(f"\n[bold]Contextual Analysis[/bold]")
        console.print(f"  Coherence score: {analysis.get('coherence_score', 0):.2f}")

def _print_batch_report(results):
    """Print batch processing report."""
    success_count = sum(1 for _, result, error in results if error is None)
    fail_count = len(results) - success_count

    console.print(f"\n[bold]Batch Report[/bold]")
    console.print("═" * 60)
    console.print(f"Total: {len(results)}")
    console.print(f"[green]Success: {success_count}[/green]")
    console.print(f"[red]Failed: {fail_count}[/red]")

    if fail_count > 0:
        console.print(f"\n[bold]Failed Files:[/bold]")
        for ir_file, _, error in results:
            if error:
                console.print(f"  [red]✗[/red] {ir_file.name}: {error}")

def _print_contract_info(data):
    """Print contract file info."""
    console.print("[bold]Contract Information[/bold]")
    header = data.get('header', {})
    console.print(f" Interface: {header.get('target_interface_id', 'Unknown')}")
    console.print(f" Clauses: {len(data.get('clauses', []))}")
    if 'generation_metadata' in header:
        console.print(f" Version: {header['generation_metadata'].get('tool_version', 'Unknown')}")

def _print_ir_info(data):
    """Print IR file info."""
    console.print("[bold]IR Information[/bold]")
    console.print(f" Unit ID: {data.get('unit_id', 'Unknown')}")
    console.print(f" Functions: {len(data.get('functions', []))}")
    console.print(f" Types: {len(data.get('types', []))}")

def _format_contract_text(contract) -> str:
    """Format contract as text."""
    lines = []
    lines.append("Contract Summary")
    lines.append("=" * 60)
    lines.append(f"Interface: {contract.header.target_interface_id}")
    lines.append(f"Clauses: {len(contract.clauses)}")
    return "\n".join(lines)

# ============================================================================
# MAIN ENTRY POINT
# ============================================================================

def main():
    """Main CLI entry point."""
    cli(obj={})

if __name__ == '__main__':
    main()