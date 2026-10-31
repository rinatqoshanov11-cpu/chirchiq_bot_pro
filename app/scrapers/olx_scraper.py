"""Web scraper for OLX and other sites."""
import asyncio
import aiohttp
from bs4 import BeautifulSoup
from typing import List, Dict, Any, Optional
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.apartment import ApartmentType
from app.services import ApartmentService, UserService
from app.utils import get_logger
from config import settings

logger = get_logger(__name__)


class ApartmentScraper:
    """Base scraper class for apartment listings."""

    def __init__(self, session: AsyncSession):
        self.session = session
        self.timeout = aiohttp.ClientTimeout(total=settings.scraper_timeout)

    async def fetch_page(self, url: str) -> Optional[str]:
        """Fetch page content."""
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 '
                          '(KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36'
        }

        try:
            async with aiohttp.ClientSession(timeout=self.timeout) as client:
                async with client.get(url, headers=headers) as response:
                    if response.status == 200:
                        return await response.text()
                    else:
                        logger.warning(f"Failed to fetch {url}: Status {response.status}")
                        return None
        except asyncio.TimeoutError:
            logger.error(f"Timeout fetching {url}")
            return None
        except Exception as e:
            logger.error(f"Error fetching {url}: {e}")
            return None

    async def scrape(self) -> List[Dict[str, Any]]:
        """Scrape apartments. To be implemented by subclasses."""
        raise NotImplementedError


class OLXScraper(ApartmentScraper):
    """Scraper for OLX.uz apartment listings."""

    BASE_URL = "https://www.olx.uz"

    async def scrape(self) -> List[Dict[str, Any]]:
        """Scrape OLX apartments."""
        listings = []

        # URLs to scrape
        urls = [
            f"{self.BASE_URL}/nedvizhimost/kvartiry/arenda-kvartir/chirchiq/",
            f"{self.BASE_URL}/nedvizhimost/kvartiry/prodazha-kvartir/chirchiq/",
        ]

        for url in urls:
            logger.info(f"Scraping: {url}")
            page_listings = await self._scrape_page(url)
            listings.extend(page_listings)
            await asyncio.sleep(2)  # Polite delay

        logger.info(f"OLX: Found {len(listings)} listings")
        return listings

    async def _scrape_page(self, url: str) -> List[Dict[str, Any]]:
        """Scrape single OLX page."""
        html = await self.fetch_page(url)
        if not html:
            return []

        soup = BeautifulSoup(html, 'lxml')
        listings = []

        # Determine type from URL
        apartment_type = ApartmentType.RENT if 'arenda' in url else ApartmentType.SALE

        # Find all listing cards
        cards = soup.find_all('div', {'data-cy': 'l-card'})

        for card in cards:
            try:
                listing = await self._parse_card(card, apartment_type)
                if listing:
                    listings.append(listing)
            except Exception as e:
                logger.error(f"Error parsing OLX card: {e}")
                continue

        return listings

    async def _parse_card(self, card, apartment_type: ApartmentType) -> Optional[Dict[str, Any]]:
        """Parse single OLX listing card."""
        try:
            # Title
            title_elem = card.find('h6')
            if not title_elem:
                return None
            title = title_elem.text.strip()

            # Price
            price_elem = card.find('p', {'data-testid': 'ad-price'})
            if not price_elem:
                return None

            price_text = price_elem.text.strip()
            price = int(''.join(filter(str.isdigit, price_text)))

            if price < 100:  # Filter out invalid prices
                return None

            # Location
            location_elem = card.find('p', {'data-testid': 'location-date'})
            location = location_elem.text.strip() if location_elem else "Chirchiq"

            # Link
            link_elem = card.find('a')
            link = self.BASE_URL + link_elem['href'] if link_elem and link_elem.get('href') else ""

            # Image
            img_elem = card.find('img')
            image = img_elem['src'] if img_elem and img_elem.get('src') else None

            # Extract rooms count from title
            rooms = self._extract_rooms(title)

            # External ID from link
            external_id = link.split('-')[-1].replace('.html', '') if link else None

            return {
                'title': title,
                'type': apartment_type,
                'rooms': rooms,
                'address': location,
                'price': price,
                'description': title,
                'photos': [image] if image else [],
                'phone_number': '+998000000000',  # Placeholder
                'source': 'olx',
                'external_id': external_id,
                'external_url': link,
            }

        except Exception as e:
            logger.error(f"Error parsing OLX listing: {e}")
            return None

    def _extract_rooms(self, title: str) -> int:
        """Extract number of rooms from title."""
        import re

        # Common patterns: "3-хонали", "3 хонали", "3-комн", "3 комн"
        patterns = [
            r'(\d+)[\s-]*(xonali|хонали|комн|room)',
        ]

        for pattern in patterns:
            match = re.search(pattern, title.lower())
            if match:
                return int(match.group(1))

        return 1  # Default


