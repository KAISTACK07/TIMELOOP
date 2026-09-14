import puppeteer from 'puppeteer';

(async () => {
  const browser = await puppeteer.launch();
  const page = await browser.newPage();
  
  page.on('console', msg => console.log('BROWSER CONSOLE:', msg.text()));
  
  await page.goto('http://localhost:5173', { waitUntil: 'networkidle0' });
  
  // Wait for run to finish (wait for Execution Controller text or a timeout)
  console.log("Running default execution...");
  await page.click('button:has(svg.lucide-play)');
  await new Promise(r => setTimeout(r, 4000));
  
  const timelineInfo = await page.evaluate(() => {
    const nodes = document.querySelectorAll('[data-debug-step]');
    const container = document.querySelector('.absolute.left-0.right-0.flex.pointer-events-none.z-10');
    let containerBox = null;
    let containerStyle = null;
    
    if (container) {
      containerBox = container.getBoundingClientRect();
      const style = window.getComputedStyle(container);
      containerStyle = {
        top: style.top,
        bottom: style.bottom,
        left: style.left,
        right: style.right,
        width: style.width,
        height: style.height,
        position: style.position,
        display: style.display,
      };
    }
    
    const nodeData = Array.from(nodes).slice(0, 3).map(n => {
      const box = n.getBoundingClientRect();
      const style = window.getComputedStyle(n);
      return {
        step: n.getAttribute('data-debug-step'),
        percent: n.getAttribute('data-debug-percent'),
        box: {x: box.x, y: box.y, width: box.width, height: box.height},
        top: style.top,
        left: style.left,
        transform: style.transform,
        opacity: style.opacity
      };
    });
    
    const webTrack = document.querySelector('svg.w-full.h-12');
    let trackBox = null;
    if (webTrack) {
      trackBox = webTrack.getBoundingClientRect();
    }
    
    return {
      nodesFound: nodes.length,
      containerBox,
      containerStyle,
      nodeData,
      trackBox
    };
  });
  
  console.log(JSON.stringify(timelineInfo, null, 2));
  
  await browser.close();
})();
