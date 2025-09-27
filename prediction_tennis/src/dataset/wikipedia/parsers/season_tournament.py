import re
import unicodedata
import requests
import logging
from typing import List, Dict, Set
from bs4 import BeautifulSoup, Tag

from prediction_tennis.src.dataset.wikipedia.models.tournaments import Tournaments


class ATPSeasonParser:
    """
    Parser for extracting ATP season tournament data from Wikipedia.

    This class fetches and parses HTML content from a Wikipedia page,
    extracting structured tournament information based on specific 
    color-coded table rows.

    Attributes:
        url (str): URL of the Wikipedia ATP season page.
        year (str): Year of the ATP season being parsed.
    """

    # Mapping of row background colors to tournament categories
    TOURNAMENT_MAPPING: Dict[str, str] = {
        "Int'Series"   : "ATP 250",
        "ATP250"       : "ATP 250",
        "SeriesGold"   : "ATP 500",
        "ATP500"       : "ATP 500",
        "MastersSeries": "ATP 1000",
        "Masters1000"  : "ATP 1000",
        "Super9"       : "ATP 1000",
        "Masters"      : "Masters Cup",
        "G.Chelem"     : "Grand Chelem",
        "J.olympiques" : "JO",
    }

    # Mapping of French surface labels to English descriptions
    SURFACE_MAPPING: Dict[str, str] = {
        "Dur(ext.)": "hard (extern)",
        "Dur(int.)": "hard (intern)",
        "Terre(ext.)": "clay (extern)",
        "Terre(int.)": "clay (intern)",
        "Gazon(ext.)": "grass (extern)",
        "Moquette(int.)": "carpet (intern)",
        "Moquette(ext.)": "carpet (extern)",
    }

    def __init__(self) -> None:
        self.url : str = ""
        self.year: str = ""
        self.logger = logging.getLogger(f"[SEASON {self.year}]")

    def initialize_variables(self, url: str, year: str):
        self.url : str = url
        self.year: str = year
        self.logger = logging.getLogger(f"[SEASON {self.year}]")

    def fetch_webpage_content(self) -> str:
        """
        Fetch HTML content from the specified URL.

        Returns:
            str: HTML content as a string. Empty string if fetch fails.
        """
        self.logger.info(f"Fetching webpage content from: {self.url}")
        headers = {"User-Agent": "Bot"}
        try:
            response = requests.get(self.url,headers=headers, timeout=10)
            response.raise_for_status()
            return response.text
        except requests.exceptions.RequestException as exc:
            self.logger.error(f"Failed to fetch content: {exc}")
            return ""

    def extract_tournament_type(self, tournament_type: str) -> str:
        """
        Extract and map tournament type from raw input.

        Args:
            tournament_type (str): Raw tournament type string.

        Returns:
            str: Mapped tournament category.

        Raises:
            NotImplementedError: If tournament type is not recognized.
        """
        cleaned_type = tournament_type.replace('\xa0', '').replace(" ", "").strip()
        mapped_type = self.TOURNAMENT_MAPPING.get(cleaned_type)
        
        if mapped_type is None:
            error_msg = f"Tournament type '{cleaned_type}' is not implemented yet."
            self.logger.error(error_msg)
            raise NotImplementedError(error_msg)
        
        return mapped_type

    def extract_prize_money(self, prize_str: str) -> int:
        """
        Extract prize money from raw input string and convert from EUR, GBP, or AUD to USD if necessary.

        Args:
            prize_str (str): Raw prize money string.

        Returns:
            int: Prize money as an integer in USD.

        Raises:
            ValueError: If prize money cannot be converted to integer.
        """
        exchange_rate_eur = 1.08  # EUR to USD conversion rate
        exchange_rate_gbp = 1.25  # GBP to USD conversion rate
        exchange_rate_aud = 0.64  # AUD to USD conversion rate
        
        is_euro = "€" in prize_str
        is_pound = "£" in prize_str
        is_aud = "A$" in prize_str or "AU$" in prize_str

        cleaned_prize = (
            prize_str.replace('\xa0', '')
            .replace('AU$', '')
            .replace('A$', '')
            .replace('$', '')
            .replace('€', '')
            .replace('£', '')
            .replace(',', '')
            .replace('[c]', '')
        )

        try:
            if cleaned_prize == "NC":
                return 0
            
            prize_money = int(cleaned_prize)

            # Convert from EUR to USD
            if is_euro:
                prize_money = int(prize_money * exchange_rate_eur)

            # Convert from GBP to USD
            elif is_pound:
                prize_money = int(prize_money * exchange_rate_gbp)

            # Convert from AUD to USD
            elif is_aud:
                prize_money = int(prize_money * exchange_rate_aud)
            
            return prize_money

        except ValueError as exc:
            error_msg = f"Could not convert prize money to integer: {prize_str} => {cleaned_prize}"
            self.logger.warning(error_msg)
            raise ValueError(error_msg) from exc

    def extract_surface(self, surface_str: str) -> str:
        """
        Extract and map surface description from French to English.

        Args:
            surface_str (str): Raw surface description.

        Returns:
            str: Mapped surface description.

        Raises:
            NotImplementedError: If surface type is not recognized.
        """
        cleaned_surface = surface_str.replace('\xa0', '').replace(" ", "").strip()
        mapped_surface = self.SURFACE_MAPPING.get(cleaned_surface)
        
        if mapped_surface is None:
            error_msg = f"Surface type '{cleaned_surface}' is not implemented yet."
            self.logger.error(error_msg)
            raise NotImplementedError(error_msg)
        
        return mapped_surface

    def handle_special_case_number_suffix(self, name_segments: List[str]) -> str:
        """
        Handle special cases where the first segment ends with a digit.

        Args:
            name_segments (List[str]): Segments of the tournament name.

        Returns:
            str: The extracted number suffix or an empty string if not applicable.
        """
        if len(name_segments) == 2 and name_segments[0][-1].isdigit():
            trailing_digit: str = name_segments[0][-1].strip()
            city: str = name_segments[1].strip()

            self.logger.debug("Extracted trailing digit '%s' and city '%s'", trailing_digit, city)

            # If the city is 'marseille', do not modify the name
            if city in ["Marseille", "Valence","Vienne"]:
                self.logger.debug("Skipping number suffix modification for city: %s", city)
                return ""

            # If the trailing digit is not "1", use it as a suffix.
            return f"-{trailing_digit}" if trailing_digit != "1" else ""

        return ""

    def handle_special_case_new_york(self, name_segments: List[str], standardized_name: str) -> str:
        """
        Handle special case for the "New York" tournament, considering "US Open".

        Args:
            name_segments (List[str]): Segments of the tournament name.
            standardized_name (str): The standardized tournament name.

        Returns:
            str: The updated tournament name if it falls under the special case.
        """
        if standardized_name == "new-york":
            first_segment: str = name_segments[0].strip().lower().replace(" ", "-")
            
            # If "us-open" is present in the first part, use it instead
            if "us-open" in first_segment:
                self.logger.debug(
                    "Special case for 'new-york' detected; using alternative name: %s",
                    first_segment,
                )
                return first_segment
            elif "western-&-southern-open" in first_segment:
                return "cincinnati" # covid effect

        return standardized_name

    def handle_special_case_paris(self, name_segments: List[str], standardized_name: str) -> str:
        """
        Handle special case for the "Paris" tournament, considering "Roland-Garros".

        Args:
            name_segments (List[str]): Segments of the tournament name.
            standardized_name (str): The standardized tournament name.

        Returns:
            str: The updated tournament name if it falls under the special case.
        """
        if standardized_name == "paris":
            first_segment: str = name_segments[0].strip().lower().replace(" ", "-")
            if "roland-garros" in first_segment:
                self.logger.debug(
                    "Special case for 'paris' detected; using alternative name: %s",
                    first_segment,
                )
                return first_segment
        return standardized_name
    
    def handle_special_case_atlanta(self, name_segments: List[str], standardized_name: str) -> str:
        """
        Handle special case for the "Atlanta" tournament, considering "Verizon Tennis Challenge".

        Args:
            name_segments (List[str]): Segments of the tournament name.
            standardized_name (str): The standardized tournament name.

        Returns:
            str: The updated tournament name if it falls under the special case.
        """
        if standardized_name == "atlanta":
            first_segment: str = name_segments[0].strip().lower().replace(" ", "-")
            
            if "verizon-tennis-challenge" in first_segment:
                self.logger.debug(
                    "Special case for 'atlanta' detected; using alternative name: %s",
                    first_segment,
                )
                return first_segment

        return standardized_name

    def handle_special_case_long_island(self, name_segments: List[str], standardized_name: str) -> str:
        """
        Handle special case for the "Long Island" tournament, considering "US Open".

        Args:
            name_segments (List[str]): Segments of the tournament name.
            standardized_name (str): The standardized tournament name.

        Returns:
            str: The updated tournament name if it falls under the special case; otherwise, an empty string.
        """
        if standardized_name == "long-island":
            first_segment: str = name_segments[0].strip().lower().replace(" ", "-")

            if "us-open" in first_segment:
                self.logger.debug(
                    "Special case for 'long-island' detected; using alternative name: %s",
                    first_segment,
                )
                return "us-open"
            
            elif "new-york-open" in first_segment:
                return "new-york"
            
        return standardized_name

    def handle_special_case_nitto_atp(self, name_segments: List[str], standardized_name: str) -> str:
        """
        Handle special case for ATP Finals tournaments with various naming conventions.

        Args:
            name_segments (List[str]): Segments of the tournament name.
            standardized_name (str): The standardized tournament name.

        Returns:
            str: The updated tournament name if a special case is detected; otherwise, the original standardized name.
        """
        nitto_atp_keywords: Set[str] = {
            "atp tour world championships",
            "nitto atp finals",
            "barclays atp world tour finals",
            "atp world tour finals", 
            "tennis masters cup",
        }

        first_segment_cleaned = name_segments[0].strip().lower()

        if first_segment_cleaned in nitto_atp_keywords:
            self.logger.debug(
                "Special case for ATP Finals detected in first segment: '%s'; "
                "overriding tournament name to 'finals-turin'.",
                first_segment_cleaned,
            )
            return "finals-turin"

        return standardized_name
    
    def handle_special_case_astana_open(self, name_segments: List[str], standardized_name: str) -> str:
        """
        Handle special case for the Astana Open tournament with various naming conventions.

        Args:
            name_segments (List[str]): Segments of the tournament name.
            standardized_name (str): The standardized tournament name.

        Returns:
            str: The updated tournament name if it falls under the special case; otherwise, the original standardized name.
        """
        astana_keywords: Set[str] = {
            "astana open",
            "astana atp 500",
            "atp astana",
            "atp 500 astana",
            "astana"
        }
        
        first_segment_cleaned = name_segments[0].strip().lower()

        if first_segment_cleaned in astana_keywords:
            self.logger.debug(
                "Special case for Astana Open detected in first segment: '%s'; "
                "overriding tournament name to 'astana'.",
                first_segment_cleaned,
            )
            return "astana"
        
        return standardized_name

    def handle_special_case_next_gen_atp(self, name_segments: List[str], standardized_name: str) -> str:
        """
        Handle special case for the Next Gen ATP Finals tournament with various naming conventions.

        Args:
            name_segments (List[str]): Segments of the tournament name.
            standardized_name (str): The standardized tournament name.

        Returns:
            str: The updated tournament name if a special case is detected; otherwise, the original standardized name.
        """
        next_gen_keywords: Set[str] = {
            "next gen atp finals",
            "next generation atp finals",
            "next gen finals",
            "atp next gen finals",
        }

        first_segment_cleaned = name_segments[0].strip().lower()

        if first_segment_cleaned in next_gen_keywords:
            self.logger.debug(
                "Special case for Next Gen ATP Finals detected in first segment: '%s'; "
                "overriding tournament name to 'next-gen-finals-jeddah'.",
                first_segment_cleaned,
            )
            return "next-gen-finals-jeddah"

        return standardized_name
            
    def handle_special_case_olympics(self, name_segments: List[str], standardized_name: str) -> str:
        """
        Handle special case for the Summer Olympic Tennis Event with various naming conventions.

        Args:
            name_segments (List[str]): Segments of the tournament name.
            standardized_name (str): The standardized tournament name.

        Returns:
            str: The updated tournament name if a special case is detected; otherwise, the original standardized name.
        """
        olympic_keywords: Set[str] = {
            "summer olympic tennis event",
            "olympic tennis event",
            "olympics tennis",
            "jeux olympiques",
            "olympic games tennis",
            "tennis at the summer olympics",
        }

        first_segment_cleaned = name_segments[0].strip().lower()

        if first_segment_cleaned in olympic_keywords:
            self.logger.debug(
                "Special case for Summer Olympic Tennis Event detected in first segment: '%s'; "
                "overriding tournament name to 'olympic-games'.",
                first_segment_cleaned,
            )
            return "olympic-games"

        return standardized_name

    def handle_special_case_milan(self, name_segments: List[str], standardized_name: str) -> str:
        """
        Handle special case for the Milan Tournament with various naming conventions.

        Args:
            name_segments (List[str]): Segments of the tournament name.
            standardized_name (str): The standardized tournament name.

        Returns:
            str: The updated tournament name if a special case is detected; otherwise, the original standardized name.
        """
        milan_keywords: Set[str] = {
            "milan tournament",
            "atp finals milan",
            "axa cup",
            "guardian direct cup",
            "atp milan",
        }

        first_segment_cleaned = name_segments[0].strip().lower()

        if first_segment_cleaned in milan_keywords:
            self.logger.debug(
                "Special case for Milan Tournament detected in first segment: '%s'; "
                "overriding tournament name to 'milan-tournament'.",
                first_segment_cleaned,
            )
            return "milan"

        return standardized_name
        
    def handle_special_case_grand_slam_cup(self, name_segments: List[str], standardized_name: str) -> str:
        """
        Handle special case for the Grand Slam Cup tournament with various naming conventions.

        Args:
            name_segments (List[str]): Segments of the tournament name.
            standardized_name (str): The standardized tournament name.

        Returns:
            str: The updated tournament name if a special case is detected; otherwise, the original standardized name.
        """
        grand_slam_keywords: Set[str] = {
            "grand slam cup",
            "atp grand slam cup",
            "tennis grand slam cup",
        }

        first_segment_cleaned = name_segments[0].strip().lower()

        if first_segment_cleaned in grand_slam_keywords:
            self.logger.debug(
                "Special case for Grand Slam Cup detected in first segment: '%s'; "
                "overriding tournament name to 'grand-slam-cup'.",
                first_segment_cleaned,
            )
            return "grand-slam-cup"

        return standardized_name
    
    def handle_special_case_acapulco(self, name_segments: List[str], standardized_name: str) -> str:
        """
        Handle special case for the Acapulco Tournament (Abierto Mexicano Telcel) with various naming conventions.

        Args:
            name_segments (List[str]): Segments of the tournament name.
            standardized_name (str): The standardized tournament name.

        Returns:
            str: The updated tournament name if a special case is detected; otherwise, the original standardized name.
        """
        acapulco_keywords: Set[str] = {
            "abierto mexicano telcel",
            "acapulco open",
            "acapulco atp",
            "mexican open acapulco",
        }

        first_segment_cleaned = name_segments[0].strip().lower()

        if first_segment_cleaned in acapulco_keywords:
            self.logger.debug(
                "Special case for Abierto Mexicano Telcel (Acapulco) detected in first segment: '%s'; "
                "overriding tournament name to 'acapulco'.",
                first_segment_cleaned,
            )
            return "acapulco"

        return standardized_name 

    def handle_special_case_houston(self, name_segments: List[str], standardized_name: str) -> str:
        """
        Handle special case for the Houston Tournament (US Men's Clay Court Championship) with various naming conventions.

        Args:
            name_segments (List[str]): Segments of the tournament name.
            standardized_name (str): The standardized tournament name.

        Returns:
            str: The updated tournament name if a special case is detected; otherwise, the original standardized name.
        """
        houston_keywords: Set[str] = {
            "us men's clay court championship",
            "us men's clay court",
            "houston atp",
            "houston tennis",
        }

        first_segment_cleaned = name_segments[0].strip().lower()

        if first_segment_cleaned in houston_keywords:
            self.logger.debug(
                "Special case for US Men's Clay Court Championship (Houston) detected in first segment: '%s'; "
                "overriding tournament name to 'houston'.",
                first_segment_cleaned,
            )
            return "houston"

        return standardized_name

    def handle_special_case_miami(self, name_segments: List[str], standardized_name: str) -> str:
        """
        Handle special case for the Miami Tournament (Lipton Championships) with various naming conventions.

        Args:
            name_segments (List[str]): Segments of the tournament name.
            standardized_name (str): The standardized tournament name.

        Returns:
            str: The updated tournament name if a special case is detected; otherwise, the original standardized name.
        """
        miami_keywords: Set[str] = {
            "lipton championships",
            "miami open",
            "atp miami",
            "miami tennis",
            "miami masters",
        }

        first_segment_cleaned = name_segments[0].strip().lower()

        if first_segment_cleaned in miami_keywords:
            self.logger.debug(
                "Special case for Lipton Championships (Miami) detected in first segment: '%s'; "
                "overriding tournament name to 'miami'.",
                first_segment_cleaned,
            )
            return "miami"

        return standardized_name
    
    def handle_special_case_wimbledon(self, name_segments: List[str], standardized_name: str) -> str:
        """
        Handle special case for the Wimbledon Tournament (The Championships) with various naming conventions.

        Args:
            name_segments (List[str]): Segments of the tournament name.
            standardized_name (str): The standardized tournament name.

        Returns:
            str: The updated tournament name if a special case is detected; otherwise, the original standardized name.
        """
        wimbledon_keywords: Set[str] = {
            "the championships",
            "wimbledon championships",
            "wimbledon tennis",
            "wimbledon atp",
        }

        first_segment_cleaned = name_segments[0].strip().lower()

        if first_segment_cleaned in wimbledon_keywords:
            self.logger.debug(
                "Special case for Wimbledon (The Championships) detected in first segment: '%s'; "
                "overriding tournament name to 'wimbledon'.",
                first_segment_cleaned,
            )
            return "wimbledon"

        return standardized_name

    def remove_parentheses_content(self, tournament_name: str) -> str:
        """
        Remove any text enclosed in parentheses '()' or square brackets '[]' 
        from the tournament name.

        Args:
            tournament_name (str): The raw tournament name.

        Returns:
            str: Cleaned tournament name with content inside parentheses removed.
        """
        cleaned_name = re.sub(r"[\(\[].*?[\)\]]", "", tournament_name).strip()
        self.logger.debug("Removed parentheses content: '%s' -> '%s'", tournament_name, cleaned_name)
        return cleaned_name
    
    def extract_tournament_name(self, tournament_name: str) -> str:
        """
        Clean and standardize the tournament name.

        This function processes a raw tournament name string, extracts and standardizes 
        the name by converting it to lowercase, replacing spaces with hyphens, handling 
        specific cases (e.g., "paris" with "roland-garros", ATP Finals cases), and applying 
        various predefined replacements. The function also normalizes the string to remove accents.

        Args:
            tournament_name (str): The raw tournament name.

        Returns:
            str: The standardized tournament name.
        """
        self.logger.debug("Starting tournament name extraction for: %s", tournament_name)

        # Split the input string into segments separated by commas.
        name_segments: List[str] = tournament_name.split(",")

        # Handle special case for number suffix
        number_suffix: str = self.handle_special_case_number_suffix(name_segments)

        # Use the last segment as the base tournament name.
        base_tournament_name: str = name_segments[-1].strip()

        # Remove parentheses or square brackets content
        base_tournament_name = self.remove_parentheses_content(base_tournament_name)

        # Convert to lowercase and replace spaces with hyphens, then append any suffix.
        standardized_tournament_name: str = (
            base_tournament_name.lower().replace(" ", "-") + number_suffix
        )
        self.logger.debug("Base standardized name: %s", standardized_tournament_name)

        # Handle special cases
        standardized_tournament_name = self.handle_special_case_nitto_atp(name_segments, standardized_tournament_name)
        standardized_tournament_name = self.handle_special_case_astana_open(name_segments, standardized_tournament_name)
        standardized_tournament_name = self.handle_special_case_paris(name_segments, standardized_tournament_name)
        standardized_tournament_name = self.handle_special_case_new_york(name_segments, standardized_tournament_name)
        standardized_tournament_name = self.handle_special_case_atlanta(name_segments, standardized_tournament_name)
        standardized_tournament_name = self.handle_special_case_long_island(name_segments, standardized_tournament_name)
        standardized_tournament_name = self.handle_special_case_next_gen_atp(name_segments, standardized_tournament_name)
        standardized_tournament_name = self.handle_special_case_olympics(name_segments, standardized_tournament_name)
        standardized_tournament_name = self.handle_special_case_milan(name_segments, standardized_tournament_name)
        standardized_tournament_name = self.handle_special_case_acapulco(name_segments, standardized_tournament_name)
        standardized_tournament_name = self.handle_special_case_grand_slam_cup(name_segments, standardized_tournament_name)
        standardized_tournament_name = self.handle_special_case_houston(name_segments, standardized_tournament_name)
        standardized_tournament_name = self.handle_special_case_miami(name_segments, standardized_tournament_name)
        standardized_tournament_name = self.handle_special_case_wimbledon(name_segments, standardized_tournament_name)

        # Apply a series of replacements to normalize specific tournament names.
        standardized_tournament_name = (
            standardized_tournament_name.replace("melbourne", "australia-open")
            .replace("genève", "geneva")
            .replace("bruxelles", "brussels")
            .replace("pékin", "beijing")
            .replace("flushing-meadows", "us-open")
            .replace("athènes", "athens")
            .replace("moscou", "moscow")
            .replace("valence", "valencia")
            .replace("vienne", "vienna")
            .replace("londres", "london")
            .replace("hô-chi-minh-ville", "ho-chi-minh-city")
            .replace("varsovie", "warsaw")
            .replace("roland-garros", "french-open")
            .replace("bâle", "basel")
            .replace("anvers", "antwerp")
            .replace("bois-le-duc", "hertogenbosch")
            .replace("cabo-san-lucas","los-cabos")
            .replace("palma-de-majorque","mallorca")
            .replace("majorque","mallorca")
            .replace("st.-petersburg","st-petersburg")
            .replace("saint-pétersbourg","st-petersburg")
            .replace("washington-d.c.","washington")
            .replace("d.c.","washington")
            .replace("oeiras","estoril")
            .replace("johannesbourg","johannesburg")
            .replace("sankt-pölten","portschach")
            .replace("santiago-du-chili","santiago")
            .replace("santa-margherita-di-pula","sardinia")
            .replace("bournemouth","brighton")
            .replace('bombay','mumbai')
            .replace("naples","napoli")
        )
        self.logger.debug(
            "Tournament name after applying replacements: %s", standardized_tournament_name
        )

        # Normalize the string to decompose accented characters and remove combining characters.
        normalized_name: str = unicodedata.normalize("NFKD", standardized_tournament_name)
        cleaned_name: str = "".join(
            char for char in normalized_name if not unicodedata.combining(char)
        )
        self.logger.debug("Final cleaned tournament name: %s", cleaned_name)

        return cleaned_name
    

    def extract_tournament_from_row(self, row: Tag) -> Tournaments:
        """
        Extract tournament information from a single table row.

        This method parses a table row and converts its cell contents 
        into a structured Tournaments object.

        Args:
            row (Tag): BeautifulSoup Tag representing a table row.

        Returns:
            Tournaments: Structured tournament data object.
        """
        cells = row.find_all("td")
        cell_texts: List[str] = [cell.get_text(strip=True) for cell in cells]

        tournament: Tournaments = Tournaments(
            name=self.extract_tournament_name(cell_texts[2]),
            year=self.year,
            type=self.extract_tournament_type(cell_texts[3]),
            money=self.extract_prize_money(cell_texts[4]),
            surface=self.extract_surface(cell_texts[5])
        )
        return tournament

    def parse(self, url: str, year: str) -> List[Tournaments]:
        """
        Parse ATP season data from Wikipedia page.

        Returns:
            List[Tournaments]: List of tournaments extracted from the page.
        """
        self.initialize_variables(url=url, year=year)

        self.logger.info(f"Parsing ATP season data from {self.url}")
        html_content = self.fetch_webpage_content()
        
        if not html_content:
            self.logger.error("No HTML content retrieved; aborting extraction.")
            return []

        soup = BeautifulSoup(html_content, "html.parser")
        
        # Locate the 'Simple' section table
        simple_heading = soup.find("h3", id="Simple", string="Simple")
        if not simple_heading:
            self.logger.error("The 'Simple' heading was not found in the HTML.")
            return []

        simple_div = simple_heading.find_parent("div")
        if not simple_div:
            self.logger.error("Parent <div> for the 'Simple' heading not found.")
            return []

        simple_table = simple_div.find_next("table")
        if not simple_table:
            self.logger.error("Table following the 'Simple' section not found.")
            return []

        tbody = simple_table.tbody
        processed_rows: List[Tournaments] = []
        
        for row in tbody.find_all("tr"):
            style = row.get("style", "")
            if "background-color" not in style:
                continue
            if "background-color:#CCCCCF" in style:
                # "info" row, skip
                continue
            
            processed = self.extract_tournament_from_row(row)
            processed_rows.append(processed)

        self.logger.info(f"Extracted and processed {len(processed_rows)} rows from the 'Simple' table")
        return processed_rows


if __name__ == "__main__":
    # Configure logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

    # Example usage: Parse and display ATP season data from the given URL
    season_url = "https://fr.wikipedia.org/wiki/Saison_2024_de_l%27ATP"
    season_year = "2024"
    parser = ATPSeasonParser()
    season_data: List[Tournaments] = parser.parse(url=season_url, year=season_year)

    for row in season_data:
        print(row.to_dict())