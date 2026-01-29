#!/usr/bin/env python3
"""Generate synthetic hearing documents for testing.

Creates realistic document content following formatting conventions:
- Numbered paragraphs [1], [2], [3]
- Standard section headings
- Regulatory citations (REDA, EPEA, Directives)
- terminology

These synthetic documents can be used for:
- Testing the ingestion pipeline
- Validating search functionality
- Training/fine-tuning extraction models
"""

import json
import random
from datetime import date, timedelta
from pathlib import Path

OUTPUT_DIR = Path(__file__).parent.parent / "test-data" / "documents"

# -specific content templates
DECISION_SECTIONS = [
    "Decision Summary",
    "Introduction",
    "Background",
    "Regulatory Framework",
    "Issues",
    "Evidence and Arguments",
    "Analysis and Findings",
    "Conditions",
    "Decision",
    "Appendix A - Conditions of Approval",
]

REGULATORY_CITATIONS = [
    "REDA, section 34",
    "REDA, section 36",
    "REDA, section 39",
    "EPEA, section 2",
    "EPEA, section 40",
    "EPEA, section 68",
    "Oil and Gas Conservation Act, section 3",
    "Water Act, section 36",
    "Pipeline Act, section 33",
    "Directive 056, section 2.1",
    "Directive 056, section 4.2",
    "Directive 067, section 3",
    "Directive 071, section 2",
    "Directive 088, section 4",
]

PARTIES = {
    "applicants": [
        ("Summit Coal Ltd.", "SCL001"),
        ("Northback Holdings Corporation", "NHC001"),
        ("Rocky Mountain Energy Inc.", "RME001"),
        ("Alberta Coal Development Corp.", "ACD001"),
    ],
    "interveners": [
        "Alberta Wilderness Association",
        "Crowsnest Pass Residents Association",
        "Oldman Watershed Council",
        "Livingstone Landowners Group",
        "Piikani Nation",
        "Stoney Nakoda Nation",
        "Kainai Nation",
    ],
}

LOCATIONS = [
    "Township 7, Range 3, W5M",
    "Township 8, Range 4, W5M",
    "Township 9, Range 2, W5M",
    "Crowsnest Pass area",
    "Livingstone Range",
    "Oldman River watershed",
    "Castle River headwaters",
]

WELL_IDENTIFIERS = ["MW-1", "MW-2", "MW-3", "MW-4", "MW-5", "MW-6", "GW-A", "GW-B", "GW-C"]


