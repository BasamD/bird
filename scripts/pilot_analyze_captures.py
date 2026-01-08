import os
import sys
import time
import json
import shutil
import base64
import argparse
import traceback
import logging
from logging.handlers import RotatingFileHandler
from pathlib import Path
from datetime import datetime, date

import cv2
import re
from typing import Any
import hashlib
from ultralytics import YOLO

# =========================
# CONFIG
# =========================
DEFAULT_ROOT = r"C:\env\vision\pilot_captures"
REPORT_ROOT = r"C:\env\vision\pilot_reports"
LOG_ROOT = r"C:\env\vision\pilot_logs"

# Directory where the dashboard and aggregated metrics will be stored.  A single
# `dashboard.html` file will be written here along with a `metrics.json`
# file containing all aggregated data.  The dashboard can be opened in a
# browser and will be refreshed automatically every 30 seconds.
DASHBOARD_DIR = Path(r"C:\env\vision\dashboard")
METRICS_FILE = DASHBOARD_DIR / "metrics.json"
DASHBOARD_FILE = DASHBOARD_DIR / "dashboard.html"

MODEL_PATH = "yolov8n.pt"
# Lower the detection threshold slightly to improve sensitivity on small birds.
CONF_THRESH = 0.25
BIRD_CLASS_ID = 14  # COCO: bird

# Minimum relative area of a detection box (fraction of ROI) to be
# considered a valid bird.  Detections smaller than this ratio are
# filtered out to reduce false positives.  You can override this via
# the ``MIN_AREA_RATIO`` environment variable.
MIN_AREA_RATIO = float(os.environ.get("MIN_AREA_RATIO", 0.002))

# Region of interest for detection (normalized coordinates).  The feeder is
# located roughly in the lower middle area of the frame.  Cropping
# improves detection reliability and reduces false negatives when large
# portions of the frame contain background.
ROI_NORM = (0.25, 0.34, 0.62, 0.72)

# Unique logic (simple pilot)
DUP_SECONDS = 15  # if we saw a bird within N seconds, treat as same "visit"
# =========================


def setup_logging():
    Path(LOG_ROOT).mkdir(parents=True, exist_ok=True)
    log_path = Path(LOG_ROOT) / f"pilot_analyzer_{date.today().isoformat()}.log"

    logger = logging.getLogger("pilot_analyzer")
    logger.setLevel(logging.DEBUG)

    fmt = logging.Formatter("[%(asctime)s] [%(levelname)s] %(message)s", "%Y-%m-%d %H:%M:%S")

    ch = logging.StreamHandler(sys.stdout)
    ch.setLevel(logging.INFO)
    ch.setFormatter(fmt)

    fh = RotatingFileHandler(str(log_path), maxBytes=2_000_000, backupCount=5, encoding="utf-8")
    fh.setLevel(logging.DEBUG)
    fh.setFormatter(fmt)

    # avoid duplicate handlers if script is reloaded
    logger.handlers.clear()
    logger.addHandler(ch)
    logger.addHandler(fh)

    logger.debug(f"Logging to {log_path}")
    return logger


log = setup_logging()


def now_str():
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def safe_mkdir(p: Path):
    p.mkdir(parents=True, exist_ok=True)


def try_lock(image_path: Path) -> Path | None:
    """
    Create a lock file to prevent double-processing.
    Returns lock path if acquired, else None.
    """
    lock_path = image_path.with_suffix(image_path.suffix + ".lock")
    try:
        # exclusive create
        fd = os.open(str(lock_path), os.O_CREAT | os.O_EXCL | os.O_WRONLY)
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            f.write(f"locked_at={now_str()}\n")
        return lock_path
    except FileExistsError:
        return None
    except Exception:
        log.error("Lock create failed:\n" + traceback.format_exc())
        return None


def release_lock(lock_path: Path):
    try:
        if lock_path.exists():
            lock_path.unlink()
    except Exception:
        log.error("Lock release failed:\n" + traceback.format_exc())


