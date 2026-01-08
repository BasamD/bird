"""
Unified Bird Capture and Analysis Script
-------------------------------------

This script connects to a camera via RTSP, runs YOLOv8 to detect birds in
the live video feed, and when a new bird visit is detected it saves a
snapshot, invokes the OpenAI API to analyse the image (guessing species and
providing a brief description), and writes an HTML report.  The
"uniqueness" logic attempts to avoid capturing the same bird repeatedly by
requiring a period of silence (no detections) after a visit before
considering the next detection a new visit.  Both the capture interval and
the unique timeout can be tuned via the constants below.

The OpenAI API key is read from the ``OPENAI_API_KEY`` environment variable
if present; otherwise it falls back to the embedded default key (which you
should replace with your own if you regenerate keys).  To prevent
accidental disclosure, only the suffix of the key is ever logged.

To run the script:

    python pilot_bird_counter.py

It will open a window showing the video feed with bounding boxes drawn
around detected birds and a counter for unique birds today.  Press ``q``
to exit gracefully.
"""

import base64
import json
import os
import threading
import time
from dataclasses import dataclass
import re
from datetime import datetime, date
from pathlib import Path
from queue import Queue, Empty
from typing import Any
import hashlib
import logging
from logging.handlers import RotatingFileHandler

import cv2
from ultralytics import YOLO

# Additional imports for threaded frame grabbing and analysis queue
import threading
from queue import Queue, Empty


# ============================================================================
# Configuration
# ============================================================================

# RTSP URL for your camera.  Replace with the actual address of your device.
RTSP_URL = (
    "rtsp://admin:admin@192.168.1.79:554/cam/realmonitor?channel=1&subtype=0&unicast=true&proto=Onvif"
)

# Path to the YOLOv8 model to use for detection.  The "n" model is small
MODEL_PATH = "yolov8n.pt"

# Directory where snapshots will be saved.  Images are organised by date.
CAPTURE_ROOT = Path(r"C:\env\vision\pilot_captures")

# Directory where HTML reports will be written.  Reports are organised by date.
REPORT_ROOT = Path(r"C:\env\vision\pilot_reports")

# Directory where log files will be written.  A new log file is created
# each day with a rotating handler.  Logs are mirrored to stdout as
# well.  See setup_logging() below for details.
LOG_ROOT = Path(r"C:\env\vision\pilot_logs")

# Detection confidence threshold.  Lower values detect more objects but may
# increase false positives.  We use a slightly lower threshold for the
# unified capture/analysis script to improve sensitivity on small birds.
CONF_THRESH = 0.25

# Define the region of interest (ROI) for detection as normalized
# coordinates (x1, y1, x2, y2).  This focuses detection on the feeder
# area of the frame, reducing false positives and CPU usage.  The
# values represent fractions of the frame dimensions.
ROI_NORM = (0.25, 0.34, 0.62, 0.72)

# Width of the resized detection image.  Detection will be performed on
# a downscaled version of the ROI to reduce CPU usage.  The aspect
# ratio is preserved.  Increase for higher accuracy at the cost of
# compute, decrease to reduce CPU load.
DETECT_RESIZE_WIDTH = 960

# YOLO class ID for birds (COCO dataset defines bird as class 14)
BIRD_CLASS_ID = 14

# Minimum relative area of a detection box (as a fraction of the ROI) to
# consider it a valid bird.  Detections with smaller area are ignored
# as noise or distant birds.  This prevents tiny boxes from triggering
# new visits and reduces false positives.  Set via the environment
# variable ``MIN_AREA_RATIO`` or defaults to 0.002 (0.2% of ROI area).
MIN_AREA_RATIO = float(os.environ.get("MIN_AREA_RATIO", 0.002))

# Minimum number of seconds between captures of distinct visits.  Once a
# snapshot is taken, another will not be taken until this many seconds have
# passed *and* the bird has been absent for ``BIRD_ABSENCE_TIMEOUT`` seconds.
CAPTURE_GAP_SEC = 15

