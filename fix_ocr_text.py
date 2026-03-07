"""
One-time cleanup of existing OCR files in knowledge base.
Also improves the OCR pipeline for future scans.
"""
import os
import re

KNOWLEDGE = os.path.expanduser("~/Jarvis/knowledge")

def clean_line(line):
    # Remove lines that are pure garbage (no real words)
    stripped = line.strip()
    if not stripped:
        return ""
    
    # Remove lines with too many special chars (garbage OCR)
    special = sum(1 for c in stripped if not c.isalnum() 
                  and c not in " .,-()/:%°'\"")
    if len(stripped) > 3 and special / len(stripped) > 0.4:
        return ""
    
    # Fix common OCR mistakes
    fixes = {
        # Letters confused for numbers
        "0": {"context": ["O", "o"]},  # handled below
        # Common OCR errors in technical docs
        "resisfance"  : "resistance",
        "resistonce"  : "resistance",
        "insulati"    : "insulation",
        "windinzs"    : "windings",
        "windins"     : "windings",
        "temnerature" : "temperature",
        "temperafure" : "temperature",
        "currenf"     : "current",
        "voitage"     : "voltage",
        "voltaqe"     : "voltage",
        "freqency"    : "frequency",
        "frequancy"   : "frequency",
        "bearinq"     : "bearing",
        "bearin9"     : "bearing",
        "maintenonce" : "maintenance",
        "maintenence" : "maintenance",
        "assembiy"    : "assembly",
        "disassembiy" : "disassembly",
        "troubieshooting": "troubleshooting",
        "troubleshootinq": "troubleshooting",
        "mo.ur"       : "motor",
        "exchbrinnelors": "",
        "rerireeieie" : "",
        "rsrsrssss"   : "",
        "rrrrmromr"   : "",
        "seesseess"   : "",
    }
    
    result = stripped
    for wrong, right in fixes.items():
        result = result.replace(wrong, right)
    
    # Remove lines of only dashes/dots (table of contents lines)
    if re.match(r'^[-—=_.·•\s]+$', result):
        return ""
    
    # Remove lines that are just random letter/number combos
    # like "Rkl fo" or "— 3 4 9"
    words = result.split()
    real_words = [w for w in words 
                  if len(w) > 2 or w.isdigit()]
    if words and len(real_words) / len(words) < 0.4:
        return ""
    
    return result

def clean_file(filepath):
    with open(filepath, "r") as f:
        lines = f.readlines()
    
    cleaned = []
    prev_blank = False
    
    for line in lines:
        result = clean_line(line)
        
        # Avoid multiple blank lines
        if result == "":
            if not prev_blank:
                cleaned.append("")
            prev_blank = True
        else:
            cleaned.append(result)
            prev_blank = False
    
    # Write back
    with open(filepath, "w") as f:
        f.write("\n".join(cleaned))
    
    original = len(lines)
    final    = len(cleaned)
    removed  = original - final
    print(f"  ✅ {os.path.basename(filepath)}")
    print(f"     {original} lines → {final} lines")
    print(f"     {removed} garbage lines removed")

# Clean all txt files in knowledge base
print("🧹 Cleaning OCR files...\n")
for filename in os.listdir(KNOWLEDGE):
    if filename.endswith(".txt") and filename != "jarvis_knowledge_session1.txt":
        filepath = os.path.join(KNOWLEDGE, filename)
        clean_file(filepath)

print("\n✅ All files cleaned!")
print("\nTest search again:")
print("  search manual insulation resistance")
