"""Compare a rendered locked soundtrack against the matching source interval."""

from __future__ import annotations

import argparse
import json

import av
import numpy as np


def decode(path: str, rate: int = 44100) -> np.ndarray:
    chunks = []
    with av.open(path) as container:
        stream = container.streams.audio[0]
        resampler = av.AudioResampler(format="fltp", layout="mono", rate=rate)
        for frame in container.decode(stream):
            converted = resampler.resample(frame)
            for item in converted if isinstance(converted, list) else [converted]:
                if item is not None:
                    chunks.append(item.to_ndarray().reshape(-1).astype(np.float32))
        converted = resampler.resample(None)
        for item in converted if isinstance(converted, list) else ([converted] if converted is not None else []):
            chunks.append(item.to_ndarray().reshape(-1).astype(np.float32))
    return np.concatenate(chunks)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("source")
    parser.add_argument("render")
    parser.add_argument("--frames", type=int, required=True)
    args = parser.parse_args()
    rate = 44100
    expected = round(args.frames / 24 * rate)
    source = decode(args.source, rate)[:expected]
    render = decode(args.render, rate)

    # AAC may add a short encoder delay. Estimate it at 4 kHz, then report
    # waveform similarity after alignment and an optimal scalar gain.
    stride = max(1, rate // 4000)
    left, right = source[::stride], render[::stride]
    limit = round(0.25 * rate / stride)
    correlations = []
    for lag in range(-limit, limit + 1):
        a, b = (left[-lag:], right[: len(left) + lag]) if lag < 0 else (left[: len(right) - lag], right[lag:])
        count = min(len(a), len(b))
        correlations.append(float(np.dot(a[:count], b[:count])))
    lag = int(np.argmax(correlations) - limit) * stride
    a, b = (source[-lag:], render[: len(source) + lag]) if lag < 0 else (source[: len(render) - lag], render[lag:])
    count = min(len(a), len(b))
    a, b = a[:count], b[:count]
    gain = float(np.dot(a, b) / max(1e-12, np.dot(a, a)))
    correlation = float(np.corrcoef(a, b)[0, 1])
    nrmse = float(np.sqrt(np.mean((b - gain * a) ** 2)) / max(1e-12, np.sqrt(np.mean(b ** 2))))
    segment_samples = round((34 / 24) * rate)
    segment_correlations = []
    for start in range(0, count, segment_samples):
        aa, bb = a[start : start + segment_samples], b[start : start + segment_samples]
        if len(aa) > rate // 2:
            segment_correlations.append(float(np.corrcoef(aa, bb)[0, 1]))
    print(json.dumps({
        "source_samples": int(len(source)), "render_samples": int(len(render)),
        "expected_seconds": args.frames / 24, "render_seconds": len(render) / rate,
        "alignment_lag_samples": lag, "correlation": correlation,
        "gain": gain, "normalized_rmse": nrmse,
        "timeline_chunk_correlations": segment_correlations,
    }, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
