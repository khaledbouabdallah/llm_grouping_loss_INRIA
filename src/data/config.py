"""
Configuration: Wikidata property codes and entity definitions
"""

# ============================================================================
# WIKIDATA PROPERTY CODES
# ============================================================================


class WikidataProperties:
    """Wikidata property codes (P-codes)"""

    # Core properties
    INSTANCE_OF = "P31"

    # Person properties
    BIRTH_DATE = "P569"
    BIRTH_PLACE = "P19"
    DEATH_DATE = "P570"
    DEATH_PLACE = "P20"
    NATIONALITY = "P27"
    OCCUPATION = "P106"
    GENDER = "P21"

    # Discovery/Invention properties
    INVENTOR = "P61"
    DISCOVERY_DATE = "P575"
    COUNTRY_OF_ORIGIN = "P495"

    # Place properties
    COUNTRY = "P17"
    COORDINATES = "P625"
    POPULATION = "P1082"
    CAPITAL_OF = "P1376"

    # Event properties
    POINT_IN_TIME = "P585"
    LOCATION = "P276"
    PARTICIPANT = "P710"


class WikidataEntities:
    """Wikidata entity codes (Q-codes)"""

    # Entity types
    HUMAN = "Q5"
    CITY = "Q515"
    BIG_CITY = "Q1549591"
    CAPITAL_CITY = "Q5119"
    INVENTION = "Q35127"
    DISCOVERY = "Q192970"
    WAR = "Q198"
    REVOLUTION = "Q18608583"
    SPORT_COMPETITION = "Q27020041"

    # Nationalities - Western (Europe + North America)
    FRANCE = "Q142"
    GERMANY = "Q183"
    USA = "Q30"
    SPAIN = "Q29"
    UK = "Q145"
    ITALY = "Q38"
    NETHERLANDS = "Q55"
    BELGIUM = "Q31"
    SWITZERLAND = "Q39"
    SWEDEN = "Q34"
    NORWAY = "Q20"
    CANADA = "Q16"
    AUSTRALIA = "Q408"

    # Nationalities - Arabic/Middle Eastern
    EGYPT = "Q79"
    SYRIA = "Q858"
    SAUDI_ARABIA = "Q851"
    LEBANON = "Q822"
    MOROCCO = "Q1028"
    IRAQ = "Q796"
    JORDAN = "Q810"
    UAE = "Q878"
    TUNISIA = "Q948"
    ALGERIA = "Q262"

    # Nationalities - East Asian
    CHINA = "Q148"
    JAPAN = "Q17"
    SOUTH_KOREA = "Q884"
    TAIWAN = "Q865"
    MONGOLIA = "Q711"

    # Nationalities - South Asian
    INDIA = "Q668"
    PAKISTAN = "Q843"
    BANGLADESH = "Q902"
    NEPAL = "Q837"
    SRI_LANKA = "Q854"

    # Nationalities - Southeast Asian
    THAILAND = "Q869"
    VIETNAM = "Q881"
    INDONESIA = "Q252"
    PHILIPPINES = "Q928"
    MALAYSIA = "Q833"

    # Nationalities - Sub-Saharan African
    NIGERIA = "Q1033"
    SOUTH_AFRICA = "Q258"
    KENYA = "Q114"
    ETHIOPIA = "Q115"
    GHANA = "Q117"
    SENEGAL = "Q1041"

    # Nationalities - Latin American
    BRAZIL = "Q155"
    ARGENTINA = "Q414"
    MEXICO = "Q96"
    CHILE = "Q298"
    COLOMBIA = "Q739"
    PERU = "Q419"
    VENEZUELA = "Q717"

    # Occupations
    SCIENTIST = "Q901"
    POLITICIAN = "Q82955"
    ARTIST = "Q483501"
    ATHLETE = "Q2066131"
    WRITER = "Q36180"
    PHYSICIST = "Q169470"
    MATHEMATICIAN = "Q170790"

    # Gender
    MALE = "Q6581097"
    FEMALE = "Q6581072"


# ============================================================================
# ENTITY CATEGORIES
# ============================================================================

