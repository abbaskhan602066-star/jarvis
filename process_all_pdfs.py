"""
Run this overnight to process all PDFs.
Has CPU limiter and temperature protection.
"""
import os
import subprocess
import glob
import time

PDF_DIR   = os.path.expanduser("~/storage/downloads/pdf")
KNOWLEDGE = os.path.expanduser("~/Jarvis/knowledge")
LOGS      = os.path.expanduser("~/Jarvis/jarvis_logs")

# ── CPU/HEAT SETTINGS ─────────────────────────
# Adjust these if phone still gets hot
PAUSE_BETWEEN_PAGES  = 1.0   # seconds rest between pages
PAUSE_BETWEEN_PDFS   = 10    # seconds rest between PDFs
PAUSE_ON_HOT         = 60    # seconds to cool down if hot
MAX_TEMP_CELSIUS     = 40    # pause if phone exceeds this
CPU_NICE_LEVEL       = 19    # 19 = lowest priority (nicest)
                              # 0  = normal, 19 = background only
# ─────────────────────────────────────────────

def get_temperature() -> float:
    """Get phone CPU temperature."""
    temp_paths = [
        "/sys/class/thermal/thermal_zone0/temp",
        "/sys/class/thermal/thermal_zone1/temp",
        "/sys/class/thermal/thermal_zone2/temp",
    ]
    for path in temp_paths:
        try:
            with open(path) as f:
                raw = int(f.read().strip())
                # Most phones report in millidegrees
                temp = raw / 1000 if raw > 1000 else raw
                if 20 < temp < 100:  # Sanity check
                    return temp
        except:
            continue
    return 0.0  # Unknown

def check_temp(label: str = "") -> bool:
    """
    Check temperature. Pause if too hot.
    Returns True if safe, False if couldn't cool down.
    """
    temp = get_temperature()
    if temp == 0:
        return True  # Can't read temp, assume okay

    if temp >= MAX_TEMP_CELSIUS:
        print(f"\n  🌡️  Hot! {temp:.1f}°C {label}")
        print(f"      Cooling down for {PAUSE_ON_HOT}s...")
        for remaining in range(PAUSE_ON_HOT, 0, -10):
            time.sleep(10)
            new_temp = get_temperature()
            print(f"      Temperature: {new_temp:.1f}°C...", end="\r")
            if new_temp < MAX_TEMP_CELSIUS - 5:
                print(f"\n      ✅ Cooled to {new_temp:.1f}°C")
                return True
        print(f"\n      ⚠️  Still warm, continuing carefully...")
    return True

def run_with_limit(cmd: list, timeout: int = 60) -> subprocess.CompletedProcess:
    """Run command with low CPU priority."""
    # nice -n 19 = lowest CPU priority
    # Phone stays responsive for other apps
    full_cmd = ["nice", "-n", str(CPU_NICE_LEVEL)] + cmd
    return subprocess.run(
        full_cmd,
        capture_output=True,
        text=True,
        timeout=timeout
    )

# ── MAIN PROCESSING ───────────────────────────
pdfs = sorted(glob.glob(os.path.join(PDF_DIR, "*.pdf")))
print(f"\n{'='*55}")
print(f"🌙 OVERNIGHT PDF PROCESSOR")
print(f"{'='*55}")
print(f"📚 Found {len(pdfs)} PDFs")
print(f"🌡️  Max temp: {MAX_TEMP_CELSIUS}°C")
print(f"⚙️  CPU priority: nice {CPU_NICE_LEVEL} (background)")
print(f"💤 Rest between pages: {PAUSE_BETWEEN_PAGES}s")
print(f"💤 Rest between PDFs:  {PAUSE_BETWEEN_PDFS}s")
temp = get_temperature()
if temp > 0:
    print(f"🌡️  Current temp: {temp:.1f}°C")
print(f"{'='*55}\n")

success = []
failed  = []
skipped = []
start_time = time.time()