def generate_paragraph_content(section: str, paragraph_num: int) -> str:
    """Generate realistic paragraph content based on section type."""
    
    if section == "Decision Summary":
        templates = [
            f"The has decided to approve the applications by {{applicant}} for coal exploration activities in {{location}}, subject to the conditions set out in Appendix A.",
            f"Having considered all of the evidence and arguments presented, the panel finds that the proposed project is in the public interest, provided that the conditions imposed adequately address the concerns raised by interveners.",
            f"The panel has carefully weighed the economic benefits of the proposed development against the potential environmental impacts and has concluded that, with appropriate mitigation measures, the project can proceed.",
        ]
    elif section == "Regulatory Framework":
        templates = [
            f"Under {{citation}}, the has authority to impose conditions on energy development approvals to protect public safety and the environment.",
            f"The panel's jurisdiction to hear this matter derives from {{citation}}, which provides for regulatory appeals of decisions made under the Oil and Gas Conservation Act.",
            f"{{citation}} requires applicants to demonstrate that their proposed activities will not cause significant adverse environmental effects that cannot be mitigated.",
        ]
    elif section == "Evidence and Arguments":
        templates = [
            f"{{applicant}} submitted that groundwater monitoring data from {{well_id}} demonstrates baseline conditions prior to any disturbance from the proposed activities.",
            f"The {{intervener}} argued that the applicant's environmental assessment failed to adequately address cumulative effects on the {{location}}.",
            f"Expert witness Dr. Smith testified that selenium concentrations in {{well_id}} were within acceptable limits under {{citation}}.",
            f"staff asked the applicant to clarify the proposed monitoring frequency, noting that {{citation}} requires quarterly sampling at a minimum.",
        ]
    elif section == "Analysis and Findings":
        templates = [
            f"The panel finds that {{applicant}}'s evidence regarding groundwater protection measures is credible and consistent with industry best practices.",
            f"While the panel acknowledges the concerns raised by {{intervener}} regarding impacts to {{location}}, the evidence does not support a finding of significant unmitigated harm.",
            f"The panel accepts the applicant's commitment to implement enhanced monitoring as set out in {{citation}} and will impose this as a condition of approval.",
        ]
    else:
        templates = [
            f"The received the application from {{applicant}} on {{date}}.",
            f"Notice of the hearing was published in accordance with {{citation}}.",
            f"The hearing was conducted over {{days}} days, during which the panel heard testimony from {{witnesses}} witnesses.",
        ]
    
    template = random.choice(templates)
    
    # Fill in placeholders
    applicant = random.choice(PARTIES["applicants"])[0]
    intervener = random.choice(PARTIES["interveners"])
    location = random.choice(LOCATIONS)
    citation = random.choice(REGULATORY_CITATIONS)
    well_id = random.choice(WELL_IDENTIFIERS)
    hearing_date = date.today() - timedelta(days=random.randint(30, 365))
    
    content = template.format(
        applicant=applicant,
        intervener=intervener,
        location=location,
        citation=citation,
        well_id=well_id,
        date=hearing_date.strftime("%B %d, %Y"),
        days=random.randint(3, 15),
        witnesses=random.randint(5, 20),
    )
    
    return content


def generate_decision_document(proceeding_id: str, applicant: tuple[str, str]) -> str:
    """Generate a synthetic decision document."""
    
    abaer_num = f"2025-ABAER-{random.randint(1, 99):03d}"
    decision_date = date.today() - timedelta(days=random.randint(1, 90))
    
    lines = [
        f"Information Security Classification: Public",
        "",
        f"{abaer_num}",
        "",
        f"Decision",
        "",
        f"{applicant[0]}",
        f"Applications for Coal Exploration Program",
        f"Proceeding {proceeding_id}",
        "",
        f"Decision Date: {decision_date.strftime('%B %d, %Y')}",
        "",
        "=" * 60,
        "",
    ]
    
    paragraph_num = 1
    
    for section in DECISION_SECTIONS:
        lines.append(f"{section}")
        lines.append("")
        
        # Generate 3-8 paragraphs per section
        num_paragraphs = random.randint(3, 8)
        for _ in range(num_paragraphs):
            content = generate_paragraph_content(section, paragraph_num)
            lines.append(f"[{paragraph_num}] {content}")
            lines.append("")
            paragraph_num += 1
    
    # Add signature block
    lines.extend([
        "",
        "Dated in Calgary, Alberta, on " + decision_date.strftime("%B %d, %Y"),
        "",
        "",
        "",
        "[Original signed by]",
        "",
        "J. Smith, P.Eng.",
        "Presiding Hearing Commissioner",
        "",
        "[Original signed by]",
        "",
        "M. Johnson, P.Geo.",
        "Hearing Commissioner",
    ])
    
    return "\n".join(lines)


