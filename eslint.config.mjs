import { defineConfig, globalIgnores } from "eslint/config";
import nextVitals from "eslint-config-next/core-web-vitals";
import nextTs from "eslint-config-next/typescript";

const webFiles = ["apps/web/**/*.{js,jsx,ts,tsx}"];
const typescriptFiles = ["apps/web/**/*.{ts,tsx}", "libs/api-client/**/*.ts"];

export default defineConfig([
  ...nextVitals.map((configuration) => ({ ...configuration, files: webFiles })),
  ...nextTs.map((configuration) => ({
    ...configuration,
    files: typescriptFiles,
  })),
  globalIgnores([
    "**/.next/**",
    "**/dist/**",
    "**/node_modules/**",
    "**/src/generated/**",
    "**/next-env.d.ts",
  ]),
]);
