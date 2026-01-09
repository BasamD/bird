"""
Unified Bird Capture and Analysis Script
-------------------------------------

This script connects to a camera via RTSP, runs YOLOv8 to detect birds in
the live video feed, and when a new bird visit is detected it saves a
snapshot, invokes the OpenAI API to analyse the image, and writes an HTML report.

To run: python pilot_bird_counter_fixed.py

Press 'q' to exit gracefully.
"""

import base64
import json
import os
import threading
import time
import re
import hashlib
import logging
from logging.handlers import RotatingFileHandler
from datetime import datetime, date
from pathlib import Path
from queue import Queue, Empty
from typing import Any, Optional, Tuple, List

import cv2
from ultralytics import YOLO

try:
    import config
except ImportError:
    print("Warning: config.py not found, using defaults")
    from pathlib import Path
    class config:
        BASE_DIR = Path(__file__).parent.parent
        CAPTURE_ROOT = BASE_DIR / "pilot_captures"
        REPORT_ROOT = BASE_DIR / "pilot_reports"
        LOG_ROOT = BASE_DIR / "pilot_logs"
        DASHBOARD_DIR = BASE_DIR / "public"
        METRICS_FILE = DASHBOARD_DIR / "metrics.json"
        RTSP_URL = "rtsp://admin:admin@192.168.1.79:554/cam/realmonitor?channel=1&subtype=0&unicast=true&proto=Onvif"
        MODEL_PATH = "yolov8n.pt"
        OPENAI_API_KEY = "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"
        CONF_THRESH = 0.25
        ROI_NORM = (0.25, 0.34, 0.62, 0.72)
        DETECT_RESIZE_WIDTH = 960
        BIRD_CLASS_ID = 14
        MIN_AREA_RATIO = 0.002
        CAPTURE_GAP_SEC = 15
        BIRD_ABSENCE_TIMEOUT = 5
        DETECTION_INTERVAL = 0.5
        VIEW_SCALE = 0.6


logger: Optional[logging.Logger] = None
frame_holder = {"frame": None, "lock": threading.Lock()}
analysis_queue: Queue = Queue()
analysis_stop_event = threading.Event()


def setup_logging() -> logging.Logger:
    config.LOG_ROOT.mkdir(parents=True, exist_ok=True)
    log_path = config.LOG_ROOT / f"pilot_counter_{date.today().isoformat()}.log"

    log = logging.getLogger("pilot_bird_counter")
    log.setLevel(logging.DEBUG)
    fmt = logging.Formatter("[%(asctime)s] [%(levelname)s] %(message)s", "%Y-%m-%d %H:%M:%S")

    ch = logging.StreamHandler()
    ch.setLevel(logging.INFO)
    ch.setFormatter(fmt)

    fh = RotatingFileHandler(str(log_path), maxBytes=5_000_000, backupCount=3, encoding="utf-8")
    fh.setLevel(logging.DEBUG)
    fh.setFormatter(fmt)

    log.handlers.clear()
    log.addHandler(ch)
    log.addHandler(fh)
    log.debug(f"Logging initialised, log file: {log_path}")
    return log


def ensure_dir(path: Path) -> None:
    path.mkdir(parents=True, exist_ok=True)


def load_openai_client() -> Tuple[Optional[Any], str]:
    """Initialize OpenAI client with hardcoded fallback key."""
    # Try config first, then hardcoded fallback
    key = config.OPENAI_API_KEY
    if not key:
        key = "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"

    if not key:
        if logger:
            logger.error("No OpenAI API key found in config or hardcoded fallback")
        return None, ""

    try:
        from openai import OpenAI
        # Initialize with explicit timeout and max retries
        client = OpenAI(
            api_key=key,
            timeout=30.0,
            max_retries=3
        )
        if logger:
            logger.info(f"OpenAI client initialized successfully (key: {key[:8]}...{key[-8:]})")
        return client, key
    except Exception as e:
        if logger:
            logger.error(f"OpenAI import/init failed: {e}")
        return None, key


def normalize_species(name: str) -> str:
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


def load_metrics() -> dict:
    try:
        if config.METRICS_FILE.exists():
            with config.METRICS_FILE.open("r", encoding="utf-8") as f:
                return json.load(f)
    except Exception as e:
        if logger:
            logger.warning(f"[metrics] failed to load: {e}")
    return {
        "total_visits": 0,
        "visits": [],
        "species_counts": {},
    }


