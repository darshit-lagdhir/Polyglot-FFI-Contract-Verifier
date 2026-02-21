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
# File Integrity Identifier: a63e7865e5dc9da7
# ==============================================================================

@dataclass
class SourceLocation:
    """Source code location."""

    file: Optional[str] = None
    line: Optional[int] = None
    column: Optional[int] = None
    file_path: Optional[str] = None  # Alias for compatibility at the end

    def __post_init__(self):
        if self.file and not self.file_path:
            self.file_path = self.file
        elif self.file_path and not self.file:
            self.file = self.file_path

    def __str__(self):
        if self.file:
            loc = self.file
            if self.line:
                loc += f":{self.line}"
                if self.column:
                    loc += f":{self.column}"
            return loc
        return "unknown location"

    def to_dict(self) -> Dict[str, Any]:
        return {"file": self.file, "line": self.line, "column": self.column}


# ============================================================================
# DIAGNOSTIC MESSAGE
# ============================================================================


@dataclass
class DiagnosticMessage:
    """Structured diagnostic message."""

    code: str
    severity: IRSeverity
    category: ErrorCategory

    title: str
    description: str

    source_location: Optional[SourceLocation] = None
    entity_id: Optional[str] = None
    stage: Optional[str] = None

    causes: List[str] = field(default_factory=list)
    solutions: List[str] = field(default_factory=list)

    technical_details: Dict[str, Any] = field(default_factory=dict)
    stack_trace: Optional[str] = None

    documentation_url: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """Serialize to dictionary."""
        return {
            "code": self.code,
            "severity": self.severity.value,
            "category": self.category.value,
            "title": self.title,
            "description": self.description,
            "source_location": self.source_location.to_dict() if self.source_location else None,
            "entity_id": self.entity_id,
            "stage": self.stage,
            "causes": self.causes,
            "solutions": self.solutions,
            "technical_details": self.technical_details,
            "documentation_url": self.documentation_url,
        }

    def format_for_terminal(self, use_color: bool = True) -> str:
        """Format for terminal display."""
        lines = []

        # Header
        if use_color:
            color = self._get_severity_color()
            reset = "\033[0m"
        else:
            color = ""
            reset = ""

        severity_str = self.severity.value.upper()
        lines.append(f"{color}{severity_str}: [{self.category.value}] {self.title}{reset}")

        # Description
        if self.description:
            lines.append(f"\n{self.description}")

        # Context
        context_items = []
        if self.source_location:
            context_items.append(f"Location: {self.source_location}")
        if self.entity_id:
            context_items.append(f"Entity: {self.entity_id}")
        if self.stage:
            context_items.append(f"Stage: {self.stage}")

        if context_items:
            lines.append("\nContext:")
            for item in context_items:
                lines.append(f"  {item}")

        # Causes
        if self.causes:
            lines.append("\nPossible Causes:")
            for cause in self.causes:
                lines.append(f"  • {cause}")

        # Solutions
        if self.solutions:
            lines.append("\nSuggested Solutions:")
            for i, solution in enumerate(self.solutions, 1):
                lines.append(f"  {i}. {solution}")

        # Technical Details
        if self.technical_details:
            lines.append("\nTechnical Details:")
            for key, value in self.technical_details.items():
                lines.append(f"  {key}: {value}")

        # Documentation
        if self.documentation_url:
            lines.append(f"\nDocumentation: {self.documentation_url}")

        return "\n".join(lines)

    def _get_severity_color(self) -> str:
        """Get ANSI color code for severity."""
        sev = self.severity
        if hasattr(sev, "value"):
            sev = sev.value

        colors = {
            "fatal": "\033[91m",
            "error": "\033[91m",
            "warning": "\033[93m",
            "info": "\033[94m",
            "debug": "\033[90m",
            "advisory": "\033[96m",
        }
        return colors.get(sev, "")


# ============================================================================
# DIAGNOSTIC COLLECTOR
# ============================================================================


