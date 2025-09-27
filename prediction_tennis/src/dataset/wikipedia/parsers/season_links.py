import re
import requests
import logging
from bs4 import BeautifulSoup
from typing import Dict, List


class ATPSeasonLinkExtractor:
    """
    A class to extract ATP season links from a Wikipedia page.

    This class provides methods to fetch webpage content, extract season links,
    and create a mapping of years to their corresponding Wikipedia URLs.
    """

    def __init__(self, base_url: str = "https://fr.wikipedia.org"):
        """
        Initialize the ATPSeasonLinkExtractor.

        Args:
            base_url (str, optional): Base URL for Wikipedia. Defaults to French Wikipedia.
        """
        self.base_url = base_url
        self.logger = logging.getLogger(__name__)

    def fetch_webpage_content(self, url: str) -> str:
        """
        Fetch the HTML content from the specified URL.

        Args:
            url (str): The webpage URL to fetch content from.

        Returns:
            str: HTML content as string if successful; otherwise, an empty string.
        """
        self.logger.info(f"Fetching webpage content from: {url}")
        headers = {"User-Agent": "Bot"}

        try:
            response = requests.get(url, headers=headers, timeout=10)
            response.raise_for_status()
            return response.text
        except requests.exceptions.RequestException as exc:
            self.logger.error(f"Failed to fetch content: {exc}")
            return ""

    def extract_season_links(self, html: str) -> List[str]:
        """
        Extract ATP season page links from the given HTML content.

        Args:
            html (str): HTML content to parse.

        Returns:
            List[str]: A list of season link strings that match the season URL pattern.
        """
        self.logger.info("Extracting ATP season links from HTML content")
        soup = BeautifulSoup(html, "html.parser")

        navbox_container = soup.find("div", class_="navbox-container")
        if navbox_container:
            nav_table = navbox_container.find("table", class_="navbox")

            if nav_table:
                # Process the correct table here
                self.logger.info("Table found")
            else:
                self.logger.info("Table not found inside navbox-container")
        else:
            self.logger.warning("No navigation table found in HTML content")
            return []

        # Extract all anchor tags with href matching the season pattern
        links = [
            anchor["href"]
            for anchor in nav_table.find_all("a", href=True)
            if anchor["href"].startswith("/wiki/Saison_")
        ]
        self.logger.info(f"Found {len(links)} season links")
        return links

    def process_season_links(self, links: List[str]) -> Dict[str, str]:
        """
        Process a list of season links to create a year-to-URL mapping.

        Args:
            links (List[str]): List of season links to process.

        Returns:
            Dict[str, str]: Dictionary with season year as key and full URL as value.
        """
        season_year_dict: Dict[str, str] = {}

        for link in links:
            # Extract a 4-digit year from each link using regex
            match = re.search(r"(\d{4})", link)
            if match:
                year = match.group(1)
                full_url = f"{self.base_url}{link}"
                season_year_dict[year] = full_url
                self.logger.debug(f"Extracted year {year} from link {full_url}")
            else:
                self.logger.warning(f"No year found in link: {link}")

        self.logger.info(f"Processed {len(season_year_dict)} season-year entries")
        return season_year_dict

    def extract_season_years(self, wikipedia_url: str) -> Dict[str, str]:
        """
        Extract a dictionary mapping season years to their corresponding links.

        Args:
            wikipedia_url (str): The URL of the Wikipedia page to scrape.

        Returns:
            Dict[str, str]: Dictionary with season year as key and season link as value.
        """
        self.logger.info(f"Starting extraction of season-year dictionary from {wikipedia_url}")

        # Fetch HTML content
        html_content = self.fetch_webpage_content(wikipedia_url)
        if not html_content:
            self.logger.error("No HTML content retrieved; aborting extraction")
            return {}

        # Extract season links
        season_links = self.extract_season_links(html_content)

        # Process links and return year-to-URL mapping
        return self.process_season_links(season_links)


if __name__ == "__main__":
    # Configure logging
    logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

    # Example usage
    wikipedia_url = "https://fr.wikipedia.org/wiki/ATP_Tour"
    extractor = ATPSeasonLinkExtractor()
    season_years = extractor.extract_season_years(wikipedia_url)

    for year, link in season_years.items():
        print(f"{year}: {link}")
