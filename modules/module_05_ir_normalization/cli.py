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
# File Integrity Identifier: 6e7df786d6d45788
# ==============================================================================

def normalize_command(args):
    """Execute normalize command."""
    formatter = OutputFormatter()

    # Build configuration
    config = IRNormalizationConfig(
        input_artifact_path=Path(args.input),
        output_dir=Path(args.output),
        compress_artifacts=args.compress,
        enable_validation=args.validate,
        fail_on_validation_errors=args.fail_on_validation_errors,
        enable_caching=args.cache,
        cache_dir=Path(args.cache_dir),
        enable_diffing=args.diff_baseline is not None,
        baseline_artifact_path=Path(args.diff_baseline) if args.diff_baseline else None,
        generate_report=args.report is not None,
        report_output_path=Path(args.report) if args.report else None,
        enable_profiling=args.profile,
    )

    # Validate configuration
    errors = config.validate_config()
    if errors:
        for error in errors:
            formatter.print_error(error)
        sys.exit(3)

    # Execute orchestrator
    orchestrator = IROrchestrator(config)

    try:
        report = orchestrator.execute()

        # Print summary
        if not args.quiet:
            print_normalization_summary(report, formatter)

        # Exit with appropriate code
        if not report.validation_passed:
            sys.exit(1)

        sys.exit(0)

    except ConfigError as e:
        formatter.print_error(f"Config error: {e.message}")
        sys.exit(3)

    except OrchestrationError as e:
        formatter.print_error(f"[{e.stage}] {e.message}")
        sys.exit(2)

    except Exception as e:
        formatter.print_error(f"Unexpected error: {e}")
        if args.verbose:
            import traceback

            traceback.print_exc()
        sys.exit(2)


def print_normalization_summary(report: OrchestrationReport, formatter: OutputFormatter):
    """Print normalization summary."""
    formatter.print_header("Normalization Summary")

    print(f"  Types normalized:   {report.types_normalized}")
    print(f"  Symbols normalized: {report.symbols_normalized}")
    print(f"  Duration:           {report.total_duration:.2f}s")

    if report.validation_passed:
        formatter.print_success("Validation PASSED")
    else:
        formatter.print_warning(f"Validation FAILED ({len(report.validation_errors)} errors)")

    if report.output_artifact_path:
        print(f"\nOutput: {report.output_artifact_path}")


# ============================================================================
# VALIDATE COMMAND
# ============================================================================


def validate_command(args):
    """Execute validate command."""
    formatter = OutputFormatter()

    artifact_path = Path(args.artifact)

    if not artifact_path.exists():
        formatter.print_error(f"Artifact not found: {artifact_path}")
        sys.exit(4)

    if not args.quiet:
        formatter.print_header("IR Artifact Validation")
        print(f"Artifact: {artifact_path}")

    try:
        if not args.quiet:
            print("\nLoading artifact...")
        artifact = load_artifact_any(artifact_path)

        if not artifact.interface_unit:
            formatter.print_error("Artifact missing interface unit")
            sys.exit(1)

        reg = TypeRegistry()
        for t in artifact.interface_unit.types:
            reg.register_type(t)

        validator = IRValidationOrchestrator(artifact.interface_unit, reg)
        report = validator.validate_complete_ir()

        if args.report:
            with open(args.report, "w") as f:
                json.dump(report.to_dict(), f, indent=2)

        if report.passed:
            if not args.quiet:
                formatter.print_success("All validation checks passed")
            sys.exit(0)
        else:
            if not args.quiet:
                formatter.print_error(f"Validation failed with {report.total_errors()} errors")
                for err in report.all_errors():
                    print(f"  - {err}")
            sys.exit(1)

    except Exception as e:
        formatter.print_error(f"Validation process failed: {e}")
        if args.verbose:
            import traceback

            traceback.print_exc()
        sys.exit(2)


# ============================================================================
# DIFF COMMAND
# ============================================================================