# Number of seconds of no detections required to consider the bird gone.  If
# detections cease for at least this long, the next detection counts as a
# new visit (subject to ``CAPTURE_GAP_SEC``).
BIRD_ABSENCE_TIMEOUT = 5

# Interval in seconds between running YOLO detection on frames.  A smaller
# interval results in more frequent detection but uses more CPU.  Note that
# frames are still grabbed continuously from the camera for display.
DETECTION_INTERVAL = 0.5

# Scale for the displayed window.  Set to 1.0 to display full resolution,
# or less to downscale for a smaller window.  This does not affect
# detection or the saved images.
VIEW_SCALE = 0.6

# OpenAI API key.  The environment variable ``OPENAI_API_KEY`` takes
# precedence.  If not set, we fall back to this default key.  Replace
# with your own key if necessary.  Only the last few characters are
# printed in logs to avoid accidental exposure.
DEFAULT_OPENAI_KEY = (
    "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"
)

# ==========================================================================
# Metrics and Dashboard helpers
#
# These helpers mirror those used in the analyser script.  They maintain
# a JSON file with visit entries and aggregated statistics and regenerate
# a single dashboard HTML.  Each call to update_metrics() reads the
# existing metrics, appends a new record, updates aggregated counts and
# writes the updated JSON and HTML.  The dashboard auto-refreshes every
# 30 seconds when viewed in a browser.
# ==========================================================================

def load_metrics() -> dict:
    """Load the metrics JSON file if it exists, otherwise return
    an empty default structure."""
    try:
        if METRICS_FILE.exists():
            with METRICS_FILE.open("r", encoding="utf-8") as f:
                return json.load(f)
    except Exception as e:
        log(f"[metrics] failed to load metrics: {e}")
    return {
        "total_visits": 0,
        "visits": [],
        "species_counts": {},
    }


# ---------------------------------------------------------------------------
# Species normalisation
#
# Many species names returned by OpenAI vary in capitalisation, plurality or
# include multiple species in a single string.  To ensure consistent
# counting and display, we derive a canonical "species_norm" value from
# the raw name.  The rules are:
#   * Lower-case and strip non-alphanumeric characters.
#   * If multiple species names are separated by commas or "and", label
#     as "multi".
#   * Singularise simple plurals (trailing 's').  Words ending in
#     'ss' are left intact.
#   * Map obvious synonyms where appropriate (for example, plain
#     "sparrow" is mapped to "house sparrow" for counting purposes).
#
def normalize_species(name: str) -> str:
    """Return a canonical species name for counting purposes."""
    if not name:
        return "unknown"
    s = name.strip().lower()
    # remove punctuation
    s = re.sub(r"[^a-z0-9\s]", "", s)
    # handle multiple species (comma or ' and ')
    if "," in s or " and " in s:
        return "multi"
    # singularise simple plurals
    if s.endswith("s") and not s.endswith("ss"):
        s = s[:-1]
    # synonym mapping
    synonyms = {
        "sparrow": "house sparrow",
        "house sparrows": "house sparrow",
    }
    return synonyms.get(s, s)


def save_metrics(metrics: dict) -> None:
    """Persist the metrics dictionary to disk."""
    DASHBOARD_DIR.mkdir(parents=True, exist_ok=True)
    try:
        with METRICS_FILE.open("w", encoding="utf-8") as f:
            json.dump(metrics, f, indent=2)
    except Exception as e:
        log(f"[metrics] failed to save metrics: {e}")


def write_dashboard_html(metrics: dict) -> None:
    """Generate the dashboard HTML from the metrics and write it to disk."""
    DASHBOARD_DIR.mkdir(parents=True, exist_ok=True)
    total_visits = metrics.get("total_visits", 0)
    species_counts = metrics.get("species_counts", {})
    visits = metrics.get("visits", [])

    # Build species count list using normalised names
    species_rows = ""
    for sp, count in sorted(species_counts.items(), key=lambda x: x[1], reverse=True):
        species_rows += f"<li>{sp}: {count}</li>\n"

    # Build visit rows.  Each entry has a link to the report and the photo.
    visit_rows = ""
    for v in visits:
        # Species display: show normalised name; raw name in title attribute
        sp_display = v.get("species_norm") or v.get("species")
        sp_raw = v.get("species_raw")
        # Use the stored relative paths directly.  They are computed relative to
        # the dashboard directory, so no further prefix is required.  This
        # prevents broken links when the dashboard is moved to a different
        # location.
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
        log(f"[dashboard] failed to write dashboard: {e}")


