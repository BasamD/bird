import time
import base64
import json
from datetime import datetime, timezone
from typing import Optional, Dict, Any
from openai import OpenAI
from supabase import Client
import requests

from config import Config
from logger import StructuredLogger

class SpeciesAnalyzer:
    def __init__(self, supabase_client: Client, config: Config):
        self.supabase = supabase_client
        self.config = config
        self.logger = StructuredLogger(supabase_client, 'analyzer')
        self.openai_client = OpenAI(api_key=config.OPENAI_API_KEY) if config.OPENAI_API_KEY else None

        if not self.openai_client:
            self.logger.warning("OpenAI API key not configured, species identification disabled")

    def analyze_visit(self, visit_id: str):
        if not self.openai_client:
            self.logger.info(f"Skipping analysis for visit {visit_id} (OpenAI not configured)")
            self._mark_visit_completed(visit_id, "unknown", None, "OpenAI API not configured")
            return

        try:
            self.logger.info(f"Starting analysis for visit {visit_id}")
            self.logger.set_correlation_id(visit_id)

            captures = self.supabase.table('captures').select('*').eq('visit_id', visit_id).execute()

            if not captures.data:
                self.logger.warning(f"No captures found for visit {visit_id}")
                self._mark_visit_completed(visit_id, "unknown", None, "No captures available")
                return

            best_capture = self._select_best_capture(captures.data)

            species, confidence, summary, bird_count = self._identify_species(best_capture)

            self._mark_visit_completed(visit_id, species, confidence, summary, bird_count)

            self.logger.info(f"Analysis complete for visit {visit_id}: {species} ({confidence})")

        except Exception as e:
            self.logger.error(f"Failed to analyze visit {visit_id}: {e}", {'error': str(e)})
            self._mark_visit_failed(visit_id, str(e))

    def _select_best_capture(self, captures) -> Dict[str, Any]:
        best_capture = None
        best_score = 0

        for capture in captures:
            detections = capture.get('detections', [])

            total_area = 0
            max_confidence = 0

            for detection in detections:
                bbox = detection.get('bbox', [])
                if len(bbox) == 4:
                    x1, y1, x2, y2 = bbox
                    area = (x2 - x1) * (y2 - y1)
                    total_area += area
                    max_confidence = max(max_confidence, detection.get('confidence', 0))

            score = total_area * max_confidence

            if score > best_score:
                best_score = score
                best_capture = capture

        return best_capture or captures[0]

    def _identify_species(self, capture: Dict[str, Any]) -> tuple:
        image_url = capture['image_url']

        for attempt in range(self.config.OPENAI_MAX_RETRIES):
            try:
                self.logger.debug(f"Calling OpenAI API (attempt {attempt + 1})")

                if image_url.startswith('http'):
                    image_content = {
                        "type": "image_url",
                        "image_url": {"url": image_url}
                    }
                else:
                    self.logger.warning("Local image URLs not yet supported, using placeholder")
                    return "unknown", "low", "Image not accessible for analysis", 1

                prompt = """Analyze this bird feeder image. Return JSON with:
- birds_present (bool): Whether any birds are visible
- count (int): Number of distinct birds
- species_guess (string): Your best guess for species name (use "unknown" only if truly uncertain)
- confidence (string): "low", "medium", or "high"
- summary (string): Brief natural language description

Provide your best species guess even if not 100% certain."""

                response = self.openai_client.chat.completions.create(
                    model=self.config.OPENAI_MODEL,
                    messages=[
                        {
                            "role": "user",
                            "content": [
                                {"type": "text", "text": prompt},
                                image_content
                            ]
                        }
                    ],
                    max_tokens=self.config.OPENAI_MAX_TOKENS,
                    timeout=self.config.OPENAI_TIMEOUT_SEC
                )

                content = response.choices[0].message.content

                result = self._parse_openai_response(content)

                species = result.get('species_guess', 'unknown')
                confidence = result.get('confidence', 'low')
                summary = result.get('summary', '')
                bird_count = result.get('count', 1)

                return species, confidence, summary, bird_count

            except Exception as e:
                self.logger.warning(f"OpenAI API attempt {attempt + 1} failed: {e}")

                if attempt < self.config.OPENAI_MAX_RETRIES - 1:
                    delay = self.config.OPENAI_RETRY_DELAY_SEC * (2 ** attempt)
                    self.logger.info(f"Retrying in {delay}s...")
                    time.sleep(delay)
                else:
                    self.logger.error("All OpenAI API attempts failed")
                    return "unknown", "low", f"Analysis failed: {str(e)}", 1

        return "unknown", "low", "Analysis failed after all retries", 1

    def _parse_openai_response(self, content: str) -> Dict[str, Any]:
        try:
            json_start = content.find('{')
            json_end = content.rfind('}') + 1

            if json_start >= 0 and json_end > json_start:
                json_str = content[json_start:json_end]
                return json.loads(json_str)
            else:
                raise ValueError("No JSON found in response")

        except Exception as e:
            self.logger.warning(f"Failed to parse JSON response, attempting text extraction: {e}")

            import re
            species_match = re.search(r'species[_\s]*guess[:\s]*["\']?([^"\'}\n]+)', content, re.IGNORECASE)
            species = species_match.group(1).strip() if species_match else "unknown"

            return {
                'birds_present': True,
                'count': 1,
                'species_guess': species,
                'confidence': 'low',
                'summary': content
            }

    def _mark_visit_completed(self, visit_id: str, species: str, confidence: Optional[str], summary: str, bird_count: int = 1):
        try:
            update_data = {
                'status': 'completed',
                'species': species,
                'species_confidence': confidence,
                'summary': summary,
                'bird_count': bird_count,
                'updated_at': datetime.now(timezone.utc).isoformat()
            }
            self.supabase.table('visits').update(update_data).eq('id', visit_id).execute()

            self._update_species_stats(species)

        except Exception as e:
            self.logger.error(f"Failed to update visit status: {e}")

    def _mark_visit_failed(self, visit_id: str, error_message: str):
        try:
            update_data = {
                'status': 'failed',
                'species': 'unknown',
                'summary': f"Analysis failed: {error_message}",
                'updated_at': datetime.now(timezone.utc).isoformat()
            }
            self.supabase.table('visits').update(update_data).eq('id', visit_id).execute()
        except Exception as e:
            self.logger.error(f"Failed to mark visit as failed: {e}")

    def _update_species_stats(self, species: str):
        if not species or species == 'unknown':
            return

        try:
            existing = self.supabase.table('species_stats').select('*').eq('species', species).execute()

            if existing.data:
                current = existing.data[0]
                self.supabase.table('species_stats').update({
                    'total_visits': current['total_visits'] + 1,
                    'last_seen': datetime.now(timezone.utc).isoformat(),
                    'updated_at': datetime.now(timezone.utc).isoformat()
                }).eq('species', species).execute()
            else:
                self.supabase.table('species_stats').insert({
                    'species': species,
                    'total_visits': 1,
                    'first_seen': datetime.now(timezone.utc).isoformat(),
                    'last_seen': datetime.now(timezone.utc).isoformat(),
                    'updated_at': datetime.now(timezone.utc).isoformat()
                }).execute()

        except Exception as e:
            self.logger.error(f"Failed to update species stats: {e}")
