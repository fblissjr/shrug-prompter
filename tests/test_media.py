"""Tests for codecs.py — tensor <-> bytes conversions."""

import base64
import io

import pytest
import torch
from PIL import Image

from media import (
    audio_dict_to_wav_bytes,
    tensor_batch_to_jpeg_bytes,
    tensor_batch_to_png_bytes,
    tensor_to_data_url_list,
    tensor_to_jpeg_bytes,
)


def _rand_image(b: int = 1, h: int = 64, w: int = 64, c: int = 3) -> torch.Tensor:
    return torch.rand(b, h, w, c, dtype=torch.float32)


class TestTensorToJpegBytes:
    def test_single_image_returns_bytes(self):
        img = _rand_image(1, 32, 32, 3)
        data = tensor_to_jpeg_bytes(img[0])
        assert isinstance(data, bytes)
        assert data[:3] == b"\xff\xd8\xff"  # JPEG magic

    def test_decodable_by_pil(self):
        img = _rand_image(1, 32, 32, 3)
        data = tensor_to_jpeg_bytes(img[0])
        decoded = Image.open(io.BytesIO(data))
        assert decoded.size == (32, 32)
        assert decoded.mode == "RGB"

    def test_quality_affects_size(self):
        img = _rand_image(1, 128, 128, 3)
        low = tensor_to_jpeg_bytes(img[0], quality=20)
        high = tensor_to_jpeg_bytes(img[0], quality=95)
        assert len(low) < len(high)

    def test_resize_max_shrinks_large_image(self):
        img = _rand_image(1, 1024, 1024, 3)
        data = tensor_to_jpeg_bytes(img[0], resize_max=256)
        decoded = Image.open(io.BytesIO(data))
        assert max(decoded.size) == 256

    def test_resize_max_preserves_small(self):
        img = _rand_image(1, 100, 50, 3)
        data = tensor_to_jpeg_bytes(img[0], resize_max=512)
        decoded = Image.open(io.BytesIO(data))
        assert decoded.size == (50, 100)

    def test_resize_max_preserves_aspect_ratio(self):
        img = _rand_image(1, 800, 400, 3)
        data = tensor_to_jpeg_bytes(img[0], resize_max=200)
        decoded = Image.open(io.BytesIO(data))
        # Original 800x400 (h x w); longest=800; ratio 200/800=0.25; w=100, h=200
        assert decoded.size == (100, 200)


class TestTensorBatchToJpegBytes:
    def test_batch_returns_list(self):
        imgs = _rand_image(3, 32, 32, 3)
        result = tensor_batch_to_jpeg_bytes(imgs)
        assert len(result) == 3
        assert all(isinstance(b, bytes) for b in result)

    def test_empty_batch(self):
        imgs = torch.zeros(0, 32, 32, 3)
        result = tensor_batch_to_jpeg_bytes(imgs)
        assert result == []

    def test_three_dim_tensor_treated_as_single(self):
        # PIL-style HWC without batch dim
        img = torch.rand(32, 32, 3)
        result = tensor_batch_to_jpeg_bytes(img)
        assert len(result) == 1


class TestTensorBatchToPngBytes:
    def test_rgba_preserved(self):
        imgs = _rand_image(1, 32, 32, 4)
        result = tensor_batch_to_png_bytes(imgs)
        decoded = Image.open(io.BytesIO(result[0]))
        assert decoded.mode == "RGBA"

    def test_png_magic(self):
        imgs = _rand_image(1, 32, 32, 3)
        data = tensor_batch_to_png_bytes(imgs)[0]
        assert data[:8] == b"\x89PNG\r\n\x1a\n"


class TestTensorToDataUrlList:
    def test_produces_valid_data_urls(self):
        imgs = _rand_image(2, 32, 32, 3)
        urls = tensor_to_data_url_list(imgs)
        assert len(urls) == 2
        for url in urls:
            assert url.startswith("data:image/jpeg;base64,")
            b64_part = url.split(",", 1)[1]
            base64.b64decode(b64_part)  # doesn't raise


class TestAudioDictToWavBytes:
    def test_mono_wav(self):
        audio = {
            "waveform": torch.randn(1, 1, 16000, dtype=torch.float32),
            "sample_rate": 16000,
        }
        data = audio_dict_to_wav_bytes(audio)
        assert data[:4] == b"RIFF"
        assert data[8:12] == b"WAVE"

    def test_stereo_wav(self):
        audio = {
            "waveform": torch.randn(1, 2, 16000, dtype=torch.float32),
            "sample_rate": 44100,
        }
        data = audio_dict_to_wav_bytes(audio)
        assert data[:4] == b"RIFF"

    def test_strips_batch_dim(self):
        # ComfyUI audio format is (B, C, T) — B is typically 1
        audio = {
            "waveform": torch.randn(1, 1, 8000),
            "sample_rate": 8000,
        }
        data = audio_dict_to_wav_bytes(audio)
        # WAV header + 8000 samples * 2 bytes = ~16044 bytes
        assert len(data) > 16000
        assert len(data) < 17000

    def test_invalid_audio_raises(self):
        with pytest.raises((KeyError, ValueError, TypeError)):
            audio_dict_to_wav_bytes({})