def update_metrics(image_path: Path, species: str, summary: str, timestamp: datetime) -> None:
    """
    Update the metrics with a new visit entry.  This function handles
    de-duplication, species normalisation and path computation to
    support the dashboard.  If an existing entry with the same ID
    exists, it is replaced and the species counts are adjusted.

    The entry contains both the raw species name returned by OpenAI
    (``species_raw``) and a normalised form (``species_norm``) used
    for counting.  Additional fields provide relative paths to the
    report and image for linking in the dashboard, a closest guess
    (identical to species_norm unless unknown or multi), a review flag
    and a placeholder for user override.
    """
    metrics = load_metrics()
    # Compute a stable event ID by hashing the image bytes.  This prevents
    # duplicate entries when the same photo is reprocessed (e.g. across runs or
    # after moving files).  The SHA1 hash provides a compact identifier.
    try:
        digest = hashlib.sha1(image_path.read_bytes()).hexdigest()
    except Exception as e:
        logger.error(f"Failed to compute digest for {image_path}: {e}")
        digest = image_path.stem
    visit_id = digest
    species_norm = normalize_species(species)
    date_str = timestamp.strftime("%Y-%m-%d")
    # Compute relative paths for dashboard links using os.path.relpath.  This
    # produces correct links regardless of where the dashboard resides on disk.
    # On Windows, backslashes are replaced with forward slashes for browser
    # compatibility.
    try:
        report_full = REPORT_ROOT / date_str / f"{image_path.stem}.html"
        report_rel = os.path.relpath(report_full, start=DASHBOARD_DIR).replace("\\", "/")
    except Exception:
        # Fallback to existing path scheme
        report_rel = f"{date_str}/{image_path.stem}.html"
    try:
        image_rel = os.path.relpath(image_path, start=DASHBOARD_DIR).replace("\\", "/")
    except Exception:
        image_rel = f"{date_str}/{image_path.name}"

    # Remove existing entry with same id, adjust counts
    visits = metrics.get("visits", [])
    counts = metrics.get("species_counts", {})
    to_remove = None
    for idx, v in enumerate(visits):
        if v.get("id") == visit_id:
            # Decrement count of old species when replacing an existing entry
            old_norm = v.get("species_norm") or normalize_species(v.get("species", ""))
            if old_norm in counts:
                counts[old_norm] -= 1
                if counts[old_norm] <= 0:
                    del counts[old_norm]
            # remove entry
            to_remove = idx
            metrics["total_visits"] = max(0, metrics.get("total_visits", 1) - 1)
            break
    if to_remove is not None:
        del visits[to_remove]

    # Build entry
    entry = {
        "id": visit_id,
        "timestamp": timestamp.strftime("%Y-%m-%d %H:%M:%S"),
        "species_raw": species,
        "species_norm": species_norm,
        "summary": summary,
        # Relative paths computed above are already relative to the dashboard directory.
        "report_rel": report_rel,
        "image_rel": image_rel,
        "closest_guess": species_norm if species_norm != "unknown" else species_norm,
        "needs_review": species_norm in ("unknown", "multi"),
        "user_override_species": None,
    }
    visits.append(entry)
    metrics["visits"] = visits
    metrics["total_visits"] = metrics.get("total_visits", 0) + 1
    # Increment normalised species count
    counts[species_norm] = counts.get(species_norm, 0) + 1
    metrics["species_counts"] = counts
    save_metrics(metrics)
    write_dashboard_html(metrics)