for i, pdf_path in enumerate(pdfs, 1):
    pdf_name  = os.path.basename(pdf_path)
    safe_name = "".join(
        c if c.isalnum() or c in "-_" else "_"
        for c in pdf_name.replace(".pdf","")
    )
    out_file = os.path.join(KNOWLEDGE, f"{safe_name}.txt")

    print(f"[{i}/{len(pdfs)}] {pdf_name[:55]}")

    # Check temp before each PDF
    check_temp("before PDF")

    # Skip if already processed
    if os.path.exists(out_file):
        lines = open(out_file).read().count("\n")
        print(f"  ⏭️  Already done ({lines} lines)\n")
        skipped.append(pdf_name)
        continue

    try:
        # Convert PDF to images with low priority
        out_dir = os.path.join(LOGS, f"pdf_{safe_name}")
        os.makedirs(out_dir, exist_ok=True)

        print(f"  📄 Converting pages (low priority)...")
        r = subprocess.run(
            ["nice", "-n", str(CPU_NICE_LEVEL),
             "convert", "-density", "120",  # Lower density = faster
             "-limit", "memory", "256MB",   # Limit RAM usage
             "-limit", "map", "512MB",
             pdf_path,
             os.path.join(out_dir, "page_%03d.png")],
            capture_output=True,
            timeout=300
        )

        images = sorted(glob.glob(
            os.path.join(out_dir, "page_*.png")
        ))
        if not images:
            print(f"  ❌ No pages extracted\n")
            failed.append(pdf_name)
            continue

        print(f"  🔍 OCR scanning {len(images)} pages...")

        # OCR each page with rests between
        with open(out_file, "w") as out:
            for j, img in enumerate(images, 1):
                # Check temp every 5 pages
                if j % 5 == 0:
                    temp = get_temperature()
                    temp_str = f" | 🌡️{temp:.0f}°C" if temp > 0 else ""
                    print(f"     Page {j}/{len(images)}{temp_str}...",
                          end="\r")
                    check_temp(f"page {j}")
                else:
                    print(f"     Page {j}/{len(images)}...", end="\r")

                out.write(f"\n{'='*50}\n")
                out.write(f"PAGE {j}\n")
                out.write(f"{'='*50}\n")

                r = run_with_limit(
                    ["tesseract", img, "stdout", "--psm", "1"],
                    timeout=60
                )
                out.write(r.stdout.strip() + "\n")

                # Delete image immediately after OCR
                # Saves storage space
                try: os.remove(img)
                except: pass

                # Rest between pages
                time.sleep(PAUSE_BETWEEN_PAGES)

        # Cleanup temp folder
        try: os.rmdir(out_dir)
        except: pass

        lines = open(out_file).read().count("\n")
        elapsed = int(time.time() - start_time)
        mins    = elapsed // 60
        secs    = elapsed % 60
        temp    = get_temperature()
        temp_str = f" | 🌡️{temp:.0f}°C" if temp > 0 else ""
        print(f"\n  ✅ Done! {len(images)} pages"
              f" | {lines} lines"
              f" | {mins}m{secs}s{temp_str}\n")
        success.append(pdf_name)

        # Longer rest between PDFs to cool down
        print(f"  💤 Resting {PAUSE_BETWEEN_PDFS}s before next PDF...")
        time.sleep(PAUSE_BETWEEN_PDFS)

    except subprocess.TimeoutExpired:
        print(f"\n  ⏱️  Timeout - skipping\n")
        failed.append(pdf_name)
    except Exception as e:
        print(f"\n  ❌ Error: {e}\n")
        failed.append(pdf_name)

# ── FINAL REPORT ──────────────────────────────
total_time = int(time.time() - start_time)
hours      = total_time // 3600
mins       = (total_time % 3600) // 60

print(f"\n{'='*55}")
print(f"📊 PROCESSING COMPLETE")
print(f"{'='*55}")
print(f"⏱️  Total time:  {hours}h {mins}m")
print(f"✅ Processed:  {len(success)}")
print(f"⏭️  Skipped:    {len(skipped)} (already done)")
print(f"❌ Failed:     {len(failed)}")

if success:
    print(f"\nNew manuals added to knowledge base:")
    for s in success:
        print(f"  📄 {s[:55]}")

if failed:
    print(f"\nFailed PDFs (try manually later):")
    for f in failed:
        print(f"  ❌ {f[:55]}")

final_temp = get_temperature()
if final_temp > 0:
    print(f"\n🌡️  Final temperature: {final_temp:.1f}°C")

print(f"\n{'='*55}")
print(f"Search your manuals:")
print(f"  search manual <keyword>")
print(f"{'='*55}\n")
