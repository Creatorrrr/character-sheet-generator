#!/usr/bin/env python3
from __future__ import annotations

import argparse
import base64
import binascii
import http.server
import io
import json
import math
import re
import socketserver
import sys
import urllib.parse
import webbrowser
from datetime import datetime
from pathlib import Path
from typing import Any


WORKFLOW = "review-image-overlays"
EXPECTED_PACK_WORKFLOW = "create-comic-storyboard-pack"
STAGE_DIRS = {
        "storyboard_blocking": "01_storyboard_blocking",
    "storyboard_sketch_ink": "02_storyboard_sketch_ink",
    "finish": "03_finish",
}
PNG_SIGNATURE = b"\x89PNG\r\n\x1a\n"
VALID_COORDINATE_SPACES = {"normalized", "pixel"}
HEX_COLOR_RE = re.compile(r"^#[0-9a-fA-F]{6}$")
PALETTE = [
    {"id": "red", "name": "Red", "hex": "#ff3b30"},
    {"id": "blue", "name": "Blue", "hex": "#1d4ed8"},
    {"id": "green", "name": "Green", "hex": "#16a34a"},
    {"id": "yellow", "name": "Yellow", "hex": "#f59e0b"},
    {"id": "purple", "name": "Purple", "hex": "#9333ea"},
    {"id": "cyan", "name": "Cyan", "hex": "#0891b2"},
]


class ReviewError(Exception):
    pass


def now_iso() -> str:
    return datetime.now().isoformat(timespec="seconds")


def slugify(value: str, fallback: str = "item") -> str:
    value = value.lower().encode("ascii", "ignore").decode("ascii")
    value = re.sub(r"[^a-z0-9]+", "-", value).strip("-")
    return value or fallback


def path_is_under(path: Path, root: Path) -> bool:
    try:
        path.resolve(strict=False).relative_to(root.resolve(strict=False))
        return True
    except ValueError:
        return False


def read_json(path: Path) -> dict[str, Any]:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise ReviewError(f"File not found: {path}") from exc
    except json.JSONDecodeError as exc:
        raise ReviewError(f"Invalid JSON in {path}: {exc}") from exc


def write_json(path: Path, data: dict[str, Any]) -> None:
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def load_pack_state(run_dir: Path) -> dict[str, Any]:
    state = read_json(run_dir / "state.json")
    if state.get("workflow") != EXPECTED_PACK_WORKFLOW:
        raise ReviewError(f"Unexpected workflow in state.json: {state.get('workflow')}")
    return state


def page_aliases(page: dict[str, Any]) -> set[str]:
    filename = str(page.get("filename") or "")
    stem = Path(filename).stem
    values = {str(page.get("id") or ""), filename, stem, slugify(stem), slugify(str(page.get("id") or ""))}
    return {value for value in values if value}


def resolve_stage_image(run_dir: Path, page: dict[str, Any], stage: str) -> Path:
    stage_record = (page.get("stages") or {}).get(stage) or {}
    output_path = stage_record.get("output_path")
    if output_path:
        path = Path(output_path)
        if not path.is_absolute() and path.exists():
            path = path.resolve(strict=False)
    else:
        stage_dir = STAGE_DIRS.get(stage)
        if not stage_dir:
            raise ReviewError(f"Unknown stage: {stage}")
        path = run_dir / stage_dir / str(page.get("filename") or "")
    if not path.is_absolute():
        path = run_dir / path
    path = path.resolve(strict=False)
    if not path_is_under(path, run_dir):
        raise ReviewError(f"Refusing to serve image outside run folder: {path}")
    if not path.exists():
        raise ReviewError(f"Stage image not found for {page.get('filename')}: {path}")
    return path


def review_pages(run_dir: Path, stage: str, items: list[str] | None = None) -> list[dict[str, Any]]:
    state = load_pack_state(run_dir)
    wanted = {slugify(Path(item).stem, str(item)) for item in items or []}
    pages = []
    for page in state.get("pages", []):
        aliases = page_aliases(page)
        if wanted and not (wanted & {slugify(Path(alias).stem, alias) for alias in aliases}):
            continue
        image_path = resolve_stage_image(run_dir, page, stage)
        pages.append(
            {
                "page_id": str(page.get("id") or ""),
                "filename": str(page.get("filename") or ""),
                "page_no": page.get("page_no") or page.get("order") or "",
                "image_path": str(image_path),
            }
        )
    if items and len(pages) != len(items):
        found = {page["filename"] for page in pages} | {page["page_id"] for page in pages}
        missing = [item for item in items if item not in found and Path(item).name not in found]
        raise ReviewError(f"Unknown review item(s): {', '.join(missing)}")
    if not pages:
        raise ReviewError("No reviewable images found.")
    return pages


