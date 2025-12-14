"""
Wikidata SPARQL client with rate limiting and error handling
"""

import requests
import time
import logging
from typing import Dict, List, Optional
from .config import (
    WikidataProperties as P,
    WikidataEntities as E,
    SPARQL_PEOPLE_TEMPLATE,
    SPARQL_DISCOVERIES_TEMPLATE,
    SPARQL_PLACES_TEMPLATE,
    SPARQL_EVENTS_TEMPLATE,
)

logger = logging.getLogger(__name__)


class WikidataClient:
    """Client for querying Wikidata with rate limiting"""

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
        """Parse SPARQL results into clean dictionaries"""
        parsed = []

        for result in results:
            item = {}
            for key, value in result.items():
                # Remove 'Label' suffix for cleaner keys
                clean_key = (
                    key.replace("Label", "_label") if key.endswith("Label") else key
                )

                # Extract value
                item[clean_key] = value["value"]

                # Extract Wikidata ID if it's an entity URI
                if "http://www.wikidata.org/entity/" in value["value"]:
                    item[f"{clean_key}_id"] = value["value"].split("/")[-1]

            parsed.append(item)

        return parsed

    def get_people(
        self,
        nationalities: List[str],
        limit: int = 100,
        min_year: int = 1850,
        max_year: int = 2000,
    ) -> List[Dict]:
        """Get people with specified nationalities"""

        nationality_list = " ".join([f"wd:{n}" for n in nationalities])

        query = SPARQL_PEOPLE_TEMPLATE.format(
            nationalities=nationality_list,
            instance_of=P.INSTANCE_OF,
            human=E.HUMAN,
            nationality_prop=P.NATIONALITY,
            birth_date=P.BIRTH_DATE,
            birth_place=P.BIRTH_PLACE,
            occupation_prop=P.OCCUPATION,
            min_year=min_year,
            max_year=max_year,
            limit=limit,
        )

        logger.info(f"Querying {len(nationalities)} nationalities, limit={limit}")
        return self.query(query)

    def get_discoveries(
        self, limit: int = 50, min_year: int = 1800, max_year: int = 2000
    ) -> List[Dict]:
        """Get scientific discoveries/inventions"""

        query = SPARQL_DISCOVERIES_TEMPLATE.format(
            inventor_prop=P.INVENTOR,
            date_prop=P.DISCOVERY_DATE,
            nationality_prop=P.NATIONALITY,
            min_year=min_year,
            max_year=max_year,
            limit=limit,
        )

        logger.info(f"Querying discoveries, limit={limit}")
        return self.query(query)

    def get_places(self, countries: List[str], limit: int = 50) -> List[Dict]:
        """Get cities from specified countries"""

        country_list = " ".join([f"wd:{c}" for c in countries])

        query = SPARQL_PLACES_TEMPLATE.format(
            countries=country_list,
            instance_of=P.INSTANCE_OF,
            city=E.CITY,
            country_prop=P.COUNTRY,
            coords_prop=P.COORDINATES,
            limit=limit,
        )

        logger.info(f"Querying places in {len(countries)} countries, limit={limit}")
        return self.query(query)

    def get_events(
        self,
        event_types: List[str],
        limit: int = 50,
        min_year: int = 1850,
        max_year: int = 2000,
    ) -> List[Dict]:
        """Get historical events of specified types"""

        event_type_list = " ".join([f"wd:{e}" for e in event_types])

        query = SPARQL_EVENTS_TEMPLATE.format(
            event_types=event_type_list,
            instance_of=P.INSTANCE_OF,
            date_prop=P.POINT_IN_TIME,
            location_prop=P.LOCATION,
            min_year=min_year,
            max_year=max_year,
            limit=limit,
        )

        logger.info(f"Querying events, limit={limit}")
        return self.query(query)

    def get_entity_facts(self, wikidata_id: str) -> Dict:
        """Get all facts for a single entity"""
        query = f"""
        SELECT ?prop ?propLabel ?value ?valueLabel WHERE {{
          wd:{wikidata_id} ?p ?value .
          ?prop wikibase:directClaim ?p .

          SERVICE wikibase:label {{ bd:serviceParam wikibase:language "en". }}
        }}
        LIMIT 100
        """

        results = self.query(query)

        # Group by property
        facts = {}
        for result in results:
            prop_id = result.get("prop_id", result.get("prop"))
            if prop_id:
                if prop_id not in facts:
                    facts[prop_id] = []
                facts[prop_id].append(
                    {
                        "value": result.get("value"),
                        "value_label": result.get("value_label"),
                    }
                )

        return facts
