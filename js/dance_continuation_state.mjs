export const DEFAULT_DANCE_CONTINUATION = Object.freeze({
  enabled: false,
  contextFrames: 24,
  taperEnabled: false,
  taperFrames: 12,
  startStrength: 1,
  endStrength: 0,
});

const finiteNumber = (value, fallback) => {
  const parsed = Number(value);
  return Number.isFinite(parsed) ? parsed : fallback;
};

const clamp = (value, low, high) => Math.max(low, Math.min(high, value));

export function normalizeDanceContinuation(raw) {
  const values = raw && typeof raw === "object" ? raw : {};
  const contextFrames = Math.max(
    0,
    Math.floor(finiteNumber(values.contextFrames, DEFAULT_DANCE_CONTINUATION.contextFrames)),
  );
  return {
    enabled: values.enabled === true,
    contextFrames,
    taperEnabled: values.taperEnabled === true,
    taperFrames: clamp(
      Math.floor(finiteNumber(values.taperFrames, DEFAULT_DANCE_CONTINUATION.taperFrames)),
      0,
      contextFrames,
    ),
    startStrength: clamp(
      finiteNumber(values.startStrength, DEFAULT_DANCE_CONTINUATION.startStrength),
      0,
      1,
    ),
    endStrength: clamp(
      finiteNumber(values.endStrength, DEFAULT_DANCE_CONTINUATION.endStrength),
      0,
      1,
    ),
  };
}