def move_with_retries(src: Path, dst_dir: Path, suffix: str = "", tries: int = 3, delay: float = 0.2) -> Path | None:
    """
    Move src into dst_dir. If src vanishes, do NOT crash.
    Returns new path or None.
    """
    safe_mkdir(dst_dir)

    if not src.exists():
        log.warning(f"move_with_retries: source missing (already moved/deleted?): {src}")
        return None

    ts = int(time.time())
    new_name = f"{src.stem}{suffix}_{ts}{src.suffix}"
    dst = dst_dir / new_name

    last_err = None
    for i in range(tries):
        try:
            # re-check each attempt
            if not src.exists():
                log.warning(f"move_with_retries: source missing on attempt {i+1}: {src}")
                return None
            shutil.move(str(src), str(dst))
            return dst
        except Exception as e:
            last_err = e
            time.sleep(delay)

    log.error(f"Failed to move after {tries} tries: {src} -> {dst_dir} | err={last_err}")
    log.error(traceback.format_exc())
    return None


def load_openai_client():
    """
    Loads the OpenAI client using the API key found in the ``OPENAI_API_KEY`` environment variable.
    Falls back to the default embedded key if the environment variable is not set.  We do *not* call
    ``os.getenv`` with the literal API key string (which breaks key lookup); instead we read
    ``OPENAI_API_KEY`` and strip it.  If no key is found, returns (None, None).
    """
    # Prefer the environment variable so users can override the default without editing code.
    default_key = (
        "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"
    )
    key = os.environ.get("OPENAI_API_KEY", "").strip() or default_key.strip()
    if not key:
        return None, None

    try:
        from openai import OpenAI
        client = OpenAI(api_key=key)
        return client, key
    except Exception:
        log.error("OpenAI import/init failed:\n" + traceback.format_exc())
        return None, key

# ---------------------------------------------------------------------------
# Metrics and Dashboard Helpers
#
# These functions mirror those defined in `pilot_bird_counter.py`.  They
# maintain a `metrics.json` file containing visit records and aggregated
# statistics (total visits and per-species counts) and update a single
# `dashboard.html` page.  The dashboard includes a meta refresh so that the
# page updates automatically when viewed in a browser.  The helper
# functions here are self-contained to avoid cross-module dependencies.

def load_metrics() -> dict:
    """Load the metrics file if it exists, or return a default structure."""
    try:
        if METRICS_FILE.exists():
            with METRICS_FILE.open("r", encoding="utf-8") as f:
                return json.load(f)
    except Exception as e:
        log.warning(f"[metrics] failed to load metrics: {e}")
    return {
        "total_visits": 0,
        "visits": [],
        "species_counts": {},
    }


# ---------------------------------------------------------------------------
# Species normalisation helpers (mirrored from pilot_bird_counter.py)
def normalize_species(name: str) -> str:
    """Return a canonical species name for counting purposes."""
    if not name:
        return "unknown"
    s = name.strip().lower()
    s = re.sub(r"[^a-z0-9\s]", "", s)
    if "," in s or " and " in s:
        return "multi"
    if s.endswith("s") and not s.endswith("ss"):
        s = s[:-1]
    synonyms = {
        "sparrow": "house sparrow",
        "house sparrows": "house sparrow",
    }
    return synonyms.get(s, s)


def save_metrics(metrics: dict) -> None:
    """Write the metrics dictionary to disk."""
    DASHBOARD_DIR.mkdir(parents=True, exist_ok=True)
    try:
        with METRICS_FILE.open("w", encoding="utf-8") as f:
            json.dump(metrics, f, indent=2)
    except Exception as e:
        log.warning(f"[metrics] failed to save metrics: {e}")


