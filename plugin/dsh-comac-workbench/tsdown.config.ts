import { defineConfig } from "tsdown";

// Lazy-CJS factory 契约（T9 定论）：产物首行必须注册 factory，副作用全在物化期。
// react 由宿主静态表提供（neverBundle）；其余依赖一律打进包（alwaysBundle——
// tsdown 默认 externalize dependencies，不写会得到 2KB 假产物，T5 实验室教训）。
export default defineConfig({
  entry: ["src/client.jsx"],
  format: ["cjs"],
  platform: "browser",
  deps: { neverBundle: [/^react(\/.*)?$/], alwaysBundle: [/^(?!react($|\/))/] },
  outDir: "lib",
  clean: false, // 手写 host 半 lib/index.js 与产物同目录——绝不清理
  minify: true,
  sourcemap: false,
  // DSH loader 只服务单文件 /plugins/<id>/client.js —— 必须关闭代码分割，
  // 一切（含 echarts 动态 import 的模块）打进单一 entry。
  outputOptions: {
    // 动态 import（ensureECharts 的 echarts 按需加载）全部内联——单文件契约
    inlineDynamicImports: true,
    entryFileNames: "client.js",
    chunkFileNames: "chunk-[hash].cjs",
    banner: [
      `window.__ModuleLoader__.load({`,
      `\tid: "dsh-comac-workbench",`,
      `\tfactory: (require) => {`,
      `\t\tvar module = { exports: {} };`,
      `\t\tvar exports = module.exports;`,
    ].join("\n"),
    footer: [`\t\treturn module.exports;`, `}`, `});`, ``].join("\n"),
  },
});
