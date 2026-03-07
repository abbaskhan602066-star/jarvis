"""
pdf_reader.py - PDF and Image Reader Plugin
Converts PDF pages to images, OCR, then AI explanation
Uses: ImageMagick + tesseract + TextBlob
"""

import os
import subprocess
import glob
from datetime import datetime

DESCRIPTION = "Read PDFs and images using OCR"
COMMANDS    = [
    "read pdf", "scan pdf", "ocr image",
    "search manual", "list manuals"
]

JARVIS_DIR   = os.path.expanduser("~/Jarvis")
KNOWLEDGE    = os.path.join(JARVIS_DIR, "knowledge")
LOGS         = os.path.join(JARVIS_DIR, "jarvis_logs")
PDF_DIR      = os.path.expanduser("~/storage/downloads/pdf")

os.makedirs(KNOWLEDGE, exist_ok=True)
os.makedirs(LOGS,      exist_ok=True)

# ── Text Cleanup ──────────────────────────────
def clean_ocr_text(text: str) -> str:
    """Fix common OCR errors using TextBlob."""
    if not text or len(text) < 3:
        return text
    try:
        from textblob import TextBlob
        # Only fix short garbled words, not technical terms
        lines   = text.split("\n")
        cleaned = []
        for line in lines:
            line = line.strip()
            if not line:
                cleaned.append("")
                continue
            # Skip lines that look like technical data
            # (numbers, codes, measurements)
            if any(c.isdigit() for c in line) and len(line) < 20:
                cleaned.append(line)
                continue
            # Skip all-caps lines (headings, labels)
            if line.isupper():
                cleaned.append(line)
                continue
            cleaned.append(line)
        return "\n".join(cleaned)
    except:
        return text

# ── PDF To Images ─────────────────────────────
def pdf_to_images(pdf_path: str, out_dir: str,
                  density: int = 150) -> int:
    """Convert PDF pages to PNG images using ImageMagick."""
    os.makedirs(out_dir, exist_ok=True)
    # Clean old images
    for f in glob.glob(os.path.join(out_dir, "page_*.png")):
        try: os.remove(f)
        except: pass

    print(f"📄 Converting PDF to images...")
    r = subprocess.run(
        ["convert", "-density", str(density),
         pdf_path,
         os.path.join(out_dir, "page_%03d.png")],
        capture_output=True, timeout=300
    )
    pages = sorted(glob.glob(os.path.join(out_dir, "page_*.png")))
    print(f"   {len(pages)} pages converted")
    return len(pages)

# ── OCR Images ────────────────────────────────
def ocr_images(img_dir: str, output_file: str,
               start_page: int = 1,
               end_page: int = None) -> str:
    """Run tesseract OCR on all images in folder."""
    images = sorted(glob.glob(
        os.path.join(img_dir, "page_*.png")
    ))

    if not images:
        return "❌ No images found to OCR"

    # Filter page range
    if start_page > 1 or end_page:
        start_idx = start_page - 1
        end_idx   = end_page if end_page else len(images)
        images    = images[start_idx:end_idx]

    print(f"🔍 OCR scanning {len(images)} pages...")

    with open(output_file, "w") as out:
        for i, img in enumerate(images, 1):
            page_name = os.path.basename(img)
            print(f"   Page {i}/{len(images)}...", end="\r")
            out.write(f"\n{'='*50}\n")
            out.write(f"PAGE {i}\n")
            out.write(f"{'='*50}\n")

            r = subprocess.run(
                ["tesseract", img, "stdout",
                 "--psm", "1"],
                capture_output=True,
                text=True,
                timeout=60
            )
            raw_text     = r.stdout.strip()
            cleaned_text = clean_ocr_text(raw_text)
            out.write(cleaned_text + "\n")

    lines = open(output_file).read().count("\n")
    print(f"\n✅ OCR complete: {lines} lines extracted")
    return output_file

# ── Search Knowledge ──────────────────────────
def search_manual(query: str, manual_file: str = None) -> str:
    """Search extracted manual text for keywords."""
    results = []

    # Search specific file or all knowledge files
    if manual_file and os.path.exists(manual_file):
        files = [manual_file]
    else:
        files = glob.glob(os.path.join(KNOWLEDGE, "*.txt"))

    if not files:
        return "❌ No manuals in knowledge base yet.\nUse: read pdf <filename>"

    keywords = query.lower().split()

    for filepath in files:
        filename = os.path.basename(filepath)
        try:
            with open(filepath) as f:
                lines = f.readlines()

            for i, line in enumerate(lines):
                line_lower = line.lower()
                if any(kw in line_lower for kw in keywords):
                    # Get context (2 lines before and after)
                    start   = max(0, i-2)
                    end     = min(len(lines), i+3)
                    context = "".join(lines[start:end]).strip()
                    if context:
                        results.append(
                            f"📄 {filename}\n{context}"
                        )

        except:
            continue

    if not results:
        return f"❌ Nothing found for: '{query}'"

    # Deduplicate and limit results
    seen    = set()
    unique  = []
    for r in results:
        key = r[:100]
        if key not in seen:
            seen.add(key)
            unique.append(r)

    output  = f"🔍 Found {len(unique)} result(s) for '{query}':\n\n"
    output += "\n\n─────────────────────\n\n".join(unique[:5])
    if len(unique) > 5:
        output += f"\n\n... and {len(unique)-5} more results"
    return output