def write_dashboard_html(metrics: dict) -> None:
    """
    Generate the dashboard HTML based on the current metrics.  The
    dashboard lists each visit with its ID, timestamp and species
    guess, and shows aggregated counts.  It includes a meta refresh
    tag so that when opened in a browser it updates automatically.
    """
    DASHBOARD_DIR.mkdir(parents=True, exist_ok=True)
    total_visits = metrics.get("total_visits", 0)
    species_counts = metrics.get("species_counts", {})
    visits = metrics.get("visits", [])

    # Build rows for species summary
    species_rows = ""
    for sp, count in sorted(species_counts.items(), key=lambda x: x[1], reverse=True):
        species_rows += f"<li>{sp}: {count}</li>\n"

    # Build rows for visits
    visit_rows = ""
    for v in visits:
        sp_display = v.get("species_norm") or v.get("species")
        sp_raw = v.get("species_raw")
        # Use stored relative paths directly.  They are computed relative to
        # the dashboard directory during metrics update, so no additional
        # prefix is necessary.
        report_href = v.get('report_rel', '')
        photo_href = v.get('image_rel', '')
        summary = v.get("summary", "")
        visit_rows += (
            f"<tr>"
            f"<td>{v.get('timestamp','')}</td>"
            f"<td>{v.get('id','')}</td>"
            f"<td title='{sp_raw}'>{sp_display}</td>"
            f"<td>{summary}</td>"
            f"<td><a href='{report_href}'>report</a> | <a href='{photo_href}'>photo</a></td>"
            f"</tr>\n"
        )

    html = f"""<!doctype html>
<html>
<head>
  <meta charset='utf-8' />
  <title>Bird Visit Dashboard</title>
  <meta http-equiv='refresh' content='30'>
  <style>
    body {{ font-family: Arial, sans-serif; margin: 20px; }}
    h1 {{ margin-top: 0; }}
    table {{ width: 100%; border-collapse: collapse; margin-top: 20px; }}
    th, td {{ border: 1px solid #ddd; padding: 8px; text-align: left; }}
    th {{ background-color: #f2f2f2; }}
  </style>
</head>
<body>
  <h1>Bird Visit Dashboard</h1>
  <p><b>Total visits:</b> {total_visits}</p>
  <h2>Species counts</h2>
  <ul>
    {species_rows}
  </ul>
  <h2>All visits</h2>
  <table>
    <tr>
      <th>Timestamp</th>
      <th>ID</th>
      <th>Species</th>
      <th>Summary</th>
      <th>Links</th>
    </tr>
    {visit_rows}
  </table>
</body>
</html>"""

    try:
        with DASHBOARD_FILE.open("w", encoding="utf-8") as f:
            f.write(html)
    except Exception as e:
        log.warning(f"[dashboard] failed to write dashboard: {e}")