def diff_command(args):
    """Execute diff command."""
    formatter = OutputFormatter()

    old_path = Path(args.old)
    new_path = Path(args.new)

    if not old_path.exists():
        formatter.print_error(f"Old artifact not found: {old_path}")
        sys.exit(4)

    if not new_path.exists():
        formatter.print_error(f"New artifact not found: {new_path}")
        sys.exit(4)

    if not args.quiet and args.format == "text":
        formatter.print_header("IR Diff")
        print(f"Old: {old_path}")
        print(f"New: {new_path}")

    try:
        old_art = load_artifact_any(old_path)
        new_art = load_artifact_any(new_path)

        computer = IRDiffComputer()
        diff = computer.compute_diff(old_art, new_art)

        if args.format == "json":
            res = {
                "overall_impact": diff.overall_impact.value,
                "statistics": {
                    "added": len(diff.entities_added),
                    "removed": len(diff.entities_removed),
                    "modified": len(diff.type_changes) + len(diff.symbol_changes),
                },
                "breaking_changes": [],  # Simplified for now
                "compatible_changes": [],
            }
            if args.recommend:
                res["recommended_bump"] = recommend_version_bump(diff).value
            print(json.dumps(res, indent=2))
        elif args.format == "markdown":
            print(f"# IR Diff: {old_path.name} → {new_path.name}")
            print(f"\n**Overall Impact:** {diff.overall_impact.value.upper()}")
            if args.recommend:
                print(f"**Recommended Version Bump:** {recommend_version_bump(diff).value.upper()}")
        else:  # Text
            print(f"\nOverall Impact: {diff.overall_impact.value.upper()}")
            print("\nStatistics:")
            print(f"  Added:    {len(diff.entities_added)} entities")
            print(f"  Removed:  {len(diff.entities_removed)} entities")
            print(f"  Modified: {len(diff.type_changes) + len(diff.symbol_changes)} entities")

            if args.recommend:
                print(f"\nRecommended Version Bump: {recommend_version_bump(diff).value.upper()}")

        sys.exit(0)

    except Exception as e:
        formatter.print_error(f"Diff failed: {e}")
        if args.verbose:
            import traceback

            traceback.print_exc()
        sys.exit(2)


# ============================================================================
# INSPECT COMMAND
# ============================================================================


def inspect_command(args):
    """Execute inspect command."""
    formatter = OutputFormatter()

    artifact_path = Path(args.artifact)

    if not artifact_path.exists():
        formatter.print_error(f"Artifact not found: {artifact_path}")
        sys.exit(4)

    try:
        artifact = load_artifact_any(artifact_path)
        unit = artifact.interface_unit

        if args.format == "json":
            print(json.dumps(artifact.to_dict(), indent=2))
            sys.exit(0)

        formatter.print_header("IR Artifact Inspection")
        print(f"Artifact: {artifact_path}")
        print(f"\nSchema Version:        {artifact.schema_version}")
        print(f"Normalization Version: {artifact.normalization_version}")
        print(f"Created:               {artifact.creation_timestamp or 'unknown'}")

        if unit:
            print("\nPlatform:")
            print(f"  Architecture:  {unit.target_architecture}")
            print(f"  OS:           {unit.operating_system}")
            print(f"  Pointer Width: {unit.pointer_width}-bit")
            print(f"  Endianness:    {unit.endianness.value}")
            print(f"  ABI Mode:      {unit.abi_mode}")

            print("\nStatistics:")
            print(f"  Types:    {len(unit.types)}")
            print(f"  Symbols:  {len(unit.symbols)}")

            if args.list_types:
                print("\nTypes:")
                for t in unit.types:
                    print(f"  - {t.entity_id[:8]}... : {type(t).__name__}")

            if args.list_functions:
                print("\nFunctions:")
                for s in unit.symbols:
                    from .ir_entities import FunctionSymbol

                    if isinstance(s, FunctionSymbol):
                        print(f"  - {s.linkage_name}")

        sys.exit(0)

    except Exception as e:
        formatter.print_error(f"Inspection failed: {e}")
        if args.verbose:
            sys.exit(2)
        sys.exit(2)