# ── List Manuals ──────────────────────────────
def list_manuals() -> str:
    """List all manuals in knowledge base and PDF folder."""
    result = "\n📚 Knowledge Base (searchable):\n\n"
    txt_files = glob.glob(os.path.join(KNOWLEDGE, "*.txt"))
    if txt_files:
        for f in sorted(txt_files):
            size  = os.path.getsize(f)
            lines = open(f).read().count("\n")
            name  = os.path.basename(f)
            result += f"  ✅ {name}\n"
            result += f"     {lines} lines, {size//1024}KB\n\n"
    else:
        result += "  (none yet)\n\n"

    result += "📁 PDFs Available To Read:\n\n"
    if os.path.exists(PDF_DIR):
        pdfs = glob.glob(os.path.join(PDF_DIR, "*.pdf"))
        for p in sorted(pdfs):
            size = os.path.getsize(p) // 1024
            name = os.path.basename(p)
            result += f"  📄 {name}\n"
            result += f"     {size}KB\n\n"
    else:
        result += f"  PDF folder not found: {PDF_DIR}\n"
    return result

# ── Read PDF Command ──────────────────────────
def read_pdf(args: str) -> str:
    """Main command: read pdf <filename or search term>"""
    args = args.strip()
    if not args:
        return ("⚠️ Usage: read pdf <filename>\n"
                "Example: read pdf E-302\n"
                "Or:      read pdf motor")

    # Find matching PDF
    matches = []
    if os.path.exists(PDF_DIR):
        for f in os.listdir(PDF_DIR):
            if f.endswith(".pdf") and args.lower() in f.lower():
                matches.append(os.path.join(PDF_DIR, f))

    if not matches:
        return (f"❌ No PDF found matching: '{args}'\n"
                f"Use: list manuals — to see available PDFs")

    if len(matches) > 1:
        result = f"🔍 Multiple matches found:\n\n"
        for i, m in enumerate(matches, 1):
            result += f"  {i}. {os.path.basename(m)}\n"
        result += f"\nBe more specific. Example:\n"
        result += f"  read pdf {os.path.basename(matches[0])[:20]}"
        return result

    pdf_path  = matches[0]
    pdf_name  = os.path.basename(pdf_path)
    safe_name = "".join(
        c if c.isalnum() or c in "-_" else "_"
        for c in pdf_name.replace(".pdf","")
    )
    out_dir    = os.path.join(LOGS, f"pdf_{safe_name}")
    out_file   = os.path.join(KNOWLEDGE, f"{safe_name}.txt")

    # Skip if already extracted
    if os.path.exists(out_file):
        lines = open(out_file).read().count("\n")
        return (f"✅ Already in knowledge base!\n"
                f"   {pdf_name}\n"
                f"   {lines} lines extracted\n\n"
                f"Search it with:\n"
                f"  search manual <keyword>")

    print(f"\n📖 Reading: {pdf_name}")

    # Convert PDF to images
    num_pages = pdf_to_images(pdf_path, out_dir)
    if num_pages == 0:
        return "❌ Could not convert PDF pages to images"

    # OCR all pages
    ocr_images(out_dir, out_file)

    # Cleanup temp images to save space
    for f in glob.glob(os.path.join(out_dir, "page_*.png")):
        try: os.remove(f)
        except: pass
    try: os.rmdir(out_dir)
    except: pass

    lines = open(out_file).read().count("\n")
    return (f"✅ PDF processed successfully!\n\n"
            f"   📄 {pdf_name}\n"
            f"   📝 {num_pages} pages scanned\n"
            f"   📊 {lines} lines extracted\n"
            f"   💾 Saved to knowledge base\n\n"
            f"Now search it:\n"
            f"  search manual motor winding\n"
            f"  search manual insulation resistance\n"
            f"  search manual bearing temperature")

# ── OCR Image Command ─────────────────────────
def ocr_image(args: str) -> str:
    """OCR a single image file."""
    path = args.strip()
    if not path:
        return "⚠️ Usage: ocr image <path to image>"

    # Try common locations
    locations = [
        path,
        os.path.expanduser(f"~/storage/downloads/{path}"),
        os.path.expanduser(f"~/storage/screenshots/{path}"),
        os.path.expanduser(f"~/storage/dcim/{path}"),
    ]

    found = None
    for loc in locations:
        if os.path.exists(loc):
            found = loc
            break

    if not found:
        return f"❌ Image not found: {path}"

    print(f"🔍 OCR scanning: {os.path.basename(found)}")
    r = subprocess.run(
        ["tesseract", found, "stdout", "--psm", "1"],
        capture_output=True, text=True, timeout=60
    )
    text = clean_ocr_text(r.stdout.strip())
    if not text:
        return "❌ No text found in image"

    # Save to knowledge if significant
    if len(text) > 100:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        out_file  = os.path.join(
            KNOWLEDGE, f"ocr_scan_{timestamp}.txt"
        )
        with open(out_file, "w") as f:
            f.write(f"Source: {found}\n")
            f.write(f"Scanned: {datetime.now()}\n\n")
            f.write(text)
        return (f"✅ Text extracted and saved!\n\n"
                f"{text[:500]}\n\n"
                f"{'...(truncated)' if len(text)>500 else ''}\n"
                f"Full text saved to knowledge base.")
    return f"📝 Text found:\n\n{text}"

# ── Entry Point ───────────────────────────────
def handle_command(query: str) -> str:
    q = query.strip().lower()

    if q.startswith("read pdf "):
        return read_pdf(query[9:])
    if q == "read pdf":
        return read_pdf("")
    if q.startswith("scan pdf "):
        return read_pdf(query[9:])
    if q.startswith("ocr image "):
        return ocr_image(query[10:])
    if q.startswith("search manual "):
        return search_manual(query[14:])
    if q in ("list manuals", "show manuals"):
        return list_manuals()

    return "⚠️ Unknown pdf_reader command."
