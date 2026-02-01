"""
HTML Report Generator
Produces self-contained HTML verification reports.
"""

import json
from datetime import datetime
from typing import Any, Dict, List
from .report_stylesheet import ReportStylesheet

class HTMLReportGenerator:
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
        timestamp = datetime.fromisoformat(context.provenance.creation_timestamp.replace('Z', '+00:00')).strftime('%Y-%m-%d %H:%M:%S')
        
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
        if not violations:
            return ""
            
        cards = []
        for v in violations:
            cards.append(self._generate_violation_card(v))
            
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
        <span class="violation-id">{v.get('violation_id', 'v')}</span>
    </div>
    
    <div class="violation-details">
        <p><strong>Constraint:</strong> {v.get('constraint_id', 'N/A')}</p>
        <p><strong>Affected Tests:</strong> {len(v.get('affected_tests', []))} failures ({affected_tests})</p>
    </div>
    
    <div class="violation-description">
        <h4>Description</h4>
        <p>{v.get('description', 'No description available.')}</p>
        <p><strong>Root Cause:</strong> {v.get('explanation', 'Undetermined')}</p>
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
        
        # Collect all constraints from contract
        all_constraints = []
        if "functions" in contract:
            for f_name, f_spec in contract["functions"].items():
                for c in f_spec.get("constraints", []):
                    all_constraints.append((c.get("id"), f_name))
        
        verified = [cid for cid, f_name in all_constraints if cid not in violated_cids]
        
        if not verified:
            return ""

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
            items = "".join([f"<li>Fix {v.get('category')} in {v.get('function_name')} (CRITICAL)</li>" for v in critical_v])
            rec_cards.append(f'<div class="recommendation-card" style="border-left: 4px solid var(--error-color); padding-left: 1rem;"><h4>Immediate Action Required</h4><ol>{items}</ol></div>')
            
        if high_v:
            items = "".join([f"<li>Improve validation for {v.get('category')} in {v.get('function_name')} (HIGH)</li>" for v in high_v])
            rec_cards.append(f'<div class="recommendation-card" style="border-left: 4px solid var(--high-error-color); padding-left: 1rem; margin-top: 1rem;"><h4>Follow-Up Actions</h4><ol>{items}</ol></div>')

        return f"""
<section class="recommendations">
    <h2>Recommendations</h2>
    {"".join(rec_cards)}
</section>
"""

    def _generate_technical_details(self, context: Any, contract: Dict[str, Any], execution_log: Dict[str, Any]) -> str:
        ctx_json = json.dumps({
            "execution_id": context.provenance.execution_id,
            "platform": f"{context.platform.os_name} {context.platform.os_version}",
            "compiler": context.compiler.compiler_name,
            "runtime": context.target_runtime.language_name
        }, indent=2)
        
        contract_stats = json.dumps({
            "total_functions": len(contract.get("functions", {})),
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