def decode_png_data_url(data_url: str) -> bytes:
    prefix = "data:image/png;base64,"
    if not isinstance(data_url, str) or not data_url.startswith(prefix):
        raise ReviewError("Overlay data must be a PNG data URL.")
    encoded = data_url[len(prefix) :]
    try:
        data = base64.b64decode(encoded, validate=True)
    except (binascii.Error, ValueError) as exc:
        raise ReviewError("Overlay PNG data is not valid base64.") from exc
    if not data.startswith(PNG_SIGNATURE):
        raise ReviewError("Overlay data is not a PNG image.")
    return data


def load_pillow():
    try:
        from PIL import Image, ImageDraw
    except ImportError as exc:
        raise ReviewError("Pillow is required for create-markup. Install pillow or use the browser UI.") from exc
    return Image, ImageDraw


def png_data_url_from_image(image: Any) -> str:
    buffer = io.BytesIO()
    image.save(buffer, format="PNG")
    return "data:image/png;base64," + base64.b64encode(buffer.getvalue()).decode("ascii")


def finite_float(value: Any, label: str) -> float:
    try:
        number = float(value)
    except (TypeError, ValueError) as exc:
        raise ReviewError(f"{label} must be a number.") from exc
    if not math.isfinite(number):
        raise ReviewError(f"{label} must be a finite number.")
    return number


def palette_hex(color_id: str, explicit_color: str = "") -> str:
    if explicit_color:
        if not HEX_COLOR_RE.match(explicit_color):
            raise ReviewError(f"Markup color must be #RRGGBB: {explicit_color}")
        return explicit_color.lower()
    for color in PALETTE:
        if color["id"] == color_id:
            return color["hex"]
    raise ReviewError(f"Unknown color_id without explicit color: {color_id}")


def rgba_from_hex(color: str, alpha: int) -> tuple[int, int, int, int]:
    color = color.lstrip("#")
    return (int(color[0:2], 16), int(color[2:4], 16), int(color[4:6], 16), alpha)


def coordinate_space_for(spec: dict[str, Any], item: dict[str, Any], mark: dict[str, Any]) -> str:
    coordinate_space = str(
        mark.get("coordinate_space")
        or item.get("coordinate_space")
        or spec.get("coordinate_space")
        or "normalized"
    )
    if coordinate_space not in VALID_COORDINATE_SPACES:
        raise ReviewError(
            "coordinate_space must be one of: " + ", ".join(sorted(VALID_COORDINATE_SPACES))
        )
    return coordinate_space


def convert_box(box: Any, width: int, height: int, coordinate_space: str, label: str) -> list[float]:
    if not isinstance(box, list) or len(box) != 4:
        raise ReviewError(f"{label} rect box must be [x, y, width, height].")
    x, y, box_width, box_height = [finite_float(value, f"{label} box[{index}]") for index, value in enumerate(box)]
    if coordinate_space == "normalized":
        if x < 0 or y < 0 or box_width <= 0 or box_height <= 0 or x + box_width > 1 or y + box_height > 1:
            raise ReviewError(f"{label} normalized box must stay within 0..1 and have positive size.")
        return [x * width, y * height, (x + box_width) * width, (y + box_height) * height]
    if x < 0 or y < 0 or box_width <= 0 or box_height <= 0 or x + box_width > width or y + box_height > height:
        raise ReviewError(f"{label} pixel box must stay within the image and have positive size.")
    return [x, y, x + box_width, y + box_height]


def convert_points(points: Any, width: int, height: int, coordinate_space: str, label: str) -> list[tuple[float, float]]:
    if not isinstance(points, list) or len(points) < 3:
        raise ReviewError(f"{label} polygon points must include at least three [x, y] points.")
    converted = []
    for index, point in enumerate(points):
        if not isinstance(point, list) or len(point) != 2:
            raise ReviewError(f"{label} polygon point {index} must be [x, y].")
        x = finite_float(point[0], f"{label} point[{index}][0]")
        y = finite_float(point[1], f"{label} point[{index}][1]")
        if coordinate_space == "normalized":
            if x < 0 or x > 1 or y < 0 or y > 1:
                raise ReviewError(f"{label} normalized polygon points must stay within 0..1.")
            converted.append((x * width, y * height))
        else:
            if x < 0 or x > width or y < 0 or y > height:
                raise ReviewError(f"{label} pixel polygon points must stay within the image.")
            converted.append((x, y))
    return converted


