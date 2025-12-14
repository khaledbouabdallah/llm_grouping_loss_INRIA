"""
Wikipedia client with rate limiting and error handling
"""

import wikipedia
import time
import logging
from typing import Optional, Dict

logger = logging.getLogger(__name__)


class WikipediaClient:
    """Client for fetching Wikipedia articles with rate limiting"""

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
        Get Wikipedia page content

        Returns:
            Dict with 'title', 'content', 'url' or None if not found
        """
        self._rate_limit()

        for attempt in range(max_retries):
            try:
                page = wikipedia.page(entity_name, auto_suggest=auto_suggest)

                result = {
                    "title": page.title,
                    "content": page.content,
                    "url": page.url,
                    "summary": page.summary,
                }

                logger.info(
                    f"Fetched Wikipedia page: {page.title} ({len(page.content)} chars)"
                )
                return result

            except wikipedia.exceptions.DisambiguationError as e:
                logger.warning(f"Disambiguation for '{entity_name}': {e.options[:3]}")

                # Try first option
                if e.options:
                    try:
                        page = wikipedia.page(e.options[0], auto_suggest=False)
                        result = {
                            "title": page.title,
                            "content": page.content,
                            "url": page.url,
                            "summary": page.summary,
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
        logger.info(f"Changed Wikipedia language to: {language}")
