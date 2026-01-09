"""
Bird Tracker Setup Diagnostics
==============================

Run this script to diagnose setup issues with the bird tracking system.
"""

import os
import sys
from pathlib import Path
import json

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent))

try:
    import config
except ImportError:
    print("❌ ERROR: config.py not found!")
    sys.exit(1)


def check_path(name: str, path: Path) -> bool:
    """Check if a path exists and is accessible."""
    print(f"\n{name}:")
    print(f"  Path: {path}")
    print(f"  Absolute: {path.absolute()}")

    if path.exists():
        print(f"  ✅ Exists")
        if path.is_dir():
            print(f"  ✅ Is directory")
            try:
                # Try to list contents
                contents = list(path.iterdir())
                print(f"  ✅ Readable ({len(contents)} items inside)")
                return True
            except Exception as e:
                print(f"  ❌ Cannot read directory: {e}")
                return False
        elif path.is_file():
            print(f"  ✅ Is file")
            try:
                size = path.stat().st_size
                print(f"  ✅ Readable ({size} bytes)")
                return True
            except Exception as e:
                print(f"  ❌ Cannot read file: {e}")
                return False
    else:
        print(f"  ❌ Does NOT exist")
        return False


def check_api_key():
    """Check OpenAI API key configuration."""
    print("\n" + "=" * 60)
    print("OpenAI API Key Configuration")
    print("=" * 60)

    key = config.OPENAI_API_KEY
    if not key:
        print("❌ OPENAI_API_KEY is not set in .env file")
        print("   Birds cannot be identified without a valid OpenAI API key")
        return False

    # Mask the key for display
    if len(key) > 20:
        masked = f"{key[:8]}...{key[-8:]}"
    else:
        masked = "***"

    print(f"✅ OPENAI_API_KEY is set: {masked}")
    print(f"   Length: {len(key)} characters")

    if len(key) < 20:
        print("⚠️  WARNING: Key seems too short (might be invalid)")
        return False

    return True


def check_metrics_file():
    """Check metrics.json file."""
    print("\n" + "=" * 60)
    print("Metrics File Status")
    print("=" * 60)

    metrics_file = config.METRICS_FILE
    check_path("metrics.json", metrics_file)

    if metrics_file.exists():
        try:
            with metrics_file.open("r", encoding="utf-8") as f:
                data = json.load(f)

            total_visits = data.get("total_visits", 0)
            visits_count = len(data.get("visits", []))
            species_count = len(data.get("species_counts", {}))

            print(f"\n  Metrics Summary:")
            print(f"    Total visits: {total_visits}")
            print(f"    Visits in list: {visits_count}")
            print(f"    Species tracked: {species_count}")

            if total_visits == 0:
                print("\n  ⚠️  WARNING: No visits recorded yet")
                print("     Either no birds have been detected, or there's a problem saving data")

            return True
        except json.JSONDecodeError as e:
            print(f"  ❌ ERROR: Invalid JSON format: {e}")
            return False
        except Exception as e:
            print(f"  ❌ ERROR reading file: {e}")
            return False


def check_dashboard():
    """Check dashboard.html file."""
    print("\n" + "=" * 60)
    print("Dashboard File Status")
    print("=" * 60)

    dashboard_file = config.DASHBOARD_FILE
    return check_path("dashboard.html", dashboard_file)


def main():
    print("=" * 60)
    print("Bird Tracker Setup Diagnostics")
    print("=" * 60)
    print("\nChecking your bird tracker configuration...\n")

    # Check base directory
    print("=" * 60)
    print("Base Directories")
    print("=" * 60)
    check_path("BASE_DIR", config.BASE_DIR)
    check_path("DASHBOARD_DIR", config.DASHBOARD_DIR)
    check_path("CAPTURE_ROOT", config.CAPTURE_ROOT)
    check_path("REPORT_ROOT", config.REPORT_ROOT)
    check_path("LOG_ROOT", config.LOG_ROOT)

    # Check API key
    check_api_key()

    # Check metrics and dashboard
    check_metrics_file()
    check_dashboard()

    # Summary
    print("\n" + "=" * 60)
    print("Diagnostic Summary")
    print("=" * 60)
    print("\nCommon Issues and Solutions:")
    print("  1. If metrics.json shows 0 visits but you've processed images:")
    print("     - Check that the analyzer script completed without errors")
    print("     - Look at the log files in the LOG_ROOT directory")
    print("     - Ensure OpenAI API key is valid (run this script to check)")
    print("\n  2. If OpenAI API key is invalid:")
    print("     - Get a new key from: https://platform.openai.com/api-keys")
    print("     - Update the OPENAI_API_KEY in your .env file")
    print("     - Restart the analyzer script")
    print("\n  3. If dashboard.html isn't updating:")
    print("     - Check file permissions on DASHBOARD_DIR")
    print("     - Ensure the analyzer script has write access")
    print("     - Check for errors in the log files")
    print("\nFor more help, check the log files in:")
    print(f"  {config.LOG_ROOT}")
    print("\n" + "=" * 60)


if __name__ == "__main__":
    main()
