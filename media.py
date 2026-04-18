"""Tensor <-> bytes conversions for images and audio.

Image tensors follow ComfyUI convention: BHWC, float32, values in [0, 1].
Audio follows ComfyUI AUDIO: {"waveform": (B, C, T) float tensor, "sample_rate": int}.
"""

from __future__ import annotations

import base64
import io
import wave

import torch
from PIL import Image

_JPEG = "JPEG"
_PNG = "PNG"


def _tensor_to_pil(img: torch.Tensor) -> Image.Image:
    """HWC float [0,1] tensor -> PIL Image. Picks RGB or RGBA by channel count."""
    if img.dim() != 3:
        raise ValueError(f"expected HWC tensor, got shape {tuple(img.shape)}")
    arr = (img.clamp(0.0, 1.0) * 255.0).to(torch.uint8).cpu().numpy()
    channels = arr.shape[-1]
    if channels == 4:
        return Image.fromarray(arr, mode="RGBA")
    if channels == 3:
        return Image.fromarray(arr, mode="RGB")
    if channels == 1:
        return Image.fromarray(arr[..., 0], mode="L")
    raise ValueError(f"unsupported channel count: {channels}")


def _maybe_resize(img: Image.Image, resize_max: int | None) -> Image.Image:
    if resize_max is None or resize_max <= 0:
        return img
    longest = max(img.size)
    if longest <= resize_max:
        return img
    scale = resize_max / longest
    new_size = (max(1, int(round(img.size[0] * scale))), max(1, int(round(img.size[1] * scale))))
    return img.resize(new_size, Image.Resampling.LANCZOS)


def tensor_to_jpeg_bytes(
    img: torch.Tensor,
    quality: int = 85,
    resize_max: int | None = None,
) -> bytes:
    """Encode a single HWC float tensor as JPEG bytes."""
    pil = _tensor_to_pil(img)
    if pil.mode == "RGBA":
        pil = pil.convert("RGB")
    pil = _maybe_resize(pil, resize_max)
    buf = io.BytesIO()
    pil.save(buf, format=_JPEG, quality=quality, optimize=False)
    return buf.getvalue()


def _iter_batch(t: torch.Tensor):
    if t.dim() == 3:
        yield t
    elif t.dim() == 4:
        for i in range(t.shape[0]):
            yield t[i]
    else:
        raise ValueError(f"expected 3D (HWC) or 4D (BHWC) tensor, got shape {tuple(t.shape)}")


def tensor_batch_to_jpeg_bytes(
    batch: torch.Tensor,
    quality: int = 85,
    resize_max: int | None = None,
) -> list[bytes]:
    """Encode each image in a BHWC (or HWC) tensor as JPEG bytes."""
    return [tensor_to_jpeg_bytes(img, quality=quality, resize_max=resize_max) for img in _iter_batch(batch)]


def tensor_batch_to_png_bytes(
    batch: torch.Tensor,
    resize_max: int | None = None,
) -> list[bytes]:
    """Encode each image as PNG (preserves alpha)."""
    results: list[bytes] = []
    for img in _iter_batch(batch):
        pil = _maybe_resize(_tensor_to_pil(img), resize_max)
        buf = io.BytesIO()
        pil.save(buf, format=_PNG, optimize=False)
        results.append(buf.getvalue())
    return results


def tensor_to_data_url_list(
    batch: torch.Tensor,
    quality: int = 85,
    resize_max: int | None = None,
) -> list[str]:
    """Encode a batch as `data:image/jpeg;base64,...` URLs (OpenAI chat format)."""
    jpegs = tensor_batch_to_jpeg_bytes(batch, quality=quality, resize_max=resize_max)
    return [f"data:image/jpeg;base64,{base64.b64encode(j).decode('ascii')}" for j in jpegs]


def audio_dict_to_wav_bytes(audio: dict) -> bytes:
    """Encode a ComfyUI AUDIO dict as 16-bit PCM WAV bytes."""
    waveform = audio["waveform"]
    sample_rate = int(audio["sample_rate"])
    if not isinstance(waveform, torch.Tensor):
        raise TypeError("audio['waveform'] must be a torch.Tensor")
    # ComfyUI shape is (B, C, T); drop batch if present.
    if waveform.dim() == 3:
        waveform = waveform[0]
    if waveform.dim() != 2:
        raise ValueError(f"expected (B,C,T) or (C,T) waveform, got shape {tuple(waveform.shape)}")
    channels = waveform.shape[0]
    # Interleave channels (sample-major), clamp, quantize to int16.
    pcm = (waveform.clamp(-1.0, 1.0) * 32767.0).to(torch.int16).cpu().numpy().T.tobytes(order="C")
    buf = io.BytesIO()
    with wave.open(buf, "wb") as wf:
        wf.setnchannels(channels)
        wf.setsampwidth(2)
        wf.setframerate(sample_rate)
        wf.writeframes(pcm)
    return buf.getvalue()
