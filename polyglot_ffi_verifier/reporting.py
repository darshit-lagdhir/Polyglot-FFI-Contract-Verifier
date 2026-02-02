"""
Reporting Module

This module orchestrates the generation of FFI verification reports in multiple formats.
It produces HTML reports for humans, Markdown for documentation, and JSON for CI/CD pipelines.

Consolidates:
- ReportGenerator: Main orchestrator
- HTMLReportGenerator: Web-ready reports
- MarkdownReportGenerator: Text-based reports
- CISummaryGenerator: CI integration data
- ReportMetadataGenerator: Provenance tracking
- ReportStylesheet: Styling for HTML results

From original implementation: Phase 11 (src/reporting/)
"""

import os
import json
from datetime import datetime
from typing import Any, Dict, List

# ============================================================================
# INTERNAL HELPERS
# ============================================================================

class ReportStylesheet:
    """
    Provides CSS styles for professional FFI verification reports.
    """

    @staticmethod
    def get_css() -> str:
        return """
:root {
    --primary-color: #2c3e50;
    --secondary-color: #34495e;
    --accent-color: #3498db;
    --success-color: #27ae60;
    --warning-color: #f39c12;
    --high-error-color: #e67e22;
    --error-color: #c0392b;
    --bg-color: #f8f9fa;
    --card-bg: #ffffff;
    --text-color: #2c3e50;
    --light-text: #7f8c8d;
    --border-color: #dee2e6;
}

body {
    font-family: 'Segoe UI', Roboto, Helvetica, Arial, sans-serif;
    line-height: 1.6;
    color: var(--text-color);
    background-color: var(--bg-color);
    margin: 0;
    padding: 0;
}

header {
    background-color: var(--primary-color);
    color: white;
    padding: 2rem 10%;
    margin-bottom: 2rem;
}

header h1 {
    margin: 0;
    font-size: 2rem;
}

.report-metadata {
    display: flex;
    flex-wrap: wrap;
    gap: 1.5rem;
    margin-top: 1rem;
    font-size: 0.9rem;
}

.status-failed { color: #ff7675; font-weight: bold; }
.status-passed { color: #55efc4; font-weight: bold; }

main {
    max-width: 1200px;
    margin: 0 auto;
    padding: 0 20px;
}

section {
    margin-bottom: 3rem;
    background: var(--card-bg);
    padding: 1.5rem;
    border-radius: 8px;
    box-shadow: 0 2px 4px rgba(0,0,0,0.05);
}

h2 {
    border-bottom: 2px solid var(--border-color);
    padding-bottom: 0.5rem;
    margin-top: 0;
}

/* Executive Summary Cards */
.summary-cards {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
    gap: 1rem;
    margin-top: 1rem;
}

.card {
    padding: 1.5rem;
    border-radius: 8px;
    text-align: center;
    color: white;
}

.card h3 { margin: 0; font-size: 2.5rem; }
.card p { margin: 0.5rem 0 0; font-weight: bold; }

.card-critical { background-color: var(--error-color); }
.card-high { background-color: var(--high-error-color); }
.card-medium { background-color: var(--warning-color); }
.card-passed { background-color: var(--success-color); }

/* Tables */
table {
    width: 100%;
    border-collapse: collapse;
    margin-top: 1rem;
}

th, td {
    padding: 12px;
    text-align: left;
    border-bottom: 1px solid var(--border-color);
}

th { background-color: #f1f3f5; font-weight: 600; }

.total-row { font-weight: bold; background-color: #f8f9fa; }
.pass-rate-excellent { color: var(--success-color); font-weight: bold; }
.pass-rate-fair { color: var(--warning-color); font-weight: bold; }
.pass-rate-poor { color: var(--error-color); font-weight: bold; }

/* Violation Cards */
.violation-card {
    border: 1px solid var(--border-color);
    border-left-width: 5px;
    border-radius: 4px;
    margin-bottom: 1.5rem;
    padding: 1rem;
}

.violations-critical .violation-card { border-left-color: var(--error-color); }
.violations-high .violation-card { border-left-color: var(--high-error-color); }
.violations-medium .violation-card { border-left-color: var(--warning-color); }

.violation-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 1rem;
}

.violation-badge {
    padding: 4px 8px;
    border-radius: 4px;
    font-size: 0.8rem;
    font-weight: bold;
    color: white;
}

.badge-critical { background-color: var(--error-color); }
.badge-high { background-color: var(--high-error-color); }
.badge-medium { background-color: var(--warning-color); }

.violation-id { color: var(--light-text); font-family: monospace; }
.impact-critical { color: var(--error-color); font-weight: bold; }

pre {
    background-color: #f1f3f5;
    padding: 10px;
    border-radius: 4px;
    overflow-x: auto;
    font-family: 'Consolas', 'Monaco', monospace;
    font-size: 0.9rem;
}

/* Technical Details */
details {
    margin-bottom: 1rem;
    border: 1px solid var(--border-color);
    border-radius: 4px;
    padding: 0.5rem;
}

summary {
    font-weight: bold;
    cursor: pointer;
    padding: 0.5rem;
}

footer {
    text-align: center;
    padding: 2rem;
    color: var(--light-text);
    font-size: 0.8rem;
    border-top: 1px solid var(--border-color);
    margin-top: 3rem;
}

@media print {
    body { background-color: white; }
    section { break-inside: avoid; border: 1px solid #eee; box-shadow: none; }
    header { background-color: white; color: black; border-bottom: 2px solid black; }
}
"""


