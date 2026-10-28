import { afterEach, describe, expect, it } from "vitest";
import { INSTALL_ROUTE, INSTALL_TYPE_UPDATE, checkedLine, loaderBackend, requestUpdate, updateStatus } from "./selfUpdate";

const URL = "https://github.com/example/plugin/releases/latest/download/plugin.zip";

describe("requestUpdate", () => {
  it("asks Decky's installer for an update with the plugin.json name", async () => {
    const calls: unknown[][] = [];
    const ok = await requestUpdate(URL, "Tuning Advisor", "0.7.0", {
      call: async (...args) => {
        calls.push(args);
      },
    });
    expect(ok).toBe(true);
    expect(calls).toEqual([[INSTALL_ROUTE, URL, "Tuning Advisor", "0.7.0", "", INSTALL_TYPE_UPDATE]]);
    expect(INSTALL_ROUTE).toBe("utilities/install_plugin");
    expect(INSTALL_TYPE_UPDATE).toBe(2);
  });

  it("reports failure when the loader refuses", async () => {
    const ok = await requestUpdate(URL, "Tuning Advisor", "0.7.0", {
      call: async () => {
        throw new Error("no route");
      },
    });
    expect(ok).toBe(false);
  });

  it("reports failure with no loader, so the link is shown instead", async () => {
    expect(await requestUpdate(URL, "Tuning Advisor", "0.7.0", null)).toBe(false);
  });

  it("refuses an empty name, which Decky could not match", async () => {
    let called = false;
    const ok = await requestUpdate(URL, "", "0.7.0", {
      call: async () => {
        called = true;
      },
    });
    expect(ok).toBe(false);
    expect(called).toBe(false);
  });
});

describe("loaderBackend", () => {
  afterEach(() => {
    delete (globalThis as { DeckyBackend?: unknown }).DeckyBackend;
  });

  it("finds Decky's backend connection", () => {
    const backend = { call: async () => undefined };
    (globalThis as { DeckyBackend?: unknown }).DeckyBackend = backend;
    expect(loaderBackend()).toBe(backend);
  });

  it("returns null when it is missing or has no call", () => {
    expect(loaderBackend()).toBeNull();
    (globalThis as { DeckyBackend?: unknown }).DeckyBackend = {};
    expect(loaderBackend()).toBeNull();
  });
});

describe("updateStatus", () => {
  const base = { current: "0.3.2", latest: "0.3.2", available: false, install_url: URL };

  it("says what the last check found", () => {
    expect(updateStatus({ ...base, latest: "0.4.0", available: true }, false)).toBe("Version 0.4.0 is available.");
    expect(updateStatus(base, false)).toBe("You have the latest version.");
    expect(updateStatus(base, true)).toBe("Checking GitHub for a new release.");
  });

  it("never claims the latest version when the check failed or never ran", () => {
    expect(updateStatus({ ...base, latest: "0.3.2", check_failed: true }, false)).toBe(
      "Could not reach GitHub. Try again later.",
    );
    expect(updateStatus({ ...base, latest: null }, false)).toBe("Not checked yet.");
    expect(updateStatus(null, false)).toBe("Not checked yet.");
  });
});

describe("checkedLine", () => {
  it("gives a short age", () => {
    const now = 1_000_000;
    expect(checkedLine(null, now)).toBe("");
    expect(checkedLine(now - 10, now)).toBe("Checked just now.");
    expect(checkedLine(now - 600, now)).toBe("Checked 10 min ago.");
    expect(checkedLine(now - 7200, now)).toBe("Checked 2 h ago.");
    expect(checkedLine(now - 3 * 86400, now)).toBe("Checked 3 days ago.");
  });
});