WESTERN_COUNTRIES = [
    WikidataEntities.FRANCE,
    WikidataEntities.GERMANY,
    WikidataEntities.USA,
    WikidataEntities.SPAIN,
    WikidataEntities.UK,
    WikidataEntities.ITALY,
    WikidataEntities.NETHERLANDS,
    WikidataEntities.BELGIUM,
    WikidataEntities.SWITZERLAND,
    WikidataEntities.SWEDEN,
    WikidataEntities.NORWAY,
    WikidataEntities.CANADA,
    WikidataEntities.AUSTRALIA,
]

ARABIC_COUNTRIES = [
    WikidataEntities.EGYPT,
    WikidataEntities.SYRIA,
    WikidataEntities.SAUDI_ARABIA,
    WikidataEntities.LEBANON,
    WikidataEntities.MOROCCO,
    WikidataEntities.IRAQ,
    WikidataEntities.JORDAN,
    WikidataEntities.UAE,
    WikidataEntities.TUNISIA,
    WikidataEntities.ALGERIA,
]

EAST_ASIAN_COUNTRIES = [
    WikidataEntities.CHINA,
    WikidataEntities.JAPAN,
    WikidataEntities.SOUTH_KOREA,
    WikidataEntities.TAIWAN,
    WikidataEntities.MONGOLIA,
]

SOUTH_ASIAN_COUNTRIES = [
    WikidataEntities.INDIA,
    WikidataEntities.PAKISTAN,
    WikidataEntities.BANGLADESH,
    WikidataEntities.NEPAL,
    WikidataEntities.SRI_LANKA,
]

SOUTHEAST_ASIAN_COUNTRIES = [
    WikidataEntities.THAILAND,
    WikidataEntities.VIETNAM,
    WikidataEntities.INDONESIA,
    WikidataEntities.PHILIPPINES,
    WikidataEntities.MALAYSIA,
]

AFRICAN_COUNTRIES = [
    WikidataEntities.NIGERIA,
    WikidataEntities.SOUTH_AFRICA,
    WikidataEntities.KENYA,
    WikidataEntities.ETHIOPIA,
    WikidataEntities.GHANA,
    WikidataEntities.SENEGAL,
]

LATIN_AMERICAN_COUNTRIES = [
    WikidataEntities.BRAZIL,
    WikidataEntities.ARGENTINA,
    WikidataEntities.MEXICO,
    WikidataEntities.CHILE,
    WikidataEntities.COLOMBIA,
    WikidataEntities.PERU,
    WikidataEntities.VENEZUELA,
]

# Backwards compatibility
ASIAN_COUNTRIES = (
    EAST_ASIAN_COUNTRIES + SOUTH_ASIAN_COUNTRIES + SOUTHEAST_ASIAN_COUNTRIES
)