class HtmlReportGenerator:
    """
    Generates visually rich, responsive HTML reports.
    """

    def generate(self, diagnostics: Dict[str, Any], execution_log: Dict[str, Any], contract: Dict[str, Any], context: Any) -> str:
        """
        Main entry point for HTML generation.
        """
        summary = diagnostics.get("summary", {})
        violations = diagnostics.get("violations", [])
        
        # Split violations by severity
        critical = [v for v in violations if v.get("severity") == "critical"]
        high = [v for v in violations if v.get("severity") == "high"]
        other = [v for v in violations if v.get("severity") not in ["critical", "high"]]
        
        html_parts = [
            '<!DOCTYPE html>',
            '<html lang="en">',
            self._generate_head(),
            '<body>',
            self._generate_header(context, summary),
            '<main>',
            self._generate_executive_summary(summary, violations),
            self._generate_test_results(execution_log),
            self._generate_violations_section("Critical Violations", critical, "violations-critical"),
            self._generate_violations_section("High Severity Violations", high, "violations-high"),
            self._generate_violations_section("Other Findings", other, "violations-medium"),
            self._generate_verified_constraints(violations, contract, execution_log),
            self._generate_recommendations(violations),
            self._generate_technical_details(context, contract, execution_log),
            '</main>',
            self._generate_footer(context),
            '</body>',
            '</html>'
        ]
        
        return "\n".join(html_parts)

    def _generate_head(self) -> str:
        return f"""
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>FFI Contract Verification Report</title>
    <style>{ReportStylesheet.get_css()}</style>
</head>
"""

    def _generate_header(self, context: Any, summary: Dict[str, Any]) -> str:
        status = "PASSED" if summary.get("severity_counts", {}).get("critical", 0) == 0 else "FAILED"
        status_class = "status-passed" if status == "PASSED" else "status-failed"
        
        lib_name = context.native_library.library_path
        # Defensive timestamp parsing
        ts = context.provenance.creation_timestamp
        try:
             timestamp = datetime.fromisoformat(ts.replace('Z', '+00:00')).strftime('%Y-%m-%d %H:%M:%S')
        except:
             timestamp = ts
        
        return f"""
<header>
    <h1>FFI Contract Verification Report</h1>
    <div class="report-metadata">
        <span><strong>Library:</strong> {lib_name}</span>
        <span><strong>Date:</strong> {timestamp}</span>
        <span><strong>Status:</strong> <span class="{status_class}">{status}</span></span>
        <span><strong>Execution ID:</strong> {context.provenance.execution_id[:8]}...</span>
    </div>
</header>
"""

    def _generate_executive_summary(self, summary: Dict[str, Any], violations: List[Dict[str, Any]]) -> str:
        sev = summary.get("severity_counts", {})
        pass_rate = summary.get("pass_rate", 0)
        
        status_text = "Verification FAILED" if sev.get("critical", 0) > 0 else "Verification PASSED"
        recommendation = "Do not deploy until critical violations are resolved." if sev.get("critical", 0) > 0 else "Library meets contract safety constraints."

        return f"""
<section class="executive-summary">
    <h2>Executive Summary</h2>
    <div class="summary-cards">
        <div class="card card-critical">
            <h3>{sev.get('critical', 0)}</h3>
            <p>Critical Violations</p>
        </div>
        <div class="card card-high">
            <h3>{sev.get('high', 0)}</h3>
            <p>High Severity</p>
        </div>
        <div class="card card-medium">
            <h3>{sev.get('medium', 0)}</h3>
            <p>Medium Severity</p>
        </div>
        <div class="card card-passed">
            <h3>{pass_rate:.1f}%</h3>
            <p>Pass Rate</p>
        </div>
    </div>
    <div class="summary-text" style="margin-top: 1.5rem">
        <p><strong>Overall Status:</strong> {status_text}</p>
        <p>A total of <strong>{len(violations)} aggregated issue(s)</strong> were identified across the contract surface.</p>
        <p><strong>Recommendation:</strong> {recommendation}</p>
    </div>
</section>
"""

    def _generate_test_results(self, execution_log: Dict[str, Any]) -> str:
        results = execution_log.get("test_results", [])
        total = len(results)
        passed = sum(1 for r in results if r.get("status") == "passed")
        failed = total - passed
        rate = (passed / total * 100) if total > 0 else 0
        rate_class = "pass-rate-excellent" if rate > 95 else ("pass-rate-fair" if rate > 80 else "pass-rate-poor")
        
        return f"""
<section class="test-results">
    <h2>Test Results</h2>
    <table>
        <thead>
            <tr>
                <th>Measurement</th>
                <th>Count</th>
            </tr>
        </thead>
        <tbody>
            <tr>
                <td>Total Tests Executed</td>
                <td>{total}</td>
            </tr>
            <tr>
                <td>Total Tests Passed</td>
                <td>{passed}</td>
            </tr>
            <tr>
                <td>Total Tests Failed</td>
                <td>{failed}</td>
            </tr>
            <tr class="total-row">
                <td>Overall Pass Rate</td>
                <td class="{rate_class}">{rate:.1f}%</td>
            </tr>
        </tbody>
    </table>
</section>
"""

    def _generate_violations_section(self, title: str, violations: List[Dict[str, Any]], css_class: str) -> str:
        if not violations: return ""
        cards = [self._generate_violation_card(v) for v in violations]
        return f"""
<section class="violations {css_class}">
    <h2>{title}</h2>
    {"".join(cards)}
</section>
"""

    def _generate_violation_card(self, v: Dict[str, Any]) -> str:
        badge_class = f"badge-{v.get('severity', 'medium')}"
        impact_class = "impact-critical" if v.get("severity") == "critical" else ""
        affected_tests = ", ".join(v.get("affected_tests", []))
        rem = v.get("remediation", {})
        steps = "".join([f"<li>{s}</li>" for s in rem.get("detailed_steps", [])])
        
        return f"""
<div class="violation-card">
    <div class="violation-header">
        <span class="violation-badge {badge_class}">{v.get('severity', '').upper()}</span>
        <h3>{v.get('category', 'Violation')} in {v.get('function_name', 'native code')}</h3>
        <span class="violation-id">{v.get('violation_id', 'v???')}</span>
    </div>
    
    <div class="violation-details">
        <p><strong>Constraint:</strong> {v.get('constraint_id', 'N/A')}</p>
        <p><strong>Affected Tests:</strong> {len(v.get('affected_tests', []))} failures ({affected_tests})</p>
    </div>
    
    <div class="violation-description">
        <h4>Description</h4>
        <p>{v.get('description', 'No description available.')}</p>
        <p><strong>Root Cause:</strong> {v.get('explanation', v.get('root_cause', 'Undetermined'))}</p>
    </div>
    
    <div class="violation-impact">
        <h4>Impact</h4>
        <p class="{impact_class}">{v.get('impact', 'Potential instability.')}</p>
        <p><strong>Exploitability:</strong> {v.get('exploitability', 'Unknown')}</p>
    </div>
    
    <div class="violation-remediation">
        <h4>Remediation</h4>
        <p><strong>{rem.get('short_description', 'No remediation provided.')}</strong></p>
        <ol>{steps}</ol>
    </div>
</div>
"""

    def _generate_verified_constraints(self, violations: List[Dict[str, Any]], contract: Dict[str, Any], execution_log: Dict[str, Any]) -> str:
        violated_cids = {v.get("constraint_id") for v in violations}
        all_constraints = []
        if "function_contracts" in contract:
             for f in contract["function_contracts"]:
                 # check both pre and post
                 for c in f.get("pre_conditions", []) + f.get("post_conditions", []):
                     all_constraints.append(c.get("constraint_id"))

        verified = [cid for cid in all_constraints if cid not in violated_cids]
        if not verified: return ""
        list_items = "".join([f"<li>✓ {cid}</li>" for cid in verified])
        
        return f"""
<section class="verified-constraints">
    <h2>Verified Constraints</h2>
    <p>The following constraints were successfully verified with no observed violations:</p>
    <ul class="verified-list" style="columns: 2; list-style-type: none; padding: 0;">
        {list_items}
    </ul>
</section>
"""

    def _generate_recommendations(self, violations: List[Dict[str, Any]]) -> str:
        critical_v = [v for v in violations if v.get("severity") == "critical"]
        high_v = [v for v in violations if v.get("severity") == "high"]
        
        if not critical_v and not high_v:
            return f"""
<section class="recommendations">
    <h2>Recommendations</h2>
    <p>Verified current contract implementation. Continue to monitor FFI surface for changes.</p>
</section>
"""
        rec_cards = []
        if critical_v:
            items = "".join([f"<li>{v.get('category')} in {v.get('function_name')} (CRITICAL)</li>" for v in critical_v])
            rec_cards.append(f'<div class="recommendation-card" style="border-left: 4px solid var(--error-color); padding-left: 1rem;"><h4>Immediate Action Required</h4><ol>{items}</ol></div>')
        if high_v:
            items = "".join([f"<li>{v.get('category')} in {v.get('function_name')} (HIGH)</li>" for v in high_v])
            rec_cards.append(f'<div class="recommendation-card" style="border-left: 4px solid var(--high-error-color); padding-left: 1rem; margin-top: 1rem;"><h4>Follow-Up Actions</h4><ol>{items}</ol></div>')

        return f"""
<section class="recommendations">
    <h2>Recommendations</h2>
    {"".join(rec_cards)}
</section>
"""

    def _generate_technical_details(self, context: Any, contract: Dict[str, Any], execution_log: Dict[str, Any]) -> str:
        # Simplistic serialization for safety
        ctx_data = {
            "execution_id": context.provenance.execution_id,
            "platform": f"{context.platform.os_name} {context.platform.os_version}",
            "compiler": context.compiler.compiler_name,
            "runtime": context.target_runtime.language_name
        }
        ctx_json = json.dumps(ctx_data, indent=2)
        
        contract_stats = json.dumps({
            "total_functions": len(contract.get("function_contracts", [])),
            "contract_hash": contract.get("provenance", {}).get("contract_hash", "N/A")
        }, indent=2)

        return f"""
<section class="technical-details">
    <h2>Technical Details</h2>
    <details>
        <summary>Execution Context</summary>
        <pre>{ctx_json}</pre>
    </details>
    <details>
        <summary>Contract Summary</summary>
        <pre>{contract_stats}</pre>
    </details>
</section>
"""

    def _generate_footer(self, context: Any) -> str:
        return f"""
<footer>
    <p>Generated by Polyglot FFI Contract Verifier v{context.provenance.tool_version}</p>
    <p>Report ID: {context.provenance.execution_id}</p>
</footer>
"""


