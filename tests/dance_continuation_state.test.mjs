import test from "node:test";
import assert from "node:assert/strict";

import { normalizeDanceContinuation } from "../js/dance_continuation_state.mjs";


test("old workflow loads with dance continuation disabled", () => {
  assert.deepEqual(normalizeDanceContinuation(undefined), {
    enabled: false,
    contextFrames: 24,
    taperEnabled: false,
    taperFrames: 12,
    startStrength: 1,
    endStrength: 0,
    contextNoiseEnabled: false,
    contextNoiseStrength: 0,
    contextNoiseTaperFrames: 4,
  });
});

test("serialized dance controls are normalized without changing intent", () => {
  assert.deepEqual(normalizeDanceContinuation({
    enabled: true,
    contextFrames: 30,
    taperEnabled: true,
    taperFrames: 18,
    startStrength: 0.8,
    endStrength: 0.2,
    contextNoiseEnabled: true,
    contextNoiseStrength: 0.3,
    contextNoiseTaperFrames: 4,
  }), {
    enabled: true,
    contextFrames: 30,
    taperEnabled: true,
    taperFrames: 18,
    startStrength: 0.8,
    endStrength: 0.2,
    contextNoiseEnabled: true,
    contextNoiseStrength: 0.3,
    contextNoiseTaperFrames: 4,
  });
});

test("invalid UI numbers clamp to backend-valid ranges", () => {
  assert.deepEqual(normalizeDanceContinuation({
    contextFrames: -4,
    taperFrames: 99,
    startStrength: 2,
    endStrength: -1,
    contextNoiseStrength: 2,
    contextNoiseTaperFrames: 99,
  }), {
    enabled: false,
    contextFrames: 0,
    taperEnabled: false,
    taperFrames: 0,
    startStrength: 1,
    endStrength: 0,
    contextNoiseEnabled: false,
    contextNoiseStrength: 1,
    contextNoiseTaperFrames: 0,
  });
});
