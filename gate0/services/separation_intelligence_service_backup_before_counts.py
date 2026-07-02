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
        raw = str(name).strip()
        n = self.normalize(raw)

        if n in self.PROCESS:
            return "Process"

        if any(x in n for x in ["white", "blanco", "opaque"]):
            return "Blanco"

        if any(x in n for x in ["varnish", "barniz", "laca", "coating"]):
            return "Barniz"

        if any(x in n for x in ["plano", "dieline", "troquel", "cut", "cutter", "knife"]):
            return "Plano"

        if any(x in n for x in ["register", "registration", "fotocell", "fotocelula", "mark"]):
            return "Technical"

        return "Spot"

    def is_generic_name(self, name):
        n = str(name).strip().lower()
        return bool(re.match(r"^(spot|color|tinta|separation|sep)[\s_-]*\d+$", n))

    def build_summary(self, separations):
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

        return {
            "total": len(items),
            "items": items,
            "counts": counts,
            "warnings": warnings,
            "process_detected": process_detected,
            "process_confirmed": len(process_detected) > 0,
        }