class MarkdownReportGenerator:
    """
    Generates structured Markdown reports.
    """

    def generate(self, diagnostics: Dict[str, Any], execution_log: Dict[str, Any], contract: Dict[str, Any], context: Any) -> str:
        summary = diagnostics.get("summary", {})
        violations = diagnostics.get("violations", [])
        
        try:
             timestamp = datetime.fromisoformat(context.provenance.creation_timestamp.replace('Z', '+00:00')).strftime('%Y-%m-%d %H:%M:%S')
        except:
             timestamp = context.provenance.creation_timestamp
             
        status_icon = "❌" if summary.get("severity_counts", {}).get("critical", 0) > 0 else "✅"
        status_text = "FAILED" if summary.get("severity_counts", {}).get("critical", 0) > 0 else "PASSED"

        md = [
            f"# FFI Contract Verification Report",
            f"",
            f"**Library:** `{context.native_library.library_path}`  ",
            f"**Date:** {timestamp}  ",
            f"**Status:** {status_icon} {status_text}",
            f"",
            f"---",
            f"",
            f"## Executive Summary",
            f"",
            f"| Metric | Value |",
            f"|--------|-------|",
            f"| Critical Violations | {summary.get('severity_counts', {}).get('critical', 0)} |",
            f"| High Severity | {summary.get('severity_counts', {}).get('high', 0)} |",
            f"| Medium Severity | {summary.get('severity_counts', {}).get('medium', 0)} |",
            f"| Pass Rate | {summary.get('pass_rate', 0):.1f}% |",
            f"",
            f"**Overall Status:** Verification {status_text}",
            f"",
            f"---",
            f"",
            f"## Test Results",
            f"",
            f"| Measurement | Count |",
            f"|-------------|-------|",
            f"| Total Tests | {len(execution_log.get('test_results', []))} |",
            f"| Passed | {sum(1 for r in execution_log.get('test_results', []) if r.get('status') == 'passed')} |",
            f"| Failed | {len(execution_log.get('test_results', [])) - sum(1 for r in execution_log.get('test_results', []) if r.get('status') == 'passed')} |",
            f"",
            f"---",
            f""
        ]

        if violations:
            md.append("## Detailed Violations")
            md.append("")
            # Sort critical first
            sorted_violations = sorted(violations, key=lambda x: {"critical": 0, "high": 1, "medium": 2, "low": 3}.get(x.get("severity"), 9))
            
            for v in sorted_violations:
                md.append(f"### [{v.get('violation_id', 'v???')}] {v.get('category')} in `{v.get('function_name')}()`")
                md.append("")
                md.append(f"**Severity:** {v.get('severity', '').upper()}  ")
                md.append(f"**Constraint:** `{v.get('constraint_id')}`  ")
                md.append(f"**Affected Tests:** {len(v.get('affected_tests', []))} failures")
                md.append("")
                md.append("#### Description")
                md.append(v.get("description", ""))
                md.append("")
                md.append("#### Impact")
                md.append(f"- {v.get('impact')}")
                md.append(f"- **Exploitability:** {v.get('exploitability')}")
                md.append("")
                md.append("#### Remediation")
                md.append(f"**{v.get('remediation', {}).get('short_description')}**")
                for step in v.get("remediation", {}).get("detailed_steps", []):
                    md.append(f"- {step}")
                md.append("")

        md.append("## Technical Details")
        md.append("")
        md.append(f"- **Execution ID:** `{context.provenance.execution_id}`")
        md.append(f"- **Platform:** {context.platform.os_name} {context.platform.os_version}")
        md.append(f"- **Tool Version:** {context.provenance.tool_version}")
        md.append("")
        md.append("---")
        md.append(f"Generated by Polyglot FFI Contract Verifier")

        return "\n".join(md)


