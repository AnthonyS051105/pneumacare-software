// Koreografi scroll native landing — port dari PNEUMACARE_Final_UI/PNEUMACARE/motion.js.
// Tidak membajak wheel/touch; hanya membaca posisi scroll lalu mengubah atribut & transform
// langsung di DOM (tanpa re-render React per frame). Menghormati prefers-reduced-motion,
// dan memakai mode "compact" (tanpa sticky) di layar <=767px atau tinggi <560px.

const clamp = (n: number, min = 0, max = 1) => Math.max(min, Math.min(max, n));

export function storyState(scrollY: number, top: number, height: number, pinHeight: number) {
  const distance = Math.max(1, height - pinHeight);
  const progress = clamp((scrollY - top) / distance);
  const stage = Math.min(2, Math.floor(progress * 3));
  return { progress, stage, sceneProgress: clamp(progress * 3 - stage) };
}

export function scrollVelocity(delta: number, elapsed: number) {
  return clamp(delta / Math.max(8, elapsed), -2.5, 2.5);
}

export function velocityTransform(speed: number, depth: number, mobile = false) {
  const gain = mobile ? 0.55 : 1;
  return {
    y: clamp(speed * depth * 13 * gain, -32, 32),
    skew: clamp(speed * depth * 0.85 * gain, -2.2, 2.2),
  };
}

export function overlapState(top: number, viewportHeight: number) {
  const progress = clamp((viewportHeight - top) / (viewportHeight * 0.65));
  return { progress, lift: (1 - progress) * 22, scale: 0.975 + 0.025 * progress };
}

const NOTES = [
  "Pemantauan mengikuti aktivitas Anda di rumah.",
  "Riwayat membantu Anda mengenali perubahan kondisi.",
  "Informasi pemantauan terhubung dengan tenaga medis.",
];

