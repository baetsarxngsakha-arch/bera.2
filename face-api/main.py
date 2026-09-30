"""NOVA v2 face-quality service scaffold.

This service deliberately does not enroll or identify people yet. Face presence is
not an identity match. Uploaded frames are decoded in memory and never persisted.
"""
from __future__ import annotations

import os
from functools import lru_cache

import cv2
import mediapipe as mp
import numpy as np
from fastapi import FastAPI, File, Header, HTTPException, UploadFile
from pydantic import BaseModel

APP_VERSION = "2.0.0-beta.1"
MAX_IMAGE_BYTES = 6 * 1024 * 1024
TOKEN = os.getenv("FACE_API_TOKEN", "")
MODEL_PATH = os.getenv("FACE_DETECTOR_MODEL_PATH", "")

app = FastAPI(title="NOVA Face Quality API", version=APP_VERSION)


class Health(BaseModel):
    ok: bool
    version: str
    identity_matching: bool
    face_detector_ready: bool


@lru_cache(maxsize=1)
def detector():
    if not MODEL_PATH or not os.path.isfile(MODEL_PATH):
        return None
    options = mp.tasks.vision.FaceDetectorOptions(
        base_options=mp.tasks.BaseOptions(model_asset_path=MODEL_PATH),
        running_mode=mp.tasks.vision.RunningMode.IMAGE,
        min_detection_confidence=0.6,
    )
    return mp.tasks.vision.FaceDetector.create_from_options(options)


def require_service_token(authorization: str | None) -> None:
    if not TOKEN:
        raise HTTPException(status_code=503, detail="FACE_API_TOKEN is not configured")
    if authorization != f"Bearer {TOKEN}":
        raise HTTPException(status_code=401, detail="Unauthorized")


async def decode_upload(image: UploadFile) -> tuple[np.ndarray, bytes]:
    raw = await image.read(MAX_IMAGE_BYTES + 1)
    if len(raw) > MAX_IMAGE_BYTES:
        raise HTTPException(status_code=413, detail="Image exceeds 6 MB limit")
    if image.content_type not in {"image/jpeg", "image/png", "image/webp"}:
        raise HTTPException(status_code=415, detail="Use JPEG, PNG, or WebP")
    decoded = cv2.imdecode(np.frombuffer(raw, dtype=np.uint8), cv2.IMREAD_COLOR)
    if decoded is None:
        raise HTTPException(status_code=400, detail="Image could not be decoded")
    return decoded, raw


@app.get("/health", response_model=Health)
def health() -> Health:
    return Health(
        ok=True,
        version=APP_VERSION,
        identity_matching=False,
        face_detector_ready=detector() is not None,
    )


@app.post("/v1/face/quality")
async def face_quality(
    image: UploadFile = File(...),
    authorization: str | None = Header(default=None),
):
    require_service_token(authorization)
    frame, _raw = await decode_upload(image)
    face_detector = detector()
    if face_detector is None:
        raise HTTPException(
            status_code=503,
            detail="Set FACE_DETECTOR_MODEL_PATH to an approved MediaPipe task model",
        )
    rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    result = face_detector.detect(mp.Image(image_format=mp.ImageFormat.SRGB, data=rgb))
    count = len(result.detections)
    focus = float(cv2.Laplacian(cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY), cv2.CV_64F).var())
    if count != 1:
        return {"ok": True, "quality": False, "face_count": count, "reason": "one_face_required"}
    box = result.detections[0].bounding_box
    face_fraction = (box.width * box.height) / float(frame.shape[0] * frame.shape[1])
    reasons = []
    if face_fraction < 0.08:
        reasons.append("face_too_small")
    if focus < 35:
        reasons.append("image_blurry")
    return {
        "ok": True,
        "quality": not reasons,
        "face_count": count,
        "face_area_fraction": round(face_fraction, 4),
        "focus_measure": round(focus, 2),
        "reasons": reasons,
        "identity_match": "not_implemented",
        "stored": False,
    }


@app.post("/v1/face/verify")
async def face_verify(
    image: UploadFile = File(...),
    authorization: str | None = Header(default=None),
):
    require_service_token(authorization)
    # Consume and validate the upload so the endpoint has the same request contract,
    # but fail closed until a commercially licensed model, PAD, encrypted templates,
    # and signed assertion flow are implemented and reviewed.
    await decode_upload(image)
    raise HTTPException(
        status_code=501,
        detail="Face identity matching and PAD are disabled in this beta",
    )
