import re


class SeparationIntelligenceService:
    """
    Official separation classification service for Gate0.

    Contract:
    - Process / Spot / Blanco / Barniz count as printable/operative.
    - Plano / Technical do not count as printable/operative.
    - Optional usage_by_name can downgrade a separation to Technical
      when its usage is confirmed to be outside the relevant printable area.
    """

    PROCESS = {
        "c": "C",
        "m": "M",
        "y": "Y",
        "k": "K",
        "cyan": "C",
        "magenta": "M",
        "yellow": "Y",
        "black": "K",
        "process cyan": "C",
        "process magenta": "M",
        "process yellow": "Y",
        "process black": "K",
    }

    PRINTABLE_TYPES = {"Process", "Spot", "Blanco", "Barniz"}
    NON_PRINTABLE_TYPES = {"Plano", "Technical"}

    def normalize(self, name):
        return re.sub(r"\s+", " ", str(name or "").strip().lower())

    def compact(self, name):
        return re.sub(r"[^a-z0-9]", "", self.normalize(name))

    def classify(self, name):
        n = self.normalize(name)
        c = self.compact(name)

        if not n:
            return "Technical"

        # PDF / separation special values.
        if n == "all":
            return "Technical"

        # Template/process-control separations used as plan references.
        if c in {"cperu", "mperu", "yperu", "kperu"}:
            return "Plano"

        # Strong non-printable/plan terms win over ink terms.
        plano_terms = [
            "plano", "dieline", "die line", "troquel", "cut", "cutter", "knife",
            "fold", "crease", "score", "guide", "guia", "guía"
        ]
        if any(term in n for term in plano_terms):
            return "Plano"

        technical_terms = [
            "technical", "technical drawing", "technical information",
            "drawing", "mechanical", "mechanical artwork",
            "dimensions", "dimension",
            "sustrato", "substrato", "substrate",
            "material", "materials", "materiales",
            "texto", "text",
            "reference", "referencia", "info", "legend", "notes", "nota"
        ]
        if any(term in n for term in technical_terms):
            return "Technical"

        # Printable special separations.
        if any(term in n for term in ["white", "blanco", "opaque white", "opaque", "wht", "ink white"]):
            return "Blanco"

        if any(term in n for term in ["varnish", "barniz", "laca", "lacquer", "coating", "gloss", "matte"]):
            return "Barniz"

        # Pure process names only. C PERU etc. were already excluded.
        if n in self.PROCESS:
            return "Process"

        return "Spot"

    def is_generic_name(self, name):
        n = self.normalize(name)
        return bool(re.match(r"^(spot|color|tinta|separation|sep)[\s_-]*\d+$", n))

    def is_printable_type(self, sep_type):
        return sep_type in self.PRINTABLE_TYPES

    def usage_key(self, name):
        return self.compact(name)

    def get_usage(self, name, usage_by_name):
        if not usage_by_name:
            return {}

        candidates = [
            str(name or ""),
            self.normalize(name),
            self.compact(name),
        ]

        for key in candidates:
            if key in usage_by_name:
                return usage_by_name.get(key) or {}

        return {}

    def apply_usage_context(self, item, usage):
        """
        Optional location-based classification.

        Expected usage keys are intentionally simple so Sprint 20B can populate them later:
        - has_confirmed_trimbox: bool
        - has_confirmed_bleedbox: bool
        - inside_trimbox_percent: number
        - inside_bleedbox_percent: number
        - outside_trimbox_percent: number
        - outside_bleedbox_percent: number
        - usage_source: str
        """
        if not usage:
            item["usage_status"] = "NO_USAGE_DATA"
            item["usage_confidence"] = "LOW"
            return item

        item["usage"] = usage
        item["usage_source"] = usage.get("usage_source") or "UNKNOWN"

        has_trimbox = bool(usage.get("has_confirmed_trimbox"))
        has_bleedbox = bool(usage.get("has_confirmed_bleedbox"))

        inside_trim = float(usage.get("inside_trimbox_percent") or 0)
        inside_bleed = float(usage.get("inside_bleedbox_percent") or 0)
        outside_trim = float(usage.get("outside_trimbox_percent") or 0)
        outside_bleed = float(usage.get("outside_bleedbox_percent") or 0)

        # If BleedBox exists, outside TrimBox is still printable when inside BleedBox.
        if has_bleedbox:
            if inside_bleed > 0 and outside_bleed < 99:
                item["usage_status"] = "PRINTABLE_IN_BLEED_OR_TRIM"
                item["usage_confidence"] = "MEDIUM"
                return item

            if outside_bleed >= 99 and item.get("is_printable"):
                item["original_type"] = item["type"]
                item["type"] = "Technical"
                item["is_printable"] = False
                item["classification_source"] = "LOCATION_CONFIRMED"
                item["usage_status"] = "NON_PRINTABLE_BY_LOCATION_CONFIRMED"
                item["usage_confidence"] = "HIGH"
                item["classification_note"] = "Separación presente solo fuera del BleedBox confirmado."
                return item

        # If only TrimBox exists, be conservative but allow downgrade when usage is fully outside.
        if has_trimbox:
            if inside_trim > 0:
                item["usage_status"] = "PRINTABLE_IN_TRIM"
                item["usage_confidence"] = "MEDIUM"
                return item

            if outside_trim >= 99 and item.get("is_printable"):
                item["original_type"] = item["type"]
                item["type"] = "Technical"
                item["is_printable"] = False
                item["classification_source"] = "LOCATION_CONFIRMED"
                item["usage_status"] = "NON_PRINTABLE_BY_LOCATION_CONFIRMED"
                item["usage_confidence"] = "MEDIUM"
                item["classification_note"] = "Separación presente solo fuera del TrimBox confirmado y sin BleedBox útil."
                return item

        item["usage_status"] = "USAGE_DATA_INCONCLUSIVE"
        item["usage_confidence"] = "LOW"
        return item

    def build_summary(
        self,
        separations,
        printable_separation_count=None,
        process_count=None,
        process_count_source=None,
        usage_by_name=None,
    ):
        separations = separations or []
        items = []

        for sep in separations:
            name = str(sep)
            sep_type = self.classify(name)
            item = {
                "name": name,
                "normalized_name": self.normalize(name),
                "compact_name": self.compact(name),
                "type": sep_type,
                "original_type": sep_type,
                "is_printable": self.is_printable_type(sep_type),
                "classification_source": "NAME",
                "is_generic": self.is_generic_name(name),
            }

            usage = self.get_usage(name, usage_by_name)
            item = self.apply_usage_context(item, usage)
            items.append(item)

        detected_total = len(items)

        process_detected = [i["name"] for i in items if i["type"] == "Process"]
        spot_detected = [i["name"] for i in items if i["type"] == "Spot"]
        white_detected = [i["name"] for i in items if i["type"] == "Blanco"]
        varnish_detected = [i["name"] for i in items if i["type"] == "Barniz"]
        plano_detected = [i["name"] for i in items if i["type"] == "Plano"]
        technical_detected = [i["name"] for i in items if i["type"] == "Technical"]

        printable_items = [i for i in items if i.get("is_printable")]
        printable_names = [i["name"] for i in printable_items]

        if process_count is None:
            process_count = len(process_detected)

        if process_count_source is None:
            process_count_source = (
                "SEPARATION_SUMMARY_CLASSIFICATION"
                if process_detected
                else "NO_PROCESS_COLORS_DETECTED"
            )

        calculated_operational_total = len(printable_items)
        operational_total = (
            calculated_operational_total
            if printable_separation_count is None
            else printable_separation_count
        )

        return {
            "total": detected_total,
            "detected_total": detected_total,
            "operational_total": operational_total,
            "calculated_operational_total": calculated_operational_total,
            "process_count": process_count,
            "process_count_source": process_count_source,
            "items": items,
            "printable_items": printable_items,
            "printable_names": printable_names,
            "process_detected": process_detected,
            "process_confirmed": len(process_detected) > 0,
            "spot_detected": spot_detected,
            "white_detected": white_detected,
            "varnish_detected": varnish_detected,
            "plano_detected": plano_detected,
            "technical_detected": technical_detected,
            "spot_count": len(spot_detected),
            "white_count": len(white_detected),
            "varnish_count": len(varnish_detected),
            "plano_count": len(plano_detected),
            "technical_count": len(technical_detected),
            "printable_spot_like_count": len(spot_detected) + len(white_detected) + len(varnish_detected),
            "non_printable_count": len(plano_detected) + len(technical_detected),
        }
