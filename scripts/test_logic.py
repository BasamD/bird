"""
Logic Tests for Fixed Bird Detection Scripts

Run with: python test_logic.py
"""

import sys
import os
from pathlib import Path
import json
import tempfile
import shutil

os.environ["OPENAI_API_KEY"] = "test_key"

try:
    import config
    import pilot_analyze_captures_fixed as analyzer
    import pilot_bird_counter_fixed as counter
except ImportError as e:
    print(f"Import error: {e}")
    print("Make sure you're in the scripts directory")
    sys.exit(1)


def test_normalize_species():
    print("\n=== Testing Species Normalization ===")
    tests = [
        ("House Sparrow", "house sparrow"),
        ("sparrows", "sparrow"),
        ("Great Tit", "great tit"),
        ("robin and sparrow", "multi"),
        ("Blue Jay, Cardinal", "multi"),
        ("", "unknown"),
        (None, "unknown"),
        ("house sparrows", "house sparrow"),  # synonym
    ]

    passed = 0
    failed = 0
    for input_val, expected in tests:
        result = analyzer.normalize_species(input_val)
        if result == expected:
            print(f"✓ '{input_val}' -> '{result}'")
            passed += 1
        else:
            print(f"✗ '{input_val}' -> '{result}' (expected '{expected}')")
            failed += 1

    print(f"\nPassed: {passed}/{len(tests)}")
    return failed == 0


def test_metrics_operations():
    print("\n=== Testing Metrics Operations ===")

    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir = Path(tmpdir)
        metrics_file = tmpdir / "metrics.json"

        config.METRICS_FILE = metrics_file
        config.DASHBOARD_DIR = tmpdir

        metrics = analyzer.load_metrics()
        assert metrics["total_visits"] == 0, "Initial visits should be 0"
        assert len(metrics["visits"]) == 0, "Initial visits list should be empty"
        print("✓ Load empty metrics")

        metrics["total_visits"] = 5
        metrics["species_counts"] = {"sparrow": 3, "robin": 2}
        analyzer.save_metrics(metrics)

        assert metrics_file.exists(), "Metrics file should exist"
        print("✓ Save metrics")

        loaded = analyzer.load_metrics()
        assert loaded["total_visits"] == 5, "Should load saved visits"
        assert loaded["species_counts"]["sparrow"] == 3, "Should load counts"
        print("✓ Load saved metrics")

        try:
            with metrics_file.open("w") as f:
                f.write("invalid json{")
            loaded = analyzer.load_metrics()
            assert loaded["total_visits"] == 0, "Should return default on error"
            print("✓ Handle corrupted metrics")
        except Exception as e:
            print(f"✗ Failed to handle corrupted metrics: {e}")
            return False

    print("All metrics tests passed!")
    return True


def test_file_locking():
    print("\n=== Testing File Locking ===")

    with tempfile.TemporaryDirectory() as tmpdir:
        test_file = Path(tmpdir) / "test.jpg"
        test_file.write_text("test")

        lock1 = analyzer.try_lock(test_file)
        assert lock1 is not None, "First lock should succeed"
        assert lock1.exists(), "Lock file should exist"
        print("✓ Acquire lock")

        lock2 = analyzer.try_lock(test_file)
        assert lock2 is None, "Second lock should fail"
        print("✓ Prevent double lock")

        analyzer.release_lock(lock1)
        assert not lock1.exists(), "Lock should be released"
        print("✓ Release lock")

        lock3 = analyzer.try_lock(test_file)
        assert lock3 is not None, "Should lock after release"
        print("✓ Re-acquire after release")
        analyzer.release_lock(lock3)

    print("All locking tests passed!")
    return True


def test_path_handling():
    print("\n=== Testing Path Handling ===")

    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir = Path(tmpdir)

        analyzer.safe_mkdir(tmpdir / "test" / "nested" / "dirs")
        assert (tmpdir / "test" / "nested" / "dirs").exists(), "Should create nested dirs"
        print("✓ Create nested directories")

        analyzer.safe_mkdir(tmpdir / "test")
        print("✓ Handle existing directory")

        test_file = tmpdir / "test" / "file.jpg"
        test_file.write_text("test")

        dst_dir = tmpdir / "destination"
        moved = analyzer.move_with_retries(test_file, dst_dir, suffix="_moved")
        assert moved is not None, "Move should succeed"
        assert moved.exists(), "Moved file should exist"
        assert not test_file.exists(), "Original should be gone"
        print("✓ Move file with retries")

        missing = tmpdir / "missing.jpg"
        result = analyzer.move_with_retries(missing, dst_dir)
        assert result is None, "Move missing file should return None"
        print("✓ Handle missing source file")

    print("All path tests passed!")
    return True


