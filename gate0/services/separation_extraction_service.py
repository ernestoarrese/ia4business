"""
Separation Extraction Service

Small shared adapter for extracting PDF separation names.

This intentionally delegates to the current mature Gate0 parser in
`gate0_check.detect_separations` so Compare Engine can use the same
source of detected separations without moving the full legacy engine yet.
"""

from pathlib import Path


def extract_pdf_separations(pdf_path):
    """
    Extract global separation names from a PDF-compatible file.

    Returns a sorted list of names such as:
    - PANTONE 485 C
    - White
    - Barniz
    """
    from gate0_check import detect_separations

    return detect_separations(str(Path(pdf_path)))
