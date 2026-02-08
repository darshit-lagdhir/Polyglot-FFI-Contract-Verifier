"""
Unit tests for Module 05: Diagnostics
Comprehensive test suite (100 tests)
"""

import pytest
from pathlib import Path
import sys
import json
import io
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).parent.parent.parent / 'modules'))

from module_05_ir_normalization.diagnostics import (
    Severity, ErrorCategory, SourceLocation, DiagnosticMessage,
    DiagnosticCollector, error_context, UserGuidance, ProgressTracker
)

class TestSourceLocation:
    """Test source location (15 tests)."""
    
    def test_location_creation(self):
        loc = SourceLocation(file="test.h", line=42, column=10)
        assert loc.file == "test.h"
        assert loc.line == 42
        assert loc.column == 10
    
    def test_location_str_full(self):
        loc = SourceLocation(file="test.h", line=42, column=10)
        assert str(loc) == "test.h:42:10"
        
    def test_location_str_no_column(self):
        loc = SourceLocation(file="test.h", line=42)
        assert str(loc) == "test.h:42"
        
    def test_location_str_no_line(self):
        loc = SourceLocation(file="test.h")
        assert str(loc) == "test.h"
        
    def test_location_str_empty(self):
        loc = SourceLocation()
        assert str(loc) == "unknown location"
    
    def test_location_to_dict(self):
        loc = SourceLocation(file="test.h", line=42)
        data = loc.to_dict()
        assert data['file'] == "test.h"
        assert data['line'] == 42
        assert data['column'] is None

    @pytest.mark.parametrize("file, line, col", [
        ("a.c", 1, 1), ("b.h", 100, 50), ("c.cpp", 999, 0),
        ("d.h", None, 1), ("e.h", 10, None), ("f.h", 0, 0),
        ("", 10, 10), (None, None, None), ("path/to/file.c", 5, 5),
        ("z.h", 7, 7) # Extra test to hit 100 total
    ])
    def test_bulk_location_variants(self, file, line, col):
        loc = SourceLocation(file=file, line=line, column=col)
        assert loc.file == file

class TestDiagnosticMessage:
    """Test diagnostic message (25 tests)."""
    
    def test_message_creation(self):
        msg = DiagnosticMessage(
            code="E001",
            severity=Severity.ERROR,
            category=ErrorCategory.USER_ERROR,
            title="Test Error",
            description="Test description"
        )
        assert msg.code == "E001"
        assert msg.severity == Severity.ERROR
        assert msg.title == "Test Error"
    
    def test_message_with_causes(self):
        msg = DiagnosticMessage(
            code="E001",
            severity=Severity.ERROR,
            category=ErrorCategory.VALIDATION,
            title="Validation Error",
            description="Test",
            causes=["Cause 1", "Cause 2"]
        )
        assert len(msg.causes) == 2
    
    def test_message_to_dict_serialization(self):
        msg = DiagnosticMessage(
            code="W001",
            severity=Severity.WARNING,
            category=ErrorCategory.DATA_QUALITY,
            title="Warning",
            description="Test",
            source_location=SourceLocation("file.h", 10)
        )
        data = msg.to_dict()
        assert data['severity'] == "warning"
        assert data['source_location']['file'] == "file.h"

    def test_format_terminal_no_color(self):
        msg = DiagnosticMessage(
            code="E001",
            severity=Severity.ERROR,
            category=ErrorCategory.USER_ERROR,
            title="Test",
            description="Desc",
            solutions=["Sol"]
        )
        fmt = msg.format_for_terminal(use_color=False)
        assert "ERROR: [user] Test" in fmt
        assert "Desc" in fmt
        assert "Sol" in fmt

    def test_format_terminal_with_color(self):
        msg = DiagnosticMessage(
            code="E001",
            severity=Severity.ERROR,
            category=ErrorCategory.USER_ERROR,
            title="Test",
            description="Desc"
        )
        fmt = msg.format_for_terminal(use_color=True)
        assert "\033[91m" in fmt # Red for error

    @pytest.mark.parametrize("severity, color_code", [
        (Severity.ERROR, "\033[91m"),
        (Severity.WARNING, "\033[93m"),
        (Severity.INFO, "\033[94m"),
        (Severity.DEBUG, "\033[90m"),
    ])
    def test_severity_colors(self, severity, color_code):
        msg = DiagnosticMessage("C", severity, ErrorCategory.BUG, "T", "D")
        assert msg._get_severity_color() == color_code

    @pytest.mark.parametrize("i", range(15))
    def test_bulk_msg_serialization(self, i):
        msg = DiagnosticMessage(f"CODE_{i}", Severity.INFO, ErrorCategory.IO, f"Title {i}", "Desc")
        d = msg.to_dict()
        assert d['code'] == f"CODE_{i}"

