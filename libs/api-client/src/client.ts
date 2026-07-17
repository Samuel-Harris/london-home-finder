import { client } from "./generated/client.gen";

export const DEFAULT_API_BASE_URL = "http://localhost:8000";

export interface ApiClientOptions {
  baseUrl?: string;
}

export function resolveApiBaseUrl(baseUrl?: string): string {
  const configuredUrl = baseUrl?.trim();
  return configuredUrl || DEFAULT_API_BASE_URL;
}

export function configureApiClient(options: ApiClientOptions = {}) {
  client.setConfig({ baseUrl: resolveApiBaseUrl(options.baseUrl) });
  return client;
}