def pages_by_reference(pages: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    indexed: dict[str, dict[str, Any]] = {}
    for page in pages:
        for value in {page["page_id"], page["filename"], Path(page["filename"]).stem, slugify(page["page_id"])}:
            if value:
                indexed[value] = page
                indexed[slugify(Path(value).stem, value)] = page
    return indexed


def markup_payload_from_spec(
    run_dir: Path,
    stage: str,
    spec: dict[str, Any],
    items: list[str] | None = None,
) -> dict[str, Any]:
    if not isinstance(spec, dict):
        raise ReviewError("Markup spec must be a JSON object.")
    spec_stage = str(spec.get("stage") or stage)
    if spec_stage != stage:
        raise ReviewError(f"Markup spec stage does not match requested stage: {spec_stage} != {stage}")
    Image, ImageDraw = load_pillow()
    pages = review_pages(run_dir, stage, items)
    indexed_pages = pages_by_reference(pages)
    raw_items = spec.get("items") or []
    if not isinstance(raw_items, list) or not raw_items:
        raise ReviewError("Markup spec must include at least one item.")

    payload_items = []
    for item_index, raw_item in enumerate(raw_items):
        if not isinstance(raw_item, dict):
            raise ReviewError(f"Markup item {item_index} must be an object.")
        page_ref = str(raw_item.get("filename") or raw_item.get("page_id") or "")
        page = indexed_pages.get(page_ref) or indexed_pages.get(slugify(Path(page_ref).stem, page_ref))
        if not page:
            raise ReviewError(f"Unknown or unsafe review item: {page_ref}")
        marks = raw_item.get("marks") or []
        if not isinstance(marks, list) or not marks:
            raise ReviewError(f"Markup item {page_ref} must include at least one mark.")

        with Image.open(page["image_path"]) as source:
            width, height = source.size
        overlays_by_color: dict[str, dict[str, Any]] = {}
        outline_width = max(2, round(min(width, height) * 0.012))
        for mark_index, mark in enumerate(marks):
            if not isinstance(mark, dict):
                raise ReviewError(f"Markup mark {item_index}.{mark_index} must be an object.")
            request = str(mark.get("request") or mark.get("note") or "").strip()
            if not request:
                raise ReviewError(f"Markup mark {item_index}.{mark_index} must include non-empty request text.")
            color_id = slugify(str(mark.get("color_id") or mark.get("color") or "overlay"), "overlay")
            color = palette_hex(color_id, str(mark.get("color") or ""))
            shape = str(mark.get("shape") or "rect")
            coordinate_space = coordinate_space_for(spec, raw_item, mark)
            entry = overlays_by_color.get(color_id)
            if not entry:
                image = Image.new("RGBA", (width, height), (0, 0, 0, 0))
                entry = {
                    "color_id": color_id,
                    "color": color,
                    "image": image,
                    "requests": [],
                    "draw": ImageDraw.Draw(image, "RGBA"),
                }
                overlays_by_color[color_id] = entry
            draw = entry["draw"]
            fill = rgba_from_hex(color, 88)
            outline = rgba_from_hex(color, 220)
            label = f"markup mark {item_index}.{mark_index}"
            if shape == "rect":
                draw.rectangle(
                    convert_box(mark.get("box"), width, height, coordinate_space, label),
                    fill=fill,
                    outline=outline,
                    width=outline_width,
                )
            elif shape == "polygon":
                points = convert_points(mark.get("points"), width, height, coordinate_space, label)
                draw.polygon(points, fill=fill)
                draw.line(points + [points[0]], fill=outline, width=outline_width, joint="curve")
            else:
                raise ReviewError(f"{label} uses unsupported shape: {shape}")
            if request not in entry["requests"]:
                entry["requests"].append(request)

        combined = Image.new("RGBA", (width, height), (0, 0, 0, 0))
        overlays = []
        for color_id in sorted(overlays_by_color):
            entry = overlays_by_color[color_id]
            combined = Image.alpha_composite(combined, entry["image"])
            requests = entry["requests"]
            request_text = requests[0] if len(requests) == 1 else "\n".join(f"- {request}" for request in requests)
            overlays.append(
                {
                    "color_id": color_id,
                    "color": entry["color"],
                    "request": request_text,
                    "data_url": png_data_url_from_image(entry["image"]),
                }
            )
        payload_items.append(
            {
                "page_id": page["page_id"],
                "filename": page["filename"],
                "overlays": overlays,
                "combined_data_url": png_data_url_from_image(combined),
            }
        )

    return {"stage": stage, "review_id": spec.get("review_id") or "", "items": payload_items}


def create_markup_manifest(
    run_dir: Path,
    stage: str,
    spec: dict[str, Any],
    review_id: str | None = None,
    items: list[str] | None = None,
) -> dict[str, Any]:
    if stage not in STAGE_DIRS:
        raise ReviewError(f"Unknown stage: {stage}")
    payload = markup_payload_from_spec(run_dir, stage, spec, items=items)
    return save_review_payload(run_dir, stage, payload, review_id=review_id or str(spec.get("review_id") or ""), items=items)


def manifest_markdown(manifest: dict[str, Any]) -> str:
    lines = [
        "# Revision Requests",
        "",
        f"- workflow: {manifest.get('workflow')}",
        f"- run_dir: {manifest.get('run_dir')}",
        f"- stage: {manifest.get('stage')}",
        f"- review_id: {manifest.get('review_id')}",
        f"- created_at: {manifest.get('created_at')}",
        "",
    ]
    for item in manifest.get("items", []):
        lines.extend(
            [
                f"## {item.get('filename')}",
                "",
                f"- source_image: {item.get('source_image')}",
                f"- combined_overlay: {item.get('combined_overlay_path') or 'none'}",
                "",
            ]
        )
        for overlay in item.get("overlays", []):
            lines.extend(
                [
                    f"### {overlay.get('color_id')} {overlay.get('color')}",
                    "",
                    f"- overlay: {overlay.get('overlay_path')}",
                    f"- request_file: {overlay.get('request_path')}",
                    "",
                    str(overlay.get("request") or ""),
                    "",
                ]
            )
    return "\n".join(lines).rstrip() + "\n"


def save_review_payload(
    run_dir: Path,
    stage: str,
    payload: dict[str, Any],
    review_id: str | None = None,
    items: list[str] | None = None,
) -> dict[str, Any]:
    run_dir = run_dir.resolve(strict=False)
    if not path_is_under(run_dir, run_dir):
        raise ReviewError(f"Invalid run folder: {run_dir}")
    payload_stage = str(payload.get("stage") or stage)
    if payload_stage != stage:
        raise ReviewError(f"Payload stage does not match requested stage: {payload_stage} != {stage}")
    pages = review_pages(run_dir, stage, items)
    pages_by_alias: dict[str, dict[str, Any]] = {}
    for page in pages:
        for value in {page["page_id"], page["filename"], Path(page["filename"]).stem, slugify(page["page_id"])}:
            if value:
                pages_by_alias[value] = page
                pages_by_alias[slugify(Path(value).stem, value)] = page

    raw_items = payload.get("items") or []
    if not isinstance(raw_items, list) or not raw_items:
        raise ReviewError("Payload must include at least one item.")

    prepared_items = []
    for raw_item in raw_items:
        if not isinstance(raw_item, dict):
            raise ReviewError("Payload items must be objects.")
        page_ref = str(raw_item.get("filename") or raw_item.get("page_id") or "")
        page = pages_by_alias.get(page_ref) or pages_by_alias.get(slugify(Path(page_ref).stem, page_ref))
        if not page:
            raise ReviewError(f"Unknown or unsafe review item: {page_ref}")
        raw_overlays = raw_item.get("overlays") or []
        if not isinstance(raw_overlays, list):
            raise ReviewError("Item overlays must be a list.")
        prepared_overlays = []
        for raw_overlay in raw_overlays:
            if not isinstance(raw_overlay, dict):
                raise ReviewError("Overlay entries must be objects.")
            request = str(raw_overlay.get("request") or raw_overlay.get("note") or "").strip()
            if not request:
                raise ReviewError("Every painted overlay must include request text before saving.")
            color_id = slugify(str(raw_overlay.get("color_id") or raw_overlay.get("color") or "overlay"), "overlay")
            color = str(raw_overlay.get("color") or "")
            png_data = decode_png_data_url(str(raw_overlay.get("data_url") or ""))
            prepared_overlays.append(
                {
                    "color_id": color_id,
                    "color": color,
                    "request": request,
                    "png_data": png_data,
                }
            )
        if not prepared_overlays:
            continue
        combined_data = None
        if raw_item.get("combined_data_url"):
            combined_data = decode_png_data_url(str(raw_item.get("combined_data_url")))
        prepared_items.append({"page": page, "overlays": prepared_overlays, "combined_data": combined_data})

    if not prepared_items:
        raise ReviewError("Payload did not include any painted overlays.")

    review_id = slugify(review_id or str(payload.get("review_id") or datetime.now().strftime("review-%Y%m%d-%H%M%S")))
    output_dir = (run_dir / "review_overlays" / stage / review_id).resolve(strict=False)
    if not path_is_under(output_dir, run_dir):
        raise ReviewError(f"Review output folder must stay under run folder: {output_dir}")
    output_dir.mkdir(parents=True, exist_ok=True)

    manifest: dict[str, Any] = {
        "workflow": WORKFLOW,
        "run_dir": str(run_dir),
        "stage": stage,
        "review_id": review_id,
        "created_at": now_iso(),
        "items": [],
        "revision_count": 0,
    }
    for prepared in prepared_items:
        page = prepared["page"]
        stem = Path(page["filename"]).stem
        manifest_item: dict[str, Any] = {
            "page_id": page["page_id"],
            "filename": page["filename"],
            "source_image": page["image_path"],
            "combined_overlay_path": "",
            "overlays": [],
        }
        if prepared["combined_data"]:
            combined_path = output_dir / f"{stem}_overlay_combined.png"
            combined_path.write_bytes(prepared["combined_data"])
            manifest_item["combined_overlay_path"] = str(combined_path)
        for overlay in prepared["overlays"]:
            overlay_path = output_dir / f"{stem}_overlay_{overlay['color_id']}.png"
            request_path = output_dir / f"{stem}_overlay_{overlay['color_id']}.txt"
            overlay_path.write_bytes(overlay["png_data"])
            request_path.write_text(overlay["request"].rstrip() + "\n", encoding="utf-8")
            manifest_item["overlays"].append(
                {
                    "color_id": overlay["color_id"],
                    "color": overlay["color"],
                    "overlay_path": str(overlay_path),
                    "request_path": str(request_path),
                    "request": overlay["request"],
                }
            )
            manifest["revision_count"] += 1
        manifest["items"].append(manifest_item)

    manifest_path = output_dir / "revision_requests.json"
    markdown_path = output_dir / "revision_requests.md"
    manifest["manifest_path"] = str(manifest_path)
    manifest["markdown_path"] = str(markdown_path)
    write_json(manifest_path, manifest)
    markdown_path.write_text(manifest_markdown(manifest), encoding="utf-8")
    return manifest


def json_response(handler: http.server.BaseHTTPRequestHandler, status: int, data: dict[str, Any]) -> None:
    body = json.dumps(data, ensure_ascii=False).encode("utf-8")
    handler.send_response(status)
    handler.send_header("Content-Type", "application/json; charset=utf-8")
    handler.send_header("Content-Length", str(len(body)))
    handler.end_headers()
    handler.wfile.write(body)


def html_response(handler: http.server.BaseHTTPRequestHandler, body: str) -> None:
    data = body.encode("utf-8")
    handler.send_response(200)
    handler.send_header("Content-Type", "text/html; charset=utf-8")
    handler.send_header("Content-Length", str(len(data)))
    handler.end_headers()
    handler.wfile.write(data)


def make_handler(run_dir: Path, stage: str, items: list[str] | None):
    pages = review_pages(run_dir, stage, items)
    page_by_filename = {page["filename"]: page for page in pages}

    class ReviewHandler(http.server.BaseHTTPRequestHandler):
        def log_message(self, format: str, *args: Any) -> None:
            sys.stderr.write("review-overlay: " + (format % args) + "\n")

        def do_GET(self) -> None:
            parsed = urllib.parse.urlparse(self.path)
            if parsed.path == "/":
                html_response(self, render_html())
                return
            if parsed.path == "/api/config":
                config_pages = [
                    {
                        "page_id": page["page_id"],
                        "filename": page["filename"],
                        "page_no": page["page_no"],
                        "image_url": f"/api/image?filename={urllib.parse.quote(page['filename'])}",
                    }
                    for page in pages
                ]
                json_response(
                    self,
                    200,
                    {
                        "workflow": WORKFLOW,
                        "run_dir": str(run_dir),
                        "stage": stage,
                        "palette": PALETTE,
                        "pages": config_pages,
                    },
                )
                return
            if parsed.path == "/api/image":
                query = urllib.parse.parse_qs(parsed.query)
                filename = query.get("filename", [""])[0]
                page = page_by_filename.get(filename)
                if not page:
                    json_response(self, 404, {"error": "unknown image"})
                    return
                image_path = Path(page["image_path"])
                data = image_path.read_bytes()
                self.send_response(200)
                self.send_header("Content-Type", "image/png")
                self.send_header("Content-Length", str(len(data)))
                self.end_headers()
                self.wfile.write(data)
                return
            json_response(self, 404, {"error": "not found"})

        def do_POST(self) -> None:
            parsed = urllib.parse.urlparse(self.path)
            if parsed.path != "/api/save":
                json_response(self, 404, {"error": "not found"})
                return
            length = int(self.headers.get("Content-Length") or "0")
            if length <= 0 or length > 200 * 1024 * 1024:
                json_response(self, 413, {"error": "invalid payload size"})
                return
            try:
                payload = json.loads(self.rfile.read(length).decode("utf-8"))
                manifest = save_review_payload(run_dir, stage, payload, items=items)
            except (ReviewError, json.JSONDecodeError) as exc:
                json_response(self, 400, {"error": str(exc)})
                return
            json_response(
                self,
                200,
                {
                    "ok": True,
                    "manifest_path": manifest["manifest_path"],
                    "markdown_path": manifest["markdown_path"],
                    "revision_count": manifest["revision_count"],
                },
            )

    return ReviewHandler


class ThreadingHTTPServer(socketserver.ThreadingMixIn, http.server.HTTPServer):
    daemon_threads = True


def render_html() -> str:
    palette_json = json.dumps(PALETTE)
    return f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Review Image Overlays</title>
  <style>
    :root {{ color-scheme: light; font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif; }}
    body {{ margin: 0; background: #f6f7f8; color: #171717; }}
    header {{ position: sticky; top: 0; z-index: 10; display: flex; align-items: center; gap: 16px; padding: 12px 16px; background: #ffffff; border-bottom: 1px solid #d8dde3; }}
    h1 {{ margin: 0; font-size: 18px; font-weight: 700; }}
    button {{ border: 1px solid #c8d0d9; background: #ffffff; border-radius: 6px; padding: 7px 10px; cursor: pointer; }}
    button:hover {{ background: #f0f3f6; }}
    .toolbar {{ display: flex; align-items: center; gap: 10px; flex-wrap: wrap; }}
    .swatch {{ width: 28px; height: 28px; border-radius: 50%; padding: 0; border: 2px solid #ffffff; box-shadow: 0 0 0 1px #aeb8c2; }}
    .swatch.active {{ box-shadow: 0 0 0 3px #111827; }}
    .status {{ margin-left: auto; font-size: 13px; color: #4b5563; }}
    main {{ padding: 16px; }}
    .grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(520px, 1fr)); gap: 18px; align-items: start; }}
    .card {{ background: #ffffff; border: 1px solid #d8dde3; border-radius: 8px; overflow: hidden; }}
    .card-header {{ display: flex; align-items: center; justify-content: space-between; gap: 10px; padding: 10px 12px; border-bottom: 1px solid #e3e7ec; }}
    .title {{ font-size: 14px; font-weight: 700; word-break: break-all; }}
    .canvas-row {{ display: grid; grid-template-columns: minmax(0, 1fr) 260px; gap: 12px; padding: 12px; }}
    .image-wrap {{ position: relative; display: inline-block; max-width: 100%; align-self: start; border: 1px solid #d8dde3; background: #fbfbfb; }}
    .image-wrap img {{ display: block; max-width: 100%; height: auto; user-select: none; }}
    .image-wrap canvas {{ position: absolute; inset: 0; width: 100%; height: 100%; touch-action: none; cursor: crosshair; }}
    .notes {{ display: flex; flex-direction: column; gap: 10px; }}
    .note-box {{ border: 1px solid #e0e5eb; border-radius: 6px; padding: 8px; }}
    .note-label {{ display: flex; align-items: center; gap: 8px; font-size: 13px; font-weight: 700; margin-bottom: 6px; }}
    .dot {{ width: 12px; height: 12px; border-radius: 50%; display: inline-block; }}
    textarea {{ width: 100%; min-height: 82px; box-sizing: border-box; border: 1px solid #c8d0d9; border-radius: 6px; padding: 7px; resize: vertical; font: inherit; font-size: 13px; }}
    .empty {{ color: #6b7280; font-size: 13px; line-height: 1.4; }}
    @media (max-width: 820px) {{
      .grid {{ grid-template-columns: 1fr; }}
      .canvas-row {{ grid-template-columns: 1fr; }}
      .notes {{ max-width: none; }}
    }}
  </style>
</head>
<body>
  <header>
    <h1>Review Image Overlays</h1>
    <div class="toolbar" id="palette"></div>
    <label>Brush <input id="brush" type="range" min="4" max="72" value="24"></label>
    <button id="undo">Undo</button>
    <button id="clear-color">Clear Color</button>
    <button id="save">Save</button>
    <div class="status" id="status">Loading...</div>
  </header>
  <main><div class="grid" id="gallery"></div></main>
  <script>
    const palette = {palette_json};
    const paletteMap = Object.fromEntries(palette.map(c => [c.id, c]));
    const state = {{ activeColor: palette[0].id, brush: 24, cards: [] }};
    const statusEl = document.getElementById('status');

    function setStatus(text) {{ statusEl.textContent = text; }}
    function escapeHtml(value) {{
      return String(value).replace(/[&<>"']/g, ch => ({{'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}}[ch]));
    }}
    function drawStroke(ctx, stroke) {{
      const color = paletteMap[stroke.colorId]?.hex || '#ff3b30';
      ctx.strokeStyle = color;
      ctx.lineWidth = stroke.brush;
      ctx.lineCap = 'round';
      ctx.lineJoin = 'round';
      ctx.globalAlpha = 0.55;
      ctx.beginPath();
      stroke.points.forEach((pt, index) => {{
        if (index === 0) ctx.moveTo(pt.x, pt.y);
        else ctx.lineTo(pt.x, pt.y);
      }});
      ctx.stroke();
      ctx.globalAlpha = 1;
    }}
    function redraw(card) {{
      card.ctx.clearRect(0, 0, card.canvas.width, card.canvas.height);
      card.strokes.forEach(stroke => drawStroke(card.ctx, stroke));
      refreshNotes(card);
    }}
    function usedColorIds(card) {{
      return [...new Set(card.strokes.map(stroke => stroke.colorId))];
    }}
    function refreshNotes(card) {{
      const used = usedColorIds(card);
      card.notesEl.innerHTML = '';
      if (!used.length) {{
        card.notesEl.innerHTML = '<div class="empty">Paint on this image to create a color-specific revision request field.</div>';
        return;
      }}
      used.forEach(colorId => {{
        const color = paletteMap[colorId];
        const box = document.createElement('div');
        box.className = 'note-box';
        box.innerHTML = `<div class="note-label"><span class="dot" style="background:${{color.hex}}"></span>${{escapeHtml(color.name)}} request</div>`;
        const textarea = document.createElement('textarea');
        textarea.value = card.notes[colorId] || '';
        textarea.placeholder = 'Describe the requested edit for the painted area.';
        textarea.addEventListener('input', () => {{ card.notes[colorId] = textarea.value; }});
        box.appendChild(textarea);
        card.notesEl.appendChild(box);
      }});
    }}
    function pointFromEvent(canvas, event) {{
      const rect = canvas.getBoundingClientRect();
      return {{
        x: (event.clientX - rect.left) * (canvas.width / rect.width),
        y: (event.clientY - rect.top) * (canvas.height / rect.height)
      }};
    }}
    function attachCanvas(card) {{
      card.canvas.addEventListener('pointerdown', event => {{
        event.preventDefault();
        card.canvas.setPointerCapture(event.pointerId);
        const stroke = {{ colorId: state.activeColor, brush: Number(document.getElementById('brush').value), points: [pointFromEvent(card.canvas, event)] }};
        card.strokes.push(stroke);
        card.activeStroke = stroke;
        card.notes[stroke.colorId] = card.notes[stroke.colorId] || '';
        redraw(card);
      }});
      card.canvas.addEventListener('pointermove', event => {{
        if (!card.activeStroke) return;
        card.activeStroke.points.push(pointFromEvent(card.canvas, event));
        redraw(card);
      }});
      card.canvas.addEventListener('pointerup', () => {{ card.activeStroke = null; }});
      card.canvas.addEventListener('pointercancel', () => {{ card.activeStroke = null; }});
    }}
    function renderPalette() {{
      const el = document.getElementById('palette');
      palette.forEach(color => {{
        const button = document.createElement('button');
        button.className = 'swatch' + (color.id === state.activeColor ? ' active' : '');
        button.title = color.name;
        button.style.background = color.hex;
        button.addEventListener('click', () => {{
          state.activeColor = color.id;
          document.querySelectorAll('.swatch').forEach(node => node.classList.remove('active'));
          button.classList.add('active');
        }});
        el.appendChild(button);
      }});
    }}
    function renderCard(page) {{
      const cardEl = document.createElement('section');
      cardEl.className = 'card';
      cardEl.innerHTML = `<div class="card-header"><div class="title">${{escapeHtml(page.filename)}}</div></div><div class="canvas-row"><div class="image-wrap"><img alt=""><canvas></canvas></div><div class="notes"></div></div>`;
      const img = cardEl.querySelector('img');
      const canvas = cardEl.querySelector('canvas');
      const notesEl = cardEl.querySelector('.notes');
      const card = {{ page, canvas, ctx: canvas.getContext('2d'), notesEl, strokes: [], notes: {{}}, activeStroke: null }};
      img.onload = () => {{
        canvas.width = img.naturalWidth;
        canvas.height = img.naturalHeight;
        redraw(card);
      }};
      img.src = page.image_url;
      attachCanvas(card);
      state.cards.push(card);
      return cardEl;
    }}
    function canvasForColor(card, colorId) {{
      const canvas = document.createElement('canvas');
      canvas.width = card.canvas.width;
      canvas.height = card.canvas.height;
      const ctx = canvas.getContext('2d');
      card.strokes.filter(stroke => stroke.colorId === colorId).forEach(stroke => drawStroke(ctx, stroke));
      return canvas;
    }}
    function combinedCanvas(card) {{
      const canvas = document.createElement('canvas');
      canvas.width = card.canvas.width;
      canvas.height = card.canvas.height;
      const ctx = canvas.getContext('2d');
      card.strokes.forEach(stroke => drawStroke(ctx, stroke));
      return canvas;
    }}
    async function saveAll(config) {{
      const items = [];
      for (const card of state.cards) {{
        const overlays = [];
        for (const colorId of usedColorIds(card)) {{
          const request = (card.notes[colorId] || '').trim();
          if (!request) {{
            setStatus(`Missing request text for ${{card.page.filename}} / ${{paletteMap[colorId].name}}`);
            return;
          }}
          overlays.push({{
            color_id: colorId,
            color: paletteMap[colorId].hex,
            request,
            data_url: canvasForColor(card, colorId).toDataURL('image/png')
          }});
        }}
        if (overlays.length) {{
          items.push({{
            page_id: card.page.page_id,
            filename: card.page.filename,
            overlays,
            combined_data_url: combinedCanvas(card).toDataURL('image/png')
          }});
        }}
      }}
      if (!items.length) {{
        setStatus('Paint at least one overlay before saving.');
        return;
      }}
      setStatus('Saving...');
      const response = await fetch('/api/save', {{
        method: 'POST',
        headers: {{ 'Content-Type': 'application/json' }},
        body: JSON.stringify({{ stage: config.stage, items }})
      }});
      const data = await response.json();
      if (!response.ok) {{
        setStatus(data.error || 'Save failed');
        return;
      }}
      setStatus(`Saved ${{data.revision_count}} request(s): ${{data.manifest_path}}`);
    }}
    async function main() {{
      renderPalette();
      const config = await (await fetch('/api/config')).json();
      const gallery = document.getElementById('gallery');
      config.pages.forEach(page => gallery.appendChild(renderCard(page)));
      document.getElementById('brush').addEventListener('input', event => {{ state.brush = Number(event.target.value); }});
      document.getElementById('undo').addEventListener('click', () => {{
        state.cards.forEach(card => {{ if (card.strokes.length) {{ card.strokes.pop(); redraw(card); }} }});
      }});
      document.getElementById('clear-color').addEventListener('click', () => {{
        state.cards.forEach(card => {{ card.strokes = card.strokes.filter(stroke => stroke.colorId !== state.activeColor); redraw(card); }});
      }});
      document.getElementById('save').addEventListener('click', () => saveAll(config));
      setStatus(`${{config.pages.length}} image(s) loaded`);
    }}
    main().catch(error => setStatus(error.message));
  </script>
</body>
</html>"""


def command_serve(args: argparse.Namespace) -> None:
    run_dir = Path(args.run_dir).resolve(strict=False)
    stage = args.stage
    handler = make_handler(run_dir, stage, args.items)
    server = ThreadingHTTPServer((args.host, args.port), handler)
    host, port = server.server_address
    url = f"http://{host}:{port}/"
    print(f"REVIEW_OVERLAY_URL: {url}")
    print(f"RUN_DIR: {run_dir}")
    print(f"STAGE: {stage}")
    if not args.no_browser:
        webbrowser.open(url)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nSTOPPED")
    finally:
        server.server_close()


def command_save_payload(args: argparse.Namespace) -> None:
    payload = read_json(Path(args.payload))
    manifest = save_review_payload(
        Path(args.run_dir),
        args.stage,
        payload,
        review_id=args.review_id,
        items=args.items,
    )
    print(f"MANIFEST: {manifest['manifest_path']}")
    print(f"MARKDOWN: {manifest['markdown_path']}")
    print(f"REVISION_COUNT: {manifest['revision_count']}")


def command_create_markup(args: argparse.Namespace) -> None:
    spec = read_json(Path(args.spec))
    if not isinstance(spec, dict):
        raise ReviewError("Markup spec must be a JSON object.")
    stage = args.stage or str(spec.get("stage") or "storyboard_sketch_ink")
    manifest = create_markup_manifest(
        Path(args.run_dir),
        stage,
        spec,
        review_id=args.review_id,
        items=args.items,
    )
    print(f"MANIFEST: {manifest['manifest_path']}")
    print(f"MARKDOWN: {manifest['markdown_path']}")
    print(f"REVISION_COUNT: {manifest['revision_count']}")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Open and save color-coded image revision overlays.")
    subparsers = parser.add_subparsers(dest="command", required=True)

    serve = subparsers.add_parser("serve")
    serve.add_argument("--run-dir", required=True)
    serve.add_argument("--stage", choices=sorted(STAGE_DIRS), default="storyboard_sketch_ink")
    serve.add_argument("--items", action="append", default=[])
    serve.add_argument("--host", default="127.0.0.1")
    serve.add_argument("--port", type=int, default=0)
    serve.add_argument("--no-browser", action="store_true")
    serve.set_defaults(func=command_serve)

    save_payload = subparsers.add_parser("save-payload")
    save_payload.add_argument("--run-dir", required=True)
    save_payload.add_argument("--stage", choices=sorted(STAGE_DIRS), default="storyboard_sketch_ink")
    save_payload.add_argument("--payload", required=True)
    save_payload.add_argument("--review-id", default="")
    save_payload.add_argument("--items", action="append", default=[])
    save_payload.set_defaults(func=command_save_payload)

    create_markup = subparsers.add_parser("create-markup")
    create_markup.add_argument("--run-dir", required=True)
    create_markup.add_argument("--stage", default="")
    create_markup.add_argument("--spec", required=True)
    create_markup.add_argument("--review-id", default="")
    create_markup.add_argument("--items", action="append", default=[])
    create_markup.set_defaults(func=command_create_markup)
    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()
    try:
        args.func(args)
    except ReviewError as exc:
        raise SystemExit(str(exc)) from exc
    return 0


if __name__ == "__main__":
    sys.exit(main())
