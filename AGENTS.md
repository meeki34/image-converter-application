# ImageConverter — Known Issues & Monitoring

## Fixed Bugs (do NOT reintroduce)

| Issue | Fix Location | What Was Wrong |
|---|---|---|
| WebP magic byte false positives | `main.py:30`, `index.html:580` | `"RIFF"` matched WAV/AVI too; now checks for `"WEBP"` at bytes 8-11 |
| Missing pillow-avif-plugin import | `main.py:7` | AVIF conversion silently failed; added `import pillow_avif` (note: renamed from `pillow_avif_plugin` in v1.5.5+) |
| Error response field name mismatch | `index.html:646,656` | Python returns `{"detail": "..."}`, JS was reading `err.error` |
| formatSelect listener leak | `index.html:591-604` | New `change` listener added on every file load (never removed); extracted to `updateQualityVisibility()` + single listener |
| `err.error` → `err.detail` in JS | `index.html:648,658` | Python FastAPI error responses use `detail` key, JS was reading `error` |

## Frontend Polish (May 2026)

- **SVG icons** replaced all emoji (camera, lock/unlock, remove X, download) for crisp rendering at any scale
- **Entry animations** — header fades in, controls panel slides up, preview/results scale in with a bounce curve
- **Gradient header** now animates (shifts between indigo → purple → pink)
- **Ambient glow** — subtle radial gradients in background + hover spotlight on upload zone (tracks mouse position)
- **Card hover** — subtle border glow on hover for depth
- **Button press** — `scale(0.98)` on click for tactile feedback
- **Primary button** uses gradient + lift + glow on hover
- **Custom select arrow** via inline SVG
- **Focus-visible** ring for keyboard accessibility
- **Placeholder states** for preview boxes ("No image loaded", "Convert to see preview")
- **Converting… placeholder** shown during conversion
- **Size comparison** now shows percentage change with color coding (green = smaller, red = larger)
- **Smooth scroll** to results after conversion
- **Refined color palette** — deeper bg (`#0b1121`), muted text `#8899b4`, borders `#283548`
- **Responsive** — fit options wrap on mobile, tighter padding

## Known Residual Issues (monitor these)

1. **`fitz.open("svg", ...)` may fail** if pymupdf < 1.23.0 (SVG support added late). Check `pymupdf>=1.25.0` in requirements.txt guards this.
2. **`pillow_heif` import inside function** — if missing, error hits runtime not startup. Test with HEIC files before deploying.
3. **Palette-mode images** (`mode == "P"`) only get converted to RGBA for JPEG target. Other formats (WebP, PNG) may render incorrectly with palette-mode inputs.
4. **SVG/HEIC detection via magic bytes** is heuristic (`<svg`, `<?xml`, `ftypheic`) — false positives possible with generic XML/MP4 files. Low risk for expected usage.
5. **GIF `save_all=True`** without `append_images`/`duration` — animated GIFs will lose animation frames.

## Running

```bash
pip install -r requirements.txt
python main.py
# -> http://localhost:8000
```

## Testing Checklist
- [ ] Convert JPEG → PNG, WebP, AVIF
- [ ] Convert PNG (with transparency) → JPEG (should strip alpha)
- [ ] Convert WebP → GIF, BMP, TIFF
- [ ] Convert HEIC file
- [ ] Convert SVG file
- [ ] Upload file > 50MB (should get 413)
- [ ] Resize with contain/cover/fill
- [ ] Preview + Download both work
- [ ] Remove file and re-upload (no leaked listeners)
