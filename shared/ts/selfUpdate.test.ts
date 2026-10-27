import { afterEach, describe, expect, it } from "vitest";
import { INSTALL_ROUTE, INSTALL_TYPE_UPDATE, loaderBackend, requestUpdate } from "./selfUpdate";

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