class DiagnosticCollector:
    """Collects and manages diagnostic messages."""

    def __init__(self, max_errors: int = 100, max_warnings: int = 200):
        self.diagnostics: List[DiagnosticMessage] = []
        self.max_errors = max_errors
        self.max_warnings = max_warnings

        self._error_count = 0
        self._warning_count = 0
        self._truncated_errors = False
        self._truncated_warnings = False

    def add(self, diagnostic: DiagnosticMessage):
        """Add diagnostic message."""
        if diagnostic.severity == IRSeverity.ERROR:
            self._error_count += 1
            if self._error_count > self.max_errors:
                if not self._truncated_errors:
                    self.diagnostics.append(
                        self._make_truncation_message(IRSeverity.ERROR, self.max_errors)
                    )
                    self._truncated_errors = True
                return

        elif diagnostic.severity == IRSeverity.WARNING:
            self._warning_count += 1
            if self._warning_count > self.max_warnings:
                if not self._truncated_warnings:
                    self.diagnostics.append(
                        self._make_truncation_message(IRSeverity.WARNING, self.max_warnings)
                    )
                    self._truncated_warnings = True
                return

        self.diagnostics.append(diagnostic)

    def add_error(self, code: str, title: str, description: str, **kwargs):
        """Add error diagnostic."""
        params = {
            "code": code,
            "severity": IRSeverity.ERROR,
            "category": kwargs.pop("category", ErrorCategory.USER_ERROR),
            "title": title,
            "description": description,
        }
        params.update(kwargs)
        diagnostic = DiagnosticMessage(**params)
        self.add(diagnostic)

    def add_warning(self, code: str, title: str, description: str, **kwargs):
        """Add warning diagnostic."""
        params = {
            "code": code,
            "severity": IRSeverity.WARNING,
            "category": kwargs.pop("category", ErrorCategory.DATA_QUALITY),
            "title": title,
            "description": description,
        }
        params.update(kwargs)
        diagnostic = DiagnosticMessage(**params)
        self.add(diagnostic)

    def add_info(self, code: str, title: str, description: str, **kwargs):
        """Add info diagnostic."""
        params = {
            "code": code,
            "severity": IRSeverity.INFO,
            "category": kwargs.pop("category", ErrorCategory.USER_ERROR),
            "title": title,
            "description": description,
        }
        params.update(kwargs)
        diagnostic = DiagnosticMessage(**params)
        self.add(diagnostic)

    def has_errors(self) -> bool:
        """Check if any errors collected."""
        return self._error_count > 0

    def has_warnings(self) -> bool:
        """Check if any warnings collected."""
        return self._warning_count > 0

    def get_errors(self) -> List[DiagnosticMessage]:
        """Get all error messages."""
        return [d for d in self.diagnostics if d.severity == IRSeverity.ERROR]

    def get_warnings(self) -> List[DiagnosticMessage]:
        """Get all warning messages."""
        return [d for d in self.diagnostics if d.severity == IRSeverity.WARNING]

    def generate_report(self, use_color: bool = True) -> str:
        """Generate human-readable report."""
        lines = ["Diagnostic Report", "=" * 80]

        lines.append("\n")
        lines.append(f"  Errors:   {self._error_count}")
        lines.append(f"  Warnings: {self._warning_count}")
        lines.append(f"  Total:    {len(self.diagnostics)}")

        errors = self.get_errors()
        if errors:
            lines.append(f"\nErrors ({len(errors)}):")
            for diagnostic in errors:
                lines.append(f"\n{diagnostic.format_for_terminal(use_color)}")
                lines.append("-" * 80)

        warnings = self.get_warnings()
        if warnings:
            lines.append(f"\nWarnings ({len(warnings)}):")
            for diagnostic in warnings:
                lines.append(f"\n{diagnostic.format_for_terminal(use_color)}")
                lines.append("-" * 80)

        return "\n".join(lines)

    def save_json_report(self, output_path: Path):
        """Save diagnostics as JSON."""
        report = {
            "summary": {
                "total_errors": self._error_count,
                "total_warnings": self._warning_count,
                "total_messages": len(self.diagnostics),
                "truncated_errors": self._truncated_errors,
                "truncated_warnings": self._truncated_warnings,
            },
            "diagnostics": [d.to_dict() for d in self.diagnostics],
        }

        output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, "w") as f:
            json.dump(report, f, indent=2)

    def _make_truncation_message(self, severity: IRSeverity, limit: int) -> DiagnosticMessage:
        """Create message indicating truncation."""
        return DiagnosticMessage(
            code="W9999",
            severity=IRSeverity.WARNING,
            category=ErrorCategory.SYSTEM_ERROR,
            title=f"{severity.value.capitalize()} limit reached",
            description=f"More than {limit} {severity.value}s detected. "
            f"Additional {severity.value}s have been suppressed.",
            solutions=[
                f"Fix reported {severity.value}s and re-run",
                f"Increase limit with --max-{severity.value}s={limit * 2}",
            ],
        )


# ============================================================================
# ERROR CONTEXT MANAGER
# ============================================================================


