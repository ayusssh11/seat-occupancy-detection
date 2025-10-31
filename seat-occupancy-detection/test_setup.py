"""
Test script to verify system setup and dependencies

Run this before starting the demo to ensure everything works!
"""

import sys


def test_python_version():
    """Test Python version"""
    print("Testing Python version...")
    version = sys.version_info
    if version.major >= 3 and version.minor >= 8:
        print(f"✓ Python {version.major}.{version.minor}.{version.micro} - OK")
        return True
    else:
        print(f"✗ Python {version.major}.{version.minor} - Need 3.8+")
        return False


def test_import(module_name, package_name=None):
    """Test if a module can be imported"""
    try:
        __import__(module_name)
        print(f"✓ {package_name or module_name} - OK")
        return True
    except ImportError:
        print(f"✗ {package_name or module_name} - NOT FOUND")
        return False


def test_pytorch():
    """Test PyTorch and CUDA"""
    print("\nTesting PyTorch...")
    try:
        import torch
        print(f"✓ PyTorch {torch.__version__} - OK")

        # Test CUDA
        if torch.cuda.is_available():
            print(f"✓ CUDA available - {torch.cuda.get_device_name(0)}")
            print(f"  CUDA version: {torch.version.cuda}")
        else:
            print("⚠ CUDA not available - will use CPU (slower)")

        return True
    except ImportError:
        print("✗ PyTorch not found")
        return False


def test_webcam():
    """Test webcam access"""
    print("\nTesting webcam...")
    try:
        import cv2
        cap = cv2.VideoCapture(0)

        if cap.isOpened():
            ret, frame = cap.read()
            if ret:
                h, w = frame.shape[:2]
                print(f"✓ Webcam accessible - Resolution: {w}x{h}")
                cap.release()
                return True
            else:
                print("✗ Webcam found but cannot read frames")
                cap.release()
                return False
        else:
            print("✗ Cannot access webcam")
            return False
    except Exception as e:
        print(f"✗ Webcam test failed: {e}")
        return False


def test_yolov5():
    """Test YOLOv5 loading"""
    print("\nTesting YOLOv5 model...")
    try:
        import torch
        print("Loading YOLOv5... (this may take a minute on first run)")
        model = torch.hub.load('ultralytics/yolov5', 'yolov5s', pretrained=True)
        print("✓ YOLOv5 model loaded successfully")
        return True
    except Exception as e:
        print(f"✗ YOLOv5 loading failed: {e}")
        return False


def test_file_structure():
    """Test if all required files exist"""
    print("\nTesting file structure...")
    import os

    required_files = [
        'main.py',
        'calibrate.py',
        'seat_mapper.py',
        'utils.py',
        'config.py',
        'requirements.txt',
        'README.md'
    ]

    all_present = True
    for file in required_files:
        if os.path.exists(file):
            print(f"✓ {file}")
        else:
            print(f"✗ {file} - MISSING")
            all_present = False

    # Check output directory
    if not os.path.exists('output'):
        os.makedirs('output')
        print("✓ Created output/ directory")
    else:
        print("✓ output/ directory exists")

    return all_present


def main():
    """Run all tests"""
    print("=" * 60)
    print("SEAT OCCUPANCY DETECTION SYSTEM - SETUP TEST")
    print("=" * 60)
    print()

    tests = [
        ("Python Version", test_python_version),
        ("File Structure", test_file_structure),
        ("Dependencies", lambda: all([
            test_import('cv2', 'opencv-python'),
            test_import('numpy'),
            test_import('torch', 'PyTorch'),
            test_import('torchvision'),
        ])),
        ("PyTorch & CUDA", test_pytorch),
        ("Webcam", test_webcam),
        ("YOLOv5 Model", test_yolov5),
    ]

    results = []

    for test_name, test_func in tests:
        print(f"\n{'─' * 60}")
        print(f"{test_name}")
        print('─' * 60)
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"✗ Test failed with error: {e}")
            results.append((test_name, False))

    # Summary
    print("\n" + "=" * 60)
    print("TEST SUMMARY")
    print("=" * 60)

    passed = sum(1 for _, result in results if result)
    total = len(results)

    for test_name, result in results:
        status = "✓ PASS" if result else "✗ FAIL"
        print(f"{status:10} | {test_name}")

    print("=" * 60)
    print(f"Result: {passed}/{total} tests passed")

    if passed == total:
        print("\n🎉 All tests passed! You're ready to go!")
        print("\nNext steps:")
        print("1. Run: python3 calibrate.py")
        print("2. Run: python3 main.py")
    else:
        print("\n⚠ Some tests failed. Please fix the issues above.")
        print("\nCommon solutions:")
        print("- Install dependencies: pip install -r requirements.txt")
        print("- Check webcam permissions")
        print("- Install CUDA if you have NVIDIA GPU")

    print("=" * 60)

    return passed == total


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
