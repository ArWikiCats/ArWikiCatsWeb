# -*- coding: utf-8 -*-
"""
Pytest configuration for the tests directory.
"""
import sys
from pathlib import Path

src_path = Path(__file__).parent.parent
sys.path.insert(0, str(src_path))