class ScraperManager:
    """Manager for all scrapers."""

    def __init__(self):
        self.scrapers = []

    async def run_all(self, session: AsyncSession, bot) -> Dict[str, int]:
        """Run all scrapers."""
        logger.info("Starting scraper run...")

        # Get or create system user for scraped listings
        system_user = await UserService.get_by_telegram_id(session, 0)

        if not system_user:
            system_user = await UserService.create_user(
                session=session,
                telegram_id=0,
                full_name="Sistema (Scraper)",
                phone_number="+998000000000",
                address="Sistema"
            )

        # Run OLX scraper
        olx_scraper = OLXScraper(session)
        listings = await olx_scraper.scrape()

        saved = 0
        skipped = 0

        for listing in listings:
            try:
                # Check for duplicates
                duplicate = await ApartmentService.find_duplicate(
                    session=session,
                    address=listing['address'],
                    rooms=listing['rooms'],
                    price=listing['price'],
                    apartment_type=listing['type']
                )

                if duplicate:
                    skipped += 1
                    continue

                # Create apartment
                await ApartmentService.create_apartment(
                    session=session,
                    owner_id=system_user.id,
                    apartment_type=listing['type'],
                    rooms=listing['rooms'],
                    address=listing['address'],
                    price=listing['price'],
                    phone_number=listing['phone_number'],
                    description=listing.get('description'),
                    photos=listing.get('photos', []),
                    source=listing.get('source', 'scraper'),
                    external_id=listing.get('external_id'),
                    external_url=listing.get('external_url')
                )

                saved += 1

            except Exception as e:
                logger.error(f"Error saving scraped apartment: {e}")
                continue

        logger.info(f"Scraper completed: {saved} saved, {skipped} skipped")

        # Notify admins if new listings found
        if saved > 0:
            await self._notify_admins(bot, saved, len(listings))

        return {
            'total': len(listings),
            'saved': saved,
            'skipped': skipped
        }

    async def _notify_admins(self, bot, saved: int, total: int):
        """Notify admins about scraper results."""
        from config import settings

        if not settings.admin_ids:
            return

        message = (
            f"🤖 Scraper yangilandi!\n\n"
            f"📊 Topildi: {total} ta e'lon\n"
            f"💾 Yangi: {saved} ta\n\n"
            f"Yangi e'lonlarni tekshirish uchun /admin dan foydalaning."
        )

        for admin_id in settings.admin_ids:
            try:
                await bot.send_message(admin_id, message)
            except Exception as e:
                logger.error(f"Error notifying admin {admin_id}: {e}")


async def run_scraper_task(session: AsyncSession, bot):
    """Run scraper task."""
    try:
        manager = ScraperManager()
        results = await manager.run_all(session, bot)
        logger.info(f"Scraper task completed: {results}")
    except Exception as e:
        logger.error(f"Scraper task error: {e}")
