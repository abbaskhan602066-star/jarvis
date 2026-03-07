"""
Electric Manuals Batch Processor
Processes all PDFs in 3) ELECTRIC PART folder
Skips already processed files automatically
CPU limited and temperature monitored
"""
import os
import subprocess
import glob
import time
import json
from datetime import datetime

# ── SETTINGS ──────────────────────────────────
SOURCE_DIR = os.path.join(
    os.path.expanduser("~"),
    "storage", "downloads", "3) ELECTRIC PART"
)
KNOWLEDGE  = os.path.join(
    os.path.expanduser("~"),
    "Jarvis", "knowledge", "electric"
)
LOGS       = os.path.join(
    os.path.expanduser("~"),
    "Jarvis", "jarvis_logs"
)
STATE_FILE = os.path.join(LOGS, "electric_progress.json")

PAUSE_BETWEEN_PAGES   = 1
PAUSE_BETWEEN_PDFS    = 10
PAUSE_BETWEEN_BATCHES = 120
BATCH_SIZE            = 10
MAX_TEMP              = 40
CPU_NICE              = 19
# ──────────────────────────────────────────────

os.makedirs(KNOWLEDGE, exist_ok=True)
os.makedirs(LOGS,      exist_ok=True)

def get_temp():
    for path in [
        "/sys/class/thermal/thermal_zone0/temp",
        "/sys/class/thermal/thermal_zone1/temp",
    ]:
        try:
            raw = int(open(path).read().strip())
            t   = raw / 1000 if raw > 1000 else raw
            if 20 < t < 100:
                return t
        except:
            continue
    return 0.0

def cool_if_needed():
    t = get_temp()
    if t == 0 or t < MAX_TEMP:
        return
    print(f"\n  🌡️  {t:.1f}°C — cooling down {PAUSE_BETWEEN_BATCHES}s...")
    time.sleep(PAUSE_BETWEEN_BATCHES)
    print(f"  🌡️  Resumed. Temp now: {get_temp():.1f}°C")

def load_state():
    try:
        if os.path.exists(STATE_FILE):
            return json.load(open(STATE_FILE))
    except:
        pass
    return {"processed": [], "failed": [], "skipped": []}

def save_state(state):
    with open(STATE_FILE, "w") as f:
        json.dump(state, f, indent=2)

def find_pdfs():
    pdfs = []
    for dirpath, dirnames, filenames in os.walk(SOURCE_DIR):
        dirnames.sort()
        for filename in sorted(filenames):
            if filename.lower().endswith(".pdf"):
                pdfs.append({
                    "path"   : os.path.join(dirpath, filename),
                    "name"   : filename,
                    "folder" : os.path.relpath(dirpath, SOURCE_DIR)
                })
    return pdfs

def make_output_path(pdf):
    folder    = pdf["folder"].replace(os.sep,"_").replace(" ","_")
    name      = pdf["name"].replace(".pdf","")
    safe      = "".join(
        c if c.isalnum() or c in "-_" else "_"
        for c in (f"{folder}__{name}" if folder != "." else name)
    )
    subfolder = os.path.join(KNOWLEDGE, 
        "".join(c if c.isalnum() or c in "-_/" 
                else "_" for c in pdf["folder"])
    )
    os.makedirs(subfolder, exist_ok=True)
    return os.path.join(subfolder, f"{safe[:80]}.txt")

def process_one(pdf):
    out_file = make_output_path(pdf)

    # Skip if already done
    if os.path.exists(out_file):
        lines = open(out_file).read().count("\n")
        return "skip", 0, f"already done ({lines} lines)"

    tmp_dir = os.path.join(LOGS, "pdf_tmp")
    os.makedirs(tmp_dir, exist_ok=True)

    # Clean old temp files
    for f in glob.glob(os.path.join(tmp_dir, "page_*.png")):
        try: os.remove(f)
        except: pass

    try:
        # Get page count using pure Python (instant)
        num_pages = 0
        try:
            import re as _re
            with open(pdf['path'], 'rb') as _f:
                _data = _f.read()
            num_pages = len(_re.findall(rb'/Type\s*/Page[^s]', _data))
        except:
            pass
        if num_pages == 0:
            num_pages = 200

        if num_pages == 0:
            return "fail", 0, "no pages found"

        # Adaptive timeouts based on file size and page count
        file_size_mb = os.path.getsize(pdf["path"]) / (1024*1024)
        mb_per_page  = file_size_mb / max(num_pages, 1)

        # Adaptive timeout based on page count at 300 DPI
        # Small PDFs (few pages) = compressed = slow per page
        # Large PDFs (many pages) = usually faster per page
        # Base: 60s per page minimum, scale with file size
        secs_per_page    = max(3, int(file_size_mb / num_pages * 10))
        convert_timeout  = max(60,  int(secs_per_page * 1.5))
        tesseract_timeout= max(90,  int(secs_per_page * 2.0))

        # Hard cap
        convert_timeout  = min(convert_timeout,  300)
        tesseract_timeout= min(tesseract_timeout, 480)

        print(f"    📐 {num_pages}p, {file_size_mb:.1f}MB "
              f"({mb_per_page:.2f}MB/p) "
              f"→ convert:{convert_timeout}s "
              f"tesseract:{tesseract_timeout}s")

        # OCR one page at a time to save storage
        tmp_img = os.path.join(tmp_dir, "current_page.png")

        with open(out_file, "w") as out:
            out.write(f"FILE: {pdf['name']}\n")
            out.write(f"FOLDER: {pdf['folder']}\n")
            out.write(f"PAGES: {num_pages}\n")
            out.write(f"SIZE: {file_size_mb:.1f}MB\n")
            out.write(f"DATE: {datetime.now()}\n")
            out.write("="*50 + "\n\n")

            for page_num in range(num_pages):
                # Convert single page only
                r = subprocess.run(
                    ["nice", "-n", str(CPU_NICE),
                     "convert",
                     "-density", "300",
                     "-limit", "memory", "128MB",
                     "-limit", "map",    "256MB",
                     f"{pdf['path']}[{page_num}]",
                     "-sharpen", "0x1",      # helps blurry scans
                     "-contrast-stretch", "0.5%x0.5%",  # improves faded text
                     "-colorspace", "Gray",  # grayscale = faster OCR
                     tmp_img],
                    capture_output=True,
                    timeout=convert_timeout
                )

                if not os.path.exists(tmp_img):
                    continue

                out.write(f"\n--- PAGE {page_num+1} ---\n")
                r = subprocess.run(
                    ["nice", "-n", str(CPU_NICE),
                     "tesseract", tmp_img, "stdout",
                     "--psm", "1"],
                    capture_output=True,
                    text=True,
                    timeout=tesseract_timeout
                )
                out.write(r.stdout.strip() + "\n")

                # Delete immediately after OCR
                try: os.remove(tmp_img)
                except: pass

                time.sleep(PAUSE_BETWEEN_PAGES)

        num_pages = num_pages

        lines = open(out_file).read().count("\n")
        return "ok", num_pages, f"{num_pages} pages, {lines} lines"

    except subprocess.TimeoutExpired:
        return "fail", 0, "timeout"
    except Exception as e:
        return "fail", 0, str(e)
    finally:
        # Always cleanup temp
        for f in glob.glob(os.path.join(tmp_dir,"page_*.png")):
            try: os.remove(f)
            except: pass