def generate_transcript_excerpt(proceeding_id: str, volume: int, day_date: date) -> str:
    """Generate a synthetic hearing transcript excerpt."""
    
    applicant = random.choice(PARTIES["applicants"])
    interveners = random.sample(PARTIES["interveners"], k=min(3, len(PARTIES["interveners"])))
    
    lines = [
        f"Transcript of Proceedings",
        f"Proceeding {proceeding_id}",
        f"Volume {volume}",
        f"{day_date.strftime('%A, %B %d, %Y')}",
        "",
        "=" * 60,
        "",
        "APPEARANCES:",
        "",
        f"For {applicant[0]}:",
        "  Mr. A. Counsel, Legal Counsel",
        "  Dr. B. Expert, Environmental Consultant",
        "",
    ]
    
    for intervener in interveners:
        lines.extend([
            f"For {intervener}:",
            f"  Ms. C. Advocate, Legal Counsel",
            "",
        ])
    
    lines.extend([
        "Staff:",
        "  Mr. D. Analyst, Technical Advisor",
        "",
        "=" * 60,
        "",
        "THE CHAIRMAN: Good morning. We are resuming the hearing",
        f"in Proceeding {proceeding_id}. We will continue with the",
        "cross-examination of the applicant's environmental witness.",
        "",
    ])
    
    # Generate Q&A exchanges
    page = 1
    line_num = 1
    
    for exchange in range(random.randint(5, 10)):
        questioner = random.choice(["MR. COUNSEL", "MS. ADVOCATE", "THE CHAIRMAN", "MR. ANALYST"])
        witness = "DR. EXPERT" if random.random() > 0.3 else "MR. WITNESS"
        
        question = random.choice([
            f"Could you please describe the methodology used for the groundwater baseline study at {random.choice(WELL_IDENTIFIERS)}?",
            f"What is your opinion regarding the potential impacts to the {random.choice(LOCATIONS)}?",
            f"Are you familiar with the requirements under {random.choice(REGULATORY_CITATIONS)}?",
            f"How do you respond to the concerns raised by the interveners regarding cumulative effects?",
        ])
        
        answer = random.choice([
            "Yes, I can address that. The methodology followed industry standard practices and was consistent with Directive 056 requirements.",
            "Based on our analysis, the potential impacts would be minimal and can be effectively mitigated through the proposed monitoring program.",
            "Yes, I am familiar with those requirements. Our assessment was designed to meet or exceed all applicable regulatory standards.",
            "The cumulative effects assessment considered all existing and reasonably foreseeable developments in the region.",
        ])
        
        lines.extend([
            f"Page {page}",
            "",
            f"{line_num}  {questioner}: {question}",
            "",
            f"{line_num + 2}  {witness}: {answer}",
            "",
        ])
        
        page += 1
        line_num += 5
    
    return "\n".join(lines)


def main():
    """Generate synthetic test documents."""
    print("=" * 60)
    print("Synthetic Document Generator")
    print("=" * 60)
    
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    
    documents_generated = []
    
    # Generate 3 synthetic decisions
    for i, (applicant_name, ba_code) in enumerate(PARTIES["applicants"][:3], start=1):
        proceeding_id = str(450 + i)
        content = generate_decision_document(proceeding_id, (applicant_name, ba_code))
        
        filename = f"synthetic-decision-{proceeding_id}.txt"
        output_path = OUTPUT_DIR / filename
        output_path.write_text(content)
        
        documents_generated.append({
            "filename": filename,
            "type": "decision",
            "proceeding_id": proceeding_id,
            "applicant": applicant_name,
        })
        print(f"  ✓ Generated: {filename}")
    
    # Generate 2 synthetic transcripts
    for i in range(2):
        proceeding_id = str(451 + i)
        volume = i + 1
        hearing_date = date.today() - timedelta(days=random.randint(30, 180))
        
        content = generate_transcript_excerpt(proceeding_id, volume, hearing_date)
        
        filename = f"synthetic-transcript-{proceeding_id}-vol{volume}.txt"
        output_path = OUTPUT_DIR / filename
        output_path.write_text(content)
        
        documents_generated.append({
            "filename": filename,
            "type": "transcript",
            "proceeding_id": proceeding_id,
            "volume": volume,
        })
        print(f"  ✓ Generated: {filename}")
    
    # Save manifest
    manifest_path = OUTPUT_DIR / "synthetic-manifest.json"
    manifest_path.write_text(json.dumps(documents_generated, indent=2))
    print(f"\n  ✓ Manifest: {manifest_path}")
    
    print("\n" + "=" * 60)
    print(f"Generated {len(documents_generated)} synthetic documents")
    print("=" * 60)
    print("\nNote: These are synthetic documents for testing only.")
    print("Use download-public-docs.py to get real documents.")


if __name__ == "__main__":
    main()
