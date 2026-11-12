"""
History Service
Reads and serves saved scan reports from the reports directory.
"""

import json
import logging
import os
from typing import List, Dict, Optional, Any

logger = logging.getLogger(__name__)


class HistoryService:
    def __init__(self, reports_dir: Optional[str] = None):
        self.reports_dir = reports_dir or os.path.join(
            os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "reports"
        )
        os.makedirs(self.reports_dir, exist_ok=True)

    def list_history(self) -> List[Dict[str, Any]]:
        """
        Lists all saved JSON scan reports sorted by timestamp descending.
        """
        entries = []
        if not os.path.exists(self.reports_dir):
            return []

        for fname in os.listdir(self.reports_dir):
            if fname.endswith(".json"):
                fpath = os.path.join(self.reports_dir, fname)
                try:
                    with open(fpath, "r", encoding="utf-8") as f:
                        data = json.load(f)
                    entries.append({
                        "id": fname.replace(".json", ""),
                        "filename": fname,
                        "timestamp": data.get("timestamp", ""),
                        "interface": data.get("interface", {}).get("name") if data.get("interface") else None,
                        "subnet": data.get("interface", {}).get("network") if data.get("interface") else None,
                        "gateway": data.get("interface", {}).get("gateway") if data.get("interface") else None,
                        "results_count": data.get("results_count", 0),
                        "tplink_count": sum(1 for r in data.get("results", []) if r.get("is_tplink_candidate")),
                    })
                except Exception as e:
                    logger.debug(f"Failed to read report {fname}: {e}")

        # Sort by timestamp descending
        return sorted(entries, key=lambda x: x.get("timestamp", ""), reverse=True)

    def get_report(self, report_id: str) -> Optional[Dict[str, Any]]:
        """
        Retrieves full JSON report content by ID or filename.
        """
        filename = report_id if report_id.endswith(".json") else f"{report_id}.json"
        fpath = os.path.join(self.reports_dir, filename)

        if not os.path.exists(fpath):
            return None

        try:
            with open(fpath, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Error reading report {filename}: {e}")
            return None