def update_metrics(image_path: Path, species: str, summary: str, timestamp: datetime) -> None:
    """
    Update the metrics with a new visit entry.  Handles de-duplication
    by ID, normalises species names, and stores additional fields for
    the dashboard (relative report and image paths, review flags, etc.).
    """
    metrics = load_metrics()
    # Compute stable event ID by hashing the image bytes.  This avoids
    # duplicate entries across runs or reprocessing.  Fallback to filename
    # stem if hashing fails.
    try:
        digest = hashlib.sha1(image_path.read_bytes()).hexdigest()
    except Exception as e:
        log.error(f"Failed to compute digest for {image_path}: {e}")
        digest = image_path.stem
    visit_id = digest
    species_norm = normalize_species(species)
    date_str = timestamp.strftime("%Y-%m-%d")
    # Compute relative paths to report and image from the dashboard directory
    try:
        report_full = Path(REPORT_ROOT) / date_str / f"{image_path.stem}.html"
        report_rel = os.path.relpath(report_full, start=DASHBOARD_DIR).replace("\\", "/")
    except Exception:
        report_rel = f"{date_str}/{image_path.stem}.html"
    try:
        image_rel = os.path.relpath(image_path, start=DASHBOARD_DIR).replace("\\", "/")
    except Exception:
        image_rel = f"{date_str}/{image_path.name}"

    visits = metrics.get("visits", [])
    counts = metrics.get("species_counts", {})
    to_remove = None
    for idx, v in enumerate(visits):
        if v.get("id") == visit_id:
            old_norm = v.get("species_norm") or normalize_species(v.get("species", ""))
            if old_norm in counts:
                counts[old_norm] -= 1
                if counts[old_norm] <= 0:
                    del counts[old_norm]
            to_remove = idx
            metrics["total_visits"] = max(0, metrics.get("total_visits", 1) - 1)
            break
    if to_remove is not None:
        del visits[to_remove]

    entry = {
        "id": visit_id,
        "timestamp": timestamp.strftime("%Y-%m-%d %H:%M:%S"),
        "species_raw": species,
        "species_norm": species_norm,
        "summary": summary,
        "report_rel": report_rel,
        "image_rel": image_rel,
        "closest_guess": species_norm if species_norm != "unknown" else species_norm,
        "needs_review": species_norm in ("unknown", "multi"),
        "user_override_species": None,
    }
    visits.append(entry)
    metrics["visits"] = visits
    metrics["total_visits"] = metrics.get("total_visits", 0) + 1
    counts[species_norm] = counts.get(species_norm, 0) + 1
    metrics["species_counts"] = counts
    save_metrics(metrics)
    write_dashboard_html(metrics)


def openai_analyze_image(
    client, api_key: str, image_path: Path, boxes: list[tuple[int, int, int, int]] | None = None
) -> dict:
    """
    Uses OpenAI Vision to describe the image and guess species.  If a list
    of bounding boxes is provided, the largest box is cropped with a
    margin and resized before being analysed.  The model is asked to
    return structured JSON containing presence, count, species guess and
    a summary.  Any errors are logged and captured in the result.
    """
    out = {
        "ok": False,
        "error": None,
        "birds_present": None,
        "count": None,
        "species_guess": None,
        "summary": None,
        "raw_text": None,
    }

    try:
        # tiny debug - do NOT print full key
        log.debug(f"[OpenAI Debug] API key present: {bool(api_key)} | key suffix: ...{api_key[-6:]}")

        # Helper functions for cropping and resizing
        def _expand_bbox(bbox: tuple[int, int, int, int], img_shape: tuple[int, int], margin_ratio: float = 0.1) -> tuple[int, int, int, int]:
            x0, y0, x1, y1 = bbox
            h, w = img_shape
            bw = x1 - x0
            bh = y1 - y0
            mx = int(bw * margin_ratio)
            my = int(bh * margin_ratio)
            nx0 = max(0, x0 - mx)
            ny0 = max(0, y0 - my)
            nx1 = min(w, x1 + mx)
            ny1 = min(h, y1 + my)
            return nx0, ny0, nx1, ny1

        def _resize_to_tile(img: Any) -> Any:
            h, w = img.shape[:2]
            target = 512
            if max(h, w) <= target:
                return img
            if h > w:
                new_h = target
                new_w = int(w * target / h)
            else:
                new_w = target
                new_h = int(h * target / w)
            return cv2.resize(img, (new_w, new_h), interpolation=cv2.INTER_AREA)

        # Choose image bytes (cropped if boxes provided)
        if boxes:
            img = cv2.imread(str(image_path))
            if img is not None and len(boxes) > 0:
                largest = max(boxes, key=lambda b: (b[2] - b[0]) * (b[3] - b[1]))
                ex_bbox = _expand_bbox(largest, img.shape[:2], margin_ratio=0.1)
                x0, y0, x1, y1 = ex_bbox
                crop = img[y0:y1, x0:x1]
                crop = _resize_to_tile(crop)
                _, buf = cv2.imencode(".jpg", crop)
                data_bytes = buf.tobytes()
                log.debug(f"Cropped image for OpenAI using bbox {largest} -> expanded {ex_bbox} (size {crop.shape})")
            else:
                data_bytes = image_path.read_bytes()
        else:
            data_bytes = image_path.read_bytes()

        b64 = base64.b64encode(data_bytes).decode("utf-8")

        prompt = (
            "You are analysing a bird‑feeder camera image.\n"
            "Return JSON ONLY with keys:\n"
            "{birds_present:boolean, count:int, species_guess:string, summary:string}\n"
            "Always provide your best guess for species_guess based on the bird's appearance and context; if truly uncertain, use 'unknown'.\n"
        )

        resp = client.responses.create(
            model="gpt-4.1-mini",
            input=[{
                "role": "user",
                "content": [
                    {"type": "input_text", "text": prompt},
                    {"type": "input_image", "image_url": f"data:image/jpeg;base64,{b64}"},
                ],
            }],
        )

        text = resp.output_text or ""
        out["raw_text"] = text
        cleaned = text.strip()
        if cleaned.startswith("```"):
            cleaned = cleaned.strip("`")
            cleaned = cleaned.replace("json", "", 1).strip()

        parsed = None
        try:
            parsed = json.loads(cleaned)
        except Exception:
            start = cleaned.find("{")
            end = cleaned.rfind("}")
            if start != -1 and end != -1 and end > start:
                parsed = json.loads(cleaned[start:end+1])

        if isinstance(parsed, dict):
            out.update({
                "ok": True,
                "birds_present": bool(parsed.get("birds_present")) if parsed.get("birds_present") is not None else None,
                "count": parsed.get("count"),
                "species_guess": parsed.get("species_guess"),
                "summary": parsed.get("summary"),
            })
        else:
            out["ok"] = True
            out["summary"] = text

        return out

    except Exception as e:
        out["error"] = str(e)
        log.error("[OpenAI] request failed: " + repr(e))
        log.error(traceback.format_exc())
        return out


