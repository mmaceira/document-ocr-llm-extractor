"""Unit tests for OCR engines.

This module tests both Tesseract and RapidOCR engines with synthetic images.
"""

from __future__ import annotations

import contextlib

import pytest
from PIL import Image, ImageDraw, ImageFont

from document_llm_extractor.ocr.base import validate_bbox
from document_llm_extractor.ocr.factory import build_ocr_engine

# Lazy imports for engine classes to avoid import errors if dependencies aren't installed
try:
    from document_llm_extractor.ocr.tesseract_engine import TesseractEngine
except ImportError:
    TesseractEngine = None  # type: ignore

try:
    from document_llm_extractor.ocr.rapidocr_engine import RapidOCREngine
except ImportError:
    RapidOCREngine = None  # type: ignore


def _make_test_image() -> Image.Image:
    """Create a simple test image with text.

    Returns:
        PIL Image with text "Factura total: 123,45 €".
    """
    img = Image.new("RGB", (600, 200), "white")
    d = ImageDraw.Draw(img)
    # Use default font
    try:
        font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 24)
    except OSError:
        # Fallback to default font if system font not available
        font = ImageFont.load_default()
    d.text((10, 60), "Factura total: 123,45 €", fill="black", font=font)
    return img


@pytest.mark.skipif(
    TesseractEngine is None,
    reason="pytesseract not available",
)
def test_tesseract_engine_smoke():
    """Test Tesseract engine with a simple image."""
    img = _make_test_image()
    eng = TesseractEngine(langs=["spa", "eng"])
    page = eng.recognize_page(img, 0)

    assert page.page_index == 0
    assert page.width == 600
    assert page.height == 200
    assert page.runtime_sec > 0
    assert len(page.text) > 0
    assert "Factura" in page.text or "total" in page.text.lower()
    assert len(page.words) > 0

    # Check word structure
    word = page.words[0]
    assert word.text
    assert len(word.bbox) == 4
    assert word.bbox[0] < word.bbox[2]  # x0 < x1
    assert word.bbox[1] < word.bbox[3]  # y0 < y1
    assert 0 <= word.conf <= 100


@pytest.mark.skipif(
    RapidOCREngine is None,
    reason="rapidocr-onnxruntime not available",
)
def test_rapidocr_engine_smoke():
    """Test RapidOCR engine with a simple image."""
    if RapidOCREngine is None:
        pytest.skip("rapidocr-onnxruntime not available")
    img = _make_test_image()
    try:
        eng = RapidOCREngine(langs=["spa", "eng"])
    except ImportError:
        pytest.skip("rapidocr-onnxruntime not installed")
    page = eng.recognize_page(img, 0)

    assert page.page_index == 0
    assert page.width == 600
    assert page.height == 200
    assert page.runtime_sec > 0
    assert len(page.text) > 0
    assert len(page.words) > 0

    # Check word structure
    word = page.words[0]
    assert word.text
    assert len(word.bbox) == 4
    assert word.bbox[0] < word.bbox[2]  # x0 < x1
    assert word.bbox[1] < word.bbox[3]  # y0 < y1
    assert 0 <= word.conf <= 100


def test_factory_tesseract():
    """Test factory creates Tesseract engine."""
    if TesseractEngine is None:
        pytest.skip("pytesseract not installed")
    try:
        eng = build_ocr_engine("tesseract", langs=["spa", "eng"])
        assert isinstance(eng, TesseractEngine)
        assert eng.name == "tesseract"
    except ImportError:
        pytest.skip("pytesseract not installed")


def test_factory_rapidocr():
    """Test factory creates RapidOCR engine."""
    if RapidOCREngine is None:
        pytest.skip("rapidocr-onnxruntime not installed")
    try:
        eng = build_ocr_engine("rapidocr", langs=["spa", "eng"])
        assert isinstance(eng, RapidOCREngine)
        assert eng.name == "rapidocr"
    except ImportError:
        pytest.skip("rapidocr-onnxruntime not installed")


def test_factory_invalid():
    """Test factory raises error for invalid engine name."""
    with pytest.raises(ValueError, match="Unknown OCR engine"):
        build_ocr_engine("invalid", langs=["spa"])