# ============================================================================
# Dashboard and metrics configuration
#
# To provide a single continuously updating "geek board" for bird analytics,
# the capture script now maintains a JSON metrics file and regenerates a
# dashboard HTML on each new visit.  The dashboard lists every visit with
# timestamp, image ID, species guess, and summary, and shows aggregated
# counts of visits and species.  Set DASHBOARD_DIR to the folder where the
# dashboard HTML and metrics JSON will live.  By default it sits alongside
# the capture/report folders.
# ============================================================================
DASHBOARD_DIR = Path(r"C:\env\vision\dashboard")
METRICS_FILE = DASHBOARD_DIR / "metrics.json"
DASHBOARD_FILE = DASHBOARD_DIR / "dashboard.html"

# ----------------------------------------------------------------------------
# Logging configuration
# ----------------------------------------------------------------------------

def setup_logging() -> logging.Logger:
    """
    Configure a rotating logger for the bird counter.  Logs are written to
    ``LOG_ROOT`` with a daily filename and also emitted to the console.  The
    logging level is DEBUG for the file handler to capture detailed
    diagnostics and INFO for the console to reduce noise.  The logger is
    returned for use throughout the script.
    """
    LOG_ROOT.mkdir(parents=True, exist_ok=True)
    log_path = LOG_ROOT / f"pilot_counter_{date.today().isoformat()}.log"
    logger = logging.getLogger("pilot_bird_counter")
    logger.setLevel(logging.DEBUG)
    fmt = logging.Formatter("[%(asctime)s] [%(levelname)s] %(message)s", "%Y-%m-%d %H:%M:%S")
    # console handler
    ch = logging.StreamHandler()
    ch.setLevel(logging.INFO)
    ch.setFormatter(fmt)
    # file handler with rotation
    fh = RotatingFileHandler(str(log_path), maxBytes=5_000_000, backupCount=3, encoding="utf-8")
    fh.setLevel(logging.DEBUG)
    fh.setFormatter(fmt)
    # avoid duplicate handlers on reload
    logger.handlers.clear()
    logger.addHandler(ch)
    logger.addHandler(fh)
    logger.debug(f"Logging initialised, log file: {log_path}")
    return logger


# Initialise the logger at import time so that all functions can use it.
logger = setup_logging()


def log(msg: str) -> None:
    """
    Compatibility shim for legacy log() usage.  Logs a message at INFO
    level via the configured logger.  Additional context (such as
    timestamps) is handled by the logger configuration.
    """
    logger.info(msg)


# ============================================================================
# Threaded frame grabbing and asynchronous analysis
#
# To reduce CPU usage and avoid read errors from the RTSP stream, we use a
# dedicated thread to continuously grab frames from the camera.  The
# detection loop reads the most recent frame from a shared holder.  This
# prevents detection from blocking on frame reads and helps mitigate
# buffering issues.  Additionally, analysis (OpenAI calls and report
# generation) is offloaded to a worker thread via a queue, so the main
# detection loop remains responsive.
# ============================================================================

# Shared holder for the most recent frame.  The frame grabber thread
# continuously updates this dictionary with the latest frame.  The
# detection loop reads from this to perform detection without blocking.
frame_holder = {"frame": None}

# Queue for analysis tasks.  When a new visit is captured, the image
# path and associated metadata are placed into this queue for the
# analysis worker to process.  This decouples slow operations (OpenAI
# calls, report generation) from the detection loop.
analysis_queue: Queue = Queue()

# Event to signal analysis worker shutdown.
analysis_stop_event = threading.Event()


def frame_grabber(rtsp_url: str, holder: dict) -> None:
    """
    Continuously grab frames from the RTSP stream and update the shared
    frame holder.  This runs in a background thread.  If the stream
    disconnects, it attempts to reconnect every few seconds.
    """
    cap = None
    while not analysis_stop_event.is_set():
        if cap is None or not cap.isOpened():
            cap = cv2.VideoCapture(rtsp_url, cv2.CAP_FFMPEG)
            if not cap.isOpened():
                log("[grabber] Failed to open RTSP stream; retrying...")
                time.sleep(2)
                continue
        ret, frame = cap.read()
        if not ret or frame is None:
            log("[grabber] Frame read failed; reconnecting...")
            cap.release()
            cap = None
            time.sleep(1)
            continue
        holder["frame"] = frame
        # Sleep very briefly to yield CPU; the main detection loop controls
        # how often detection runs via DETECTION_INTERVAL.
        time.sleep(0.01)


