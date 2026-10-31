#!/usr/bin/env python3
"""Engine script to replace pump.co.id with pumps.id across repository files."""

import os
import re
import sys
from pathlib import Path

HEAD_BLOCK = """<!-- START of .head content -->
<script src="https://cekkode.github.io/js/wa-enricher.js"></script>
<script src="https://cekkode.github.io/js/formsender.js"></script>
<!-- END of .head content -->"""

TEXT_EXTENSIONS = {
    ".html", ".xml", ".txt", ".json", ".js", ".css", ".md", ".yml", ".yaml", ".map", ".rss"
}

EXCLUDED_DIRS = {".git"}

def replace_domain_in_text(text: str) -> tuple[str, int]:
    count = 0
    
    # 1. Exact uppercase
    if "PUMP.CO.ID" in text:
        c = text.count("PUMP.CO.ID")
        text = text.replace("PUMP.CO.ID", "PUMPS.ID")
        count += c
        
    # 2. Exact Titlecase
    if "Pump.co.id" in text:
        c = text.count("Pump.co.id")
        text = text.replace("Pump.co.id", "Pumps.id")
        count += c
        
    # 3. Exact lowercase
    if "pump.co.id" in text:
        c = text.count("pump.co.id")
        text = text.replace("pump.co.id", "pumps.id")
        count += c
        
    # 4. Any other case variant via regex
    def match_sub(m):
        nonlocal count
        count += 1
        val = m.group(0)
        if val.isupper():
            return "PUMPS.ID"
        elif val[0].isupper():
            return "Pumps.id"
        else:
            return "pumps.id"
            
    text, n = re.subn(r"(?i)pump\.co\.id", match_sub, text)
    return text, count

def ensure_head_block(text: str) -> tuple[str, bool]:
    if "wa-enricher.js" in text:
        return text, False
    # Find </head>
    m = re.search(r"</head\s*>", text, flags=re.IGNORECASE)
    if not m:
        return text, False
    idx = m.start()
    prefix = text[:idx]
    style = "\n" if "\r\n" not in text else "\r\n"
    leading = "" if (prefix.endswith("\n") or prefix.endswith("\r\n")) else style
    block = HEAD_BLOCK.replace("\n", style)
    updated = prefix + leading + block + style + text[idx:]
    return updated, True

def main():
    root = Path(__file__).resolve().parents[2]
    print(f"Scanning repository at: {root}")
    
    total_files = 0
    modified_files = 0
    total_domain_replacements = 0
    head_injections = 0
    
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = [d for d in dirnames if d not in EXCLUDED_DIRS]
        for name in filenames:
            path = Path(dirpath) / name
            ext = path.suffix.lower()
            if ext not in TEXT_EXTENSIONS and name not in {"CNAME", "robots.txt", ".clients"}:
                continue
                
            total_files += 1
            try:
                raw = path.read_bytes()
                has_bom = raw.startswith(b"\xef\xbb\xbf")
                text = raw[3:].decode("utf-8") if has_bom else raw.decode("utf-8")
            except Exception:
                continue
                
            updated, c = replace_domain_in_text(text)
            was_head_injected = False
            if ext == ".html":
                updated, was_head_injected = ensure_head_block(updated)
                if was_head_injected:
                    head_injections += 1
                    
            if c > 0 or was_head_injected:
                total_domain_replacements += c
                modified_files += 1
                out_raw = (b"\xef\xbb\xbf" if has_bom else b"") + updated.encode("utf-8")
                path.write_bytes(out_raw)
                
    print(f"Scan complete:")
    print(f"  Scanned text files:    {total_files}")
    print(f"  Modified files:        {modified_files}")
    print(f"  Domain replacements:   {total_domain_replacements}")
    print(f"  Head script injections:{head_injections}")

if __name__ == "__main__":
    main()
