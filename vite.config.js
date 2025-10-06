import { defineConfig } from "vite";
import { resolve } from "path";
import { readdirSync } from "fs";

const jsDir = resolve(__dirname, "assets/js");
const inputs = Object.fromEntries(
  readdirSync(jsDir)
    .filter((file) => file.endsWith(".js"))
    .map((file) => [file.replace(".js", ""), resolve(jsDir, file)])
);

export default defineConfig({
  build: {
    outDir: "static",
    rollupOptions: {
      input: inputs,
      output: {
        entryFileNames: (chunk) => `js/[name].js`,
        assetFileNames: (assetInfo) => {
          if (assetInfo.name && assetInfo.name.endsWith(".css")) {
            return `css/[name].css`;
          }
          return `assets/[name][extname]`;
        },
      },
    },
  },
});