def save_metrics(metrics: dict) -> None:
    config.DASHBOARD_DIR.mkdir(parents=True, exist_ok=True)
    try:
        with config.METRICS_FILE.open("w", encoding="utf-8") as f:
            json.dump(metrics, f, indent=2)
    except Exception as e:
        if logger:
            logger.warning(f"[metrics] failed to save: {e}")


def write_dashboard_html(metrics: dict) -> None:
    config.DASHBOARD_DIR.mkdir(parents=True, exist_ok=True)
    total_visits = metrics.get("total_visits", 0)
    species_counts = metrics.get("species_counts", {})
    visits = metrics.get("visits", [])

    species_rows = ""
    for sp, count in sorted(species_counts.items(), key=lambda x: x[1], reverse=True):
        species_rows += f"<li>{sp}: {count}</li>\n"

    visit_rows = ""
    for v in visits:
        sp_display = v.get("species_norm") or v.get("species")
        sp_raw = v.get("species_raw")
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

    dashboard_file = config.DASHBOARD_DIR / "dashboard.html"
    try:
        with dashboard_file.open("w", encoding="utf-8") as f:
            f.write(html)
    except Exception as e:
        if logger:
            logger.warning(f"[dashboard] failed to write: {e}")


def update_metrics(image_path: Path, species: str, summary: str, timestamp: datetime) -> None:
    metrics = load_metrics()
    try:
        digest = hashlib.sha1(image_path.read_bytes()).hexdigest()
    except Exception as e:
        if logger:
            logger.error(f"Failed to compute digest for {image_path}: {e}")
        digest = image_path.stem

    visit_id = digest
    species_norm = normalize_species(species)
    date_str = timestamp.strftime("%Y-%m-%d")

    try:
        report_full = config.REPORT_ROOT / date_str / f"{image_path.stem}.html"
        report_rel = os.path.relpath(report_full, start=config.DASHBOARD_DIR).replace("\\", "/")
    except Exception:
        report_rel = f"{date_str}/{image_path.stem}.html"

    try:
        image_rel = os.path.relpath(image_path, start=config.DASHBOARD_DIR).replace("\\", "/")
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
    client, api_key: str, image_path: Path, boxes: Optional[List[Tuple[int, int, int, int]]] = None
) -> dict:
    """Analyze bird image using OpenAI Vision API with retry logic."""
    result: dict = {
        "ok": False,
        "error": None,
        "summary": None,
        "species_guess": None,
        "raw": None,
    }

    if client is None:
        result["error"] = "OpenAI client not initialized"
        if logger:
            logger.warning("OpenAI analyze called but client is None")
        return result

    def _expand_bbox(
        bbox: Tuple[int, int, int, int], img_shape: Tuple[int, int], margin_ratio: float = 0.1
    ) -> Tuple[int, int, int, int]:
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

    # Retry logic for transient failures
    max_attempts = 3
    for attempt in range(max_attempts):
        try:
            # Prepare image data (crop to bird if boxes provided)
            if boxes:
                full_img = cv2.imread(str(image_path))
                if full_img is not None and len(boxes) > 0:
                    largest = max(boxes, key=lambda b: (b[2] - b[0]) * (b[3] - b[1]))
                    ex_bbox = _expand_bbox(largest, full_img.shape[:2], margin_ratio=0.1)
                    x0, y0, x1, y1 = ex_bbox
                    crop = full_img[y0:y1, x0:x1]
                    crop = _resize_to_tile(crop)
                    _, buf = cv2.imencode(".jpg", crop)
                    img_bytes = buf.tobytes()
                    if logger:
                        logger.debug(f"Cropped image using bbox {largest}, size {crop.shape}")
                else:
                    img_bytes = image_path.read_bytes()
            else:
                img_bytes = image_path.read_bytes()

            b64 = base64.b64encode(img_bytes).decode("ascii")

            # Call OpenAI Vision API
            if logger and attempt > 0:
                logger.info(f"[OpenAI] Retry attempt {attempt + 1}/{max_attempts}")

            response = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "text",
                                "text": "Analyze this bird feeder image. Return JSON with: birds_present (bool), count (int), species_guess (string), summary (string). Provide your best species guess; use 'unknown' only if truly uncertain."
                            },
                            {
                                "type": "image_url",
                                "image_url": {
                                    "url": f"data:image/jpeg;base64,{b64}"
                                }
                            }
                        ]
                    }
                ],
                max_tokens=300
            )

            text = response.choices[0].message.content.strip()
            result["raw"] = text
            cleaned = text

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
                    try:
                        parsed = json.loads(cleaned[start : end + 1])
                    except Exception:
                        parsed = None

            if isinstance(parsed, dict):
                result["ok"] = True
                result["summary"] = parsed.get("summary")
                result["species_guess"] = parsed.get("species_guess")
            else:
                result["ok"] = True
                result["summary"] = text
                result["species_guess"] = None

            if logger:
                logger.info(f"[OpenAI] Successfully identified: {result.get('species_guess', 'unknown')}")
            return result

        except Exception as e:
            error_str = str(e)
            if logger:
                logger.error(f"[OpenAI] Attempt {attempt + 1}/{max_attempts} failed: {repr(e)}")

            # Check if it's a fatal error (don't retry)
            if "401" in error_str or "invalid_api_key" in error_str:
                if logger:
                    logger.error("[OpenAI] Fatal error - invalid API key, not retrying")
                result["error"] = f"Invalid API key: {error_str}"
                return result

            # If not the last attempt, wait before retry
            if attempt < max_attempts - 1:
                wait_time = (attempt + 1) * 2  # Progressive backoff: 2s, 4s, 6s
                if logger:
                    logger.info(f"[OpenAI] Waiting {wait_time}s before retry...")
                time.sleep(wait_time)
            else:
                # Last attempt failed
                if logger:
                    logger.error(f"[OpenAI] All {max_attempts} attempts failed")
                result["error"] = f"Failed after {max_attempts} attempts: {error_str}"

    return result