def main():
    print(f"\n{'='*55}")
    print(f"⚡ ELECTRIC MANUALS PROCESSOR")
    print(f"{'='*55}")

    # Find all PDFs
    print("🔍 Scanning for PDFs...")
    all_pdfs = find_pdfs()
    print(f"   Found {len(all_pdfs)} PDFs\n")

    # Show folder breakdown
    folders = {}
    for p in all_pdfs:
        f = p["folder"]
        folders[f] = folders.get(f, 0) + 1
    print("📁 Folders:")
    for folder, count in sorted(folders.items()):
        print(f"   {folder}: {count} PDFs")

    # Load state
    state         = load_state()
    done_paths    = set(state["processed"])
    failed_paths  = set(state["failed"])
    remaining     = [
        p for p in all_pdfs
        if p["path"] not in done_paths
        and p["path"] not in failed_paths
    ]

    print(f"\n📊 Status:")
    print(f"   Total:     {len(all_pdfs)}")
    print(f"   Done:      {len(done_paths)}")
    print(f"   Failed:    {len(failed_paths)}")
    print(f"   Remaining: {len(remaining)}")

    if not remaining:
        print("\n🎉 All PDFs already processed!")
        return

    # Estimate
    secs  = len(remaining) * (20 * (4+PAUSE_BETWEEN_PAGES) + PAUSE_BETWEEN_PDFS)
    secs += (len(remaining) // BATCH_SIZE) * PAUSE_BETWEEN_BATCHES
    print(f"\n⏱️  Estimated: ~{secs//3600}h {(secs%3600)//60}m")
    temp = get_temp()
    if temp:
        print(f"🌡️  Temp now: {temp:.1f}°C")
    print(f"\n{'='*55}")
    print("Starting in 3 seconds... CTRL+C to cancel")
    print(f"{'='*55}\n")
    time.sleep(3)

    start = time.time()

    for i, pdf in enumerate(remaining, 1):
        # Batch rest
        if i > 1 and (i-1) % BATCH_SIZE == 0:
            batch_num = (i-1) // BATCH_SIZE
            elapsed   = int(time.time()-start)
            print(f"\n{'─'*55}")
            print(f"📦 Batch {batch_num} done | "
                  f"{i-1}/{len(remaining)} | "
                  f"{elapsed//3600}h{(elapsed%3600)//60}m elapsed")
            print(f"💤 Resting {PAUSE_BETWEEN_BATCHES}s...")
            print(f"{'─'*55}\n")
            time.sleep(PAUSE_BETWEEN_BATCHES)

        cool_if_needed()

        name = pdf["name"][:45]
        fold = pdf["folder"]
        print(f"[{i}/{len(remaining)}] {fold}/{name}")

        status, pages, msg = process_one(pdf)

        if status == "ok":
            state["processed"].append(pdf["path"])
            print(f"  ✅ {msg}")
        elif status == "skip":
            state["skipped"].append(pdf["path"])
            print(f"  ⏭️  {msg}")
        else:
            state["failed"].append(pdf["path"])
            print(f"  ❌ {msg}")

        save_state(state)

        if status != "skip":
            time.sleep(PAUSE_BETWEEN_PDFS)

    # Final report
    total = int(time.time()-start)
    print(f"\n{'='*55}")
    print(f"🎉 COMPLETE!")
    print(f"   Time:      {total//3600}h {(total%3600)//60}m")
    print(f"   Processed: {len(state['processed'])}")
    print(f"   Skipped:   {len(state['skipped'])}")
    print(f"   Failed:    {len(state['failed'])}")
    if state["failed"]:
        print(f"\n❌ Failed PDFs:")
        for f in state["failed"]:
            print(f"   {os.path.basename(f)}")
    print(f"\nSearch your manuals:")
    print(f"  search manual <keyword>")
    print(f"{'='*55}\n")

if __name__ == "__main__":
    main()