def analysis_worker() -> None:
    """
    Worker thread that processes images placed in the analysis queue.  It
    performs OpenAI analysis, writes reports, and updates metrics.  This
    allows the detection loop to remain responsive while potentially
    slow operations are handled asynchronously.
    """
    while not analysis_stop_event.is_set():
        try:
            task = analysis_queue.get(timeout=0.5)
        except Empty:
            continue
        # Unpack task: includes bounding boxes for cropping, bird count,
        # unique index and capture timestamp.  Boxes may be empty if no
        # detections passed the area filter.
        image_path, boxes, detected_birds, unique_idx, timestamp = task
        # Perform OpenAI analysis with optional cropping.  The client is
        # reinitialised here to avoid threading issues.
        client, key = load_openai_client()
        analysis = openai_analyze_image(client, key, image_path, boxes)
        # Generate report
        report_dir = REPORT_ROOT / timestamp.date().isoformat()
        report_path = write_html_report(
            report_dir, image_path, detected_birds, unique_idx, analysis
        )
        # Update metrics and dashboard
        species = analysis.get("species_guess") if analysis and analysis.get("ok") else "unknown"
        summary = analysis.get("summary") if analysis and analysis.get("ok") else (
            analysis.get("error") if analysis else "No analysis"
        )
        update_metrics(image_path, species or "unknown", summary or "", timestamp)
        analysis_queue.task_done()





# ============================================================================
# Helper functions
# ============================================================================

def ensure_dir(path: Path) -> None:
    """Create a directory (and parents) if it doesn't already exist."""
    path.mkdir(parents=True, exist_ok=True)


def log(msg: str) -> None:
    """Print a timestamped message to stdout."""
    print(f"[{datetime.now().strftime('%H:%M:%S')}] {msg}", flush=True)


def load_openai_client():
    """
    Initialise the OpenAI client.  The API key is read from the
    ``OPENAI_API_KEY`` environment variable if set; otherwise the default
    key defined above is used.  Returns a tuple of (client, key).  If the
    ``openai`` package is not installed or initialisation fails, returns
    (None, key).
    """
    key = os.environ.get("OPENAI_API_KEY", "").strip() or DEFAULT_OPENAI_KEY.strip()
    if not key:
        return None, None
    try:
        from openai import OpenAI
        client = OpenAI(api_key=key)
        return client, key
    except Exception as e:
        log(f"[OpenAI] init failed: {e}")
        return None, key