# ============================================================================
# CACHE COMMAND
# ============================================================================


def cache_command(args):
    """Execute cache subcommands."""
    formatter = OutputFormatter()
    cache_dir = Path(args.cache_dir or ".pfcv/cache/module_05")

    if args.subcommand == "stats":
        formatter.print_header("Cache Statistics")
        print(f"Cache Directory: {cache_dir}")

        if not cache_dir.exists():
            print("\nCache directory does not exist.")
            sys.exit(0)

        index_path = cache_dir / "index.json"
        item_count = 0
        if index_path.exists():
            try:
                with open(index_path) as f:
                    index = json.load(f)
                    item_count = len(index)
            except BaseException:
                pass

        artifacts_dir = cache_dir / "artifacts"
        total_size = 0
        if artifacts_dir.exists():
            for f in artifacts_dir.glob("**/*"):
                if f.is_file():
                    total_size += f.stat().st_size

        print(f"\nArtifacts: {item_count}")
        print(f"Total Disk Usage: {total_size / (1024 * 1024):.2f} MB")

    elif args.subcommand == "list":
        formatter.print_header("Cached Artifacts")
        index_path = cache_dir / "index.json"
        if index_path.exists():
            try:
                with open(index_path) as f:
                    index = json.load(f)
                    for k, v in index.items():
                        print(f"  {k} -> {v.get('artifact_path')}")
            except BaseException:
                print("Error reading index")
        else:
            print("No cached artifacts")

    elif args.subcommand == "clear":
        if cache_dir.exists():
            import shutil

            shutil.rmtree(cache_dir)
            formatter.print_success("Cache cleared")
        else:
            formatter.print_info("Cache already empty")

    sys.exit(0)


# ============================================================================
# CONFIG COMMAND
# ============================================================================


def config_command(args):
    """Execute config command."""
    config_template = {
        "input_artifact": "path/to/module_04_output.json",
        "output_dir": ".pfcv/ir_artifacts",
        "compress_artifacts": True,
        "enable_validation": True,
        "fail_on_validation_errors": True,
        "enable_caching": True,
        "cache_dir": ".pfcv/cache/module_05",
        "enable_diffing": False,
        "baseline_artifact": None,
        "generate_report": True,
        "report_output": ".pfcv/reports/ir_normalization_report.json",
        "enable_profiling": False,
    }

    if args.format == "json":
        output = json.dumps(config_template, indent=2)
    else:  # yaml (fake yaml output for template)
        output = "# PFCV IR Normalization Config\n\n"
        for key, value in config_template.items():
            if value is None:
                output += f"{key}: null\n"
            elif isinstance(value, bool):
                output += f"{key}: {str(value).lower()}\n"
            elif isinstance(value, str):
                output += f'{key}: "{value}"\n'
            else:
                output += f"{key}: {value}\n"

    if args.output:
        out_path = Path(args.output)
        out_path.parent.mkdir(parents=True, exist_ok=True)
        with open(out_path, "w") as f:
            f.write(output)
        print(f"Config written to {args.output}")
    else:
        print(output)

    sys.exit(0)


# ============================================================================
# ARGUMENT PARSING
# ============================================================================


