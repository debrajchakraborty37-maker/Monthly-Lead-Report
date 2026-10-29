const { chromium } = require('playwright');
(async () => {
  const [html, png] = process.argv.slice(2);
  const b = await chromium.launch();
  const p = await b.newPage({ viewport: { width: 1578, height: 912 } });
  await p.goto('file://' + require('path').resolve(html));
  await p.screenshot({ path: png, fullPage: true });
  await b.close();
})();
