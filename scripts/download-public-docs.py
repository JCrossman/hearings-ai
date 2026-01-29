#!/usr/bin/env python3
"""Download public hearing documents for POC testing.

These documents are publicly available from static.aer.ca and require no authentication.
"""

import asyncio
from pathlib import Path

import httpx

# Public documents for testing
PUBLIC_DOCUMENTS = [
    # Decisions
    {
        "url": "https://static.aer.ca/prd/documents/decisions/2024/2024-ABAER-001.pdf",
        "filename": "2024-ABAER-001.pdf",
        "description": "AlphaBow Energy Ltd. Regulatory Appeals Decision (87 pages)",
    },
    {
        "url": "https://static.aer.ca/prd/documents/decisions/2024/2024-ABAER-004.pdf",
        "filename": "2024-ABAER-004.pdf",
        "description": "Canadian Natural SAGD Decision",
    },
    {
        "url": "https://static.aer.ca/prd/documents/decisions/2024/2024-ABAER-007.pdf",
        "filename": "2024-ABAER-007.pdf",
        "description": "Qualico Developments Pipeline Reconsideration (43 pages)",
    },
    {
        "url": "https://static.aer.ca/prd/documents/decisions/2021/2021ABAER010.pdf",
        "filename": "2021-ABAER-010.pdf",
        "description": "Grassy Mountain Coal Project Joint Review (200+ pages)",
    },
    # Transcripts
    {
        "url": "https://static.aer.ca/aer/documents/applications/hearings/proceeding411-vol-1-march-08-2022.pdf",
        "filename": "proceeding-411-vol-1.pdf",
        "description": "Proceeding 411 Transcript Volume 1",
    },
    {
        "url": "https://static.aer.ca/aer/documents/applications/hearings/Proceeding-432-Vol-4-March-11-2024.pdf",
        "filename": "proceeding-432-vol-4.pdf",
        "description": "Proceeding 432 Transcript Volume 4",
    },
    # Procedural
    {
        "url": "https://static.aer.ca/prd/documents/decisions/Participatory_Procedural/1927181_20200715.pdf",
        "filename": "proceeding-397-scheduling.pdf",
        "description": "Proceeding 397 Scheduling Order",
    },
    {
        "url": "https://static.aer.ca/prd/documents/decisions/Participatory_Procedural/1927181_20201005.pdf",
        "filename": "proceeding-397-confidentiality.pdf",
        "description": "Proceeding 397 Confidentiality Ruling",
    },
]

OUTPUT_DIR = Path(__file__).parent.parent / "test-data" / "documents"


async def download_document(client: httpx.AsyncClient, doc: dict) -> bool:
    """Download a single document."""
    output_path = OUTPUT_DIR / doc["filename"]

    if output_path.exists():
        print(f"  ✓ Already exists: {doc['filename']}")
        return True

    try:
        print(f"  ↓ Downloading: {doc['filename']}")
        response = await client.get(doc["url"], follow_redirects=True)
        response.raise_for_status()

        output_path.write_bytes(response.content)
        size_mb = len(response.content) / (1024 * 1024)
        print(f"    ✓ Downloaded: {doc['filename']} ({size_mb:.1f} MB)")
        return True

    except httpx.HTTPError as e:
        print(f"    ✗ Failed: {doc['filename']} - {e}")
        return False


async def main():
    """Download all public documents."""
    print("=" * 60)
    print("Public Document Downloader")
    print("=" * 60)
    print(f"\nOutput directory: {OUTPUT_DIR}")
    print(f"Documents to download: {len(PUBLIC_DOCUMENTS)}\n")

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    async with httpx.AsyncClient(timeout=60.0) as client:
        results = await asyncio.gather(
            *[download_document(client, doc) for doc in PUBLIC_DOCUMENTS],
            return_exceptions=True,
        )

    success = sum(1 for r in results if r is True)
    failed = len(results) - success

    print("\n" + "=" * 60)
    print(f"Complete: {success} downloaded, {failed} failed")
    print("=" * 60)

    if success > 0:
        print("\nNext steps:")
        print("1. Run the ingestion pipeline to index these documents")
        print("2. Use sample-proceedings.json for metadata")
        print("3. Test search queries against the indexed content")


if __name__ == "__main__":
    asyncio.run(main())
