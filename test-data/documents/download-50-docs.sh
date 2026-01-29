#!/bin/bash

BASE_URL="https://static.aer.ca/prd/documents/decisions"
DOWNLOADED=0
TARGET=50

echo "Downloading 50 diverse decision documents..."
echo ""

# Function to try downloading
download_doc() {
    local year=$1
    local num=$2
    local numstr=$(printf "%03d" $num)
    local filename="${year}-ABAER-${numstr}.pdf"
    local url_file="${year}ABAER${numstr}.pdf"
    local url="${BASE_URL}/${year}/${url_file}"
    
    if [ ! -f "$filename" ]; then
        if curl -s -f -o "$filename" "$url"; then
            local size=$(du -h "$filename" | cut -f1)
            echo "  ✓ $filename ($size)"
            return 0
        else
            rm -f "$filename"
            return 1
        fi
    fi
    return 1
}

# Download from multiple years
for year in 2024 2023 2022 2021 2020 2019; do
    if [ $DOWNLOADED -ge $TARGET ]; then break; fi
    echo "Trying ${year} documents..."
    
    for num in {1..50}; do
        if [ $DOWNLOADED -ge $TARGET ]; then break; fi
        if download_doc $year $num; then
            ((DOWNLOADED++))
        fi
        sleep 0.3
    done
    echo ""
done

echo ""
echo "✓ Downloaded $DOWNLOADED new documents"
echo "Total documents: $(ls -1 *.pdf 2>/dev/null | wc -l)"