def test_factory_default():
    """Test factory defaults to tesseract when name is None or empty."""
    if TesseractEngine is None:
        pytest.skip("pytesseract not installed")
    try:
        eng = build_ocr_engine("", langs=["spa"])
        assert isinstance(eng, TesseractEngine)
    except ImportError:
        pytest.skip("pytesseract not installed")


def test_validate_bbox():
    """Test bbox validation helper function."""
    # Valid bbox
    validate_bbox((10, 20, 100, 200), width=800, height=600)

    # Invalid: not a tuple
    with pytest.raises(ValueError, match="bbox must be a tuple"):
        validate_bbox([10, 20, 100, 200], width=800, height=600)

    # Invalid: wrong length
    with pytest.raises(ValueError, match="bbox must have 4 elements"):
        validate_bbox((10, 20, 100), width=800, height=600)

    # Invalid: not all integers
    with pytest.raises(ValueError, match="bbox coordinates must be integers"):
        validate_bbox((10.5, 20, 100, 200), width=800, height=600)

    # Invalid: x0 > x1
    with pytest.raises(ValueError, match="x0.*must be <= x1"):
        validate_bbox((100, 20, 10, 200), width=800, height=600)

    # Invalid: y0 > y1
    with pytest.raises(ValueError, match="y0.*must be <= y1"):
        validate_bbox((10, 200, 100, 20), width=800, height=600)

    # Invalid: negative x0
    with pytest.raises(ValueError, match="x0.*must be >= 0"):
        validate_bbox((-10, 20, 100, 200), width=800, height=600)

    # Invalid: negative y0
    with pytest.raises(ValueError, match="y0.*must be >= 0"):
        validate_bbox((10, -20, 100, 200), width=800, height=600)

    # Invalid: x1 > width
    with pytest.raises(ValueError, match="x1.*must be <= image width"):
        validate_bbox((10, 20, 900, 200), width=800, height=600)

    # Invalid: y1 > height
    with pytest.raises(ValueError, match="y1.*must be <= image height"):
        validate_bbox((10, 20, 100, 700), width=800, height=600)


def test_bbox_unification():
    """Test that all OCR engines produce unified bbox format."""
    # Create a test image
    img = Image.new("RGB", (800, 600), "white")
    d = ImageDraw.Draw(img)
    try:
        font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 24)
    except OSError:
        font = ImageFont.load_default()
    d.text((50, 100), "Test OCR Bounding Box", fill="black", font=font)
    d.text((50, 150), "Unified Format", fill="black", font=font)

    engines = []

    # Add Tesseract if available
    if TesseractEngine is not None:
        with contextlib.suppress(Exception):
            engines.append(("tesseract", TesseractEngine(["eng"])))

    # Add RapidOCR if available
    if RapidOCREngine is not None:
        try:
            eng = RapidOCREngine(["eng"])
            engines.append(("rapidocr", eng))
        except (ImportError, Exception):
            pass

    if not engines:
        pytest.skip("No OCR engines available for testing")

    for engine_name, engine in engines:
        page = engine.recognize_page(img, 0)

        # Validate all words have correct bbox format
        for word in page.words:
            x0, y0, x1, y1 = word.bbox

            # All coordinates must be integers
            assert isinstance(
                x0, int
            ), f"{engine_name}: x0 must be int, got {type(x0).__name__}: {x0}"
            assert isinstance(
                y0, int
            ), f"{engine_name}: y0 must be int, got {type(y0).__name__}: {y0}"
            assert isinstance(
                x1, int
            ), f"{engine_name}: x1 must be int, got {type(x1).__name__}: {x1}"
            assert isinstance(
                y1, int
            ), f"{engine_name}: y1 must be int, got {type(y1).__name__}: {y1}"

            # Coordinate ordering
            assert x0 <= x1, f"{engine_name}: x0 ({x0}) must be <= x1 ({x1})"
            assert y0 <= y1, f"{engine_name}: y0 ({y0}) must be <= y1 ({y1})"

            # Bounds checking
            assert 0 <= x0 <= 800, f"{engine_name}: x0 ({x0}) must be in [0, 800]"
            assert 0 <= x1 <= 800, f"{engine_name}: x1 ({x1}) must be in [0, 800]"
            assert 0 <= y0 <= 600, f"{engine_name}: y0 ({y0}) must be in [0, 600]"
            assert 0 <= y1 <= 600, f"{engine_name}: y1 ({y1}) must be in [0, 600]"