/** Pasang pengontrol cerita pada root landing. Mengembalikan fungsi cleanup. */
export function mountStory(root: HTMLElement): () => void {
  const win = window;
  const story = root.querySelector<HTMLElement>("[data-story]");
  const pin = root.querySelector<HTMLElement>("[data-story-pin]");
  if (!story || !pin) return () => {};
  const steps = [...root.querySelectorAll<HTMLElement>("[data-story-jump]")];
  const tech = [...root.querySelectorAll<HTMLElement>("[data-tech]")];
  const velocityNodes = [...root.querySelectorAll<HTMLElement>("[data-velocity]")];
  const panels = [...root.querySelectorAll<HTMLElement>("[data-overlap]")];
  const count = root.querySelector<HTMLElement>("[data-story-count]");
  const note = root.querySelector<HTMLElement>("[data-story-note]");
  const rail = root.querySelector<HTMLElement>("[data-story-rail]");

  const reducedQuery = win.matchMedia("(prefers-reduced-motion: reduce)");
  let reduced = reducedQuery.matches;
  let frame = 0;
  let active = true;
  let lastY = win.scrollY;
  let lastEvent = win.performance.now();
  let lastFrame = lastEvent;
  let speed = 0;
  let targetSpeed = 0;
  let currentStage = -1;
  let storyTop = 0;
  let storyHeight = 0;
  let pinHeight = 0;
  let panelTops: number[] = [];
  let compact = win.innerWidth <= 767 || win.innerHeight < 560;
  const isReduced = () => reduced || compact;

  function setStage(stage: number) {
    if (stage === currentStage) return;
    currentStage = stage;
    story!.dataset.stage = String(stage);
    steps.forEach((el, i) => {
      if (i === stage) el.setAttribute("aria-current", "step");
      else el.removeAttribute("aria-current");
    });
    tech.forEach((el, i) => el.toggleAttribute("data-active", i === stage));
    if (count) count.textContent = String(stage + 1).padStart(2, "0");
    if (note) note.textContent = NOTES[stage];
    if (isReduced() && rail) rail.style.height = ((stage + 1) / 3) * 100 + "%";
  }

  function measure() {
    storyTop = story!.getBoundingClientRect().top + win.scrollY;
    storyHeight = story!.offsetHeight;
    pinHeight = pin!.offsetHeight;
    panelTops = panels.map((el) => el.getBoundingClientRect().top + win.scrollY);
  }

  function applyPreference() {
    root.classList.toggle("motion-reduced", isReduced());
    velocityNodes.forEach((el) => (el.style.transform = ""));
    panels.forEach((el) => (el.style.transform = ""));
    targetSpeed = 0;
    speed = 0;
    measure();
    schedule();
  }

  function schedule() {
    if (active && !frame) frame = win.requestAnimationFrame(update);
  }

  function update(now: number) {
    frame = 0;
    if (!active || !root.isConnected) return;
    const dt = clamp(now - lastFrame, 8, 64);
    lastFrame = now;
    // Redam target saat scroll berhenti, lalu kembalikan transform ke netral.
    if (now - lastEvent > 48) targetSpeed *= Math.exp(-dt / 85);
    speed += (targetSpeed - speed) * (1 - Math.exp(-dt / 65));
    if (!isReduced()) {
      const state = storyState(win.scrollY, storyTop, storyHeight, pinHeight);
      setStage(state.stage);
      if (rail) rail.style.height = state.progress * 100 + "%";
      velocityNodes.forEach((el) => {
        const t = velocityTransform(speed, Number(el.dataset.velocity), win.innerWidth <= 767);
        el.style.transform = `translate3d(0,${t.y.toFixed(2)}px,0) skewY(${t.skew.toFixed(3)}deg)`;
      });
      panels.forEach((el, i) => {
        const t = overlapState(panelTops[i] - win.scrollY, win.innerHeight);
        el.style.transform = `translate3d(0,${t.lift.toFixed(2)}px,0) scale(${t.scale.toFixed(4)})`;
      });
    }
    if (Math.abs(speed) > 0.006 || Math.abs(targetSpeed) > 0.006) schedule();
    else {
      speed = 0;
      targetSpeed = 0;
      velocityNodes.forEach((el) => (el.style.transform = ""));
    }
  }

  function onScroll() {
    const now = win.performance.now();
    const y = win.scrollY;
    targetSpeed = scrollVelocity(y - lastY, clamp(now - lastEvent, 8, 100));
    lastY = y;
    lastEvent = now;
    schedule();
  }

  function onResize() {
    const nextCompact = win.innerWidth <= 767 || win.innerHeight < 560;
    if (nextCompact !== compact) {
      compact = nextCompact;
      applyPreference();
    } else {
      measure();
      schedule();
    }
  }

  function onClick(event: MouseEvent) {
    const jump = (event.target as HTMLElement).closest<HTMLElement>("[data-story-jump]");
    if (!jump || !root.contains(jump)) return;
    const stage = Number(jump.dataset.storyJump);
    if (isReduced()) return setStage(stage);
    measure();
    win.scrollTo({ top: storyTop + (storyHeight - pinHeight) * ((stage + 0.1) / 3), behavior: "smooth" });
  }

  function onPreference(event: MediaQueryListEvent) {
    reduced = event.matches;
    applyPreference();
  }

  function onLoaded() {
    measure();
    schedule();
  }

  win.addEventListener("scroll", onScroll, { passive: true });
  win.addEventListener("resize", onResize, { passive: true });
  root.addEventListener("click", onClick);
  reducedQuery.addEventListener("change", onPreference);
  const pictures = [...root.querySelectorAll("img")];
  pictures.forEach((img) => img.addEventListener("load", onLoaded));
  const resizeObserver = new ResizeObserver(onResize);
  resizeObserver.observe(story);
  resizeObserver.observe(pin);

  setStage(0);
  applyPreference();
  schedule();

  return () => {
    active = false;
    if (frame) win.cancelAnimationFrame(frame);
    win.removeEventListener("scroll", onScroll);
    win.removeEventListener("resize", onResize);
    root.removeEventListener("click", onClick);
    reducedQuery.removeEventListener("change", onPreference);
    pictures.forEach((img) => img.removeEventListener("load", onLoaded));
    resizeObserver.disconnect();
  };
}
