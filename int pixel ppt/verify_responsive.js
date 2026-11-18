const { chromium } = require("C:/Users/Percy/OneDrive/Desktop/Job record/Classroom/LingLam_3D/.opencode/skills/zan-html-to-ppt/scripts/node_modules/playwright-core");
const fs = require("fs");
const path = require("path");

(async () => {
  const outDir = path.join(__dirname, "html_preview");
  fs.mkdirSync(outDir, { recursive: true });
  const browser = await chromium.launch({
    headless: true,
    executablePath: "C:/Users/Percy/AppData/Local/ms-playwright/chromium-1223/chrome-win64/chrome.exe",
  });
  for (const [name, w, h] of [["720p", 1280, 720], ["phone", 390, 844]]) {
    const page = await browser.newPage({ viewport: { width: w, height: h }, deviceScaleFactor: 1 });
    await page.goto("http://127.0.0.1:8765/Pixel_Isle_INT4096.html", { waitUntil: "networkidle" });
    await page.evaluate(() => document.fonts.ready);
    await page.waitForTimeout(1600);
    const info = await page.evaluate(() => ({
      transform: document.getElementById("deckStage").style.transform,
      scrollWidth: document.documentElement.scrollWidth,
      innerWidth: window.innerWidth,
      stageRect: (() => { const r = document.getElementById("deckStage").getBoundingClientRect(); return { x: r.x, y: r.y, w: r.width, h: r.height }; })(),
    }));
    console.log(name, JSON.stringify(info));
    await page.screenshot({ path: path.join(outDir, `responsive-${name}.png`) });
    await page.close();
  }
  await browser.close();
})();