class CISummaryGenerator:
    """
    Generates CI-friendly JSON data including exit codes and status badges.
    """

    def generate(self, diagnostics: Dict[str, Any], execution_log: Dict[str, Any], context: Any) -> Dict[str, Any]:
        """
        Builds the ci_summary.json structure.
        """
        summary = diagnostics.get("summary", {})
        violations = diagnostics.get("violations", [])
        
        test_results = execution_log.get("test_results", [])
        passed_count = sum(1 for r in test_results if r.get("status") == "passed")
        failed_count = len(test_results) - passed_count
        
        has_critical = summary.get("severity_counts", {}).get("critical", 0) > 0
        status = "failed" if has_critical else "passed"
        exit_code = 1 if has_critical else 0
        
        badge = self._generate_status_badge(status, summary)
        blocking_issues = self._extract_blocking_issues(violations)
        
        return {
            "provenance": {
                "producing_phase": "Phase 11: Report Generation",
                "execution_id": context.provenance.execution_id,
                "timestamp": context.provenance.creation_timestamp,
                "tool_version": context.provenance.tool_version
            },
            "verification_status": status,
            "summary": {
                "total_tests": len(test_results),
                "passed_tests": passed_count,
                "failed_tests": failed_count,
                "pass_rate": summary.get("pass_rate", 0),
                "total_violations": len(violations),
                "critical_violations": summary.get("severity_counts", {}).get("critical", 0),
                "high_severity_violations": summary.get("severity_counts", {}).get("high", 0),
                "medium_severity_violations": summary.get("severity_counts", {}).get("medium", 0),
                "low_severity_violations": summary.get("severity_counts", {}).get("low", 0)
            },
            "status_badge": badge,
            "exit_code": exit_code,
            "blocking_issues": blocking_issues,
            "reports": {
                "html": "reports/verification_report.html",
                "markdown": "reports/verification_report.md",
                "diagnostics": "artifacts/diagnostics.json"
            }
        }

    def _generate_status_badge(self, status: str, summary: Dict[str, Any]) -> Dict[str, str]:
        critical = summary.get("severity_counts", {}).get("critical", 0)
        
        if status == "failed":
            message = f"FAILED ({critical} critical)"
            color = "red"
        else:
            message = "PASSED"
            color = "green"
            
        return {
            "label": "FFI Verification",
            "message": message,
            "color": color
        }

    def _extract_blocking_issues(self, violations: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        blocking = []
        for v in violations:
            if v.get("severity") == "critical":
                blocking.append({
                    "violation_id": v.get("violation_id"),
                    "severity": "critical",
                    "function": v.get("function_name"),
                    "description": v.get("description", "Critical contract violation")
                })
        return blocking


class ReportMetadataGenerator:
    """
    Generates report_metadata.json to track verification outputs.
    """

    def generate(self, reports: Dict[str, str], context: Any) -> Dict[str, Any]:
        """
        Creates metadata structure for the generated reports.
        """
        from datetime import datetime
        return {
            "provenance": {
                "producing_phase": "Phase 11: Report Generation",
                "execution_id": context.provenance.execution_id,
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "tool_version": context.provenance.tool_version
            },
            "generated_artifacts": [
                {"format": fmt, "path": path} for fmt, path in reports.items()
            ],
            "metadata": {
                "report_count": len(reports),
                "target_library": context.native_library.library_path,
                "platform": context.platform.os_name
            }
        }


# ============================================================================
# PUBLIC API
# ============================================================================

class ReportGenerator:
    """
    Orchestrates the generation of FFI verification reports in multiple formats.
    """
    
    def __init__(self):
        self.html_gen = HtmlReportGenerator()
        self.md_gen = MarkdownReportGenerator()
        self.ci_gen = CISummaryGenerator()
        self.meta_gen = ReportMetadataGenerator()

    def generate_reports(self, context: Any) -> Dict[str, Any]:
        """
        Loads artifacts, generates reports, and saves them to the reports/ directory.
        """
        # 1. Load Artifacts
        artifacts = self._load_artifacts(context)
        
        # 2. Setup output directory
        reports_dir = os.path.join(context.artifacts.working_directory, "reports")
        os.makedirs(reports_dir, exist_ok=True)
        
        # 3. Generate content
        html_content = self.html_gen.generate(
            artifacts["diagnostics"], 
            artifacts["execution_log"], 
            artifacts["contract"], 
            context
        )
        
        md_content = self.md_gen.generate(
            artifacts["diagnostics"], 
            artifacts["execution_log"], 
            artifacts["contract"], 
            context
        )
        
        ci_summary = self.ci_gen.generate(
            artifacts["diagnostics"], 
            artifacts["execution_log"], 
            context
        )
        
        # 4. Save files
        html_path = os.path.join(reports_dir, "verification_report.html")
        with open(html_path, 'w', encoding='utf-8') as f:
            f.write(html_content)
            
        md_path = os.path.join(reports_dir, "verification_report.md")
        with open(md_path, 'w', encoding='utf-8') as f:
            f.write(md_content)
            
        ci_path = os.path.join(reports_dir, "ci_summary.json")
        with open(ci_path, 'w', encoding='utf-8') as f:
            json.dump(ci_summary, f, indent=2)
            
        # 5. Metadata
        report_map = {
            "html": html_path,
            "markdown": md_path,
            "ci_summary": ci_path
        }
        metadata = self.meta_gen.generate(report_map, context)
        
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
            contract_path = os.path.join(artifacts_dir, "contract.json")
            
        if not os.path.exists(contract_path):
             # Try to find any json file in artifacts that looks like a contract if strict path fails
            raise FileNotFoundError(f"Contract missing: {contract_path}. Run 'synthesize' first.")
            
        with open(contract_path, 'r', encoding='utf-8') as f:
            contract = json.load(f)
            
        return {
            "diagnostics": diagnostics,
            "execution_log": execution_log,
            "contract": contract
        }
from datetime import timezone
