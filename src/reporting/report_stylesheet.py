"""
Report Stylesheet
Defines the CSS for self-contained HTML reports.
"""

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
