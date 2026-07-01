import csv
from datetime import datetime
from pathlib import Path


class HistoryService:
    def __init__(self, history_csv: Path):
        self.history_csv = Path(history_csv)
        self.history_csv.parent.mkdir(parents=True, exist_ok=True)

    def save_analysis(self, data: dict):
        summary = data.get("readiness_summary", {})
        assessment = data.get("readiness_assessment", {})
        metrics = assessment.get("readiness_metrics", {})
        top_risks = summary.get("top_risks", [])
        top = top_risks[0] if top_risks else {}

        fieldnames = [
            "timestamp","session_id","client","file","score","status","decision",
            "critical_count","warning_count","info_count",
            "top_risk","top_risk_title","top_risk_severity",
            "analysis_duration_seconds","feedback_score","feedback_comment",
        ]

        file_exists = self.history_csv.exists()

        with self.history_csv.open("a", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            if not file_exists:
                writer.writeheader()

            writer.writerow({
                "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "session_id": data.get("session_id"),
                "client": data.get("client"),
                "file": data.get("file"),
                "score": summary.get("score"),
                "status": summary.get("status"),
                "decision": summary.get("decision"),
                "critical_count": metrics.get("critical_count", 0),
                "warning_count": metrics.get("warning_count", 0),
                "info_count": metrics.get("info_count", 0),
                "top_risk": top.get("check", ""),
                "top_risk_title": top.get("title") or top.get("check", ""),
                "top_risk_severity": top.get("business_severity") or top.get("severity") or "",
                "analysis_duration_seconds": data.get("analysis_duration_seconds", ""),
                "feedback_score": "",
                "feedback_comment": "",
            })

    def update_feedback(self, session_id: str, feedback_score: str, feedback_comment: str) -> bool:
        if not self.history_csv.exists():
            return False

        rows = []
        updated = False

        with self.history_csv.open("r", newline="", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            fieldnames = reader.fieldnames
            for row in reader:
                if row.get("session_id") == session_id:
                    row["feedback_score"] = feedback_score
                    row["feedback_comment"] = feedback_comment
                    updated = True
                rows.append(row)

        if not updated:
            return False

        with self.history_csv.open("w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(rows)

        return True