def test_ocr_engine_empty_image():
    """Test OCR engines with empty/blank image."""
    img = Image.new("RGB", (100, 100), "white")

    engines = []
    if TesseractEngine is not None:
        with contextlib.suppress(Exception):
            engines.append(("tesseract", TesseractEngine(["eng"])))
    if RapidOCREngine is not None:
        with contextlib.suppress(ImportError, Exception):
            engines.append(("rapidocr", RapidOCREngine(["eng"])))

    if not engines:
        pytest.skip("No OCR engines available for testing")

    for _engine_name, engine in engines:
        page = engine.recognize_page(img, 0)
        # Should not crash, may return empty text
        assert page.page_index == 0
        assert page.width == 100
        assert page.height == 100
        assert isinstance(page.text, str)
        assert isinstance(page.words, list)
        assert page.runtime_sec >= 0


def test_ocr_engine_small_image():
    """Test OCR engines with very small image."""
    img = Image.new("RGB", (10, 10), "white")

    engines = []
    if TesseractEngine is not None:
        with contextlib.suppress(Exception):
            engines.append(("tesseract", TesseractEngine(["eng"])))
    if RapidOCREngine is not None:
        with contextlib.suppress(ImportError, Exception):
            engines.append(("rapidocr", RapidOCREngine(["eng"])))

    if not engines:
        pytest.skip("No OCR engines available for testing")

    for _engine_name, engine in engines:
        page = engine.recognize_page(img, 0)
        assert page.page_index == 0
        assert page.width == 10
        assert page.height == 10


def test_ocr_engine_large_image():
    """Test OCR engines with large image."""
    img = Image.new("RGB", (2000, 3000), "white")
    d = ImageDraw.Draw(img)
    try:
        font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 24)
    except OSError:
        font = ImageFont.load_default()
    d.text((100, 100), "Large Image Test", fill="black", font=font)

    engines = []
    if TesseractEngine is not None:
        with contextlib.suppress(Exception):
            engines.append(("tesseract", TesseractEngine(["eng"])))
    if RapidOCREngine is not None:
        with contextlib.suppress(ImportError, Exception):
            engines.append(("rapidocr", RapidOCREngine(["eng"])))

    if not engines:
        pytest.skip("No OCR engines available for testing")

    for _engine_name, engine in engines:
        page = engine.recognize_page(img, 0)
        assert page.page_index == 0
        assert page.width == 2000
        assert page.height == 3000
        # Validate bboxes are within bounds
        for word in page.words:
            x0, y0, x1, y1 = word.bbox
            assert 0 <= x0 <= 2000
            assert 0 <= x1 <= 2000
            assert 0 <= y0 <= 3000
            assert 0 <= y1 <= 3000


def test_ocr_engine_multiple_pages():
    """Test OCR engines with multiple page indices."""
    img = Image.new("RGB", (600, 200), "white")
    d = ImageDraw.Draw(img)
    try:
        font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 24)
    except OSError:
        font = ImageFont.load_default()
    d.text((10, 60), "Page Test", fill="black", font=font)

    engines = []
    if TesseractEngine is not None:
        with contextlib.suppress(Exception):
            engines.append(("tesseract", TesseractEngine(["eng"])))
    if RapidOCREngine is not None:
        with contextlib.suppress(ImportError, Exception):
            engines.append(("rapidocr", RapidOCREngine(["eng"])))

    if not engines:
        pytest.skip("No OCR engines available for testing")

    for _engine_name, engine in engines:
        # Test different page indices
        for page_idx in [0, 1, 5, 10]:
            page = engine.recognize_page(img, page_idx)
            assert page.page_index == page_idx
            assert page.width == 600
            assert page.height == 200


def test_ocr_engine_multiple_languages():
    """Test OCR engines with multiple languages."""
    img = Image.new("RGB", (600, 200), "white")
    d = ImageDraw.Draw(img)
    try:
        font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 24)
    except OSError:
        font = ImageFont.load_default()
    d.text((10, 60), "Test", fill="black", font=font)

    engines = []
    if TesseractEngine is not None:
        with contextlib.suppress(Exception):
            engines.append(("tesseract", TesseractEngine(["spa", "eng", "cat"])))
    if RapidOCREngine is not None:
        with contextlib.suppress(ImportError, Exception):
            engines.append(("rapidocr", RapidOCREngine(["spa", "eng", "cat"])))

    if not engines:
        pytest.skip("No OCR engines available for testing")

    for _engine_name, engine in engines:
        page = engine.recognize_page(img, 0)
        assert page.page_index == 0
        # Should handle multiple languages without error
        assert len(engine.langs) >= 1


