import io
import cv2
import numpy as np
import pytesseract
from pytesseract import Output
from typing import List, Tuple, Dict
from PIL import Image, ImageOps
from google.genai import types


def image_to_bytes(img: Image.Image) -> bytes:
    # Convert PIL image to JPEG bytes
    buf = io.BytesIO()
    img.save(buf, format="JPEG", quality=90)
    return buf.getvalue()


def detect_and_correct_rotation(pil_img: Image.Image) -> Image.Image:
    # Detect rotation using Tesseract OSD and correct orientation
    pil_img = ImageOps.exif_transpose(pil_img)
    bgr = cv2.cvtColor(np.array(pil_img), cv2.COLOR_RGB2BGR)

    def rot(bgr_img, a):
        if a == 0: return bgr_img
        if a == 90: return cv2.rotate(bgr_img, cv2.ROTATE_90_COUNTERCLOCKWISE)
        if a == 180: return cv2.rotate(bgr_img, cv2.ROTATE_180)
        if a == 270: return cv2.rotate(bgr_img, cv2.ROTATE_90_CLOCKWISE)

    def osd_angle(pil_img):
        try:
            osd = pytesseract.image_to_osd(pil_img, config="--psm 0", output_type=Output.DICT)
            a = int(osd.get("rotate", 0))
            return a if a in (0, 90, 180, 270) else None
        except Exception:
            return None

    def avg_conf(pil_img):
        try:
            d = pytesseract.image_to_data(pil_img, config="--psm 6", output_type=Output.DICT)
            confs = [int(c) for c in d["conf"] if c not in ("-1", -1)]
            return (sum(confs) / len(confs)) if confs else -1
        except Exception:
            return -1

    angle = osd_angle(pil_img)
    if angle is None:
        scores = {}
        for a in (0, 90, 180, 270):
            test_pil = Image.fromarray(cv2.cvtColor(rot(bgr, a), cv2.COLOR_BGR2RGB))
            scores[a] = avg_conf(test_pil)
        angle = max(scores, key=scores.get)

    if angle and angle != 0:
        print(f"DETECTED ROTAION: {angle}°, ROTAING IMAGE")
        bgr = rot(bgr, angle)

    rotated_pil = Image.fromarray(cv2.cvtColor(bgr, cv2.COLOR_BGR2RGB))
    return rotated_pil


def gemini_vision_ocr(
    images: List[Image.Image],
    client,
    model: str = "gemini-2.5-flash-lite"
) -> Tuple[str, Dict]:
    # Run OCR using Gemini Vision with rotation correction (in-memory only)
    print("USING OCR ")
    pages_text = []
    meta = {"pages": []}

    for i, img in enumerate(images, start=1):
        try:
            img_corrected = detect_and_correct_rotation(img)
            img_bytes = image_to_bytes(img_corrected)
            part = types.Part.from_bytes(data=img_bytes, mime_type="image/jpeg")
            prompt = "Extract all readable text from this image page and return plain text only."
            response = client.models.generate_content(model=model, contents=[prompt, part])
            text = getattr(response, "text", "") or ""
            pages_text.append(text.strip())
            meta["pages"].append({
                "page": i,
                "source": model,
                "rotation_applied": True
            })
        except Exception as e:
            meta["pages"].append({
                "page": i,
                "error": str(e)
            })
            pages_text.append("")
            print(f"OCR FAILED {i}: {e}")

    full_text = "\n\n---PAGE_BREAK---\n\n".join(pages_text)
    return full_text, meta
