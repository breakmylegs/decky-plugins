import { describe, expect, it } from "vitest";
import { describeStep, formatBytes, formatDuration, formatPercent, formatSpeed, truncate } from "./format";
import { resetToasts, shouldToast } from "./toastOnce";

describe("format", () => {
  it("formats bytes in SI units", () => {
    expect(formatBytes(0)).toBe("0 B");
    expect(formatBytes(999)).toBe("999 B");
    expect(formatBytes(1500)).toBe("1.50 KB");
    expect(formatBytes(12_300_000)).toBe("12.3 MB");
    expect(formatBytes(4_000_000_000)).toBe("4.00 GB");
    expect(formatBytes(-1)).toBe("-");
    expect(formatBytes(null)).toBe("-");
  });

  it("formats speeds", () => {
    expect(formatSpeed(0)).toBe("0 B/s");
    expect(formatSpeed(2_000_000)).toBe("2.00 MB/s");
  });

  it("formats durations and treats bad input as no ETA", () => {
    expect(formatDuration(45)).toBe("45s");
    expect(formatDuration(600)).toBe("10m 0s");
    expect(formatDuration(3_700)).toBe("1h 1m");
    expect(formatDuration(90_000)).toBe("1d 1h");
    expect(formatDuration(null)).toBe("No ETA");
    expect(formatDuration(8_640_000 * 2)).toBe("No ETA");
  });

  it("never rounds a partial download up to 100%", () => {
    expect(formatPercent(0.995)).toBe("99%");
    expect(formatPercent(1)).toBe("100%");
    expect(formatPercent(0.001)).toBe("<1%");
    expect(formatPercent(0.42)).toBe("42%");
  });

  it("truncates long names", () => {
    expect(truncate("abcdef", 5)).toBe("ab...");
    expect(truncate("abc", 5)).toBe("abc");
  });

  it("describes connection test steps", () => {
    expect(describeStep({ step: "auth", ok: false, detail: "Sign-in failed." })).toBe("Sign-in: Failed. Sign-in failed.");
    expect(describeStep({ step: "url", ok: true, detail: "" })).toBe("Address: OK");
  });
});

describe("toastOnce", () => {
  it("toasts a key once per window", () => {
    resetToasts();
    expect(shouldToast("a", 0)).toBe(true);
    expect(shouldToast("a", 1000)).toBe(false);
    expect(shouldToast("b", 1000)).toBe(true);
    expect(shouldToast("a", 11 * 60 * 1000)).toBe(true);
  });
});
