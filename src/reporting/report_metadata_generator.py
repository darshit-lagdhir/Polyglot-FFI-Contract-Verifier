"""
Report Metadata Generator
Tracks generated report artifacts and provenance.
"""

import os
import json
from datetime import datetime, timezone
from typing import Any, Dict, List

class ReportMetadataGenerator:
    """
    Generates report_metadata.json to track verification outputs.
    """

    def generate(self, reports: Dict[str, str], context: Any) -> Dict[str, Any]:
        """
        Creates metadata structure for the generated reports.
        """
        return {
            "provenance": {
                "producing_phase": "1: Report Generation",
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
