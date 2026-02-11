"""
Module 06: Contract Schema - CLI Interface

Command-line interface for contract operations:
- generate: Create contracts from IR
- validate: Validate contract correctness
- diff: Compare contract versions
- inspect: Examine contract contents
- list: List available contracts
- cache: Manage artifact cache
"""

import sys
import json
from pathlib import Path
from typing import Optional, List
import click

from .contract_generation import ContractGenerator, GenerationConfig
from .contract_validation import ContractValidator, ValidationContext
from .contract_serialization import ContractFileManager, ContractArtifactManager
from .contract_diff_advanced import AdvancedContractDiffer
from .contract_entities import ContractDocument


class CLIContext:
    """Context object for CLI commands."""

    def __init__(self):
        self.verbose = False
        self.quiet = False
        self.format = "text"
        self.config_file: Optional[Path] = None
        self.cache_dir = Path.home() / ".pfcv" / "contracts"


pass_context = click.make_pass_decorator(CLIContext, ensure=True)


@click.group()
@click.option("--verbose", "-v", is_flag=True, help="Enable verbose output")
@click.option("--quiet", "-q", is_flag=True, help="Suppress output except errors")
@click.option(
    "--format",
    type=click.Choice(["text", "json", "markdown"]),
    default="text",
    help="Output format",
)
@click.option("--config", type=click.Path(exists=True), help="Configuration file")
@click.version_option(version="1.0.0", prog_name="pfcv-contract")
@pass_context
def cli(ctx: CLIContext, verbose: bool, quiet: bool, format: str, config: Optional[str]):
    """PFCV Contract CLI - Manage FFI contracts."""
    ctx.verbose = verbose
    ctx.quiet = quiet
    ctx.format = format
    if config:
        ctx.config_file = Path(config)


@cli.command()
@click.argument("ir-artifact", type=click.Path(exists=True))
@click.option("-o", "--output", type=click.Path(), help="Output file path")
@click.option(
    "--confidence", type=float, default=0.5, help="Minimum confidence threshold (0.0-1.0)"
)
@click.option("--summary", is_flag=True, help="Show generation summary")
@click.option("--pretty/--compact", default=True, help="Pretty-print JSON")
@pass_context
def generate(
    ctx: CLIContext,
    ir_artifact: str,
    output: Optional[str],
    confidence: float,
    summary: bool,
    pretty: bool,
):
    """Generate contract from IR artifact."""
    try:
        if not ctx.quiet and ctx.format == "text":
            click.echo("Generating contract from IR artifact...")

        config = GenerationConfig(confidence_threshold=confidence)
        generator = ContractGenerator(config)

        # In a real implementation, we would load the IR artifact here.
        # For now, we use a placeholder as the IR integration is in Module 05.
        contract = generator.generate(
            ir_artifact=None, target_interface_id=f"ir_from_{Path(ir_artifact).stem}"
        )

        if output:
            file_manager = ContractFileManager()
            file_manager.save(contract, Path(output))
            if not ctx.quiet:
                click.echo(f"✓ Contract written to {output}")
        else:
            if ctx.format == "json":
                click.echo(contract.to_json())
            else:
                click.echo(f"Contract version: {contract.header.contract_version}")
                click.echo(f"Clauses: {len(contract.clauses)}")

        if summary and not ctx.quiet and ctx.format == "text":
            click.echo("\nGeneration Summary:")
            click.echo(f"  Total clauses: {len(contract.clauses)}")

        sys.exit(0)
    except Exception as e:
        click.echo(f"Error: {e}", err=True)
        sys.exit(2)


@cli.command()
@click.argument("contract-file", type=click.Path(exists=True))
@click.option("--ir", type=click.Path(exists=True), help="IR artifact for validation")
@click.option("--strict", is_flag=True, help="Treat warnings as errors")
@click.option("--report", type=click.Path(), help="Write report to file")
@pass_context
def validate(
    ctx: CLIContext, contract_file: str, ir: Optional[str], strict: bool, report: Optional[str]
):
    """Validate contract correctness."""
    try:
        if not ctx.quiet and ctx.format == "text":
            click.echo("Validating contract...")

        file_manager = ContractFileManager()
        contract = file_manager.load(Path(contract_file))

        validation_ctx = ValidationContext(strict_mode=strict)
        validator = ContractValidator(validation_ctx)

        # Basic validation for now (referential requires IR)
        result = validator.validate(contract, skip_referential=True, skip_constraint=True)

        if result.passed:
            if not ctx.quiet:
                click.echo("✓ Schema validation passed")
                click.echo("\nContract is valid.")
            sys.exit(0)
        else:
            if not ctx.quiet:
                click.echo(result.generate_report())
                click.echo("\nContract validation FAILED")
            sys.exit(1)
    except Exception as e:
        click.echo(f"Error: {e}", err=True)
        sys.exit(2)


