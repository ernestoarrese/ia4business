import shutil
import zipfile
from pathlib import Path


class ZIPInventoryService:
    ANALYZABLE_EXTENSIONS = {".pdf", ".ai"}
    IMAGE_EXTENSIONS = {".psd", ".tif", ".tiff", ".jpg", ".jpeg", ".png"}
    FONT_EXTENSIONS = {".otf", ".ttf"}

    def safe_extract_zip(self, zip_path: Path, extract_dir: Path):
        extract_dir = Path(extract_dir)
        extract_dir.mkdir(parents=True, exist_ok=True)

        with zipfile.ZipFile(zip_path, "r") as z:
            for member in z.infolist():
                member_path = Path(member.filename)

                if member.is_dir():
                    continue

                if member_path.is_absolute() or ".." in member_path.parts:
                    continue

                target = extract_dir / member.filename
                target.parent.mkdir(parents=True, exist_ok=True)

                with z.open(member) as src, target.open("wb") as dst:
                    shutil.copyfileobj(src, dst)

    def scan_folder(self, folder: Path) -> dict:
        folder = Path(folder)

        analyzable = []
        images = []
        fonts = []
        others = []

        for path in folder.rglob("*"):
            if not path.is_file():
                continue

            suffix = path.suffix.lower()

            if "__MACOSX" in path.parts:
                continue

            if path.name.startswith("._") or path.name == ".DS_Store":
                continue

            if path.stat().st_size == 0:
                continue

            item = {
                "name": path.name,
                "relative_path": str(path.relative_to(folder)),
                "size_mb": round(path.stat().st_size / (1024 * 1024), 2),
                "extension": suffix,
            }

            if suffix in self.ANALYZABLE_EXTENSIONS:
                analyzable.append(item)
            elif suffix in self.IMAGE_EXTENSIONS:
                images.append(item)
            elif suffix in self.FONT_EXTENSIONS:
                fonts.append(item)
            else:
                others.append(item)

        return {
            "analyzable": sorted(analyzable, key=lambda x: x["relative_path"].lower()),
            "images": sorted(images, key=lambda x: x["relative_path"].lower()),
            "fonts": sorted(fonts, key=lambda x: x["relative_path"].lower()),
            "others": sorted(others, key=lambda x: x["relative_path"].lower()),
        }

    def possible_duplicate_note(self, analyzable: list[dict]) -> str:
        stems = {}

        for item in analyzable:
            stem = Path(item["name"]).stem.lower()
            stems.setdefault(stem, []).append(item["name"])

        duplicates = [names for names in stems.values() if len(names) > 1]

        if not duplicates:
            return ""

        return "Hay archivos con nombres similares. Pueden corresponder al mismo diseño; selecciona solo la versión que deseas analizar."
