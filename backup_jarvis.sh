#!/bin/bash
# Backup Jarvis to a zip file for migration
echo "📦 Backing up Jarvis..."

BACKUP="$HOME/storage/downloads/Jarvis_backup_$(date +%Y%m%d).zip"

cd ~
zip -r "$BACKUP" Jarvis/ \
    --exclude "Jarvis/jarvis_logs/temp*" \
    --exclude "Jarvis/jarvis_logs/voice*" \
    --exclude "Jarvis/__pycache__/*" \
    --exclude "Jarvis/plugins/__pycache__/*" \
    --exclude "Jarvis/jarvis_logs/pdf_*"

SIZE=$(ls -lh "$BACKUP" | awk '{print $5}')
echo "✅ Backup complete!"
echo "   File: $BACKUP"
echo "   Size: $SIZE"
echo ""
echo "To restore on new device:"
echo "  1. Install Termux"
echo "  2. pkg install python ffmpeg termux-api flac"
echo "  3. pip install flask gtts speechrecognition textblob"
echo "  4. pkg install mupdf tesseract"
echo "  5. Copy zip to new phone"
echo "  6. unzip Jarvis_backup_XXXXXXXX.zip"
echo "  7. cd Jarvis && python jarvis.py"
