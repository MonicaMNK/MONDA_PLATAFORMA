// RNF-06: Lighthouse accesibilidad >= 90
// Ejecutar: npx lighthouse http://localhost:8001 --output json --output-path reports/lighthouse-20261109.json --preset desktop --only-categories accessibility --chrome-flags="--headless --no-sandbox"

const lighthouse = require('lighthouse');
const chromeLauncher = require('chrome-launcher');

(async () => {
  const chrome = await chromeLauncher.launch({
    chromeFlags: ['--headless', '--no-sandbox', '--disable-gpu'],
  });
  const options = {
    logLevel: 'info',
    output: 'json',
    onlyCategories: ['accessibility'],
    port: chrome.port,
  };
  const runnerResult = await lighthouse('http://localhost:8001', options);
  const reportJson = runnerResult.lhr;
  const accessibilityScore = Math.round(reportJson.categories.accessibility.score * 100);
  console.log(`Lighthouse accesibilidad: ${accessibilityScore}`);
  console.log(`Criterio RNF-06: >= 90 => ${accessibilityScore >= 90 ? 'CUMPLE' : 'NO CUMPLE'}`);
  await chrome.kill();
  process.exit(accessibilityScore >= 90 ? 0 : 1);
})();
