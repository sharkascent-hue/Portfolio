// Records the hero (top 1440x810) of each site as smooth frames by stepping a virtual clock:
// rAF, timers, performance.now/Date, CSS/Web animations and <video> all advance exactly 1/FPS per frame.
import pw from '/opt/node-tools/node_modules/playwright/index.js'; const { chromium } = pw;
import fs from 'fs';
const FPS = 24, SECONDS = +(process.env.SECS || 7.5);
const SITES = {
  reply: 'http://localhost:8765/reply/', allleaders: 'https://allleadersfollow.vercel.app/index.html', mejia: 'https://mejia-psi.vercel.app/',
  bigbear: 'https://www.bigbearplanetariums.ie/', fivestar: 'https://www.5starhomeimprovements.ie/', attics: 'https://www.atticsrus.ie/',
  diamond: 'https://www.diamondflooringdublin.ie/', alfitness: 'https://www.alfitnessandcoaching.com/home', omni: 'https://www.omnirenovations.ie/home',
};
const WAIT = { alfitness: 7000, reply: 18000 };   // ms to let each site settle before recording (default 12000)
const PRE = { reply: 4 };                         // seconds of clock to run past (an intro splash) before saving frames
const SWAP = { 'atticsrus.ie/video.mp4': 'attics', 'vid/vid6.mp4': 'diamond', '0fddad46-c769-40bb-8d19-29523d1cbafa.mp4': 'mejia' };
const shim = () => {
  // one virtual clock from the moment the page starts: a pump drives it in real time while the page loads,
  // then the recorder steps it exactly 1/FPS per frame. rAF, timers, performance.now and Date all read it.
  const R = { now: performance.now.bind(performance), dnow: Date.now, raf: window.requestAnimationFrame.bind(window), st: window.setTimeout.bind(window) };
  const base = R.now(), dbase = R.dnow(); let vt = 0, manual = false, id = 1; const rafs = new Map(), timers = new Map();
  performance.now = () => base + vt; Date.now = () => dbase + vt;
  window.requestAnimationFrame = (cb) => { const i = ++id; rafs.set(i, cb); return i; };
  window.cancelAnimationFrame = (i) => { rafs.delete(i); };
  window.setTimeout = (cb, ms = 0, ...a) => { const i = ++id; timers.set(i, { cb, at: vt + (+ms || 0), a }); return i; };
  window.setInterval = (cb, ms = 0, ...a) => { const i = ++id; timers.set(i, { cb, at: vt + (+ms || 0), every: Math.max(+ms || 0, 4), a }); return i; };
  window.clearTimeout = window.clearInterval = (i) => { timers.delete(i); };
  const run = (to) => {   // advance the clock to `to` ms, firing timers in order, then one animation frame
    for (let guard = 0; guard < 5000; guard++) {
      let next = null; for (const [i, t] of timers) if (t.at <= to && (!next || t.at < next[1].at)) next = [i, t];
      if (!next) break; const [i, t] = next; vt = Math.max(vt, t.at);
      if (t.every) t.at += t.every; else timers.delete(i);
      try { typeof t.cb === 'function' ? t.cb(...t.a) : eval(t.cb); } catch (e) {}
    }
    vt = to; const cbs = [...rafs.values()]; rafs.clear(); for (const cb of cbs) { try { cb(base + vt); } catch (e) {} }
  };
  const pump = () => { if (!manual) { run(R.now() - base); R.raf(pump); } }; R.raf(pump);
  window.__rec = {
    start() { manual = true; for (const v of document.querySelectorAll('video')) { v.__t0 = v.currentTime || 0; v.pause(); } for (const an of document.getAnimations()) an.pause(); },
    async step(dt) {
      run(vt + dt);
      for (const an of document.getAnimations()) { if (an.playState !== 'finished') { an.pause(); an.currentTime = (an.currentTime || 0) + dt; } }
      await Promise.all([...document.querySelectorAll('video')].map(v => new Promise(res => {
        if (!v.duration || !isFinite(v.duration)) return res();
        v.pause(); const target = (v.__t0 + vt / 1000) % v.duration;
        if (Math.abs(v.currentTime - target) < 0.001) return res();
        const done = () => { v.removeEventListener('seeked', done); res(); }; v.addEventListener('seeked', done); v.currentTime = target; R.st(res, 1500);
      })));
    },
  };
};
const only = process.argv.slice(2);
const b = await chromium.launch({ executablePath: '/opt/pw-browsers/chromium-1194/chrome-linux/chrome', args: ['--use-gl=angle','--use-angle=swiftshader','--enable-unsafe-swiftshader','--ignore-gpu-blocklist','--autoplay-policy=no-user-gesture-required'] });
for (const [k, u] of Object.entries(SITES)) {
  if (only.length && !only.includes(k)) continue;
  const ctx = await b.newContext({ viewport: { width: 1440, height: 810 }, deviceScaleFactor: 1 });
  await ctx.route(/\.mp4(\?|$)/, async (route) => {
    const hit = Object.entries(SWAP).find(([frag]) => route.request().url().includes(frag));
    if (hit) return route.fulfill({ status: 200, contentType: 'video/webm', body: fs.readFileSync(`src/${hit[1]}.webm`) });
    return route.continue();
  });
  const p = await ctx.newPage(); await p.addInitScript(shim);
  await p.goto(u, { waitUntil: 'networkidle', timeout: 60000 }).catch(() => {});
  await p.mouse.move(1435, 805);
  for (const t of ['Accept All', 'Accept all', 'Accept', 'I agree', 'Got it']) { const btn = p.getByRole('button', { name: t, exact: true }); if (await btn.count().catch(() => 0)) { await btn.first().click({ timeout: 2000 }).catch(() => {}); break; } }
  await p.addStyleTag({ content: '[class*=cookie],[id*=cookie],[class*=Cookie],[id*=Cookie]{display:none!important}' }).catch(() => {});
  await p.evaluate(async () => {   // load every video into memory so it can be seeked frame by frame
    await Promise.all([...document.querySelectorAll('video')].map(async v => {
      const src = v.currentSrc || v.src || v.querySelector('source')?.src; if (!src) return;
      try { const blob = await (await fetch(src)).blob(); v.querySelectorAll('source').forEach(s => s.remove()); v.src = URL.createObjectURL(blob); v.muted = true; v.loop = true;
        await new Promise(r => { v.addEventListener('loadeddata', r, { once: true }); setTimeout(r, 8000); }); v.play().catch(() => {}); } catch (e) {}
    }));
  });
  await p.waitForTimeout(WAIT[k] ?? 12000);   // intros play out on the pumped clock
  await p.evaluate(() => window.__rec.start());
  const dir = `frames/${k}`; fs.rmSync(dir, { recursive: true, force: true }); fs.mkdirSync(dir, { recursive: true });
  for (let i = 0; i < (PRE[k] || 0) * FPS; i++) await p.evaluate((dt) => window.__rec.step(dt), 1000 / FPS);
  const n = Math.round(FPS * SECONDS), t0 = Date.now();
  for (let i = 0; i < n; i++) {
    await p.evaluate((dt) => window.__rec.step(dt), 1000 / FPS);
    await p.screenshot({ path: `${dir}/${String(i).padStart(4, '0')}.jpg`, type: 'jpeg', quality: 92, timeout: 120000 });
  }
  console.log('ok', k, n, 'frames', Math.round((Date.now() - t0) / 1000) + 's');
  await ctx.close();
}
await b.close(); console.log('DONE');