# Complete mapping of country code to (country_name, culture_group)
COUNTRY_METADATA = {
    # Western
    #  DONE "Q30": ("United States", "Western"),
    #  DONE "Q142": ("France", "Western"),
    #  DONE "Q183": ("Germany", "Western"),
    #  DONE "Q145": ("United Kingdom", "Western"),
    # "Q29": ("Spain", "Western"),
    # "Q38": ("Italy", "Western"),
    # "Q55": ("Netherlands", "Western"),
    # "Q31": ("Belgium", "Western"),
    # "Q39": ("Switzerland", "Western"),
    # "Q34": ("Sweden", "Western"),
    # "Q20": ("Norway", "Western"),
    # "Q16": ("Canada", "Western"),
    # "Q408": ("Australia", "Western"),
    # Arabic/Middle Eastern
    # DONE "Q79": ("Egypt", "Arabic"),
    # DONE "Q858": ("Syria", "Arabic"),
    # DONE "Q851": ("Saudi Arabia", "Arabic"),
    # "Q822": ("Lebanon", "Arabic"),
    # DONE "Q1028": ("Morocco", "Arabic"),
    # "Q796": ("Iraq", "Arabic"),
    # "Q810": ("Jordan", "Arabic"),
    # "Q878": ("United Arab Emirates", "Arabic"),
    # "Q948": ("Tunisia", "Arabic"),
    # "Q262": ("Algeria", "Arabic"),
    # East Asian
    # DONE "Q148": ("China", "East Asian"),
    # DONE "Q17": ("Japan", "East Asian"),
    "Q884": ("South Korea", "East Asian"),
    "Q865": ("Taiwan", "East Asian"),
    # "Q711": ("Mongolia", "East Asian"),
    # South Asian
    "Q668": ("India", "South Asian"),
    "Q843": ("Pakistan", "South Asian"),
    "Q902": ("Bangladesh", "South Asian"),
    # "Q837": ("Nepal", "South Asian"),
    # "Q854": ("Sri Lanka", "South Asian"),
    # Southeast Asian
    "Q869": ("Thailand", "Southeast Asian"),
    "Q881": ("Vietnam", "Southeast Asian"),
    "Q252": ("Indonesia", "Southeast Asian"),
    # "Q928": ("Philippines", "Southeast Asian"),
    # "Q833": ("Malaysia", "Southeast Asian"),
    # Sub-Saharan African
    "Q1033": ("Nigeria", "African"),
    "Q258": ("South Africa", "African"),
    # "Q114": ("Kenya", "African"),
    "Q115": ("Ethiopia", "African"),
    # "Q117": ("Ghana", "African"),
    "Q1041": ("Senegal", "African"),
    # Latin American
    "Q155": ("Brazil", "Latin American"),
    "Q414": ("Argentina", "Latin American"),
    "Q96": ("Mexico", "Latin American"),
    "Q298": ("Chile", "Latin American"),
    # "Q739": ("Colombia", "Latin American"),
    # "Q419": ("Peru", "Latin American"),
    # "Q717": ("Venezuela", "Latin American"),
}


OCCUPATIONS = [
    WikidataEntities.SCIENTIST,
    WikidataEntities.POLITICIAN,
    WikidataEntities.ARTIST,
    WikidataEntities.ATHLETE,
    WikidataEntities.WRITER,
]

# Event types for querying
EVENT_TYPES = [
    WikidataEntities.WAR,
    WikidataEntities.REVOLUTION,
    WikidataEntities.SPORT_COMPETITION,
]


# ============================================================================
# SPARQL QUERY TEMPLATES - MULTILINGUAL
# ============================================================================

