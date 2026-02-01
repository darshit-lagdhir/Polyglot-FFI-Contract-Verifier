"""
Badge Generator
Generates status badge metadata for shields.io.
"""

import json
from pathlib import Path
from typing import Dict, Any

class BadgeGenerator:
    """
    Creates shields.io compatible JSON for verification status badges.
    """

    def generate_badge(self, ci_summary: Dict[str, Any]) -> Dict[str, Any]:
        status = ci_summary.get('verification_status', 'unknown')
        summary = ci_summary.get('summary', {})
        critical = summary.get('critical_violations', 0)
        pass_rate = summary.get('pass_rate', 0)
        
        if status == 'passed':
            color = 'brightgreen'
            message = f'PASSED ({pass_rate:.1f}%)'
        elif critical > 0:
            color = 'red'
            message = f'FAILED ({critical} critical)'
        else:
            color = 'orange'
            message = f'WARNINGS ({pass_rate:.1f}%)'
            
        return {
            'schemaVersion': 1,
            'label': 'FFI Verification',
            'message': message,
            'color': color,
            'namedLogo': 'python',
            'logoColor': 'white'
        }

    def generate_shields_url(self, badge: Dict[str, Any]) -> str:
        # Placeholder for URL generation logic if needed
        return f"https://img.shields.io/endpoint?url=<YOUR_BADGE_URL>"

    def write_badge_json(self, badge: Dict[str, Any], output_path: str) -> None:
        path = Path(output_path)
        path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, 'w') as f:
            json.dump(badge, f, indent=2)
