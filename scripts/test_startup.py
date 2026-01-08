"""
Quick test script to verify all dependencies and basic functionality
"""
import sys
import traceback

def test_imports():
    print("Testing imports...")
    try:
        import cv2
        print(f"✓ OpenCV {cv2.__version__}")
    except Exception as e:
        print(f"✗ OpenCV: {e}")
        return False

    try:
        from ultralytics import YOLO
        print(f"✓ Ultralytics")
    except Exception as e:
        print(f"✗ Ultralytics: {e}")
        return False

    try:
        import openai
        print(f"✓ OpenAI {openai.__version__}")
    except Exception as e:
        print(f"✗ OpenAI: {e}")
        return False

    try:
        import numpy
        print(f"✓ NumPy {numpy.__version__}")
    except Exception as e:
        print(f"✗ NumPy: {e}")
        return False

    return True

def test_config():
    print("\nTesting config...")
    try:
        import config
        print(f"✓ Config loaded")
        print(f"  RTSP_URL: {config.RTSP_URL[:50]}...")
        print(f"  MODEL_PATH: {config.MODEL_PATH}")
        print(f"  OPENAI_API_KEY: {'SET' if config.OPENAI_API_KEY else 'NOT SET'}")
        return True
    except Exception as e:
        print(f"✗ Config: {e}")
        traceback.print_exc()
        return False

def test_yolo():
    print("\nTesting YOLO model...")
    try:
        from ultralytics import YOLO
        model = YOLO('yolov8n.pt')
        print(f"✓ YOLO model loaded successfully")
        return True
    except Exception as e:
        print(f"✗ YOLO model: {e}")
        traceback.print_exc()
        return False

def test_opencv_window():
    print("\nTesting OpenCV window creation...")
    try:
        import cv2
        import numpy as np

        # Create a simple test image
        img = np.zeros((100, 100, 3), dtype=np.uint8)
        cv2.putText(img, "Test", (10, 50), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)

        # Try to create a window
        cv2.namedWindow("Test Window", cv2.WINDOW_NORMAL)
        cv2.imshow("Test Window", img)
        print(f"✓ OpenCV window created (closing in 2 seconds...)")
        cv2.waitKey(2000)
        cv2.destroyAllWindows()
        return True
    except Exception as e:
        print(f"✗ OpenCV window: {e}")
        traceback.print_exc()
        return False

def main():
    print("=" * 50)
    print("Bird Tracker Startup Test")
    print("=" * 50)
    print()

    all_ok = True
    all_ok = test_imports() and all_ok
    all_ok = test_config() and all_ok
    all_ok = test_yolo() and all_ok
    all_ok = test_opencv_window() and all_ok

    print()
    print("=" * 50)
    if all_ok:
        print("✓ All tests passed!")
        print("You can now run pilot_bird_counter_fixed.py")
    else:
        print("✗ Some tests failed")
        print("Please fix the issues above before running the main script")
    print("=" * 50)

    return 0 if all_ok else 1

if __name__ == "__main__":
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        print("\nTest interrupted")
        sys.exit(1)
    except Exception as e:
        print(f"\nUnexpected error: {e}")
        traceback.print_exc()
        sys.exit(1)
