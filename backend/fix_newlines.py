#!/usr/bin/env python3
"""
Script to fix file encodings and line endings
"""

import os
import sys
import codecs

def fix_file_encoding(filepath):
    """Convert a file to UTF-8 encoding"""
    print(f"Processing {filepath}...")
    
    # Try different encodings
    encodings = ['utf-16le', 'utf-16be', 'utf-8']
    content = None
    
    for encoding in encodings:
        try:
            with open(filepath, 'rb') as f:
                raw = f.read()
                # Check for BOM
                if raw.startswith(codecs.BOM_UTF16_LE):
                    encoding = 'utf-16le'
                elif raw.startswith(codecs.BOM_UTF16_BE):
                    encoding = 'utf-16be'
                elif raw.startswith(codecs.BOM_UTF8):
                    encoding = 'utf-8'
                
                content = raw.decode(encoding)
                print(f"Successfully read file as {encoding}")
                break
        except UnicodeDecodeError:
            continue
    
    if content is None:
        print("Error: Could not determine file encoding")
        return False
    
    # Write back as UTF-8
    try:
        with open(filepath, 'w', encoding='utf-8', newline='\n') as f:
            f.write(content)
        print("Successfully converted to UTF-8")
        return True
    except Exception as e:
        print(f"Error writing file: {e}")
        return False

def main():
    if len(sys.argv) < 2:
        print("Usage: python fix_newlines.py <file>")
        sys.exit(1)
    
    filepath = sys.argv[1]
    if not os.path.exists(filepath):
        print(f"Error: File {filepath} not found")
        sys.exit(1)
    
    success = fix_file_encoding(filepath)
    if success:
        print("File converted successfully")
    else:
        print("Failed to convert file")
        sys.exit(1)

if __name__ == '__main__':
    main() 