def write_html_report(report_dir: Path, image_path: Path, yolo_boxes: list, birds: int, unique_today: int, counted_unique: bool, openai_result: dict):
    safe_mkdir(report_dir)

    report_path = report_dir / (image_path.stem + ".html")
    img_copy_path = report_dir / image_path.name

    try:
        # Copy image next to report for easy viewing
        if image_path.exists():
            shutil.copy2(str(image_path), str(img_copy_path))
    except Exception:
        log.error("Failed copying image to report dir:\n" + traceback.format_exc())

    # Use a consistent report layout across scripts.  Build the HTML
    # directly rather than mixing cards and lists.  For simplicity we
    # include the core fields (time, image name, detections, unique
    # status, running unique count) and the OpenAI analysis.  We omit
    # individual bounding box coordinates in the final report but they
    # remain available in logs.
    species = (openai_result or {}).get("species_guess", "unknown")
    summary = (openai_result or {}).get("summary", None)
    if not summary:
        # fall back to raw text if summary missing or empty
        summary = (openai_result or {}).get("raw_text", "No summary available.")
    error_msg = None
    if openai_result and not openai_result.get("ok"):
        error_msg = openai_result.get("error")

    html = f"""<!doctype html>
<html>
<head>
  <meta charset="utf-8" />
  <title>Bird Visit Report</title>
  <style>
    body {{ font-family: Arial, sans-serif; margin: 20px; }}
    .meta {{ background:#f3f3f3; padding:12px; border-radius:8px; }}
    img {{ max-width: 100%; height: auto; border-radius: 8px; border: 1px solid #ddd; }}
  </style>
</head>
<body>
  <h1>Bird Visit Report</h1>
  <div class="meta">
    <p><b>Time:</b> {datetime.now()}</p>
    <p><b>Image:</b> {image_path.name}</p>
    <p><b>Detections (YOLO birds):</b> {birds}</p>
    <p><b>Counted as unique:</b> {counted_unique}</p>
    <p><b>Unique birds today:</b> {unique_today}</p>
  </div>
  <h2>Image</h2>
  <img src="{image_path.name}" alt="Captured bird" />
  <h2>Analysis</h2>
  <p><b>Species guess:</b> {species}</p>
  <p><b>Summary:</b> {summary}</p>
  {f'<p><b>OpenAI error:</b> {error_msg}</p>' if error_msg else ''}
</body>
</html>
"""
    report_path.write_text(html, encoding="utf-8")
    return report_path


