# ImageConverter

Browser-based image converter. Drop an image, pick a format, convert.

Supported: JPEG, PNG, WebP, GIF, BMP, TIFF, ICO, AVIF, HEIC (read), SVG (read).

Built with FastAPI + Pillow + PyMuPDF.

## Run locally

```sh
pip install -r requirements.txt
python main.py
# → http://localhost:8000
```

## Deploy on Render (free)

1. Push this repo to GitHub
2. Go to [render.com](https://render.com) → New Web Service
3. Connect your repo
4. Set:
   - **Start Command**: `uvicorn main:app --host 0.0.0.0 --port $PORT`
5. Deploy

The free tier sleeps after 15 min of inactivity. First visit after sleep takes ~30s to wake.

## Deploy on Railway (free)

1. Push to GitHub
2. Go to [railway.app](https://railway.app) → New Project → Deploy from GitHub
3. Auto-detects Python. Set start command if needed:
   - `uvicorn main:app --host 0.0.0.0 --port $PORT`