def write_html_report(report_dir: Path, image_path: Path, birds: int, unique_idx: int, openai_result: dict) -> Path:
    ensure_dir(report_dir)
    report_path = report_dir / f"{image_path.stem}.html"

    try:
        rel_img_path = os.path.relpath(image_path, start=report_dir).replace("\\", "/")
    except Exception:
        rel_img_path = image_path.name

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
    <p><b>Image:</b> {image_path.name}</p>
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


def frame_grabber(rtsp_url: str, holder: dict) -> None:
    cap = None
    while not analysis_stop_event.is_set():
        if cap is None or not cap.isOpened():
            cap = cv2.VideoCapture(rtsp_url, cv2.CAP_FFMPEG)
            if not cap.isOpened():
                if logger:
                    logger.warning("[grabber] Failed to open RTSP stream; retrying...")
                time.sleep(2)
                continue

        ret, frame = cap.read()
        if not ret or frame is None:
            if logger:
                logger.warning("[grabber] Frame read failed; reconnecting...")
            cap.release()
            cap = None
            time.sleep(1)
            continue

        with holder["lock"]:
            holder["frame"] = frame

        time.sleep(0.01)

    if cap:
        cap.release()


def analysis_worker() -> None:
    while not analysis_stop_event.is_set():
        try:
            task = analysis_queue.get(timeout=0.5)
        except Empty:
            continue

        image_path, boxes, detected_birds, unique_idx, timestamp = task

        client, key = load_openai_client()
        analysis = openai_analyze_image(client, key, image_path, boxes)

        report_dir = config.REPORT_ROOT / timestamp.date().isoformat()
        report_path = write_html_report(
            report_dir, image_path, detected_birds, unique_idx, analysis
        )

        species = analysis.get("species_guess") if analysis and analysis.get("ok") else "unknown"
        summary = analysis.get("summary") if analysis and analysis.get("ok") else (
            analysis.get("error") if analysis else "No analysis"
        )
        update_metrics(image_path, species or "unknown", summary or "", timestamp)

        if logger:
            logger.info(f"Analyzed {image_path.name}: {species} - {report_path}")

        analysis_queue.task_done()


