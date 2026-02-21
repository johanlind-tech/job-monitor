"""
Global scraper configuration.

Per-user settings (keywords, delivery days, etc.) now live in the
Supabase user_preferences table.  This file keeps only the settings
that the *scraper pipeline itself* needs at import time.
"""

# Keywords used by the Platsbanken API scraper to drive search queries.
# These are the same defaults seeded into user_preferences but are kept
# here so the scraper can run without a DB round-trip for query terms.
KEYWORDS_INCLUDE = [
    # English
    "CEO", "Country Manager", "General Manager", "Managing Director",
    "Business Unit Director", "BU Director", "Vice President", "VP",
    "Senior Vice President", "SVP", "CMO", "CCO", "CSO", "CBDO",
    "Commercial Director", "Marketing Director", "Commercial Lead",
    "Head of Commercial", "Head of Marketing",
    # Swedish
    "VD", "Landschef", "Affärsområdesdirektör", "Affärsområdeschef",
    "Marknadsdirektör", "Kommersiell direktör", "Affärsutvecklingsdirektör",
    "Försäljningsdirektör",
]

KEYWORDS_EXCLUDE = [
    "junior", "assistant", "coordinator",
    "assisterande", "assistent",
]

# Map each source to its primary country. Default is SE (Sweden).
# Used by the pipeline to tag jobs with the correct country code.
SOURCE_COUNTRY: dict[str, str] = {
    # Denmark
    "nigel_wright": "DK",     # Nigel Wright Nordics (DK-based)
    # Norway
    "bonesvirik": "NO",
    "visindi": "NO",
    # International / multi-country sources default to SE unless
    # location parsing overrides it later.
}

SITES = [
    "capa",
    "interimsearch",
    "wise",
    "headagent",
    "michaelberglund",
    "mason",
    "hammerhanborg",
    "novare",
    "platsbanken",
    # New sources
    "wes",
    "stardust",
    "academicsearch",
    "signpost",
    "inhouse",
    "peopleprovide",
    "futurevalue_rekrytering",
    "futurevalue_interim",
    "avanti",
    "pooliaexecutive",
    "nigel_wright",
    "gazella",
    "alumni",
    "properpeople",
    "jobway",
    "beyondretail",
    "bonesvirik",
    "visindi",
    "vindex",
    # Batch 2
    "executive",
    "cip",
    "trib",
    "mesh",
    "brightpeople",
    "bondi",
    "basedonpeople",
    "bohmans",
    "addpeople",
    "compasshrg",
    "levelrecruitment",
    "performiq",
    "safemind",
]