@contextmanager
def error_context(collector: DiagnosticCollector, stage: str, entity_id: Optional[str] = None):
    """
    Context manager for error enrichment.

    Usage:
        with error_context(collector, "type_normalization", "struct_123"):
            normalize_type(...)
    """
    try:
        yield
    except Exception as e:
        # Capture exception with context
        error_code = "E9999"
        category = ErrorCategory.BUG

        # Try to categorize exception
        name = type(e).__name__.lower()
        if "conversion" in name:
            error_code = "E1001"
            category = ErrorCategory.CONVERSION
        elif "validation" in name:
            error_code = "E2001"
            category = ErrorCategory.VALIDATION

        collector.add_error(
            code=error_code,
            title=f"Error in {stage}",
            description=str(e),
            category=category,
            stage=stage,
            entity_id=entity_id,
            stack_trace=traceback.format_exc(),
            technical_details={"exception_type": type(e).__name__},
        )
        raise


# ============================================================================
# USER GUIDANCE
# ============================================================================


class UserGuidance:
    """Provides contextual user guidance."""

    ERROR_GUIDANCE = {
        "E1001": {
            "title": "Conversion Error",
            "suggestions": [
                "Verify input is valid Module 04 artifact",
                "Check artifact version compatibility",
                "Re-run Module 04 ingestion if needed",
            ],
        },
        "E2001": {
            "title": "Validation Error",
            "suggestions": [
                "Inspect problematic entity with pfcv-ir inspect",
                "Review validation report for specific issues",
                "Compare with compiler output",
            ],
        },
        "E2101": {
            "title": "Structure Size Mismatch",
            "suggestions": [
                "Verify Module 04 ingestion captured all fields",
                "Check for compiler-specific packing attributes",
                "Compare with 'clang -cc1 -fdump-record-layouts'",
            ],
        },
    }

    @classmethod
    def get_guidance(cls, error_code: str) -> Dict[str, Any]:
        """Get guidance for error code."""
        return cls.ERROR_GUIDANCE.get(
            error_code,
            {
                "title": "Unknown Error",
                "suggestions": [
                    "Review error message carefully",
                    "Check documentation: https://pfcv.dev/troubleshooting",
                    "Report issue if persistent",
                ],
            },
        )

    @staticmethod
    def get_common_issues_help() -> str:
        """Get help for common issues."""
        return """
Common Issues and Solutions
═══════════════════════════════════════════════════════════════════════════════

1. "Structure size mismatch"
Cause: Padding computation doesn't match compiler layout
Fix: Check for packing attributes, compare with clang -fdump-record-layouts

2. "Type reference cannot be resolved"
Cause: Module 04 artifact incomplete or corrupted
Fix: Re-run Module 04 ingestion, verify all headers included

3. "Invalid artifact version"
Cause: Module 04 artifact version not supported
Fix: Update Module 04 to compatible version, or update Module 05

4. "Permission denied"
Cause: Cannot write to cache directory
Fix: Check permissions, use --cache-dir with writable location

For more help: https://pfcv.dev/troubleshooting
        """


# ============================================================================
# PROGRESS TRACKER
# ============================================================================


class ProgressTracker:
    """Tracks and reports pipeline progress."""

    def __init__(self, verbose: bool = True):
        self.verbose = verbose
        self.current_stage: Optional[str] = None
        self.stages_total: int = 0
        self.stages_completed: int = 0

    def start_pipeline(self, total_stages: int):
        """Signal pipeline start."""
        self.stages_total = total_stages
        if self.verbose:
            print(f"Starting IR normalization ({total_stages} stages)...")

    def start_stage(self, stage_name: str, description: str = ""):
        """Signal stage start."""
        self.current_stage = stage_name
        if self.verbose:
            progress = f"[{self.stages_completed + 1}/{self.stages_total}]"
            print(f"{progress} {stage_name}: {description}")

    def update_stage_progress(self, current: int, total: int, item: str = ""):
        """Update progress within stage."""
        if self.verbose and total > 0:
            pct = (current / total) * 100
            print(f"  Processing: {current}/{total} ({pct:.0f}%) {item}", end="\r")

    def complete_stage(self, duration: float):
        """Signal stage completion."""
        self.stages_completed += 1
        if self.verbose:
            print(f"  ✓ {self.current_stage or 'Stage'} Complete ({duration:.2f}s)")

    def report_error(self, error: str):
        """Report error."""
        if self.verbose:
            print(f"  ✗ Error: {error}")


__all__ = [
    "IRSeverity",
    "Severity",
    "ErrorCategory",
    "SourceLocation",
    "DiagnosticMessage",
    "DiagnosticCollector",
    "error_context",
    "UserGuidance",
    "ProgressTracker",
]


# Compatibility Alias
Severity = IRSeverity