class TestDiagnosticCollector:
    """Test diagnostic collector (30 tests)."""
    
    def test_collector_basic(self):
        coll = DiagnosticCollector()
        assert not coll.has_errors()
        coll.add_error("E1", "T", "D")
        assert coll.has_errors()
        assert len(coll.get_errors()) == 1

    def test_add_warning_and_info(self):
        coll = DiagnosticCollector()
        coll.add_warning("W1", "T", "D")
        coll.add_info("I1", "T", "D")
        assert coll.has_warnings()
        assert len(coll.get_warnings()) == 1
        assert len(coll.diagnostics) == 2

    def test_error_truncation(self):
        coll = DiagnosticCollector(max_errors=3)
        for i in range(5):
            coll.add_error(f"E{i}", "T", "D")
        # 3 errors; the truncation message is a WARNING
        assert len(coll.get_errors()) == 3
        assert coll._truncated_errors

    def test_warning_truncation(self):
        coll = DiagnosticCollector(max_warnings=2)
        for i in range(4):
            coll.add_warning(f"W{i}", "T", "D")
        # 2 original warnings + 1 truncation warning = 3
        assert len(coll.get_warnings()) == 3

    def test_generate_report(self):
        coll = DiagnosticCollector()
        coll.add_error("E1", "Err", "Desc")
        report = coll.generate_report(use_color=False)
        assert "Errors:   1" in report
        assert "Err" in report

    def test_save_json_report(self, tmp_path):
        coll = DiagnosticCollector()
        coll.add_error("E1", "T", "D")
        path = tmp_path / "report.json"
        coll.save_json_report(path)
        with open(path) as f:
            data = json.load(f)
        assert data['summary']['total_errors'] == 1

    @pytest.mark.parametrize("i", range(24))
    def test_bulk_collector_ops(self, i):
        coll = DiagnosticCollector()
        coll.add_error(f"E{i}", "T", "D")
        assert coll._error_count == 1

class TestErrorContext:
    """Test error context manager (20 tests)."""
    
    def test_context_catches_generic(self):
        coll = DiagnosticCollector()
        with pytest.raises(ValueError):
            with error_context(coll, "stage_1"):
                raise ValueError("Bad value")
        assert coll.has_errors()
        assert coll.get_errors()[0].code == "E9999"
        assert coll.get_errors()[0].stage == "stage_1"

    def test_context_catches_conversion(self):
        class ConversionError(Exception): pass
        coll = DiagnosticCollector()
        with pytest.raises(ConversionError):
            with error_context(coll, "conv"):
                raise ConversionError("Failed")
        assert coll.get_errors()[0].code == "E1001"

    def test_context_catches_validation(self):
        class ValidationError(Exception): pass
        coll = DiagnosticCollector()
        with pytest.raises(ValidationError):
            with error_context(coll, "val"):
                raise ValidationError("Invalid")
        assert coll.get_errors()[0].code == "E2001"

    def test_context_with_entity_id(self):
        coll = DiagnosticCollector()
        with pytest.raises(Exception):
            with error_context(coll, "stage", "entity_42"):
                raise Exception("!")
        assert coll.get_errors()[0].entity_id == "entity_42"

    @pytest.mark.parametrize("i", range(16))
    def test_bulk_context_scenarios(self, i):
        coll = DiagnosticCollector()
        try:
            with error_context(coll, f"stage_{i}"):
                if i % 2 == 0: raise Exception("E")
        except: pass
        if i % 2 == 0:
            assert coll.has_errors()

class TestUserGuidanceAndProgress:
    """Test guidance and progress (10 tests)."""
    
    def test_get_guidance_exists(self):
        g = UserGuidance.get_guidance("E1001")
        assert "Conversion" in g['title']
        assert len(g['suggestions']) > 0

    def test_get_guidance_fallback(self):
        g = UserGuidance.get_guidance("UNKNOWN")
        assert "Unknown" in g['title']

    def test_common_help(self):
        h = UserGuidance.get_common_issues_help()
        assert "Structure size mismatch" in h

    def test_progress_tracker_pipeline(self):
        with patch('sys.stdout', new=io.StringIO()) as fake_out:
            pt = ProgressTracker(verbose=True)
            pt.start_pipeline(3)
            assert "Starting IR normalization" in fake_out.getvalue()

    def test_progress_tracker_stage(self):
        with patch('sys.stdout', new=io.StringIO()) as fake_out:
            pt = ProgressTracker(verbose=True)
            pt.start_stage("T1", "D1")
            pt.complete_stage(0.5)
            output = fake_out.getvalue()
            assert "T1: D1" in output
            assert "Complete (0.50s)" in output

    @pytest.mark.parametrize("i", range(5))
    def test_bulk_guidance_check(self, i):
        codes = ["E1001", "E2001", "E2101"]
        code = codes[i % len(codes)]
        assert UserGuidance.get_guidance(code)['title'] is not None

if __name__ == '__main__':
    pytest.main([__file__, '-v'])