# People multilingual template - fetches ALL labels in SPARQL (no ORDER BY)
# Without ORDER BY, OPTIONAL labels work fine and are MUCH faster than API calls
SPARQL_PEOPLE_MULTILINGUAL_TEMPLATE = """
SELECT DISTINCT
    ?person
    ?personLabel_en ?personLabel_fr ?personLabel_ar ?personLabel_arz
    ?birthDate
    ?birthPlace
    ?birthPlaceLabel_en ?birthPlaceLabel_fr ?birthPlaceLabel_ar ?birthPlaceLabel_arz
    ?nationality
    ?nationalityLabel_en ?nationalityLabel_fr ?nationalityLabel_ar ?nationalityLabel_arz
    ?occupation
    ?occupationLabel_en ?occupationLabel_fr ?occupationLabel_ar ?occupationLabel_arz
    ?gender
    ?deathDate
WHERE {{
  VALUES ?nationality {{ {nationalities} }}

  ?person wdt:{instance_of} wd:{human} .
  ?person wdt:{nationality_prop} ?nationality .
  ?person wdt:{birth_date} ?birthDate .
  ?person wdt:{birth_place} ?birthPlace .
  ?person wdt:{occupation_prop} ?occupation .

  OPTIONAL {{ ?person wdt:{gender_prop} ?gender . }}
  OPTIONAL {{ ?person wdt:{death_date} ?deathDate . }}

  FILTER(YEAR(?birthDate) > {min_year})
  FILTER(YEAR(?birthDate) < {max_year})

  # Person labels
  OPTIONAL {{
    ?person rdfs:label ?personLabel_en .
    FILTER(LANG(?personLabel_en) = "en")
  }}
  OPTIONAL {{
    ?person rdfs:label ?personLabel_fr .
    FILTER(LANG(?personLabel_fr) = "fr")
  }}
  OPTIONAL {{
    ?person rdfs:label ?personLabel_ar .
    FILTER(LANG(?personLabel_ar) = "ar")
  }}
  OPTIONAL {{
    ?person rdfs:label ?personLabel_arz .
    FILTER(LANG(?personLabel_arz) = "arz")
  }}

  # Birth place labels
  OPTIONAL {{
    ?birthPlace rdfs:label ?birthPlaceLabel_en .
    FILTER(LANG(?birthPlaceLabel_en) = "en")
  }}
  OPTIONAL {{
    ?birthPlace rdfs:label ?birthPlaceLabel_fr .
    FILTER(LANG(?birthPlaceLabel_fr) = "fr")
  }}
  OPTIONAL {{
    ?birthPlace rdfs:label ?birthPlaceLabel_ar .
    FILTER(LANG(?birthPlaceLabel_ar) = "ar")
  }}
  OPTIONAL {{
    ?birthPlace rdfs:label ?birthPlaceLabel_arz .
    FILTER(LANG(?birthPlaceLabel_arz) = "arz")
  }}

  # Nationality labels
  OPTIONAL {{
    ?nationality rdfs:label ?nationalityLabel_en .
    FILTER(LANG(?nationalityLabel_en) = "en")
  }}
  OPTIONAL {{
    ?nationality rdfs:label ?nationalityLabel_fr .
    FILTER(LANG(?nationalityLabel_fr) = "fr")
  }}
  OPTIONAL {{
    ?nationality rdfs:label ?nationalityLabel_ar .
    FILTER(LANG(?nationalityLabel_ar) = "ar")
  }}
  OPTIONAL {{
    ?nationality rdfs:label ?nationalityLabel_arz .
    FILTER(LANG(?nationalityLabel_arz) = "arz")
  }}

  # Occupation labels
  OPTIONAL {{
    ?occupation rdfs:label ?occupationLabel_en .
    FILTER(LANG(?occupationLabel_en) = "en")
  }}
  OPTIONAL {{
    ?occupation rdfs:label ?occupationLabel_fr .
    FILTER(LANG(?occupationLabel_fr) = "fr")
  }}
  OPTIONAL {{
    ?occupation rdfs:label ?occupationLabel_ar .
    FILTER(LANG(?occupationLabel_ar) = "ar")
  }}
  OPTIONAL {{
    ?occupation rdfs:label ?occupationLabel_arz .
    FILTER(LANG(?occupationLabel_arz) = "arz")
  }}
}}
LIMIT {limit}
"""

