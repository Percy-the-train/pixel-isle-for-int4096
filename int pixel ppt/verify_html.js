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
  const page = await browser.newPage({ viewport: { width: 1920, height: 1080 }, deviceScaleFactor: 1 });
  const errors = [];
  page.on("console", (msg) => { if (msg.type() === "error") errors.push(msg.text()); });
  page.on("pageerror", (err) => errors.push(String(err)));
  await page.goto("http://127.0.0.1:8765/Pixel_Isle_INT4096.html", { waitUntil: "networkidle" });
  await page.evaluate(() => document.fonts.ready);
  await page.addStyleTag({ content: `
    *, *::before, *::after { animation: none !important; transition: none !important; }
    .reveal { opacity: 1 !important; transform: none !important; }
    .type { width: 10ch !important; border-right: none !important; }
  ` });

  const total = await page.evaluate(() => document.querySelectorAll(".slide").length);
  console.log("slides", total);
  for (let i = 0; i < total; i++) {
    await page.evaluate((i) => window.deck.show(i), i);
    await page.waitForTimeout(180);
    await page.screenshot({ path: path.join(outDir, `slide-${String(i + 1).padStart(2, "0")}.png`) });
  }

  const report = await page.evaluate(() => {
    const slides = [...document.querySelectorAll(".slide")];
    return slides.map((slide, i) => {
      const sr = slide.getBoundingClientRect();
      const problems = [];
      slide.querySelectorAll("h1,h2,h3,p,li,td,th,dd,.stat-number,.slide-title,.banner,.metric,.chip,.fig,.drop").forEach((el) => {
        const r = el.getBoundingClientRect();
        if (r.width === 0 || r.height === 0) return;
        if (r.left < sr.left - 2 || r.right > sr.right + 2 || r.top < sr.top - 2 || r.bottom > sr.bottom + 2) {
          problems.push(`${el.tagName.toLowerCase()}:${(el.textContent || "").slice(0, 30)}`);
        }
        if (el.scrollHeight > el.clientHeight + 4 && getComputedStyle(el).overflow !== "visible") {
          problems.push(`overflow:${(el.textContent || "").slice(0, 30)}`);
        }
      });
      return { slide: i + 1, problems: [...new Set(problems)].slice(0, 8) };
    });
  });
  console.log(JSON.stringify(report, null, 2));
  console.log("console errors", errors);
  await browser.close();
})();