def openai_analyze_image(
    client, api_key: str, image_path: Path, boxes: list[tuple[int, int, int, int]] | None = None
) -> dict:
    """
    Analyse an image with the OpenAI Responses API.  If a list of
    bounding boxes is provided, the largest box is cropped (with an
    additional margin) and resized to a square tile before being sent
    to the model.  This improves species identification accuracy and
    reduces cost.  Without boxes, the full image is analysed.  The
    model is instructed to return a structured JSON response with a
    species guess and summary.  Errors are captured and returned in
    the result dictionary.
    """
    result: dict = {
        "ok": False,
        "error": None,
        "summary": None,
        "species_guess": None,
        "raw": None,
    }
    if client is None:
        result["error"] = "OpenAI disabled"
        return result

    # Helper to expand a bounding box by a margin
    def _expand_bbox(
        bbox: tuple[int, int, int, int], img_shape: tuple[int, int], margin_ratio: float = 0.1
    ) -> tuple[int, int, int, int]:
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

    # Helper to resize image to a maximum dimension of 512 pixels
    def _resize_to_tile(img) -> Any:
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

    try:
        # Determine which image to send: crop if boxes provided
        if boxes:
            # Load full image
            full_img = cv2.imread(str(image_path))
            if full_img is not None and len(boxes) > 0:
                # Choose the largest box by area
                largest = max(boxes, key=lambda b: (b[2] - b[0]) * (b[3] - b[1]))
                ex_bbox = _expand_bbox(largest, full_img.shape[:2], margin_ratio=0.1)
                x0, y0, x1, y1 = ex_bbox
                crop = full_img[y0:y1, x0:x1]
                # Resize crop to max dimension 512
                crop = _resize_to_tile(crop)
                _, buf = cv2.imencode(".jpg", crop)
                img_bytes = buf.tobytes()
                logger.debug(
                    f"Cropped image using bbox {largest} -> expanded {ex_bbox}, size {crop.shape}"
                )
            else:
                # fallback: read full image bytes
                img_bytes = image_path.read_bytes()
        else:
            img_bytes = image_path.read_bytes()

        # Encode image bytes
        b64 = base64.b64encode(img_bytes).decode("ascii")
        data_url = f"data:image/jpeg;base64,{b64}"

        # Prompt instructing the model to return structured JSON
        prompt = (
            "You are analysing a backyard bird‑feeder camera image.\n"
            "Return JSON with keys: birds_present (bool), count (int), species_guess (string), summary (string).\n"
            "Always provide your best guess for species_guess based on the bird's appearance and context; if truly uncertain, use 'unknown'.\n"
            "Keep the summary concise."
        )

        # Send request
        response = client.responses.create(
            model="gpt-4.1-mini",
            input=[
                {
                    "role": "user",
                    "content": [
                        {"type": "input_text", "text": prompt},
                        {"type": "input_image", "image_url": data_url},
                    ],
                }
            ],
        )

        text = (response.output_text or "").strip()
        result["raw"] = text
        cleaned = text
        if cleaned.startswith("```"):
            cleaned = cleaned.strip("`")
            cleaned = cleaned.replace("json", "", 1).strip()
        parsed = None
        try:
            parsed = json.loads(cleaned)
        except Exception:
            # fallback: find JSON substring
            start = cleaned.find("{")
            end = cleaned.rfind("}")
            if start != -1 and end != -1 and end > start:
                try:
                    parsed = json.loads(cleaned[start : end + 1])
                except Exception:
                    parsed = None

        if isinstance(parsed, dict):
            result["ok"] = True
            result["summary"] = parsed.get("summary")
            result["species_guess"] = parsed.get("species_guess")
        else:
            # If the model did not return JSON, treat raw text as summary
            result["ok"] = True
            result["summary"] = text
            result["species_guess"] = None
    except Exception as e:
        result["error"] = str(e)
        logger.error(f"[OpenAI] request failed: {e}")

    return result


def write_html_report(report_dir: Path, image_path: Path, birds: int, unique_idx: int, openai_result: dict) -> Path:
    """
    Write an HTML report for a captured image.  The report includes meta
    information about the capture (time, count, etc.), the species guess
    and summary from OpenAI, and a link to the image itself.  Returns the
    path to the HTML file.
    """
    ensure_dir(report_dir)
    image_filename = image_path.name
    report_path = report_dir / f"{image_path.stem}.html"

    # Compute a relative path from the report to the image.  This
    # ensures that the HTML references the image correctly regardless
    # of the date‑based folder structure.  On Windows backslashes are
    # replaced with forward slashes to satisfy browsers.
    try:
        rel_img_path = os.path.relpath(image_path, start=report_dir).replace("\\", "/")
    except Exception:
        rel_img_path = image_path.as_uri()

    # Construct OpenAI summary block
    if openai_result is None or not openai_result.get("ok"):
        openai_block = f"<p><b>OpenAI error:</b> {openai_result.get('error') if openai_result else 'disabled'}</p>"
    else:
        species = openai_result.get("species_guess") or "unknown"
        summary = openai_result.get("summary") or ""
        openai_block = (
            f"<p><b>Species guess:</b> {species}</p>"
            f"<p><b>Summary:</b> {summary}</p>"
        )

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
    <p><b>Image:</b> {image_filename}</p>
    <p><b>Detections (YOLO birds):</b> {birds}</p>
    <p><b>Visit count today:</b> {unique_idx}</p>
  </div>
  <h2>Image</h2>
  <img src="{rel_img_path}" alt="Captured bird" />
  <h2>Analysis</h2>
  {openai_block}
