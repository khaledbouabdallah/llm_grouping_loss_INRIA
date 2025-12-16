"""
Wikipedia client with rate limiting, multilingual support, and metadata extraction
"""

import wikipedia
import requests
import time
import logging
from typing import Optional, Dict, List
import re

logger = logging.getLogger(__name__)


class WikipediaClient:
    """Client for fetching Wikipedia articles with rate limiting and metadata extraction"""

    def __init__(self, language: str = "en", rate_limit_delay: float = 0.1):
        """
        Args:
            language: Wikipedia language code ('en', 'ar', 'fr', etc.)
            rate_limit_delay: Seconds to wait between requests
        """
        self.language = language
        self.rate_limit_delay = rate_limit_delay
        self.last_request_time = 0
        wikipedia.set_lang(language)

    def _rate_limit(self):
        """Enforce rate limiting"""
        elapsed = time.time() - self.last_request_time
        if elapsed < self.rate_limit_delay:
            time.sleep(self.rate_limit_delay - elapsed)
        self.last_request_time = time.time()

    def get_page(
        self, entity_name: str, auto_suggest: bool = True, max_retries: int = 3
    ) -> Optional[Dict]:
        """
        Get Wikipedia page content with metadata

        Returns:
            Dict with 'title', 'content', 'url', 'summary', 'metadata' or None if not found
        """
        self._rate_limit()

        for attempt in range(max_retries):
            try:
                page = wikipedia.page(entity_name, auto_suggest=auto_suggest)

                # Extract metadata
                metadata = self._extract_metadata(
                    page.content, page.title, page.summary
                )

                result = {
                    "title": page.title,
                    "content": page.content,
                    "url": page.url,
                    "summary": page.summary,
                    "metadata": metadata,
                }

                logger.info(
                    f"Fetched Wikipedia page: {page.title} ({metadata['text_length_chars']} chars)"
                )
                return result

            except wikipedia.exceptions.DisambiguationError as e:
                logger.warning(f"Disambiguation for '{entity_name}': {e.options[:3]}")

                # Try first option
                if e.options:
                    try:
                        page = wikipedia.page(e.options[0], auto_suggest=False)
                        metadata = self._extract_metadata(
                            page.content, page.title, page.summary
                        )

                        result = {
                            "title": page.title,
                            "content": page.content,
                            "url": page.url,
                            "summary": page.summary,
                            "metadata": metadata,
                            "disambiguation": True,
                            "chosen_option": e.options[0],
                        }
                        logger.info(f"Used disambiguation option: {e.options[0]}")
                        return result
                    except Exception as inner_e:
                        logger.error(
                            f"Failed to fetch disambiguation option: {inner_e}"
                        )
                        return None

                return None

            except wikipedia.exceptions.PageError:
                logger.warning(f"Page not found: '{entity_name}'")
                return None

            except Exception as e:
                logger.error(
                    f"Wikipedia error for '{entity_name}' (attempt {attempt + 1}/{max_retries}): {e}"
                )
                if attempt < max_retries - 1:
                    time.sleep(1)
                else:
                    return None

        return None

    def _extract_metadata(self, content: str, title: str, summary: str) -> Dict:
        """
        Extract metadata from Wikipedia article content

        Returns dict with:
        - text_length_chars
        - text_length_words
        - summary_length
        - num_sections (approximate)
        """
        metadata = {
            "text_length_chars": len(content),
            "text_length_words": len(content.split()),
            "summary_length": len(summary),
            "num_sections": self._count_sections(content),
        }

        return metadata

    def _count_sections(self, content: str) -> int:
        """Count approximate number of sections (== headers)"""
        # Count lines that look like section headers
        # Wikipedia plaintext uses "\n\n" for sections or "==" markers in some cases
        sections = content.count("\n\n\n")  # Major breaks
        return max(sections, 1)  # At least 1 section

    def get_page_multilingual(
        self, entity_names: Dict[str, str], languages: List[str] = ["en", "fr", "ar"]
    ) -> Dict[str, Optional[Dict]]:
        """
        Fetch Wikipedia pages in multiple languages with metadata

        Args:
            entity_names: Dict mapping language codes to entity names
                         e.g., {"en": "Albert Einstein", "fr": "Albert Einstein", "ar": "ألبرت أينشتاين"}
            languages: List of language codes to fetch (default: ["en", "fr", "ar"])

        Returns:
            Dict mapping language codes to page data
            e.g., {"en": {title, content, url, summary, metadata}, "fr": {...}, "ar": {...}}
        """
        results = {}

        for lang in languages:
            entity_name = entity_names.get(lang)

            if not entity_name:
                logger.warning(f"No entity name provided for language: {lang}")
                results[lang] = None
                continue

            # Change language
            self.change_language(lang)

            # Fetch page with metadata
            page_data = self.get_page(entity_name)

            results[lang] = page_data

        return results

    def get_summary(self, entity_name: str, sentences: int = 3) -> Optional[str]:
        """Get Wikipedia summary (first few sentences)"""
        self._rate_limit()

        try:
            summary = wikipedia.summary(entity_name, sentences=sentences)
            logger.info(f"Fetched summary for: {entity_name}")
            return summary
        except Exception as e:
            logger.error(f"Failed to get summary for '{entity_name}': {e}")
            return None

    def search(self, query: str, results: int = 10) -> list:
        """Search Wikipedia"""
        self._rate_limit()

        try:
            search_results = wikipedia.search(query, results=results)
            logger.info(f"Search for '{query}': {len(search_results)} results")
            return search_results
        except Exception as e:
            logger.error(f"Search failed for '{query}': {e}")
            return []

    def change_language(self, language: str):
        """Change Wikipedia language"""
        self.language = language
        wikipedia.set_lang(language)
        logger.debug(f"Changed Wikipedia language to: {language}")

    def get_page_by_title(self, title: str, max_retries: int = 3) -> Optional[Dict]:
        """
        Get Wikipedia page by exact title (no search, no disambiguation)

        Args:
            title: Exact Wikipedia article title
            max_retries: Number of retry attempts

        Returns:
            Dict with page data or None if not found
        """
        self._rate_limit()

        for attempt in range(max_retries):
            try:
                # Fetch by exact title - no auto_suggest
                page = wikipedia.page(title, auto_suggest=False)

                # Extract metadata
                metadata = self._extract_metadata(
                    page.content, page.title, page.summary
                )

                result = {
                    "title": page.title,
                    "content": page.content,
                    "url": page.url,
                    "summary": page.summary,
                    "metadata": metadata,
                }

                logger.info(
                    f"Fetched Wikipedia page: {page.title} ({metadata['text_length_chars']} chars)"
                )
                return result

            except wikipedia.exceptions.PageError:
                logger.warning(f"Page not found by exact title: '{title}'")
                return None

            except Exception as e:
                logger.error(
                    f"Wikipedia error for '{title}' (attempt {attempt + 1}/{max_retries}): {e}"
                )
                if attempt < max_retries - 1:
                    time.sleep(1)
                else:
                    return None

        return None