# Events multilingual template
SPARQL_EVENTS_MULTILINGUAL_TEMPLATE = """
SELECT DISTINCT
    ?event
    ?eventLabel_en ?eventLabel_fr ?eventLabel_ar ?eventLabel_arz
    ?date
    ?location
    ?locationLabel_en ?locationLabel_fr ?locationLabel_ar ?locationLabel_arz
    ?eventType
    ?eventTypeLabel_en ?eventTypeLabel_fr ?eventTypeLabel_ar ?eventTypeLabel_arz
    (COUNT(DISTINCT ?sitelink) as ?num_wikipedia_languages)
WHERE {{
  VALUES ?eventType {{ {event_types} }}

  ?event wdt:{instance_of} ?eventType .
  ?event wdt:{date_prop} ?date .

  # Location (optional)
  OPTIONAL {{ ?event wdt:{location_prop} ?location . }}

  FILTER(YEAR(?date) > {min_year})
  FILTER(YEAR(?date) < {max_year})

  # English labels
  OPTIONAL {{
    ?event rdfs:label ?eventLabel_en .
    FILTER(LANG(?eventLabel_en) = "en")
  }}
  OPTIONAL {{
    ?location rdfs:label ?locationLabel_en .
    FILTER(LANG(?locationLabel_en) = "en")
  }}
  OPTIONAL {{
    ?eventType rdfs:label ?eventTypeLabel_en .
    FILTER(LANG(?eventTypeLabel_en) = "en")
  }}

  # French labels
  OPTIONAL {{
    ?event rdfs:label ?eventLabel_fr .
    FILTER(LANG(?eventLabel_fr) = "fr")
  }}
  OPTIONAL {{
    ?location rdfs:label ?locationLabel_fr .
    FILTER(LANG(?locationLabel_fr) = "fr")
  }}
  OPTIONAL {{
    ?eventType rdfs:label ?eventTypeLabel_fr .
    FILTER(LANG(?eventTypeLabel_fr) = "fr")
  }}

  # Arabic labels
  OPTIONAL {{
    ?event rdfs:label ?eventLabel_ar .
    FILTER(LANG(?eventLabel_ar) = "ar")
  }}
  OPTIONAL {{
    ?location rdfs:label ?locationLabel_ar .
    FILTER(LANG(?locationLabel_ar) = "ar")
  }}
  OPTIONAL {{
    ?eventType rdfs:label ?eventTypeLabel_ar .
    FILTER(LANG(?eventTypeLabel_ar) = "ar")
  }}

  # Egyptian Arabic labels (fallback)
  OPTIONAL {{
    ?event rdfs:label ?eventLabel_arz .
    FILTER(LANG(?eventLabel_arz) = "arz")
  }}
  OPTIONAL {{
    ?location rdfs:label ?locationLabel_arz .
    FILTER(LANG(?locationLabel_arz) = "arz")
  }}
  OPTIONAL {{
    ?eventType rdfs:label ?eventTypeLabel_arz .
    FILTER(LANG(?eventTypeLabel_arz) = "arz")
  }}

  BIND(xsd:integer(strafter(str(?event), 'Q')) as ?qid)
}}
ORDER BY {order_direction}(?qid)
LIMIT {limit}
OFFSET {offset}
"""

# Discoveries multilingual template
SPARQL_DISCOVERIES_MULTILINGUAL_TEMPLATE = """
SELECT DISTINCT
    ?discovery
    ?discoveryLabel_en ?discoveryLabel_fr ?discoveryLabel_ar ?discoveryLabel_arz
    ?inventor
    ?inventorLabel_en ?inventorLabel_fr ?inventorLabel_ar ?inventorLabel_arz
    ?date
    ?country
    ?countryLabel_en ?countryLabel_fr ?countryLabel_ar ?countryLabel_arz
WHERE {{
  ?discovery wdt:{inventor_prop} ?inventor .
  ?discovery wdt:{date_prop} ?date .

  # Country (optional)
  OPTIONAL {{ ?inventor wdt:{nationality_prop} ?country . }}

  FILTER(YEAR(?date) > {min_year})
  FILTER(YEAR(?date) < {max_year})

  # English labels
  OPTIONAL {{
    ?discovery rdfs:label ?discoveryLabel_en .
    FILTER(LANG(?discoveryLabel_en) = "en")
  }}
  OPTIONAL {{
    ?inventor rdfs:label ?inventorLabel_en .
    FILTER(LANG(?inventorLabel_en) = "en")
  }}
  OPTIONAL {{
    ?country rdfs:label ?countryLabel_en .
    FILTER(LANG(?countryLabel_en) = "en")
  }}

  # French labels
  OPTIONAL {{
    ?discovery rdfs:label ?discoveryLabel_fr .
    FILTER(LANG(?discoveryLabel_fr) = "fr")
  }}
  OPTIONAL {{
    ?inventor rdfs:label ?inventorLabel_fr .
    FILTER(LANG(?inventorLabel_fr) = "fr")
  }}
  OPTIONAL {{
    ?country rdfs:label ?countryLabel_fr .
    FILTER(LANG(?countryLabel_fr) = "fr")
  }}

  # Arabic labels
  OPTIONAL {{
    ?discovery rdfs:label ?discoveryLabel_ar .
    FILTER(LANG(?discoveryLabel_ar) = "ar")
  }}
  OPTIONAL {{
    ?inventor rdfs:label ?inventorLabel_ar .
    FILTER(LANG(?inventorLabel_ar) = "ar")
  }}
  OPTIONAL {{
    ?country rdfs:label ?countryLabel_ar .
    FILTER(LANG(?countryLabel_ar) = "ar")
  }}

  # Egyptian Arabic labels (fallback)
  OPTIONAL {{
    ?discovery rdfs:label ?discoveryLabel_arz .
    FILTER(LANG(?discoveryLabel_arz) = "arz")
  }}
  OPTIONAL {{
    ?inventor rdfs:label ?inventorLabel_arz .
    FILTER(LANG(?inventorLabel_arz) = "arz")
  }}
  OPTIONAL {{
    ?country rdfs:label ?countryLabel_arz .
    FILTER(LANG(?countryLabel_arz) = "arz")
  }}

  BIND(xsd:integer(strafter(str(?discovery), 'Q')) as ?qid)
}}
ORDER BY {order_direction}(?qid)
LIMIT {limit}
OFFSET {offset}
"""

