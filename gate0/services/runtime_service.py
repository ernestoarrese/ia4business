import time
from pathlib import Path


class RuntimeService:
    def __init__(self, uploads_dir: Path, reports_dir: Path, temp_dir: Path, ttl_seconds: int = 1800):
        self.uploads_dir = Path(uploads_dir)
        self.reports_dir = Path(reports_dir)
        self.temp_dir = Path(temp_dir)
        self.ttl_seconds = ttl_seconds

        self.uploads_dir.mkdir(parents=True, exist_ok=True)
        self.reports_dir.mkdir(parents=True, exist_ok=True)
        self.temp_dir.mkdir(parents=True, exist_ok=True)

    def session_paths(self, session_id: str) -> dict:
        return {
            "pdf": self.uploads_dir / f"{session_id}.pdf",
            "json": self.reports_dir / f"{session_id}.json",
            "csv": self.reports_dir / f"{session_id}.csv",
        }

    def cleanup_old_files(self):
        now = time.time()

        for folder in [self.uploads_dir, self.reports_dir, self.temp_dir]:
            for path in folder.glob("*"):
                try:
                    if path.is_file() and now - path.stat().st_mtime > self.ttl_seconds:
                        path.unlink()
                except Exception:
                    pass