def create_parser() -> argparse.ArgumentParser:
    """Create argument parser."""
    parser = argparse.ArgumentParser(
        prog="pfcv-ir",
        description="PFCV IR Normalization Tool",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
    pfcv-ir normalize raw_interface.json
pfcv-ir diff v1_ir.json v2_ir.json
pfcv-ir inspect ir_artifact.json --list-functions

For more information: https://pfcv.readthedocs.io/module_05/
        """,
    )

    parser.add_argument("--version", action="version", version=f"%(prog)s {__version__}")
    parser.add_argument("--verbose", action="store_true", help="Enable verbose output")
    parser.add_argument("--quiet", action="store_true", help="Suppress output except errors")
    parser.add_argument("--config", help="Load configuration from file")

    subparsers = parser.add_subparsers(dest="command", help="Commands")

    # Normalize command
    normalize_parser = subparsers.add_parser("normalize", help="Normalize raw interface artifact")
    normalize_parser.add_argument("input", help="Input artifact path")
    normalize_parser.add_argument(
        "-o", "--output", default=".pfcv/ir_artifacts", help="Output directory"
    )
    normalize_parser.add_argument(
        "--compress", action="store_true", default=True, help="Compress artifacts"
    )
    normalize_parser.add_argument("--no-compress", dest="compress", action="store_false")
    normalize_parser.add_argument(
        "--validate", action="store_true", default=True, help="Run validation"
    )
    normalize_parser.add_argument("--no-validate", dest="validate", action="store_false")
    normalize_parser.add_argument("--fail-on-validation-errors", action="store_true", default=True)
    normalize_parser.add_argument(
        "--cache", action="store_true", default=True, help="Enable caching"
    )
    normalize_parser.add_argument("--no-cache", dest="cache", action="store_false")
    normalize_parser.add_argument(
        "--cache-dir", default=".pfcv/cache/module_05", help="Cache directory"
    )
    normalize_parser.add_argument("--diff-baseline", help="Baseline artifact for diffing")
    normalize_parser.add_argument("--report", help="Output report file")
    normalize_parser.add_argument("--profile", action="store_true", help="Enable profiling")

    # Validate command
    validate_parser = subparsers.add_parser("validate", help="Validate IR artifact")
    validate_parser.add_argument("artifact", help="IR artifact to validate")
    validate_parser.add_argument("--report", help="Output validation report")

    # Diff command
    diff_parser = subparsers.add_parser("diff", help="Compare two IR artifacts")
    diff_parser.add_argument("old", help="Old artifact")
    diff_parser.add_argument("new", help="New artifact")
    diff_parser.add_argument("--format", choices=["text", "json", "markdown"], default="text")
    diff_parser.add_argument("--output", help="Output file")
    diff_parser.add_argument("--filter", choices=["breaking", "compatible", "all"], default="all")
    diff_parser.add_argument(
        "--recommend", action="store_true", help="Show version bump recommendation"
    )

    # Inspect command
    inspect_parser = subparsers.add_parser("inspect", help="Inspect IR artifact")
    inspect_parser.add_argument("artifact", help="IR artifact to inspect")
    inspect_parser.add_argument("--list-types", action="store_true", help="List all types")
    inspect_parser.add_argument("--list-functions", action="store_true", help="List all functions")
    inspect_parser.add_argument("--format", choices=["text", "json"], default="text")

    # Cache command
    cache_parser = subparsers.add_parser("cache", help="Manage artifact cache")
    cache_parser.add_argument("--cache-dir", help="Override default cache directory")
    cache_subparsers = cache_parser.add_subparsers(dest="subcommand")
    cache_subparsers.add_parser("stats", help="Show cache statistics")
    cache_subparsers.add_parser("list", help="List cached artifacts")
    cache_subparsers.add_parser("clear", help="Clear cache")

    # Config command
    config_parser = subparsers.add_parser("config", help="Generate configuration template")
    config_parser.add_argument("--output", help="Output file")
    config_parser.add_argument("--format", choices=["yaml", "json"], default="yaml")

    return parser


# ============================================================================
# ============================================================================


def main():
    parser = create_parser()
    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        sys.exit(0)

    # Dispatch to command handler
    if args.command == "normalize":
        normalize_command(args)
    elif args.command == "validate":
        validate_command(args)
    elif args.command == "diff":
        diff_command(args)
    elif args.command == "inspect":
        inspect_command(args)
    elif args.command == "cache":
        cache_command(args)
    elif args.command == "config":
        config_command(args)
    else:
        parser.print_help()
        sys.exit(127)


if __name__ == "__main__":
    main()

__all__ = ["main", "create_parser", "OutputFormatter"]