def detect_birds_yolo(model, image_path: Path):
    """
    Run YOLO detection on a single image and return the number of birds,
    bounding boxes, and the original image.  To improve reliability, we
    crop the region of interest (ROI) around the feeder before running
    detection.  The ROI is defined by the global ``ROI_NORM`` tuple
    containing normalized coordinates (x1, y1, x2, y2).  After detection
    on the cropped region, box coordinates are translated back to the
    full-image coordinate system.

    Returns:
        birds (int): number of detected birds
        boxes (list of tuples): list of (x1, y1, x2, y2) bounding boxes
        img (numpy.ndarray): the original image in BGR format
    """
    img = cv2.imread(str(image_path))
    if img is None:
        return 0, [], None

    # Compute ROI in pixel coordinates
    h, w = img.shape[:2]
    x1n, y1n, x2n, y2n = ROI_NORM
    x1 = max(0, min(w - 1, int(x1n * w)))
    y1 = max(0, min(h - 1, int(y1n * h)))
    x2 = max(1, min(w, int(x2n * w)))
    y2 = max(1, min(h, int(y2n * h)))

    # Crop ROI
    roi = img[y1:y2, x1:x2]

    # Run detection on ROI
    res = model(roi, conf=CONF_THRESH, verbose=False)[0]
    boxes = []
    birds = 0

    # Compute ROI area for area ratio filtering
    roi_area = max(1.0, (x2 - x1) * (y2 - y1))
    raw_detections = 0
    for b in res.boxes:
        cls = int(b.cls[0])
        if cls != BIRD_CLASS_ID:
            continue
        raw_detections += 1
        # Adjust bounding box coordinates to full image coordinates
        bx1, by1, bx2, by2 = map(int, b.xyxy[0])
        adj_x1 = bx1 + x1
        adj_y1 = by1 + y1
        adj_x2 = bx2 + x1
        adj_y2 = by2 + y1
        # Compute area ratio relative to ROI
        bw = max(0, adj_x2 - adj_x1)
        bh = max(0, adj_y2 - adj_y1)
        area_ratio = (bw * bh) / roi_area if roi_area > 0 else 0.0
        if area_ratio < MIN_AREA_RATIO:
            log.debug(f"Filtered detection (small area): ratio={area_ratio:.4f} < {MIN_AREA_RATIO:.4f}")
            continue
        birds += 1
        boxes.append((adj_x1, adj_y1, adj_x2, adj_y2))
    if raw_detections > 0:
        log.debug(f"YOLO detections: {raw_detections} raw, {birds} accepted after area filter")

    return birds, boxes, img


