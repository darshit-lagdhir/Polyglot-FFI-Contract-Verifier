"""
Report Generator
Main orchestrator for Phase 11 comprehensive report generation.
"""

import os
import json
from typing import Any, Dict, List

from .html_report_generator import HTMLReportGenerator
from .markdown_report_generator import MarkdownReportGenerator
from .ci_summary_generator import CISummaryGenerator
from .report_metadata_generator import ReportMetadataGenerator

class ReportGenerator:
    """
    Orchestrates the generation of FFI verification reports in multiple formats.
    """

    def generate_reports(self, context: Any) -> Dict[str, Any]:
        """
        Loads artifacts, generates reports, and saves them to the reports/ directory.
        """
        # 1. Load Artifacts
        artifacts = self._load_artifacts(context)
        
        # 2. Setup output directory
        reports_dir = os.path.join(context.artifacts.working_directory, "reports")
        os.makedirs(reports_dir, exist_ok=True)
        
        # 3. Initialize generators
        html_gen = HTMLReportGenerator()
        md_gen = MarkdownReportGenerator()
        ci_gen = CISummaryGenerator()
        meta_gen = ReportMetadataGenerator()
        
        # 4. Generate content
        html_content = html_gen.generate(
            artifacts["diagnostics"], 
            artifacts["execution_log"], 
            artifacts["contract"], 
            context
        )
        
        md_content = md_gen.generate(
            artifacts["diagnostics"], 
            artifacts["execution_log"], 
            artifacts["contract"], 
            context
        )
        
        ci_summary = ci_gen.generate(
            artifacts["diagnostics"], 
            artifacts["execution_log"], 
            context
        )
        
        # 5. Save files
        html_path = os.path.join(reports_dir, "verification_report.html")
        with open(html_path, 'w', encoding='utf-8') as f:
            f.write(html_content)
            
        md_path = os.path.join(reports_dir, "verification_report.md")
        with open(md_path, 'w', encoding='utf-8') as f:
            f.write(md_content)
            
        ci_path = os.path.join(reports_dir, "ci_summary.json")
        with open(ci_path, 'w', encoding='utf-8') as f:
            json.dump(ci_summary, f, indent=2)
            
        # 6. Metadata
        report_map = {
            "html": html_path,
            "markdown": md_path,
            "ci_summary": ci_path
        }
        metadata = meta_gen.generate(report_map, context)
        
        meta_path = os.path.join(reports_dir, "report_metadata.json")
        with open(meta_path, 'w', encoding='utf-8') as f:
            json.dump(metadata, f, indent=2)
            
        return metadata

    def _load_artifacts(self, context: Any) -> Dict[str, Any]:
        """
        Loads the required artifacts from the artifacts directory.
        """
        artifacts_dir = context.artifacts.working_directory
        
        # Phase 10 Output
        diag_path = context.artifacts.diagnostics_path
        if not os.path.exists(diag_path):
            # Fallback to looking in artifacts dir
            diag_path = os.path.join(artifacts_dir, "diagnostics.json")
            
        if not os.path.exists(diag_path):
            raise FileNotFoundError(f"Diagnostics artifact missing: {diag_path}. Run 'diagnose' first.")
            
        with open(diag_path, 'r', encoding='utf-8') as f:
            diagnostics = json.load(f)
            
        # Phases 8-9 Output
        log_path = context.artifacts.execution_log_path
        if not os.path.exists(log_path):
            log_path = os.path.join(artifacts_dir, "execution_log.json")
            
        if not os.path.exists(log_path):
            raise FileNotFoundError(f"Execution log missing: {log_path}. Run 'execute' first.")
            
        with open(log_path, 'r', encoding='utf-8') as f:
            execution_log = json.load(f)
            
        # Phase 4 Output
        contract_path = context.artifacts.contract_path
        if not os.path.exists(contract_path):
            raise FileNotFoundError(f"Contract missing: {contract_path}. Run 'synthesize' first.")
            
        with open(contract_path, 'r', encoding='utf-8') as f:
            contract = json.load(f)
            
        # Phase 7 Output (Optional but recommended)
        coverage = {}
        # coverage_path = context.artifacts.test_coverage_path # Not in ArtifactPaths yet?
        # TODO: Add to ArtifactPaths if needed
        
        return {
            "diagnostics": diagnostics,
            "execution_log": execution_log,
            "contract": contract,
            "coverage": coverage
        }