# Places multilingual template
SPARQL_PLACES_MULTILINGUAL_TEMPLATE = """
SELECT DISTINCT
    ?place
    ?placeLabel_en ?placeLabel_fr ?placeLabel_ar ?placeLabel_arz
    ?country
    ?countryLabel_en ?countryLabel_fr ?countryLabel_ar ?countryLabel_arz
    ?coords
    ?population
    ?placeType
    ?placeTypeLabel_en ?placeTypeLabel_fr ?placeTypeLabel_ar ?placeTypeLabel_arz
WHERE {{
  VALUES ?country {{ {countries} }}

  ?place wdt:{instance_of} ?placeType .
  ?place wdt:{country_prop} ?country .

  # Coordinates (optional)
  OPTIONAL {{ ?place wdt:{coords_prop} ?coords . }}

  # Population (optional)
  OPTIONAL {{ ?place wdt:{population_prop} ?population . }}

  # Filter for cities/capitals
  FILTER(?placeType IN (wd:{city}, wd:{capital}, wd:{big_city}))

  # English labels
  OPTIONAL {{
    ?place rdfs:label ?placeLabel_en .
    FILTER(LANG(?placeLabel_en) = "en")
  }}
  OPTIONAL {{
    ?country rdfs:label ?countryLabel_en .
    FILTER(LANG(?countryLabel_en) = "en")
  }}
  OPTIONAL {{
    ?placeType rdfs:label ?placeTypeLabel_en .
    FILTER(LANG(?placeTypeLabel_en) = "en")
  }}

  # French labels
  OPTIONAL {{
    ?place rdfs:label ?placeLabel_fr .
    FILTER(LANG(?placeLabel_fr) = "fr")
  }}
  OPTIONAL {{
    ?country rdfs:label ?countryLabel_fr .
    FILTER(LANG(?countryLabel_fr) = "fr")
  }}
  OPTIONAL {{
    ?placeType rdfs:label ?placeTypeLabel_fr .
    FILTER(LANG(?placeTypeLabel_fr) = "fr")
  }}

  # Arabic labels
  OPTIONAL {{
    ?place rdfs:label ?placeLabel_ar .
    FILTER(LANG(?placeLabel_ar) = "ar")
  }}
  OPTIONAL {{
    ?country rdfs:label ?countryLabel_ar .
    FILTER(LANG(?countryLabel_ar) = "ar")
  }}
  OPTIONAL {{
    ?placeType rdfs:label ?placeTypeLabel_ar .
    FILTER(LANG(?placeTypeLabel_ar) = "ar")
  }}

  # Egyptian Arabic labels (fallback)
  OPTIONAL {{
    ?place rdfs:label ?placeLabel_arz .
    FILTER(LANG(?placeLabel_arz) = "arz")
  }}
  OPTIONAL {{
    ?country rdfs:label ?countryLabel_arz .
    FILTER(LANG(?countryLabel_arz) = "arz")
  }}
  OPTIONAL {{
    ?placeType rdfs:label ?placeTypeLabel_arz .
    FILTER(LANG(?placeTypeLabel_arz) = "arz")
  }}

  BIND(xsd:integer(strafter(str(?place), 'Q')) as ?qid)
}}
ORDER BY {order_direction}(?qid)
LIMIT {limit}
OFFSET {offset}
"""
