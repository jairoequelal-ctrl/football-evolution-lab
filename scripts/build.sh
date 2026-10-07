#!/usr/bin/env bash
set -euo pipefail
python -m football_lab.pipeline "$@"
python -m football_lab.analysis
python scripts/export_page.py
python scripts/publication_cards.py
python scripts/validate_data.py
