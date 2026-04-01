#!/bin/bash
# probe_et_gr.sh
# Probes various et.gr API URL patterns to find the correct PDF endpoint
# Run with: bash probe_et_gr.sh

OUTDIR="/home/dantonakaki/greek_legislation/api_probe"
mkdir -p "$OUTDIR"

echo "============================================"
echo "  Probing et.gr API for correct PDF URL"
echo "  Results saved to: $OUTDIR"
echo "============================================"

# Helper function — downloads a URL, saves it, reports file type and size
probe() {
    local label="$1"
    local url="$2"
    local outfile="$OUTDIR/${label}.bin"

    echo ""
    echo "[$label]"
    echo "  URL : $url"

    # -sL = silent + follow redirects, -o = output file
    http_code=$(curl -sL \
        -o "$outfile" \
        -w "%{http_code}" \
        --max-time 30 \
        "$url")

    size=$(ls -lh "$outfile" | awk '{print $5}')
    type=$(file "$outfile")

    echo "  HTTP: $http_code"
    echo "  Size: $size"
    echo "  Type: $type"

    # If it looks like JSON, pretty-print the first 300 chars
    if echo "$type" | grep -qi "json\|text\|ascii"; then
        echo "  Content preview:"
        cat "$outfile" | head -c 300
        echo ""
    fi
}

# --- Pattern 1: original with www ---
probe "01_www_newFek" \
    "https://www.et.gr/api/Bulletin?newFek=1&year=2000"

# --- Pattern 2: without www ---
probe "02_nowww_newFek" \
    "https://et.gr/api/Bulletin?newFek=1&year=2000"

# --- Pattern 3: different param names ---
probe "03_fek_param" \
    "https://et.gr/api/Bulletin?fek=1&year=2000"

probe "04_fekNum_param" \
    "https://et.gr/api/Bulletin?fekNum=1&year=2000"

probe "05_id_param" \
    "https://et.gr/api/Bulletin?id=1&year=2000"

# --- Pattern 4: with type parameter ---
probe "06_type_pdf" \
    "https://et.gr/api/Bulletin?newFek=1&year=2000&type=pdf"

probe "07_type_1" \
    "https://et.gr/api/Bulletin?newFek=1&year=2000&type=1"

probe "08_type_2" \
    "https://et.gr/api/Bulletin?newFek=1&year=2000&type=2"

# --- Pattern 5: different base endpoints ---
probe "09_idocs" \
    "https://et.gr/idocs-nph/search/pdfViewerForm.html?args=5AtMutRoR1zEe8qQnplQQXdtvSoClrL6xbXLJgFxC_4GePFAfpQ2RIQNFM6OPgQNvNANXWAFT8AIQ5n5KXEM"

probe "10_api_root" \
    "https://et.gr/api/"

probe "11_api_search" \
    "https://et.gr/api/search?fek=1&year=2000"

probe "12_api_laws" \
    "https://et.gr/api/laws?fek=1&year=2000"

probe "13_api_document" \
    "https://et.gr/api/Document?fek=1&year=2000"

probe "14_api_fek" \
    "https://et.gr/api/fek?num=1&year=2000"

# --- Pattern 6: try a more recent year (better chance of working) ---
probe "15_year2023" \
    "https://et.gr/api/Bulletin?newFek=1&year=2023"

probe "16_year2024" \
    "https://et.gr/api/Bulletin?newFek=1&year=2024"

echo ""
echo "============================================"
echo "  SUMMARY — checking which files are PDFs:"
echo "============================================"
for f in "$OUTDIR"/*.bin; do
    label=$(basename "$f" .bin)
    type=$(file "$f")
    if echo "$type" | grep -qi "pdf"; then
        echo "  ✅ PDF FOUND: $label"
        echo "     $type"
    else
        echo "  ❌ $label → $(echo $type | cut -c1-80)"
    fi
done

echo ""
echo "[DONE] Check $OUTDIR for raw responses"
