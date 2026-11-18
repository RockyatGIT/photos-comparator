# Google Photos Dual-Account Comparator

A modern full-stack web application built with **FastAPI**, **PIL / ImageHash**, and a responsive **Tailwind CSS** UI to connect **two separate Google Photos accounts**, scan for duplicates or near-duplicate burst shots across customizable date ranges, compare photos side-by-side with an interactive pixel-level diff slider, and identify unique photos for reconciliation.

---

## Key Features

1. **Dual Google OAuth 2.0 & Modern Photos Picker API**:
   - Independent authorization for **Account 1** and **Account 2**.
   - Automatic token refresh and secure offline session handling.
   - Forced account chooser (`prompt=consent select_account`) to prevent browser session cross-contamination.
   - Built for Google's official **Google Photos Picker API** (`photospicker.googleapis.com`) with fallback to Library API.

2. **Date Range Filtering & Dual View Mode**:
   - Filter photos by custom date range or quick presets: **7D**, **30D**, **This Year**, **All**, or **Auto-Fit** (auto-adjusts to earliest and latest photos in database).
   - **Dual View Mode**: Synchronized side-by-side gallery of Account 1 and Account 2 for visual inspection.

3. **Perceptual Image Similarity Matching (pHash, dHash, aHash)**:
   - Uses discrete cosine transform (DCT) based perceptual hashing.
   - Categorizes matches by Hamming distance:
     - **Exact Match** (100%): Identical visual hash.
     - **Near Duplicate** (93.8% - 98.4%): Re-compressed, slightly resized, or minor crop.
     - **Similar / Burst** (84.4% - 92.2%): Taken seconds apart with subtle angle change.
   - Compares capture timestamp deltas to identify burst sequences.

4. **Interactive Side-by-Side Diff Slider**:
   - Split-screen comparison modal with an interactive divider to drag across both images and reveal pixel differences in real-time.
   - Side-by-side EXIF metadata table (capture time, dimensions, file name).

5. **Reconciliation (Unique Photos)**:
   - Dedicated views for **"Only in Account 1"** and **"Only in Account 2"** to quickly identify un-backed-up or un-transferred photos.

6. **Instant Demo Mode**:
   - Test all features immediately without waiting for Google Cloud credentials by clicking **"Load Demo Data"**.

---

## Architecture

The backend follows an **industry-standard Layered Architecture (Service-Repository-Controller Pattern)**:
- **Presentation Layer (`backend/api/`)**: FastAPI sub-routers for `/auth`, `/photos`, `/matcher`, `/settings`, `/status` with dependency injection.
- **Business Logic Layer (`backend/services/`)**: `AuthService`, `PhotosService`, `MatchingService`, `DemoService`.
- **Data Access Layer (`backend/repositories/`)**: `AccountRepository`, `PhotoRepository`, `MatchRepository`, `SettingsRepository`.
- **Core Layer (`backend/core/`)**: Centralized Pydantic configuration (`config.py`) and SQLite connection manager with automated schema migrations (`database.py`).
- **DTOs & Schemas (`backend/schemas/`)**: Strongly typed Pydantic models for validation and OpenAPI docs.

---

## Quick Start

### 1. Prerequisites
- Python 3.10+
- A Google Cloud Project (or use Demo Mode)

### 2. Installation
```bash
git clone https://github.com/RockyatGIT/photos-comparator.git
cd photos-comparator
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### 3. Run the Application
```bash
python run.py
```
Open **[http://localhost:8000](http://localhost:8000)** in your web browser.

---

## Google Cloud Console Setup

To connect your real Google Photos accounts:

1. **Create a Google Cloud Project**:
   - Visit [Google Cloud Console](https://console.cloud.google.com/) and create a project (e.g. `Photos-Comparator`).

2. **Enable Required APIs**:
   - Go to **APIs & Services > Library**.
   - Search for **"Google Photos Picker API"** and click **Enable** (Essential for photo selection).
   - Also search for **"Photos Library API"** and click **Enable**.

3. **Configure OAuth Consent Screen**:
   - Go to **APIs & Services > OAuth consent screen**.
   - Choose **External** user type and click **Create**.
   - Fill in app name and user support email.
   - Under **Test Users**, add the Gmail addresses of **both Google Accounts** you plan to connect.

4. **Create OAuth 2.0 Web Client Credentials**:
   - Go to **APIs & Services > Credentials > Create Credentials > OAuth client ID**.
   - Select **Web application**.
   - Under **Authorized redirect URIs**, add:
     ```
     http://localhost:8000/api/auth/callback
     ```
   - Click **Create** and copy your **Client ID** and **Client Secret**.

5. **Configure Credentials in App**:
   - Paste the credentials into the **Setup Guide** tab in the web interface (or into `.env`):
     ```ini
     GOOGLE_CLIENT_ID="YOUR_CLIENT_ID.apps.googleusercontent.com"
     GOOGLE_CLIENT_SECRET="YOUR_CLIENT_SECRET"
     REDIRECT_URI="http://localhost:8000/api/auth/callback"
     ```
   - Restart the server (`python run.py`) and click **Connect** for each account!

---

## License

MIT License
