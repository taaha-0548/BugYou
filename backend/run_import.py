#!/usr/bin/env python3
"""
Direct import runner
"""

import os
import sys

# Add backend directory to path
sys.path.insert(0, os.path.dirname(__file__))

# Import and run
from import_sample_data import import_sequential_data

if __name__ == "__main__":
    import_sequential_data() 