def test_roi_validation():
    print("\n=== Testing ROI Validation ===")

    roi = config.ROI_NORM
    assert len(roi) == 4, "ROI should have 4 values"
    assert all(0 <= v <= 1 for v in roi), "ROI values should be normalized (0-1)"
    assert roi[0] < roi[2], "x1 should be less than x2"
    assert roi[1] < roi[3], "y1 should be less than y2"
    print(f"✓ ROI valid: {roi}")

    print("All ROI tests passed!")
    return True


def test_config_values():
    print("\n=== Testing Configuration ===")

    assert hasattr(config, "CAPTURE_ROOT"), "Should have CAPTURE_ROOT"
    assert hasattr(config, "REPORT_ROOT"), "Should have REPORT_ROOT"
    assert hasattr(config, "MODEL_PATH"), "Should have MODEL_PATH"
    assert hasattr(config, "CONF_THRESH"), "Should have CONF_THRESH"
    assert hasattr(config, "BIRD_CLASS_ID"), "Should have BIRD_CLASS_ID"
    print("✓ All config attributes present")

    assert 0 < config.CONF_THRESH < 1, "Confidence threshold should be 0-1"
    assert config.BIRD_CLASS_ID == 14, "COCO bird class should be 14"
    assert config.CAPTURE_GAP_SEC > 0, "Capture gap should be positive"
    print("✓ Config values valid")

    print("All config tests passed!")
    return True


def test_dashboard_generation():
    print("\n=== Testing Dashboard Generation ===")

    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir = Path(tmpdir)
        config.DASHBOARD_DIR = tmpdir

        test_metrics = {
            "total_visits": 3,
            "species_counts": {"sparrow": 2, "robin": 1},
            "visits": [
                {
                    "id": "test1",
                    "timestamp": "2024-01-01 10:00:00",
                    "species_raw": "House Sparrow",
                    "species_norm": "house sparrow",
                    "summary": "A sparrow at the feeder",
                    "report_rel": "reports/test1.html",
                    "image_rel": "images/test1.jpg"
                }
            ]
        }

        analyzer.write_dashboard_html(test_metrics)

        dashboard = tmpdir / "dashboard.html"
        assert dashboard.exists(), "Dashboard should be created"
        print("✓ Dashboard file created")

        content = dashboard.read_text()
        assert "Bird Visit Dashboard" in content, "Should have title"
        assert "Total visits" in content, "Should show total"
        assert "sparrow: 2" in content, "Should show species count"
        assert "test1" in content, "Should list visit"
        print("✓ Dashboard content valid")

        assert 'meta http-equiv=\'refresh\'' in content, "Should have auto-refresh"
        print("✓ Dashboard has auto-refresh")

    print("All dashboard tests passed!")
    return True


def test_thread_safety():
    print("\n=== Testing Thread Safety ===")

    assert "lock" in counter.frame_holder, "frame_holder should have lock"
    assert hasattr(counter.frame_holder["lock"], "acquire"), "Should be a real lock"
    print("✓ Frame holder has thread lock")

    print("All thread safety checks passed!")
    return True


def run_all_tests():
    print("=" * 60)
    print("Running Logic Tests for Fixed Bird Detection Scripts")
    print("=" * 60)

    tests = [
        ("Species Normalization", test_normalize_species),
        ("Metrics Operations", test_metrics_operations),
        ("File Locking", test_file_locking),
        ("Path Handling", test_path_handling),
        ("ROI Validation", test_roi_validation),
        ("Config Values", test_config_values),
        ("Dashboard Generation", test_dashboard_generation),
        ("Thread Safety", test_thread_safety),
    ]

    results = []
    for name, test_func in tests:
        try:
            passed = test_func()
            results.append((name, passed))
        except Exception as e:
            print(f"\n✗ {name} FAILED with exception: {e}")
            import traceback
            traceback.print_exc()
            results.append((name, False))

    print("\n" + "=" * 60)
    print("TEST SUMMARY")
    print("=" * 60)

    passed_count = sum(1 for _, passed in results if passed)
    total_count = len(results)

    for name, passed in results:
        status = "✓ PASS" if passed else "✗ FAIL"
        print(f"{status}: {name}")

    print("=" * 60)
    print(f"Total: {passed_count}/{total_count} test suites passed")

    if passed_count == total_count:
        print("\n🎉 All tests passed! Scripts are ready to use.")
        return 0
    else:
        print(f"\n⚠️  {total_count - passed_count} test suite(s) failed.")
        return 1


if __name__ == "__main__":
    sys.exit(run_all_tests())
