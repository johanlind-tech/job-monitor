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
]
