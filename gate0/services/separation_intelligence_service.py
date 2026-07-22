import re


class SeparationIntelligenceService:
    PROCESS = {
        "cyan": "Cyan",
        "magenta": "Magenta",
        "yellow": "Yellow",
        "black": "Black",
        "c": "Cyan",
        "m": "Magenta",
        "y": "Yellow",
        "k": "Black",
    }

    def normalize(self, name):
        return re.sub(r"[^a-z0-9]", "", str(name).lower())

    def classify(self, name):
        raw = str(name or "").strip()
        n = raw.lower()
        compact = n.replace(" ", "")

        if compact in {"cperu", "mperu", "yperu", "kperu"}:
            return "Plano"

        if compact in {"all"}:
            return "Technical"

        if any(x in n for x in [
            "plano", "dieline", "troquel", "cut", "cutter", "knife",
            "pie", "sustrato", "substrato", "substrate", "material", "materials", "materiales", "texto", "text",
            "dimensions", "dimension", "mechanical", "mechanical artwork",
            "technical drawing", "technical information"
        ]):
            return "Plano"

        if any(x in n for x in ["technical", "drawing"]):
            return "Technical"

        if any(x in n for x in ["white", "blanco"]):
            return "Blanco"

        if compact in {"cyan", "magenta", "yellow", "black", "c", "m", "y", "k"}:
            return "Process"

        return "Spot"

    def is_generic_name(self, name):
        n = str(name).strip().lower()
        return bool(re.match(r"^(spot|color|tinta|separation|sep)[\s_-]*\d+$", n))

    def build_summary(
        self,
        separations,
        printable_separation_count=None,
        process_count=None,
        process_count_source=None,
    ):
        separations = separations or []

        items = []
        normalized_seen = {}
        warnings = []

        for sep in separations:
            name = str(sep).strip()
            if not name:
                continue

            sep_type = self.classify(name)
            norm = self.normalize(name)

            item = {
                "name": name,
                "type": sep_type,
                "is_generic": self.is_generic_name(name),
            }

            items.append(item)
            normalized_seen.setdefault(norm, []).append(name)

            if item["is_generic"]:
                warnings.append({
                    "type": "GENERIC_NAME",
                    "message": f"Nombre genérico detectado: {name}",
                })

        for norm, names in normalized_seen.items():
            unique_names = sorted(set(names))
            if len(unique_names) > 1:
                warnings.append({
                    "type": "POSSIBLE_DUPLICATE",
                    "message": f"Posible duplicidad: {', '.join(unique_names)}",
                })

        counts = {}
        for item in items:
            counts[item["type"]] = counts.get(item["type"], 0) + 1

        process_detected = [i["name"] for i in items if i["type"] == "Process"]

        detected_total = len(items)
        operational_total = detected_total if printable_separation_count is None else printable_separation_count

        return {
            "total": detected_total,
            "detected_total": detected_total,
            "operational_total": operational_total,
            "process_count": process_count,
            "process_count_source": process_count_source,
            "items": items,
            "counts": counts,
            "warnings": warnings,
            "process_detected": process_detected,
            "process_confirmed": len(process_detected) > 0,
        }