def iter_new_images(root: Path):
    # scan all jpgs under root/YYYY-MM-DD/
    for p in sorted(root.rglob("*.jpg"), key=lambda x: x.stat().st_mtime):
        # skip report copies, skip nobird
        if "_no_bird" in str(p).lower():
            continue
        # skip files still being written (very new)
        try:
            if time.time() - p.stat().st_mtime < 0.3:
                continue
        except Exception:
            continue
        yield p


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", default=DEFAULT_ROOT)
    ap.add_argument("--watch", action="store_true")
    args = ap.parse_args()

    root = Path(args.root)
    safe_mkdir(root)

    log.info("Pilot analyzer starting")
    log.info(f"Folder: {root}")

    model = YOLO(MODEL_PATH)

    client, key = load_openai_client()
    if key is not None:
        log.info(f"[OpenAI Debug] key present={bool(key)} suffix=...{(key[-6:] if key else '')}")
    if client is None:
        log.warning("OpenAI disabled (OPENAI_API_KEY missing or OpenAI init failed)")

    today = date.today().isoformat()
    daily_unique = 0
    last_seen_ts = 0

    nobird_dir = root / "_no_bird"
    safe_mkdir(nobird_dir)

    processed = set()
    # Load existing event IDs from metrics to avoid reprocessing duplicates.  Each
    # event ID is a SHA1 hash of the image bytes (as produced in update_metrics).
    try:
        _loaded_metrics = load_metrics()
        existing_ids: set[str] = set(v.get("id") for v in _loaded_metrics.get("visits", []))
        log.debug(f"Loaded {len(existing_ids)} existing event IDs from metrics for deduplication")
    except Exception:
        existing_ids = set()

    def process_one(image_path: Path):
        nonlocal daily_unique, last_seen_ts, existing_ids

        # lock to prevent double-process (especially if watch loop is fast)
        lock_path = try_lock(image_path)
        if lock_path is None:
            return

        try:
            # if file already processed in-memory this run, skip (extra safety)
            if image_path in processed:
                return

            # Compute event ID and check against existing IDs to prevent duplicate
            # processing across runs.  If the event_id is already present in
            # metrics, skip this file.  Event ID calculation matches that in
            # update_metrics.
            try:
                event_id = hashlib.sha1(image_path.read_bytes()).hexdigest()
            except Exception:
                event_id = image_path.stem
            if event_id in existing_ids:
                log.info(f"Skipping {image_path} as event_id already processed")
                processed.add(image_path)
                return

            birds, boxes, img = detect_birds_yolo(model, image_path)

            counted_unique = False
            now = time.time()

            if birds > 0:
                # unique logic (simple): if last bird was long enough ago -> new visit
                if (now - last_seen_ts) > DUP_SECONDS:
                    daily_unique += 1
                    counted_unique = True
                last_seen_ts = now

                openai_result = {}
                if client is not None and key:
                    # Pass the bounding boxes to the OpenAI analysis so it can
                    # crop the image for improved accuracy and reduced cost.
                    openai_result = openai_analyze_image(client, key, image_path, boxes)
                else:
                    openai_result = {"ok": False, "error": "OpenAI disabled."}

                report_dir = Path(REPORT_ROOT) / today
                report_path = write_html_report(
                    report_dir, image_path, boxes, birds, daily_unique, counted_unique, openai_result
                )

                # Update metrics and dashboard for each positive detection
                species = openai_result.get("species_guess") if openai_result and openai_result.get("ok") else "unknown"
                summary = openai_result.get("summary") if openai_result and openai_result.get("ok") else (
                    openai_result.get("error") if openai_result else ""
                )
                update_metrics(image_path, species, summary, datetime.now())
                # Add the new event_id to existing_ids to avoid duplicate
                # processing of the same image if encountered again during
                # this run.
                existing_ids.add(event_id)

                log.info(f"birds={birds} unique_today={daily_unique} unique={counted_unique} report={report_path}")

            else:
                # no birds -> move to _no_bird safely, do not crash if missing
                moved = move_with_retries(image_path, nobird_dir, suffix="", tries=3, delay=0.2)
                if moved:
                    log.info(f"birds=0 moved_to={moved}")

            processed.add(image_path)

        except Exception:
            log.error("process_one fatal:\n" + traceback.format_exc())
        finally:
            release_lock(lock_path)

    def loop_once():
        for p in iter_new_images(root):
            if p not in processed:
                process_one(p)

    if args.watch:
        while True:
            loop_once()
            time.sleep(0.35)
    else:
        loop_once()


if __name__ == "__main__":
    main()
