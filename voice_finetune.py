"""
Voice finetune system for Filipino accent corrections.
Learns from user corrections over time.
"""
import json, os, re

FINETUNE_FILE = os.path.expanduser("~/Jarvis/knowledge/voice_corrections.json")

# Pre-loaded Filipino English accent patterns
# Format: "what STT hears" -> "what you actually said"
DEFAULT_CORRECTIONS = {
    # Common Filipino pronunciation patterns
    "moon":         "MΩ",      # mega ohm
    "meg":          "MΩ",
    "megaohm":      "MΩ",
    "induration":   "insulation",
    "insolation":   "insulation",
    "installation": "insulation",
    "insulation resistance": "insulation resistance",
    "ohm":          "Ω",
    "resistance":   "resistance",
    "jenerator":    "generator",
    "jenset":       "genset",
    "compressa":    "compressor",
    "purp":         "pump",
    "pomp":         "pump",
    "bawlb":        "valve",
    "walb":         "valve",
    "balb":         "valve",
    "switsbord":    "switchboard",
    "switchbord":   "switchboard",
    "alternaytor":  "alternator",
    "oltayneytor":  "alternator",
    "transpormer":  "transformer",
    "transphormer": "transformer",
    "brikker":      "breaker",
    "kontaktor":    "contactor",
    "kontactor":    "contactor",
    "serkwit":      "circuit",
    "sirkwit":      "circuit",
    "kaybol":       "cable",
    "kabol":        "cable",
    "bayring":      "bearing",
    "bering":       "bearing",
    "winding":      "winding",
    "windings":     "windings",
    "kargo":        "cargo",
    "sentripugal":  "centrifugal",
    "sentripogal":  "centrifugal",
    "inyeksyon":    "injection",
    "incheksyon":   "injection",
    "pressyor":     "pressure",
    "presar":       "pressure",
    "temperachur":  "temperature",
    "temperatur":   "temperature",
    "owtput":       "output",
    "inpoot":       "input",
    "gripo":        "valve",
    "ekwipment":    "equipment",
    "ekwipman":     "equipment",
    "sked":         "schedule",
    "skedul":       "schedule",
    "mantinans":    "maintenance",
    "mantenance":   "maintenance",
    "mayntenance":  "maintenance",
    "trowbol":      "trouble",
    "trobul":       "trouble",
    "troblesut":    "troubleshoot",
    "alarms":       "alarms",
    "alarum":       "alarm",
    "listo":        "list",
    "listahan":     "list",
    "manual":       "manual",
    "manywal":      "manual",
    "e302":         "E-302",
    "e 302":        "E-302",
    "e301":         "E-301",
    "e303":         "E-303",
    "e304":         "E-304",

    # ─── HILIGAYNON / ILONGGO ACCENT PATTERNS ───────────
    # P and F confusion (Hiligaynon has no F sound)
    "pire":         "fire",
    "pault":        "fault",
    "pans":         "fans",
    "pan":          "fan",
    "plow":         "flow",
    "plange":       "flange",
    "plush":        "flush",
    "plex":         "flex",
    "prequency":    "frequency",
    "prequensya":   "frequency",
    "puel":         "fuel",
    "pilter":       "filter",
    "pilters":      "filters",
    "pinish":       "finish",
    "pip":          "pipe",
    "pipes":        "pipes",
    "piping":       "piping",

    # V and B confusion
    "balbe":        "valve",
    "balb":         "valve",
    "bolts":        "volts",
    "bolt":         "volt",
    "boltage":      "voltage",
    "bolta":        "volta",
    "bariable":     "variable",
    "bentilasyon":  "ventilation",
    "bentilation":  "ventilation",
    "bentilaston":  "ventilation",

    # R rolling / substitution
    "lun":          "run",
    "lunning":      "running",
    "lunhours":     "running hours",
    "lun aurs":     "running hours",
    "lon":          "run",
    "lonning":      "running",

    # Dropped or added H
    "awa":          "power",
    "awers":        "hours",
    "aur":          "hour",
    "aurs":         "hours",
    "awa supply":   "power supply",
    "ours":         "hours",

    # TH → D or T substitution
    "dree":         "three",
    "dat":          "that",
    "dis":          "this",
    "de":           "the",
    "dem":          "them",
    "dey":          "they",
    "troot":        "through",
    "tru":          "through",
    "trough":       "through",

    # I and E confusion
    "isterday":     "yesterday",
    "ensulation":   "insulation",
    "elictric":     "electric",
    "iliktrik":     "electric",
    "ilektrik":     "electric",
    "inching":      "engine",
    "inchine":      "engine",
    "injin":        "engine",
    "injen":        "engine",

    # Word endings dropped
    "reportin":     "reporting",
    "workin":       "working",
    "checkin":      "checking",
    "runnin":       "running",
    "testin":       "testing",
    "startin":      "starting",
    "stoppin":      "stopping",

    # Maritime specific Hiligaynon pronunciation
    "dyesel":       "diesel",
    "disel":        "diesel",
    "dizel":        "diesel",
    "diyesel":      "diesel",
    "kuldogwater":  "cooling water",
    "kulling":      "cooling",
    "kulwater":     "cooling water",
    "lub oil":      "lube oil",
    "luboil":       "lube oil",
    "lyub":         "lube",
    "lyubrikasyon": "lubrication",
    "lubrikasyon":  "lubrication",
    "pompa":        "pump",
    "pompang":      "pumping",
    "gripo":        "valve",
    "griyo":        "valve",
    "bayb":         "pipe",
    "tubo":         "pipe",
    "tubong":       "piping",
    "koryente":     "electricity",
    "koriyente":    "electricity",
    "kuryente":     "electricity",
    "motor motor":  "motor",
    "manekin":      "maneuver",
    "maniobra":     "maneuver",

    # Numbers and units
    "wan":          "one",
    "tu":           "two",
    "tri":          "three",
    "por":          "four",
    "payb":         "five",
    "seks":         "six",
    "sebentey":     "seventy",
    "ertey":        "thirty",
    "porty":        "forty",
    "paypty":       "fifty",
    "sikstey":      "sixty",
    "eytey":        "eighty",
    "nayntey":      "ninety",
    "megaom":       "megaohm",
    "megaoms":      "megaohms",
    "megom":        "megaohm",
    "kilowat":      "kilowatt",
    "kilowat":      "kilowatt",
    "ampir":        "ampere",
    "amper":        "ampere",
    "ampers":       "amperes",
    "hertz":        "hertz",
    "herts":        "hertz",
    "hurs":         "hertz",

    # Common ship phrases
    "stand bay":    "standby",
    "stenbay":      "standby",
    "stanbay":      "standby",
    "de watch":     "the watch",
    "on watch":     "on watch",
    "ow watch":     "off watch",
    "morning raunds": "morning rounds",
    "rawnds":       "rounds",
    "rawnd":        "round",
    "checap":       "checkup",
    "chek ap":      "checkup",
    "dily report":  "daily report",
    "dayly":        "daily",
    "repart":       "report",
    "riport":       "report",
    "de report":    "the report",
    "hand ober":    "handover",
    "handober":     "handover",
    "log bot":      "logbook",
    "logbot":       "logbook",
    "defect":       "defect",
    "dipek":        "defect",
    "dipects":      "defects",
    "ripair":       "repair",
    "ripayr":       "repair",

    # ETO specific terms
    "jayro":        "gyro",
    "jairo":        "gyro",
    "radar":        "radar",
    "eychef":       "HF",
    "bihef":        "VHF",
    "biyep":        "VHF",
    "biyetep":      "VHF",
    "uhep":         "UHF",
    "gipies":       "GPS",
    "echnawas":     "HNWAS",
    "binas":        "BNWAS",
    "ssas":         "SSAS",
    "arpa":         "ARPA",
    "ecdis":        "ECDIS",
    "ekdis":        "ECDIS",
    "gmdss":        "GMDSS",
    "jimdis":       "GMDSS",
    "inmarsat":     "INMARSAT",
    "inmarsad":     "INMARSAT",
    "nabtek":       "NAVTEX",
    "nabteks":      "NAVTEX",
    "epirb":        "EPIRB",
    "iperb":        "EPIRB",
    "sart":         "SART",
    "satcom":       "SATCOM",
    "satcoms":      "SATCOM",
    "e312":         "E-312",
    "e317":         "E-317",
}

