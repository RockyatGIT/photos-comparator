import sys
from pathlib import Path

# Add project root to sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent))

from backend.core.config import settings
import uvicorn

if __name__ == "__main__":
    print("=" * 60)
    print(f" {settings.PROJECT_NAME} v{settings.VERSION}")
    print(f" http://{settings.HOST}:{settings.PORT}")
    print("=" * 60)
    uvicorn.run(
        "backend.app:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.RELOAD
    )
