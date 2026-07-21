import { spawnSync } from "node:child_process";
import { createHash } from "node:crypto";
import { mkdtemp, readdir, readFile, rm } from "node:fs/promises";
import { tmpdir } from "node:os";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";

const packageDirectory = join(dirname(fileURLToPath(import.meta.url)), "..");
const generatedDirectory = join(packageDirectory, "src", "generated");

async function snapshot(directory) {
  const entries = await readdir(directory, {
    recursive: true,
    withFileTypes: true,
  });
  const files = entries
    .filter((entry) => entry.isFile())
    .map((entry) => join(entry.parentPath, entry.name))
    .sort();

  return Promise.all(
    files.map(async (file) => ({
      file: file.slice(directory.length + 1),
      hash: createHash("sha256")
        .update(await readFile(file))
        .digest("hex"),
    })),
  );
}

const temporaryDirectory = await mkdtemp(join(tmpdir(), "lhf-api-client-"));
let generatedClientIsStale = false;

try {
  const generation = spawnSync(
    "pnpm",
    ["exec", "openapi-ts", "--output", temporaryDirectory],
    {
      cwd: packageDirectory,
      stdio: "inherit",
    },
  );

  if (generation.error) {
    throw generation.error;
  }
  if (generation.status !== 0) {
    throw new Error(
      `openapi-ts exited with status ${generation.status ?? "unknown"}`,
    );
  }

  const [current, expected] = await Promise.all([
    snapshot(generatedDirectory),
    snapshot(temporaryDirectory),
  ]);
  generatedClientIsStale = JSON.stringify(current) !== JSON.stringify(expected);
} finally {
  await rm(temporaryDirectory, { force: true, recursive: true });
}

if (generatedClientIsStale) {
  console.error(
    "Generated API client is stale. Run `pnpm --filter @lhf/api-client generate` and commit the result.",
  );
  process.exit(1);
}