</body>
</html>
"""
    report_path.write_text(html, encoding="utf-8")
    return report_path


# ============================================================================
# Main capture and analysis loop
# ============================================================================

def run_capture_and_analyse() -> None:
    """
    Connect to the RTSP stream, run detection, capture snapshots when
    appropriate, run OpenAI analysis on each snapshot, and generate reports.
    The loop continues until the user presses 'q' or the video stream ends.
    """
    # Prepare directories
    ensure_dir(CAPTURE_ROOT)
    ensure_dir(REPORT_ROOT)

    # Load YOLO model once
    log("Loading YOLO model...")
    model = YOLO(MODEL_PATH)

    # Start the frame grabber thread
    grabber_thread = threading.Thread(target=frame_grabber, args=(RTSP_URL, frame_holder), daemon=True)
    grabber_thread.start()

    # Start the analysis worker thread
    worker_thread = threading.Thread(target=analysis_worker, daemon=True)
    worker_thread.start()

    # Prepare display window
    cv2.namedWindow("Bird Feed", cv2.WINDOW_NORMAL)

    # State for visit counting
    today = date.today().isoformat()
    unique_count = 0
    last_capture_time = 0.0
    last_bird_detection_time = 0.0
    bird_present = False

    # Timing for detection interval
    last_detection_timestamp = 0.0

    try:
        while True:
            # Get the latest frame from the grabber
            frame = frame_holder.get("frame")
            if frame is None:
                # No frame available yet; wait and retry
                time.sleep(0.05)
                continue

            now = time.time()
            # Run detection at the specified interval
            run_detection = (now - last_detection_timestamp) >= DETECTION_INTERVAL
            detected_birds = 0
            accepted_boxes: list[tuple[int, int, int, int]] = []

            # Copy frame for overlay drawing (avoid modifying shared frame)
            display_frame = frame.copy()

            if run_detection:
                last_detection_timestamp = now
                # Crop ROI from the full frame
                h, w = frame.shape[:2]
                x1n, y1n, x2n, y2n = ROI_NORM
                x1 = max(0, min(w - 1, int(x1n * w)))
                y1 = max(0, min(h - 1, int(y1n * h)))
                x2 = max(1, min(w, int(x2n * w)))
                y2 = max(1, min(h, int(y2n * h)))
                roi = frame[y1:y2, x1:x2]
                roi_h, roi_w = roi.shape[:2]
                # Resize ROI for detection
                if roi_w > 0 and roi_h > 0:
                    scale = DETECT_RESIZE_WIDTH / float(roi_w)
                    new_h = int(roi_h * scale)
                    roi_resized = cv2.resize(roi, (DETECT_RESIZE_WIDTH, new_h), interpolation=cv2.INTER_AREA)
                results = model(roi_resized, conf=CONF_THRESH, verbose=False)[0]
                # Compute scaling factors back to original ROI
                scale_x = (x2 - x1) / float(DETECT_RESIZE_WIDTH)
                scale_y = (y2 - y1) / float(new_h)
                # Compute ROI area for area ratio filtering
                roi_area = max(1.0, (x2 - x1) * (y2 - y1))
                raw_detections = 0
                for box in results.boxes:
                    cls_id = int(box.cls[0])
                    if cls_id != BIRD_CLASS_ID:
                        continue
                    raw_detections += 1
                    # Map resized box coords back to original frame
                    rx1, ry1, rx2, ry2 = box.xyxy[0]
                    rx1 = float(rx1) * scale_x + x1
                    ry1 = float(ry1) * scale_y + y1
                    rx2 = float(rx2) * scale_x + x1
                    ry2 = float(ry2) * scale_y + y1
                    # Calculate area ratio relative to ROI
                    box_w = max(0.0, rx2 - rx1)
                    box_h = max(0.0, ry2 - ry1)
                    area_ratio = (box_w * box_h) / roi_area if roi_area > 0 else 0.0
                    # Filter detections by area ratio
                    if area_ratio < MIN_AREA_RATIO:
                        logger.debug(
                            f"Filtered detection due to small area ratio: {area_ratio:.4f} < {MIN_AREA_RATIO:.4f}"
                        )
                        continue
                    # Accept detection
                    accepted_boxes.append((int(rx1), int(ry1), int(rx2), int(ry2)))
                    # Draw box on display_frame
                    cv2.rectangle(
                        display_frame, (int(rx1), int(ry1)), (int(rx2), int(ry2)), (0, 255, 0), 2
                    )
                    cv2.putText(
                        display_frame,
                        "bird",
                        (int(rx1), max(0, int(ry1) - 6)),
                        cv2.FONT_HERSHEY_SIMPLEX,
                        0.6,
                        (0, 255, 0),
                        2,
                    )
                if raw_detections > 0:
                    logger.debug(
                        f"Detections: {raw_detections} raw, {len(accepted_boxes)} accepted after area filter"
                    )

            # Update state based on detections
            # Use the number of accepted boxes for bird count
            detected_birds = len(accepted_boxes)
            if detected_birds > 0:
                last_bird_detection_time = now
                if not bird_present:
                    # Bird has just appeared after absence
                    if (now - last_capture_time) >= CAPTURE_GAP_SEC:
                        unique_count += 1
                        log(f"New bird visit #{unique_count}")
                        # Save full resolution frame
                        day_dir = CAPTURE_ROOT / today
                        ensure_dir(day_dir)
                        filename = f"bird_{unique_count}_{int(now)}.jpg"
                        image_path = day_dir / filename
                        cv2.imwrite(str(image_path), frame)
                        # Queue analysis task with bounding boxes and bird count.  The
                        # accepted_boxes list captures only those detections passing the
                        # area filter.  This allows the analysis worker to crop the
                        # bird region for the OpenAI call.
                        analysis_queue.put(
                            (image_path, accepted_boxes.copy(), detected_birds, unique_count, datetime.now())
                        )
                        last_capture_time = now
                    bird_present = True
            else:
                # No birds detected this interval
                if bird_present and ((now - last_bird_detection_time) >= BIRD_ABSENCE_TIMEOUT):
                    bird_present = False

            # Overlay unique count on display frame
            if VIEW_SCALE != 1.0:
                disp_h, disp_w = display_frame.shape[:2]
                display_scaled = cv2.resize(display_frame, (int(disp_w * VIEW_SCALE), int(disp_h * VIEW_SCALE)), interpolation=cv2.INTER_AREA)
            else:
                display_scaled = display_frame
            cv2.putText(
                display_scaled,
                f"Unique birds today: {unique_count}",
                (10, 30),
                cv2.FONT_HERSHEY_SIMPLEX,
                1.0,
                (255, 255, 0),
                2,
            )
            cv2.imshow("Bird Feed", display_scaled)
            # Break on 'q'
            if cv2.waitKey(1) & 0xFF == ord("q"):
                log("Quit requested; exiting.")
                break

            # Reset daily counter at midnight
            current_date = date.today().isoformat()
            if current_date != today:
                today = current_date
                unique_count = 0
                last_capture_time = 0.0
                last_bird_detection_time = 0.0
                bird_present = False
    finally:
        # Signal threads to stop and wait for queue to empty
        analysis_stop_event.set()
        # Wait for worker thread to finish processing queued tasks
        try:
            analysis_queue.join()
        except Exception:
            pass
        cv2.destroyAllWindows()
        log(f"Final count for {today}: {unique_count}")


if __name__ == "__main__":
    run_capture_and_analyse()