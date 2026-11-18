import time
from datetime import datetime, timezone, timedelta
from typing import Dict, Any, List
from PIL import Image, ImageDraw
import imagehash

from ..core.config import settings
from ..repositories.account_repo import AccountRepository
from ..repositories.photo_repo import PhotoRepository

class DemoService:
    def __init__(
        self,
        account_repo: AccountRepository = AccountRepository,
        photo_repo: PhotoRepository = PhotoRepository
    ):
        self.account_repo = account_repo
        self.photo_repo = photo_repo

    @staticmethod
    def create_synthetic_image(
        title: str,
        subtitle: str,
        color1: tuple,
        color2: tuple,
        variation: int = 0
    ) -> Image.Image:
        """Generates synthetic high-quality test images for offline testing."""
        width, height = 400, 300
        img = Image.new("RGB", (width, height), color1)
        draw = ImageDraw.Draw(img)

        # Gradient background
        for y in range(height):
            r = int(color1[0] + (color2[0] - color1[0]) * (y / height))
            g = int(color1[1] + (color2[1] - color1[1]) * (y / height))
            b = int(color1[2] + (color2[2] - color1[2]) * (y / height))
            draw.line([(0, y), (width, y)], fill=(r, g, b))

        # Geometric shapes
        draw.rectangle([50 + variation, 60, 200 + variation, 210], outline=(255, 255, 255), width=4)
        draw.ellipse([220, 80 + variation, 340, 200 + variation], fill=(255, 230, 100))
        draw.polygon([(100 + variation, 240), (200 + variation, 90), (300 + variation, 240)], outline=(120, 240, 180), width=3)

        # Title & subtitle
        draw.text((20, 20), title, fill=(255, 255, 255))
        draw.text((20, 260), subtitle, fill=(240, 240, 240))
        return img

    def seed_demo_data(self) -> Dict[str, Any]:
        """Seeds demo accounts and realistic sample photos with known duplicate, burst, and unique pairs."""
        now = datetime.now(timezone.utc)

        # 1. Ensure test accounts exist in database if not already connected
        acc1 = self.account_repo.get(1)
        if not acc1:
            self.account_repo.save_token(
                account_id=1,
                email=settings.DEMO_ACCOUNT_1_EMAIL,
                name=settings.DEMO_ACCOUNT_1_NAME,
                picture=f"{settings.DEMO_AVATAR_BASE_URL}?seed=Alex",
                access_token="demo_token_1",
                refresh_token="demo_refresh_1",
                expires_at=time.time() + 86400
            )

        acc2 = self.account_repo.get(2)
        if not acc2:
            self.account_repo.save_token(
                account_id=2,
                email=settings.DEMO_ACCOUNT_2_EMAIL,
                name=settings.DEMO_ACCOUNT_2_NAME,
                picture=f"{settings.DEMO_AVATAR_BASE_URL}?seed=Vault",
                access_token="demo_token_2",
                refresh_token="demo_refresh_2",
                expires_at=time.time() + 86400
            )

        demo_scenarios = [
            ("Sunset at the Beach", "Vacation 2026 - Golden Hour", (255, 107, 107), (78, 205, 196), True, True, 0, 0),
            ("Mountain Sunrise Hike", "Alps Trail Peak", (44, 62, 80), (238, 90, 36), True, True, 0, 0),
            ("City Skyline at Night", "Downtown Rooftop View", (19, 15, 64), (104, 109, 224), True, True, 4, 3),
            ("Coffee & Notebook", "Morning Café Session", (112, 111, 211), (255, 177, 66), True, True, 8, 12),
            ("Forest Walk & Redwoods", "National Park Trail", (30, 39, 46), (11, 232, 129), True, False, 0, 0),
            ("Architectural Facade", "Modern Art Museum", (24, 44, 97), (87, 88, 187), True, False, 0, 0),
            ("Family Dinner Gathering", "Thanksgiving Feast", (179, 57, 57), (248, 180, 0), False, True, 0, 0),
            ("Abstract Neon Lights", "Art Installation", (232, 65, 24), (255, 221, 89), False, True, 0, 0),
            ("Cat in Window Sunlight", "Afternoon Nap", (87, 95, 207), (255, 94, 87), True, True, 2, 2),
            ("Autumn Road Trip", "Scenic Highway Drive", (214, 48, 49), (253, 203, 110), True, True, 0, 0),
        ]

        photos_acc1 = []
        photos_acc2 = []

        for idx, (title, subtitle, c1, c2, in_acc1, in_acc2, var2, time_delta) in enumerate(demo_scenarios):
            base_time = now - timedelta(days=idx * 2)

            if in_acc1:
                img1 = self.create_synthetic_image(title, subtitle, c1, c2, variation=0)
                filename = f"acc1_demo_{idx}.jpg"
                thumb_path = settings.THUMBNAILS_DIR / filename
                img1.save(thumb_path, "JPEG", quality=90)

                photos_acc1.append({
                    "account_id": 1,
                    "google_id": f"demo_acc1_{idx}",
                    "filename": f"{title.lower().replace(' ', '_')}.jpg",
                    "mime_type": "image/jpeg",
                    "base_url": "",
                    "thumbnail_path": str(thumb_path),
                    "creation_time": base_time.isoformat(),
                    "width": 1920,
                    "height": 1080,
                    "camera_make": "Sony",
                    "camera_model": "A7 IV",
                    "phash": str(imagehash.phash(img1)),
                    "dhash": str(imagehash.dhash(img1)),
                    "ahash": str(imagehash.average_hash(img1)),
                })

            if in_acc2:
                img2 = self.create_synthetic_image(title, subtitle, c1, c2, variation=var2)
                filename = f"acc2_demo_{idx}.jpg"
                thumb_path = settings.THUMBNAILS_DIR / filename
                img2.save(thumb_path, "JPEG", quality=90)

                t2 = base_time + timedelta(seconds=time_delta)
                photos_acc2.append({
                    "account_id": 2,
                    "google_id": f"demo_acc2_{idx}",
                    "filename": f"{title.lower().replace(' ', '_')}_copy.jpg",
                    "mime_type": "image/jpeg",
                    "base_url": "",
                    "thumbnail_path": str(thumb_path),
                    "creation_time": t2.isoformat(),
                    "width": 1920,
                    "height": 1080,
                    "camera_make": "Sony",
                    "camera_model": "A7 IV",
                    "phash": str(imagehash.phash(img2)),
                    "dhash": str(imagehash.dhash(img2)),
                    "ahash": str(imagehash.average_hash(img2)),
                })

        self.photo_repo.save_photos(photos_acc1 + photos_acc2)

        return {
            "account_1_photos": len(photos_acc1),
            "account_2_photos": len(photos_acc2),
            "total_demo_photos": len(photos_acc1) + len(photos_acc2)
        }

demo_service = DemoService()