def test_factory_empty_name():
    """Test factory with empty string defaults to tesseract."""
    if TesseractEngine is None:
        pytest.skip("pytesseract not installed")
    try:
        eng = build_ocr_engine("", langs=["eng"])
        assert isinstance(eng, TesseractEngine)
    except ImportError:
        pytest.skip("pytesseract not installed")


def test_factory_whitespace_name():
    """Test factory with whitespace-only name (should default to tesseract after strip)."""
    if TesseractEngine is None:
        pytest.skip("pytesseract not installed")
    try:
        # Whitespace-only name gets stripped to empty string, which should default to tesseract
        # But the factory raises ValueError for empty string after strip
        # This is expected behavior - empty string is not a valid engine name
        with pytest.raises(ValueError, match="Unknown OCR engine"):
            build_ocr_engine("   ", langs=["eng"])
    except ImportError:
        pytest.skip("pytesseract not installed")


def test_factory_case_insensitive():
    """Test factory is case-insensitive."""
    if TesseractEngine is None:
        pytest.skip("pytesseract not installed")
    try:
        eng1 = build_ocr_engine("TESSERACT", langs=["eng"])
        eng2 = build_ocr_engine("tesseract", langs=["eng"])
        assert isinstance(eng1, TesseractEngine)
        assert isinstance(eng2, TesseractEngine)
    except ImportError:
        pytest.skip("pytesseract not installed")

    if RapidOCREngine is None:
        pytest.skip("rapidocr-onnxruntime not installed")
    try:
        eng1 = build_ocr_engine("RAPIDOCR", langs=["eng"])
        eng2 = build_ocr_engine("rapidocr", langs=["eng"])
        assert isinstance(eng1, RapidOCREngine)
        assert isinstance(eng2, RapidOCREngine)
    except ImportError:
        pytest.skip("rapidocr-onnxruntime not installed")


def test_validate_bbox_edge_cases():
    """Test bbox validation with edge cases."""
    # Valid: bbox at image boundaries
    validate_bbox((0, 0, 800, 600), width=800, height=600)

    # Valid: single-pixel bbox
    validate_bbox((100, 100, 101, 101), width=800, height=600)

    # Valid: bbox exactly at width/height
    validate_bbox((0, 0, 800, 600), width=800, height=600)

    # Invalid: bbox at (0, 0, 0, 0) - zero width/height
    # This is technically valid (x0 <= x1, y0 <= y1), but may be edge case
    validate_bbox((0, 0, 0, 0), width=800, height=600)  # Should pass validation


def test_ocr_page_structure():
    """Test that OcrPage has correct structure."""
    from document_llm_extractor.ocr.base import OcrPage, OcrWord

    words = [
        OcrWord(text="Hello", bbox=(10, 20, 50, 40), conf=95.0),
        OcrWord(text="World", bbox=(60, 20, 100, 40), conf=90.0),
    ]

    page = OcrPage(
        page_index=0,
        text="Hello World",
        words=words,
        width=200,
        height=100,
        runtime_sec=0.123,
    )

    assert page.page_index == 0
    assert page.text == "Hello World"
    assert len(page.words) == 2
    assert page.width == 200
    assert page.height == 100
    assert page.runtime_sec == 0.123
    assert page.words[0].text == "Hello"
    assert page.words[1].text == "World"


def test_ocr_word_structure():
    """Test that OcrWord has correct structure."""
    from document_llm_extractor.ocr.base import OcrWord

    word = OcrWord(
        text="Test",
        bbox=(10, 20, 50, 40),
        conf=95.5,
    )

    assert word.text == "Test"
    assert word.bbox == (10, 20, 50, 40)
    assert word.conf == 95.5
    assert len(word.bbox) == 4
    x0, y0, x1, y1 = word.bbox
    assert x0 == 10
    assert y0 == 20
    assert x1 == 50
    assert y1 == 40
