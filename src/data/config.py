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

    # Nationalities - Western
    FRANCE = "Q142"
    GERMANY = "Q183"
    USA = "Q30"
    SPAIN = "Q29"
    UK = "Q145"

    # Nationalities - Arabic/Middle Eastern
    EGYPT = "Q79"
    SYRIA = "Q858"
    SAUDI_ARABIA = "Q851"
    LEBANON = "Q822"
    MOROCCO = "Q1028"
    IRAQ = "Q796"

    # Nationalities - Asian
    CHINA = "Q148"
    JAPAN = "Q17"
    INDIA = "Q668"
    SOUTH_KOREA = "Q884"

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
]

ARABIC_COUNTRIES = [
    WikidataEntities.EGYPT,
    WikidataEntities.SYRIA,
    WikidataEntities.SAUDI_ARABIA,
    WikidataEntities.LEBANON,
]

ASIAN_COUNTRIES = [
    WikidataEntities.CHINA,
    WikidataEntities.JAPAN,
    WikidataEntities.INDIA,
    WikidataEntities.SOUTH_KOREA,
]

OCCUPATIONS = [
    WikidataEntities.SCIENTIST,
    WikidataEntities.POLITICIAN,
    WikidataEntities.ARTIST,
    WikidataEntities.ATHLETE,
    WikidataEntities.WRITER,
]


# ============================================================================
# SPARQL QUERY TEMPLATES
# ============================================================================

SPARQL_PEOPLE_TEMPLATE = """
SELECT DISTINCT ?person ?personLabel ?birthDate ?birthPlace ?birthPlaceLabel
                ?nationality ?nationalityLabel ?occupation ?occupationLabel WHERE {{
  VALUES ?nationality {{ {nationalities} }}

  ?person wdt:{instance_of} wd:{human} .
  ?person wdt:{nationality_prop} ?nationality .
  ?person wdt:{birth_date} ?birthDate .
  ?person wdt:{birth_place} ?birthPlace .
  ?person wdt:{occupation_prop} ?occupation .

  FILTER(YEAR(?birthDate) > {min_year})
  FILTER(YEAR(?birthDate) < {max_year})

  SERVICE wikibase:label {{ bd:serviceParam wikibase:language "en". }}
}}
LIMIT {limit}
"""

SPARQL_DISCOVERIES_TEMPLATE = """
SELECT DISTINCT ?discovery ?discoveryLabel ?inventor ?inventorLabel
                ?date ?country ?countryLabel WHERE {{
  ?discovery wdt:{inventor_prop} ?inventor .
  ?discovery wdt:{date_prop} ?date .

  OPTIONAL {{ ?inventor wdt:{nationality_prop} ?country . }}

  FILTER(YEAR(?date) > {min_year})
  FILTER(YEAR(?date) < {max_year})

  SERVICE wikibase:label {{ bd:serviceParam wikibase:language "en". }}
}}
LIMIT {limit}
"""

SPARQL_PLACES_TEMPLATE = """
SELECT DISTINCT ?place ?placeLabel ?country ?countryLabel ?coords WHERE {{
  VALUES ?country {{ {countries} }}

  ?place wdt:{instance_of} wd:{city} .
  ?place wdt:{country_prop} ?country .
  ?place wdt:{coords_prop} ?coords .

  SERVICE wikibase:label {{ bd:serviceParam wikibase:language "en". }}
}}
LIMIT {limit}
"""

SPARQL_EVENTS_TEMPLATE = """
SELECT DISTINCT ?event ?eventLabel ?date ?location ?locationLabel WHERE {{
  VALUES ?eventType {{ {event_types} }}

  ?event wdt:{instance_of} ?eventType .
  ?event wdt:{date_prop} ?date .
  ?event wdt:{location_prop} ?location .

  FILTER(YEAR(?date) > {min_year})
  FILTER(YEAR(?date) < {max_year})

  SERVICE wikibase:label {{ bd:serviceParam wikibase:language "en". }}
}}
LIMIT {limit}
"""