@cli.command()
@click.argument("old-contract", type=click.Path(exists=True))
@click.argument("new-contract", type=click.Path(exists=True))
@click.option(
    "--filter",
    "impact_filter",
    type=click.Choice(["breaking", "compatible", "neutral"]),
    help="Filter changes by impact",
)
@click.option("--migration", is_flag=True, help="Include migration guide")
@pass_context
def diff(
    ctx: CLIContext,
    old_contract: str,
    new_contract: str,
    impact_filter: Optional[str],
    migration: bool,
):
    """Compare contract versions."""
    try:
        file_manager = ContractFileManager()
        old = file_manager.load(Path(old_contract))
        new = file_manager.load(Path(new_contract))

        differ = AdvancedContractDiffer()
        result = differ.compute_diff(old, new)

        if ctx.format == "json":
            impact_val = (
                result.overall_impact.value
                if hasattr(result.overall_impact, "value")
                else result.overall_impact
            )
            output = {
                "old_version": str(result.old_version),
                "new_version": str(result.new_version),
                "breaking_changes": len(result.get_breaking_changes()),
                "overall_impact": impact_val,
            }
            click.echo(json.dumps(output, indent=2))
        else:
            click.echo(result.format_summary())
            if migration and result.migration_guide:
                click.echo("\n" + result.migration_guide.format_guide())

        sys.exit(0 if not result.has_breaking_changes() else 1)
    except Exception as e:
        click.echo(f"Error: {e}", err=True)
        sys.exit(2)


@cli.command()
@click.argument("contract-file", type=click.Path(exists=True))
@click.option("--stats", is_flag=True, help="Show contract statistics")
@click.option("--list-clauses", is_flag=True, help="List all clauses")
@click.option("--show-header", is_flag=True, help="Show header only")
@pass_context
def inspect(
    ctx: CLIContext, contract_file: str, stats: bool, list_clauses: bool, show_header: bool
):
    """Examine contract contents."""
    try:
        file_manager = ContractFileManager()
        contract = file_manager.load(Path(contract_file))

        if show_header:
            click.echo("Contract Header")
            click.echo("=" * 60)
            click.echo(f"Contract Version: {contract.header.contract_version}")
            click.echo(f"Schema Version: {contract.header.schema_version}")
            click.echo(f"Target Interface: {contract.header.target_interface_id}")
        elif stats:
            click.echo("Contract Statistics")
            click.echo("=" * 60)
            click.echo(f"\nContract Version: {contract.header.contract_version}")
            click.echo(f"Total Clauses: {len(contract.clauses)}")

            from collections import Counter

            type_counts = Counter()
            for c in contract.clauses:
                ctype = c.clause_type.value if hasattr(c.clause_type, "value") else c.clause_type
                type_counts[ctype] += 1

            click.echo("\nClauses by Type:")
            for clause_type, count in type_counts.most_common():
                click.echo(f"  {clause_type}: {count}")
        elif list_clauses:
            click.echo("Contract Clauses")
            click.echo("=" * 60)
            for clause in contract.clauses:
                ctype = (
                    clause.clause_type.value
                    if hasattr(clause.clause_type, "value")
                    else clause.clause_type
                )
                click.echo(f"  {clause.clause_id} ({ctype})")
        else:
            click.echo(f"Contract: {contract.header.contract_version}")
            click.echo(f"Clauses: {len(contract.clauses)}")
        sys.exit(0)
    except Exception as e:
        click.echo(f"Error: {e}", err=True)
        sys.exit(2)


@cli.command(name="list")
@click.option("--cache-dir", type=click.Path(), help="Cache directory")
@pass_context
def list_contracts(ctx: CLIContext, cache_dir: Optional[str]):
    """List available contracts."""
    try:
        cache_path = Path(cache_dir) if cache_dir else ctx.cache_dir
        if not cache_path.exists():
            click.echo(f"Cache directory not found: {cache_path}")
            sys.exit(0)

        click.echo("Available Contracts")
        click.echo("=" * 60)

        # Simple scan of the directory
        found = False
        for file in cache_path.glob("*.json"):
            click.echo(f"  {file.name}")
            found = True

        if not found:
            click.echo("\nNo contracts found in cache.")
        sys.exit(0)
    except Exception as e:
        click.echo(f"Error: {e}", err=True)
        sys.exit(2)


@cli.group()
def cache():
    """Manage contract cache."""
    pass


@cache.command()
@pass_context
def stats(ctx: CLIContext):
    """Show cache statistics."""
    try:
        cache_path = ctx.cache_dir
        click.echo("Cache Statistics")
        click.echo("=" * 60)
        click.echo(f"\nCache Directory: {cache_path}")
        if cache_path.exists():
            total_size = sum(f.stat().st_size for f in cache_path.rglob("*") if f.is_file())
            click.echo(f"Total Size: {total_size / 1024:.1f} KB")
        else:
            click.echo("Cache directory does not exist.")
        sys.exit(0)
    except Exception as e:
        click.echo(f"Error: {e}", err=True)
        sys.exit(2)


@cache.command()
@click.option("--confirm", is_flag=True, help="Confirm cache clear")
@pass_context
def clear(ctx: CLIContext, confirm: bool):
    """Clear contract cache."""
    if not confirm:
        click.echo("Use --confirm to clear cache")
        sys.exit(0)
    try:
        cache_path = ctx.cache_dir
        if cache_path.exists():
            import shutil

            shutil.rmtree(cache_path)
            click.echo("✓ Cache cleared")
        else:
            click.echo("Cache directory does not exist.")
        sys.exit(0)
    except Exception as e:
        click.echo(f"Error: {e}", err=True)
        sys.exit(2)


def main():
    """Main entry point for CLI."""
    try:
        cli(obj=CLIContext())
    except Exception as e:
        click.echo(f"Unexpected error: {e}", err=True)
        sys.exit(10)


if __name__ == "__main__":
    main()

__all__ = ["cli", "main"]
