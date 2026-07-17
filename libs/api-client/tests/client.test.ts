import { beforeEach, describe, expect, it, vi } from "vitest";

const { client } = vi.hoisted(() => ({
  client: {
    setConfig: vi.fn(),
  },
}));

vi.mock("../src/generated/client.gen", () => ({ client }));

import {
  configureApiClient,
  DEFAULT_API_BASE_URL,
  resolveApiBaseUrl,
} from "@lhf/api-client";

describe("API client configuration", () => {
  beforeEach(() => {
    client.setConfig.mockClear();
  });

  it("uses the local API by default", () => {
    expect(resolveApiBaseUrl()).toBe(DEFAULT_API_BASE_URL);
    expect(configureApiClient()).toBe(client);
    expect(client.setConfig).toHaveBeenCalledWith({
      baseUrl: DEFAULT_API_BASE_URL,
    });
  });

  it("trims and applies an explicit API base URL", () => {
    expect(configureApiClient({ baseUrl: "  http://localhost:8123/  " })).toBe(
      client,
    );
    expect(client.setConfig).toHaveBeenCalledWith({
      baseUrl: "http://localhost:8123/",
    });
  });
});
