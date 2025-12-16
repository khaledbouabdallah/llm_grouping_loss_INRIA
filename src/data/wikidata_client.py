"""
Wikidata SPARQL client with rate limiting and multilingual support
"""

import requests
import time
import logging
from typing import Dict, List, Optional
from .config import (
    WikidataProperties as P,
    WikidataEntities as E,
    SPARQL_PEOPLE_MULTILINGUAL_TEMPLATE,
    SPARQL_EVENTS_MULTILINGUAL_TEMPLATE,
    SPARQL_DISCOVERIES_MULTILINGUAL_TEMPLATE,
    SPARQL_PLACES_MULTILINGUAL_TEMPLATE,
    EVENT_TYPES,
)

logger = logging.getLogger(__name__)


class WikidataClient:
    """Client for querying Wikidata with rate limiting and multilingual support"""

    ENDPOINT = "https://query.wikidata.org/sparql"

    def __init__(self, rate_limit_delay: float = 1.0):
        """
        Args:
            rate_limit_delay: Seconds to wait between requests
        """
        self.rate_limit_delay = rate_limit_delay
        self.last_request_time = 0
        self.session = requests.Session()
        self.session.headers.update(
            {"User-Agent": "LLMGroupingLossResearch/1.0 (Educational Research)"}
        )

    def _rate_limit(self):
        """Enforce rate limiting"""
        elapsed = time.time() - self.last_request_time
        if elapsed < self.rate_limit_delay:
            time.sleep(self.rate_limit_delay - elapsed)
        self.last_request_time = time.time()

    def query(self, sparql_query: str, max_retries: int = 3) -> List[Dict]:
        """
        Execute SPARQL query with retries

        Returns:
            List of result dictionaries
        """
        self._rate_limit()

        params = {"query": sparql_query, "format": "json"}

        for attempt in range(max_retries):
            try:
                response = self.session.get(self.ENDPOINT, params=params, timeout=60)
                response.raise_for_status()

                data = response.json()
                results = data["results"]["bindings"]

                logger.info(f"Query successful: {len(results)} results")
                return self._parse_results(results)

            except requests.exceptions.Timeout:
                logger.warning(f"Query timeout (attempt {attempt + 1}/{max_retries})")
                if attempt < max_retries - 1:
                    time.sleep(2**attempt)  # Exponential backoff
                else:
                    raise

            except requests.exceptions.RequestException as e:
                logger.error(f"Query failed: {e}")
                if attempt < max_retries - 1:
                    time.sleep(2**attempt)
                else:
                    raise

        return []

    def _parse_results(self, results: List[Dict]) -> List[Dict]:
        """Parse SPARQL results into clean dictionaries with Arabic fallback"""
        parsed = []

        for result in results:
            item = {}
            for key, value in result.items():
                # Extract value
                item[key] = value["value"]

                # Extract Wikidata ID if it's an entity URI
                if "http://www.wikidata.org/entity/" in value["value"]:
                    # Remove language suffix if present (e.g., "personLabel_en" -> "person")
                    base_key = key.split("_")[0] if "_" in key else key
                    item[f"{base_key}_id"] = value["value"].split("/")[-1]

            # Handle Arabic fallback: if ar is missing, use arz
            item = self._apply_arabic_fallback(item)

            parsed.append(item)

        return parsed

    def _apply_arabic_fallback(self, item: Dict) -> Dict:
        """
        Apply Arabic fallback logic: prioritize 'ar', use 'arz' if 'ar' is missing
        Adds metadata about which Arabic variant was used
        """
        # Find all keys that have Arabic variants
        keys_with_ar = [k.replace("_ar", "") for k in item.keys() if k.endswith("_ar")]

        for base_key in keys_with_ar:
            ar_key = f"{base_key}_ar"
            arz_key = f"{base_key}_arz"

            # If ar exists, use it and mark as 'ar'
            if item.get(ar_key):
                item[f"{base_key}_arabic_variant"] = "ar"
            # If ar missing but arz exists, copy arz to ar and mark as 'arz'
            elif item.get(arz_key):
                item[ar_key] = item[arz_key]
                item[f"{base_key}_arabic_variant"] = "arz"
                logger.debug(f"Using Egyptian Arabic (arz) fallback for {base_key}")
            else:
                # Neither exists
                item[f"{base_key}_arabic_variant"] = None

        return item

    def get_people_multilingual(
        self,
        nationalities: List[str],
        limit: int = 100,
        min_year: int = 1850,
        max_year: int = 2000,
    ) -> List[Dict]:
        """
        Get people with specified nationalities, returning labels in en, fr, ar

        Note: Results are in random order (no ORDER BY to avoid timeout).
        Max limit: 10000 per query. For more, split by nationality or year range.
        """

        nationality_list = " ".join([f"wd:{n}" for n in nationalities])

        query = SPARQL_PEOPLE_MULTILINGUAL_TEMPLATE.format(
            nationalities=nationality_list,
            instance_of=P.INSTANCE_OF,
            human=E.HUMAN,
            nationality_prop=P.NATIONALITY,
            birth_date=P.BIRTH_DATE,
            birth_place=P.BIRTH_PLACE,
            occupation_prop=P.OCCUPATION,
            gender_prop=P.GENDER,
            death_date=P.DEATH_DATE,
            min_year=min_year,
            max_year=max_year,
            limit=limit,
        )

        logger.info(
            f"Querying {len(nationalities)} nationalities (multilingual), limit={limit}"
        )
        return self.query(query)

    def get_sitelinks_count(self, wikidata_id: str) -> int:
        """
        Get count of Wikipedia language versions for an entity
        Fetches via Wikidata API (much faster than SPARQL aggregation)

        Args:
            wikidata_id: Wikidata ID (e.g., 'Q937')

        Returns:
            Count of Wikipedia language versions (0 if error)
        """
        self._rate_limit()

        url = f"https://www.wikidata.org/wiki/Special:EntityData/{wikidata_id}.json"

        try:
            response = self.session.get(url, timeout=10)
            response.raise_for_status()
            data = response.json()

            sitelinks = data["entities"][wikidata_id].get("sitelinks", {})

            # Count only Wikipedia sites (exclude Wikiquote, Wiktionary, etc.)
            # Wikipedia site keys end with 'wiki' but not 'wikiquote', 'wikisource', etc.
            wikipedia_count = sum(
                1
                for key in sitelinks.keys()
                if key.endswith("wiki")
                and "quote" not in key
                and "source" not in key
                and "books" not in key
                and "versity" not in key
                and "voyage" not in key
                and "news" not in key
            )

            logger.debug(f"Sitelinks for {wikidata_id}: {wikipedia_count}")
            return wikipedia_count

        except Exception as e:
            logger.warning(f"Failed to get sitelinks for {wikidata_id}: {e}")
            return 0

    def get_wikipedia_titles(self, wikidata_id: str) -> dict:
        """
        Get exact Wikipedia article titles from Wikidata sitelinks
        Returns dict: {'en': 'Article_Title', 'fr': 'Titre', 'ar': 'عنوان'}

        This is MORE RELIABLE than searching by entity name!
        """
        self._rate_limit()

        url = f"https://www.wikidata.org/wiki/Special:EntityData/{wikidata_id}.json"

        try:
            response = self.session.get(url, timeout=10)
            response.raise_for_status()
            data = response.json()

            sitelinks = data["entities"][wikidata_id].get("sitelinks", {})

            titles = {}

            # Extract titles for each language
            if "enwiki" in sitelinks:
                titles["en"] = sitelinks["enwiki"]["title"]
            if "frwiki" in sitelinks:
                titles["fr"] = sitelinks["frwiki"]["title"]
            if "arwiki" in sitelinks:
                titles["ar"] = sitelinks["arwiki"]["title"]

            logger.debug(f"Wikipedia titles for {wikidata_id}: {titles}")
            return titles

        except Exception as e:
            logger.warning(f"Failed to get Wikipedia titles for {wikidata_id}: {e}")
            return {}

    def get_entity_labels(
        self, wikidata_id: str, languages: list = ["en", "fr", "ar"]
    ) -> dict:
        """
        Get labels for an entity in multiple languages via Wikidata API
        Much faster than fetching via SPARQL OPTIONAL clauses

        Args:
            wikidata_id: Wikidata ID (e.g., 'Q937')
            languages: List of language codes

        Returns:
            Dict: {'en': 'Label', 'fr': 'Libellé', 'ar': 'تسمية'}
        """
        self._rate_limit()

        url = f"https://www.wikidata.org/wiki/Special:EntityData/{wikidata_id}.json"

        try:
            response = self.session.get(url, timeout=10)
            response.raise_for_status()
            data = response.json()

            labels_data = data["entities"][wikidata_id].get("labels", {})

            labels = {}
            for lang in languages:
                if lang in labels_data:
                    labels[lang] = labels_data[lang]["value"]
                # Try arz fallback for ar
                elif lang == "ar" and "arz" in labels_data:
                    labels[lang] = labels_data["arz"]["value"]

            return labels

        except Exception as e:
            logger.debug(f"Failed to get labels for {wikidata_id}: {e}")
            return {}

    def get_events_multilingual(
        self,
        event_types: List[str] = None,
        limit: int = 50,
        offset: int = 0,
        min_year: int = 1800,
        max_year: int = 2000,
        order_asc: bool = True,
    ) -> List[Dict]:
        """Get events with specified types, returning labels in en, fr, ar"""

        if event_types is None:
            event_types = EVENT_TYPES

        event_type_list = " ".join([f"wd:{e}" for e in event_types])
        order_direction = "ASC" if order_asc else "DESC"

        query = SPARQL_EVENTS_MULTILINGUAL_TEMPLATE.format(
            event_types=event_type_list,
            instance_of=P.INSTANCE_OF,
            date_prop=P.POINT_IN_TIME,
            location_prop=P.LOCATION,
            min_year=min_year,
            max_year=max_year,
            order_direction=order_direction,
            limit=limit,
            offset=offset,
        )

        logger.info(
            f"Querying {len(event_types)} event types (multilingual), limit={limit}, offset={offset}"
        )
        return self.query(query)

    def get_discoveries_multilingual(
        self,
        limit: int = 50,
        offset: int = 0,
        min_year: int = 1800,
        max_year: int = 2000,
        order_asc: bool = True,
    ) -> List[Dict]:
        """Get discoveries/inventions, returning labels in en, fr, ar"""

        order_direction = "ASC" if order_asc else "DESC"

        query = SPARQL_DISCOVERIES_MULTILINGUAL_TEMPLATE.format(
            inventor_prop=P.INVENTOR,
            date_prop=P.DISCOVERY_DATE,
            nationality_prop=P.NATIONALITY,
            min_year=min_year,
            max_year=max_year,
            order_direction=order_direction,
            limit=limit,
            offset=offset,
        )

        logger.info(
            f"Querying discoveries (multilingual), limit={limit}, offset={offset}"
        )
        return self.query(query)

    def get_places_multilingual(
        self,
        countries: List[str],
        limit: int = 50,
        offset: int = 0,
        order_asc: bool = True,
    ) -> List[Dict]:
        """Get places/cities from specified countries, returning labels in en, fr, ar"""

        country_list = " ".join([f"wd:{c}" for c in countries])
        order_direction = "ASC" if order_asc else "DESC"

        query = SPARQL_PLACES_MULTILINGUAL_TEMPLATE.format(
            countries=country_list,
            instance_of=P.INSTANCE_OF,
            city=E.CITY,
            capital=E.CAPITAL_CITY,
            big_city=E.BIG_CITY,
            country_prop=P.COUNTRY,
            coords_prop=P.COORDINATES,
            population_prop=P.POPULATION,
            order_direction=order_direction,
            limit=limit,
            offset=offset,
        )

        logger.info(
            f"Querying places in {len(countries)} countries (multilingual), limit={limit}, offset={offset}"
        )
        return self.query(query)
