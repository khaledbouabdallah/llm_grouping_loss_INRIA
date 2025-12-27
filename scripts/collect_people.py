"""
Comprehensive Data Collection Script - Country by Country
Collects People, Events, Discoveries, Places with pre-filtering for existing entities
"""

from src.data import (
    EntityDatabase,
    WikidataClient,
    WikipediaClient,
    COUNTRY_METADATA,
)
from src.utils import setup_logging
import logging
import time
from datetime import datetime

setup_logging(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize clients
db = EntityDatabase("data/entities.db")
wikidata = WikidataClient(rate_limit_delay=0.1)  # Fast since labels in SPARQL

# Create separate Wikipedia clients for each language to avoid API bugs
wikipedia_clients = {
    "en": WikipediaClient(language="en", rate_limit_delay=0.1),
    "fr": WikipediaClient(language="fr", rate_limit_delay=0.1),
    "ar": WikipediaClient(language="ar", rate_limit_delay=0.1),
}


def has_complete_labels(entity, entity_type_key="person"):
    """Check if entity has complete labels in en, fr, ar"""
    required_keys = [
        f"{entity_type_key}Label_en",
        f"{entity_type_key}Label_fr",
    ]

    for key in required_keys:
        if not entity.get(key):
            return False

    # Check ar (fallback already applied)
    ar_key = f"{entity_type_key}Label_ar"
    if not entity.get(ar_key):
        return False

    return True


def collect_people_for_country(
    country_code: str, country_name: str, culture_group: str, limit: int = 10000
) -> int:
    """
    Collect people for a single country with pre-filtering
    """
    logger.info("=" * 80)
    logger.info(
        f"COLLECTING: {country_name} ({country_code}) - Culture: {culture_group}"
    )
    logger.info("=" * 80)

    start_time = time.time()

    # Step 1: Query SPARQL
    logger.info(f"Step 1/7: Querying Wikidata for {country_name}...")
    people = wikidata.get_people_multilingual(
        nationalities=[country_code],
        limit=limit,
        min_year=1850,
        max_year=2000,
    )
    logger.info(f"Got {len(people)} results from SPARQL")

    # Step 2: Deduplicate by person ID
    logger.info("Step 2/7: Deduplicating by person ID...")
    seen_ids = set()
    unique_people = []
    for person in people:
        person_id = person["person"].split("/")[-1]
        if person_id not in seen_ids:
            seen_ids.add(person_id)
            unique_people.append(person)

    duplicates_removed = len(people) - len(unique_people)
    logger.info(
        f"Deduplicated to {len(unique_people)} unique people ({duplicates_removed} SPARQL duplicates removed)"
    )
    people = unique_people

    # Step 3: Pre-filter entities already in DB
    logger.info("Step 3/7: Checking which entities already exist in database...")
    new_people = []
    existing_count = 0

    for person in people:
        wikidata_id = person["person"].split("/")[-1]
        if not db.entity_exists(wikidata_id):
            new_people.append(person)
        else:
            existing_count += 1

    logger.info(
        f"Pre-filtered: {len(new_people)} new entities, {existing_count} already in DB ({existing_count*100/len(people):.1f}% already collected)"
    )
    people = new_people

    if len(people) == 0:
        logger.info(f"✅ All entities for {country_name} already in database!")
        return

    # Step 4: Validate missing fields
    logger.info("Step 4/7: Validating entities (checking for missing fields)...")
    filtered_count = 0
    missing_fields_log = []

    for person in people:
        missing = []
        if not has_complete_labels(person, "person"):
            missing.append("person_labels")
        if not person.get("birthPlaceLabel_en"):
            missing.append("birthPlace_labels")
        if not person.get("nationalityLabel_en"):
            missing.append("nationality_labels")
        if not person.get("occupationLabel_en"):
            missing.append("occupation_labels")

        if missing:
            filtered_count += 1
            wikidata_id = person["person"].split("/")[-1]
            missing_fields_log.append(
                {
                    "wikidata_id": wikidata_id,
                    "wikidata_url": f"https://www.wikidata.org/wiki/{wikidata_id}",
                    "person_name": person.get("personLabel_en", "N/A"),
                    "missing_fields": missing,
                }
            )

    logger.info(
        f"Found {filtered_count} entities with missing fields (will be filtered)"
    )

    # Step 5: Filter to complete entities
    logger.info("Step 5/7: Filtering entities with complete labels...")
    complete_people = [
        p
        for p in people
        if has_complete_labels(p, "person")
        and p.get("birthPlaceLabel_en")
        and p.get("nationalityLabel_en")
        and p.get("occupationLabel_en")
    ]

    filtered_out = len(people) - len(complete_people)
    logger.info(
        f"Filtered to {len(complete_people)} entities with complete labels ({filtered_out} removed)"
    )

    if len(complete_people) == 0:
        logger.warning(f"No complete entities to collect for {country_name}")
        return

    # Step 6: Fetch Wikipedia and store
    logger.info("Step 6/7: Fetching Wikipedia texts and storing in database...")

    stored_count = 0
    wiki_errors = 0

    for i, person in enumerate(complete_people, 1):
        if i % 10 == 0:
            elapsed = time.time() - start_time
            rate = i / elapsed if elapsed > 0 else 0
            remaining = (len(complete_people) - i) / rate if rate > 0 else 0
            logger.info(
                f"  Processing entity {i}/{len(complete_people)} ({i*100//len(complete_people)}%, {stored_count} stored so far) - ETA: {remaining/60:.1f}min"
            )

        try:
            wikidata_id = person["person"].split("/")[-1]

            # Add entity to database
            entity_id = db.add_entity(
                wikidata_id=wikidata_id,
                entity_type="person",
                culture=culture_group,
                country=country_name,
            )

            if entity_id is None:
                continue

            # Add labels
            db.add_entity_label(entity_id, "en", person.get("personLabel_en"))
            db.add_entity_label(entity_id, "fr", person.get("personLabel_fr"))
            db.add_entity_label(entity_id, "ar", person.get("personLabel_ar"))

            # Add facts with labels
            facts_to_add = [
                ("birthDate", person.get("birthDate"), {}),
                ("deathDate", person.get("deathDate"), {}),
                ("gender", person.get("gender"), {}),
                (
                    "birthPlace",
                    person.get("birthPlace"),
                    {
                        "en": person.get("birthPlaceLabel_en"),
                        "fr": person.get("birthPlaceLabel_fr"),
                        "ar": person.get("birthPlaceLabel_ar"),
                    },
                ),
                (
                    "nationality",
                    person.get("nationality"),
                    {
                        "en": person.get("nationalityLabel_en"),
                        "fr": person.get("nationalityLabel_fr"),
                        "ar": person.get("nationalityLabel_ar"),
                    },
                ),
                (
                    "occupation",
                    person.get("occupation"),
                    {
                        "en": person.get("occupationLabel_en"),
                        "fr": person.get("occupationLabel_fr"),
                        "ar": person.get("occupationLabel_ar"),
                    },
                ),
            ]

            for prop, value, labels in facts_to_add:
                if value:
                    fact_id = db.add_fact(entity_id, prop, value)
                    if fact_id and labels:
                        for lang, label in labels.items():
                            if label:
                                db.add_fact_label(fact_id, lang, label)

            # Fetch num_wikipedia_languages
            num_langs = wikidata.get_sitelinks_count(wikidata_id)
            db.add_metadata(entity_id, "num_wikipedia_languages", str(num_langs))

            # Fetch Wikipedia texts
            for lang in ["en", "fr", "ar"]:
                lang_label = person.get(f"personLabel_{lang}")
                logger.info(
                    f"Attempting to fetch {lang} Wikipedia for '{lang_label}' (entity: {wikidata_id})"
                )

                if lang_label:
                    try:
                        # Use language-specific client to avoid API bugs
                        wiki_client = wikipedia_clients[lang]
                        logger.info(
                            f"Using {lang} Wikipedia client (language: {wiki_client.language})"
                        )

                        wiki_page = wiki_client.get_page(lang_label)

                        if wiki_page:
                            logger.info(
                                f"Successfully fetched {lang} Wikipedia page: {wiki_page['title']}"
                            )
                            db.add_wikipedia_text(
                                entity_id=entity_id,
                                language=lang,
                                title=wiki_page["title"],
                                summary=wiki_page["summary"],
                                content=wiki_page["content"],
                                url=wiki_page["url"],
                                text_length_chars=wiki_page["metadata"][
                                    "text_length_chars"
                                ],
                                text_length_words=wiki_page["metadata"][
                                    "text_length_words"
                                ],
                                num_sections=wiki_page["metadata"]["num_sections"],
                            )
                        else:
                            logger.warning(
                                f"get_page() returned None for '{lang_label}' in {lang}"
                            )
                    except Exception as e:
                        logger.error(
                            f"Exception fetching {lang} Wikipedia for '{lang_label}': {e}"
                        )
                        wiki_errors += 1

            stored_count += 1

        except Exception as e:
            logger.error(f"Error processing entity {i}: {e}")
            continue

    # Step 7: Summary
    elapsed = time.time() - start_time
    logger.info("=" * 80)
    logger.info(f"COMPLETED: {country_name}")
    logger.info(f"  Total time: {elapsed/60:.1f} minutes")
    logger.info(
        f"  SPARQL results: {len(people) + existing_count} (with {duplicates_removed} duplicates)"
    )
    logger.info(
        f"  Already in DB: {existing_count} ({existing_count*100/(len(people)+existing_count):.1f}%)"
    )
    logger.info(f"  New entities: {len(people)}")
    logger.info(f"  Filtered out (incomplete): {filtered_out}")
    logger.info(f"  Successfully stored: {stored_count}")
    logger.info("=" * 80)
    return stored_count


def collect_all_people():
    """
    Collect all people country by country across all culture groups
    """
    logger.info("\n" + "=" * 80)
    logger.info("STARTING COMPREHENSIVE PEOPLE COLLECTION")
    logger.info(f"Timestamp: {datetime.now().isoformat()}")
    logger.info("=" * 80 + "\n")

    total_start = time.time()

    countries_processed = 0
    total_stored = 0

    # Iterate through all countries in COUNTRY_METADATA
    for country_code, (country_name, culture_group) in COUNTRY_METADATA.items():
        try:
            stored_count = collect_people_for_country(
                country_code=country_code,
                country_name=country_name,
                culture_group=culture_group,
                limit=10000,
            )
            if stored_count:
                total_stored += stored_count
            countries_processed += 1
        except Exception as e:
            logger.error(f"Failed to collect {country_name}: {e}")
            continue

    # Final summary
    total_elapsed = time.time() - total_start
    logger.info("\n" + "=" * 80)
    logger.info("COLLECTION COMPLETE")
    logger.info(
        f"  Total time: {total_elapsed/60:.1f} minutes ({total_elapsed/3600:.1f} hours)"
    )
    logger.info(f"  Countries processed: {countries_processed}")
    logger.info(f"  Total new people stored: {total_stored}")
    logger.info(f"  Database path: {db.db_path}")
    logger.info("=" * 80 + "\n")


if __name__ == "__main__":
    collect_all_people()
