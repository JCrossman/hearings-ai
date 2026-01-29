#!/bin/bash

# Download decision documents from 2019-2024
# Format: YYYY-ABAER-XXX

BASE_URL="https://static.aer.ca/prd"
DOWNLOADED=0
TARGET=50

echo "Downloading documents..."

# Try 2024 documents (001-020)
for i in {1..20}; do
    if [ $DOWNLOADED -ge $TARGET ]; then break; fi
    NUM=$(printf "%03d" $i)
    FILE="2024-ABAER-${NUM}.pdf"
    if [ ! -f "$FILE" ]; then
        echo "Downloading $FILE..."
        curl -s -f -o "$FILE" "${BASE_URL}/${FILE}" && ((DOWNLOADED++)) && echo "  ✓ $FILE (${DOWNLOADED}/${TARGET})" || rm -f "$FILE"
        sleep 0.5
    fi
done

# Try 2023 documents (001-030)
for i in {1..30}; do
    if [ $DOWNLOADED -ge $TARGET ]; then break; fi
    NUM=$(printf "%03d" $i)
    FILE="2023-ABAER-${NUM}.pdf"
    if [ ! -f "$FILE" ]; then
        echo "Downloading $FILE..."
        curl -s -f -o "$FILE" "${BASE_URL}/${FILE}" && ((DOWNLOADED++)) && echo "  ✓ $FILE (${DOWNLOADED}/${TARGET})" || rm -f "$FILE"
        sleep 0.5
    fi
done

# Try 2022 documents (001-030)
for i in {1..30}; do
    if [ $DOWNLOADED -ge $TARGET ]; then break; fi
    NUM=$(printf "%03d" $i)
    FILE="2022-ABAER-${NUM}.pdf"
    if [ ! -f "$FILE" ]; then
        echo "Downloading $FILE..."
        curl -s -f -o "$FILE" "${BASE_URL}/${FILE}" && ((DOWNLOADED++)) && echo "  ✓ $FILE (${DOWNLOADED}/${TARGET})" || rm -f "$FILE"
        sleep 0.5
    fi
done

# Try 2021 documents (001-030)
for i in {1..30}; do
    if [ $DOWNLOADED -ge $TARGET ]; then break; fi
    NUM=$(printf "%03d" $i)
    FILE="2021-ABAER-${NUM}.pdf"
    if [ ! -f "$FILE" ]; then
        echo "Downloading $FILE..."
        curl -s -f -o "$FILE" "${BASE_URL}/${FILE}" && ((DOWNLOADED++)) && echo "  ✓ $FILE (${DOWNLOADED}/${TARGET})" || rm -f "$FILE"
        sleep 0.5
    fi
done

# Try 2020 documents
for i in {1..20}; do
    if [ $DOWNLOADED -ge $TARGET ]; then break; fi
    NUM=$(printf "%03d" $i)
    FILE="2020-ABAER-${NUM}.pdf"
    if [ ! -f "$FILE" ]; then
        echo "Downloading $FILE..."
        curl -s -f -o "$FILE" "${BASE_URL}/${FILE}" && ((DOWNLOADED++)) && echo "  ✓ $FILE (${DOWNLOADED}/${TARGET})" || rm -f "$FILE"
        sleep 0.5
    fi
done

echo ""
echo "Downloaded $DOWNLOADED new documents"
echo "Total documents: $(ls -1 *.pdf 2>/dev/null | wc -l)"