def run_capture_and_analyse() -> None:
    global logger
    logger = setup_logging()

    ensure_dir(config.CAPTURE_ROOT)
    ensure_dir(config.REPORT_ROOT)

    logger.info("Loading YOLO model...")
    model = YOLO(config.MODEL_PATH)

    grabber_thread = threading.Thread(target=frame_grabber, args=(config.RTSP_URL, frame_holder), daemon=True)
    grabber_thread.start()

    worker_thread = threading.Thread(target=analysis_worker, daemon=True)
    worker_thread.start()

    cv2.namedWindow("Bird Feed", cv2.WINDOW_NORMAL)

    today = date.today().isoformat()
    unique_count = 0
    last_capture_time = 0.0
    last_bird_detection_time = 0.0
    bird_present = False
    last_detection_timestamp = 0.0

    try:
        while True:
            with frame_holder["lock"]:
                frame = frame_holder.get("frame")

            if frame is None:
                time.sleep(0.05)
                continue

            now = time.time()
            run_detection = (now - last_detection_timestamp) >= config.DETECTION_INTERVAL
            detected_birds = 0
            accepted_boxes: List[Tuple[int, int, int, int]] = []

            display_frame = frame.copy()

            if run_detection:
                last_detection_timestamp = now
                h, w = frame.shape[:2]
                x1n, y1n, x2n, y2n = config.ROI_NORM
                x1 = max(0, min(w - 1, int(x1n * w)))
                y1 = max(0, min(h - 1, int(y1n * h)))
                x2 = max(1, min(w, int(x2n * w)))
                y2 = max(1, min(h, int(y2n * h)))

                roi = frame[y1:y2, x1:x2]
                roi_h, roi_w = roi.shape[:2]

                if roi_w > 0 and roi_h > 0:
                    scale = config.DETECT_RESIZE_WIDTH / float(roi_w)
                    new_h = int(roi_h * scale)
                    roi_resized = cv2.resize(roi, (config.DETECT_RESIZE_WIDTH, new_h), interpolation=cv2.INTER_AREA)

                    results = model(roi_resized, conf=config.CONF_THRESH, verbose=False)[0]

                    scale_x = (x2 - x1) / float(config.DETECT_RESIZE_WIDTH)
                    scale_y = (y2 - y1) / float(new_h)
                    roi_area = max(1.0, (x2 - x1) * (y2 - y1))

                    for box in results.boxes:
                        cls_id = int(box.cls[0])
                        if cls_id != config.BIRD_CLASS_ID:
                            continue

                        rx1, ry1, rx2, ry2 = box.xyxy[0]
                        rx1 = float(rx1) * scale_x + x1
                        ry1 = float(ry1) * scale_y + y1
                        rx2 = float(rx2) * scale_x + x1
                        ry2 = float(ry2) * scale_y + y1

                        box_w = max(0.0, rx2 - rx1)
                        box_h = max(0.0, ry2 - ry1)
                        area_ratio = (box_w * box_h) / roi_area if roi_area > 0 else 0.0

                        if area_ratio < config.MIN_AREA_RATIO:
                            continue

                        accepted_boxes.append((int(rx1), int(ry1), int(rx2), int(ry2)))
                        cv2.rectangle(display_frame, (int(rx1), int(ry1)), (int(rx2), int(ry2)), (0, 255, 0), 2)
                        cv2.putText(display_frame, "bird", (int(rx1), max(0, int(ry1) - 6)),
                                  cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)

            detected_birds = len(accepted_boxes)

            if detected_birds > 0:
                last_bird_detection_time = now
                if not bird_present:
                    if (now - last_capture_time) >= config.CAPTURE_GAP_SEC:
                        unique_count += 1
                        logger.info(f"New bird visit #{unique_count}")

                        day_dir = config.CAPTURE_ROOT / today
                        ensure_dir(day_dir)
                        filename = f"bird_{unique_count}_{int(now)}.jpg"
                        image_path = day_dir / filename
                        cv2.imwrite(str(image_path), frame)

                        analysis_queue.put(
                            (image_path, accepted_boxes.copy(), detected_birds, unique_count, datetime.now())
                        )
                        last_capture_time = now
                    bird_present = True
            else:
                if bird_present and ((now - last_bird_detection_time) >= config.BIRD_ABSENCE_TIMEOUT):
                    bird_present = False

            if config.VIEW_SCALE != 1.0:
                disp_h, disp_w = display_frame.shape[:2]
                display_scaled = cv2.resize(
                    display_frame,
                    (int(disp_w * config.VIEW_SCALE), int(disp_h * config.VIEW_SCALE)),
                    interpolation=cv2.INTER_AREA
                )
            else:
                display_scaled = display_frame

            cv2.putText(display_scaled, f"Unique birds today: {unique_count}", (10, 30),
                      cv2.FONT_HERSHEY_SIMPLEX, 1.0, (255, 255, 0), 2)
            cv2.imshow("Bird Feed", display_scaled)

            if cv2.waitKey(1) & 0xFF == ord("q"):
                logger.info("Quit requested; exiting.")
                break

            current_date = date.today().isoformat()
            if current_date != today:
                today = current_date
                unique_count = 0
                last_capture_time = 0.0
                last_bird_detection_time = 0.0
                bird_present = False

    finally:
        analysis_stop_event.set()
        try:
            analysis_queue.join()
        except Exception:
            pass
        cv2.destroyAllWindows()
        logger.info(f"Final count for {today}: {unique_count}")


if __name__ == "__main__":
    run_capture_and_analyse()
