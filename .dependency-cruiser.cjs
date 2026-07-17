/** @type {import('dependency-cruiser').IConfiguration} */
module.exports = {
  forbidden: [
    {
      name: "no-circular",
      comment: "Cycles make package ownership and extraction unsafe.",
      severity: "error",
      from: {},
      to: {
        circular: true,
        viaOnly: { dependencyTypesNot: ["type-only"] },
      },
    },
    {
      name: "libraries-not-to-apps",
      comment: "Shared libraries never depend on deployable applications.",
      severity: "error",
      from: { path: "^libs/" },
      to: { path: "^apps/" },
    },
    {
      name: "api-client-only-consumed-by-web",
      comment: "Only the web application consumes the generated API client.",
      severity: "error",
      from: { path: "^(?!apps/web/|libs/api-client/)" },
      to: { path: "^libs/api-client/" },
    },
    {
      name: "web-only-to-api-client",
      comment:
        "The web application reaches backend behavior only through the API client.",
      severity: "error",
      from: { path: "^apps/web/" },
      to: { path: "^libs/(?!api-client/)" },
    },
    {
      name: "web-not-to-generated-client-internals",
      comment:
        "The web application imports the API client's handwritten public entry point.",
      severity: "error",
      from: { path: "^apps/web/" },
      to: { path: "^libs/api-client/src/generated/" },
    },
    {
      name: "not-to-unresolvable",
      comment: "Every import must resolve in the installed workspace.",
      severity: "error",
      from: {},
      to: { couldNotResolve: true },
    },
    {
      name: "no-undeclared-packages",
      comment: "Every external import must appear in the closest package.json.",
      severity: "error",
      from: { path: "^(apps|libs)/" },
      to: {
        dependencyTypes: ["unknown", "npm-no-pkg", "npm-unknown"],
      },
    },
  ],
  options: {
    combinedDependencies: false,
    doNotFollow: { path: "node_modules" },
    exclude: { path: "(^|/)node_modules/" },
    enhancedResolveOptions: {
      conditionNames: ["import", "require", "node", "default", "types"],
      exportsFields: ["exports"],
    },
    tsPreCompilationDeps: true,
  },
};
