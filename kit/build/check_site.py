#!/usr/bin/env python3
"""Compatibility entrypoint for the current full-site contract checker."""
from pathlib import Path
import sys
from check_current import validate
validate(Path(sys.argv[1]) if len(sys.argv)>1 else Path(__file__).resolve().parent.parent/'site/public')
