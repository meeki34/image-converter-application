import io
from pathlib import Path

from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.responses import Response, HTMLResponse
from PIL import Image, ImageOps
import pillow_avif  # noqa: F401

app = FastAPI(title="ImageConverter")

MAX_SIZE = 50 * 1024 * 1024
SUPPORTED_INPUT = {
    "jpeg",
    "png",
    "webp",
    "gif",
    "bmp",
    "tiff",
    "ico",
    "avif",
    "heic",
    "svg",
}
SUPPORTED_OUTPUT = {"jpeg", "png", "webp", "gif", "bmp", "tiff", "ico", "avif"}
LOSSY_FORMATS = {"jpeg", "webp", "avif"}
TEMPLATE_DIR = Path(__file__).parent / "templates"

MAGIC_MAP = {
    b"\xff\xd8\xff": "jpeg",
    b"\x89PNG": "png",
    b"WEBP": "webp",
    b"GIF8": "gif",
    b"BM": "bmp",
    b"II*\x00": "tiff",
    b"MM\x00*": "tiff",
    b"\x00\x00\x01\x00": "ico",
    b"ftypavif": "avif",
    b"ftypheic": "heic",
    b"ftypmif1": "heic",
    b"<svg": "svg",
    b"<?xml": "svg",
}

LANCZOS = Image.Resampling.LANCZOS


def detect_format(data: bytes) -> str | None:
    for magic_bytes, fmt in MAGIC_MAP.items():
        if magic_bytes in data[:32]:
            return fmt
    try:
        img = Image.open(io.BytesIO(data))
        return img.format.lower() if img.format else None
    except Exception:
        return None


def open_as_pil(data: bytes, fmt: str) -> Image.Image:
    if fmt == "heic":
        import pillow_heif

        heif_file = pillow_heif.open_heif(io.BytesIO(data))
        return Image.frombytes(heif_file.mode, heif_file.size, heif_file.data)
    if fmt == "svg":
        import fitz

        doc = fitz.open("svg", io.BytesIO(data))
        page = doc[0]
        pix = page.get_pixmap(alpha=True)
        return Image.frombytes("RGBA", (pix.width, pix.height), pix.samples)
    return Image.open(io.BytesIO(data))


def apply_resize(
    img: Image.Image, width: int | None, height: int | None, fit: str
) -> Image.Image:
    if width is None and height is None:
        return img
    if width is not None and height is not None:
        if fit == "contain":
            img.thumbnail((width, height), LANCZOS)
            return img
        elif fit == "cover":
            return ImageOps.cover(img, (width, height), method=LANCZOS)
        else:
            return img.resize((width, height), LANCZOS)
    if width is not None:
        ratio = width / img.width
        h = int(img.height * ratio)
        return img.resize((width, h), LANCZOS)
    else:
        ratio = height / img.height  # type: ignore[operator]
        w = int(img.width * ratio)
        return img.resize((w, height), LANCZOS)  # type: ignore[arg-type]


def save_as_format(img: Image.Image, fmt: str, quality: int) -> bytes:
    if fmt == "ico":
        buf = io.BytesIO()
        img.save(buf, format="ICO")
        return buf.getvalue()
    buf = io.BytesIO()
    save_kwargs: dict = {"format": fmt.upper()}
    if fmt in LOSSY_FORMATS:
        save_kwargs["quality"] = quality
        if fmt == "webp":
            save_kwargs["lossless"] = False
    if fmt == "gif":
        save_kwargs["save_all"] = True
    if fmt == "jpeg" and img.mode in ("RGBA", "P", "LA"):
        img = img.convert("RGB")
    img.save(buf, **save_kwargs)
    return buf.getvalue()


@app.get("/", response_class=HTMLResponse)
async def index():
    html_path = TEMPLATE_DIR / "index.html"
    return HTMLResponse(html_path.read_text(encoding="utf-8"))


@app.post("/convert")
async def convert(
    file: UploadFile = File(...),
    target_format: str = Form(...),
    quality: int = Form(85),
    width: int | None = Form(None),
    height: int | None = Form(None),
    fit: str = Form("contain"),
):
    target_format = target_format.lower()
    if target_format not in SUPPORTED_OUTPUT:
        raise HTTPException(400, f"Unsupported output format: {target_format}")

    data = await file.read()
    if len(data) > MAX_SIZE:
        raise HTTPException(413, "File too large. Max 50MB")

    src_fmt = detect_format(data)
    if not src_fmt or src_fmt not in SUPPORTED_INPUT:
        raise HTTPException(400, "Unsupported or unrecognized file format")

    if src_fmt == target_format:
        return Response(
            content=data,
            media_type=file.content_type or "application/octet-stream",
            headers={
                "Content-Disposition": f'attachment; filename="converted.{target_format}"'
            },
        )

    try:
        img = open_as_pil(data, src_fmt)
        if img.mode == "P" and target_format in ("jpeg",):
            img = img.convert("RGBA")
        img = apply_resize(img, width, height, fit)
        result = save_as_format(img, target_format, quality)
    except Exception as e:
        raise HTTPException(422, f"Conversion failed: {str(e)}")

    ext = target_format.replace("jpeg", "jpg")
    media_map = {
        "jpeg": "image/jpeg",
        "png": "image/png",
        "webp": "image/webp",
        "gif": "image/gif",
        "bmp": "image/bmp",
        "tiff": "image/tiff",
        "ico": "image/x-icon",
        "avif": "image/avif",
    }
    return Response(
        content=result,
        media_type=media_map.get(target_format, "application/octet-stream"),
        headers={"Content-Disposition": f'attachment; filename="converted.{ext}"'},
    )


@app.post("/preview")
async def preview(
    file: UploadFile = File(...),
    target_format: str = Form(...),
    quality: int = Form(85),
    width: int | None = Form(None),
    height: int | None = Form(None),
    fit: str = Form("contain"),
):
    target_format = target_format.lower()
    if target_format not in SUPPORTED_OUTPUT:
        raise HTTPException(400, f"Unsupported output format: {target_format}")

    data = await file.read()
    if len(data) > MAX_SIZE:
        raise HTTPException(413, "File too large. Max 50MB")

    src_fmt = detect_format(data)
    if not src_fmt or src_fmt not in SUPPORTED_INPUT:
        raise HTTPException(400, "Unsupported or unrecognized file format")

    try:
        img = open_as_pil(data, src_fmt)
        orig_w, orig_h = img.size
        if img.mode == "P" and target_format in ("jpeg",):
            img = img.convert("RGBA")
        img = apply_resize(img, width, height, fit)
        result = save_as_format(img, target_format, quality)
        preview_img = Image.open(io.BytesIO(result))
        preview_img.thumbnail((800, 800), LANCZOS)
        buf = io.BytesIO()
        preview_img.save(buf, format="PNG")
        import base64

        b64 = base64.b64encode(buf.getvalue()).decode()
        return {
            "preview": f"data:image/png;base64,{b64}",
            "width": orig_w,
            "height": orig_h,
        }
    except Exception as e:
        raise HTTPException(422, f"Preview failed: {str(e)}")


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