def load_corrections():
    """Load corrections from file, merge with defaults."""
    corrections = dict(DEFAULT_CORRECTIONS)
    try:
        if os.path.exists(FINETUNE_FILE):
            user = json.load(open(FINETUNE_FILE))
            corrections.update(user)  # user corrections override defaults
    except:
        pass
    return corrections

def save_correction(wrong, correct):
    """Save a new user correction."""
    try:
        data = {}
        if os.path.exists(FINETUNE_FILE):
            data = json.load(open(FINETUNE_FILE))
        data[wrong.lower().strip()] = correct.strip()
        json.dump(data, open(FINETUNE_FILE, "w"), indent=2)
        return True
    except:
        return False

def apply_finetune(text):
    """Apply all corrections to transcribed text."""
    if not text:
        return text
    corrections = load_corrections()
    result = text.lower()

    # Sort by length (longest first) to avoid partial replacements
    for wrong, correct in sorted(corrections.items(),
                                  key=lambda x: len(x[0]),
                                  reverse=True):
        pattern = r'\b' + re.escape(wrong) + r'\b'
        result = re.sub(pattern, correct, result,
                       flags=re.IGNORECASE)
    return result

def list_corrections():
    """Return all corrections as formatted string."""
    corrections = load_corrections()
    lines = ["=== Voice Corrections ==="]
    user_file = {}
    try:
        if os.path.exists(FINETUNE_FILE):
            user_file = json.load(open(FINETUNE_FILE))
    except:
        pass
    for wrong, correct in sorted(corrections.items()):
        tag = " [custom]" if wrong in user_file else ""
        lines.append(f"  '{wrong}' → '{correct}'{tag}")
    return "\n".join(lines)

if __name__ == "__main__":
    print(list_corrections())
