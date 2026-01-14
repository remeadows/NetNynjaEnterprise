import { defineConfig } from "tsup";

export default defineConfig({
  entry: ["src/index.ts"],
  format: ["cjs", "esm"],
  // DTS disabled: auth-service is an application, not a library
  // Type checking is done via 'tsc --noEmit' in the typecheck script
  dts: false,
  clean: true,
  sourcemap: true,
  minify: false,
  target: "node20",
  external: ["pg-native"],
});
