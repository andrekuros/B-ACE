const API = "/api";

const state = {
  view: "live",
  jobId: null,
  ws: null,
  episode: null,
  replayIdx: 0,
  playing: false,
};

function $(id) { return document.getElementById(id); }

async function api(path, opts) {
  const res = await fetch(API + path, {
    headers: { "Content-Type": "application/json" },
    ...opts,
  });
  if (!res.ok) throw new Error(await res.text());
  return res.json();
}

function switchView(name) {
  state.view = name;
  document.querySelectorAll("nav button").forEach((b) => {
    b.classList.toggle("active", b.dataset.view === name);
  });
  ["live", "replay", "experiment"].forEach((v) => {
    $(`view-${v}`).classList.toggle("hidden", v !== name);
  });
}

document.querySelectorAll("nav button").forEach((b) => {
  b.addEventListener("click", () => switchView(b.dataset.view));
});

async function refreshHealth() {
  try {
    const h = await api("/health");
    $("health").textContent = `ok · v${h.version}`;
  } catch {
    $("health").textContent = "server offline";
  }
}

function worldToCanvas(pos, canvas) {
  // pos in GDM; map ±80 NM (~±1480 GDM) into canvas
  const scale = canvas.width / (160 * 18.52);
  const cx = canvas.width / 2;
  const cy = canvas.height / 2;
  return [cx + pos[0] * scale, cy + pos[2] * scale];
}

function drawSnapshots(canvas, snapshots) {
  const ctx = canvas.getContext("2d");
  ctx.clearRect(0, 0, canvas.width, canvas.height);
  ctx.strokeStyle = "rgba(138,160,181,0.2)";
  ctx.beginPath();
  ctx.moveTo(canvas.width / 2, 0);
  ctx.lineTo(canvas.width / 2, canvas.height);
  ctx.moveTo(0, canvas.height / 2);
  ctx.lineTo(canvas.width, canvas.height / 2);
  ctx.stroke();

  (snapshots || []).forEach((snap, envIdx) => {
    const ox = (envIdx % 2) * 8;
    const oy = Math.floor(envIdx / 2) * 8;
    (snap.fighters || []).forEach((f) => {
      const [x, y] = worldToCanvas(f.pos, canvas);
      ctx.fillStyle = f.team === 0 ? "#4aa3ff" : "#ff6b5a";
      ctx.globalAlpha = f.alive ? 1 : 0.25;
      ctx.beginPath();
      ctx.arc(x + ox, y + oy, 5, 0, Math.PI * 2);
      ctx.fill();
      const rad = (f.hdg * Math.PI) / 180;
      ctx.strokeStyle = ctx.fillStyle;
      ctx.beginPath();
      ctx.moveTo(x + ox, y + oy);
      ctx.lineTo(x + ox + Math.sin(rad) * 14, y + oy - Math.cos(rad) * 14);
      ctx.stroke();
      ctx.globalAlpha = 1;
    });
    (snap.missiles || []).forEach((m) => {
      const [x, y] = worldToCanvas(m.pos, canvas);
      ctx.fillStyle = m.pitbull ? "#ffd166" : "#c4b5fd";
      ctx.fillRect(x - 2, y - 2, 4, 4);
    });
  });
}

async function refreshJobs() {
  const jobs = await api("/jobs");
  const ul = $("job-list");
  ul.innerHTML = "";
  jobs.forEach((j) => {
    const li = document.createElement("li");
    li.textContent = `${j.id.slice(0, 8)} · ${j.num_envs} envs · ${j.status}`;
    li.onclick = () => connectJob(j.id);
    if (j.id === state.jobId) li.classList.add("active");
    ul.appendChild(li);
  });
}

function connectJob(id) {
  state.jobId = id;
  if (state.ws) state.ws.close();
  const proto = location.protocol === "https:" ? "wss" : "ws";
  state.ws = new WebSocket(`${proto}://${location.host}/api/jobs/${id}/ws`);
  state.ws.onmessage = (ev) => {
    const msg = JSON.parse(ev.data);
    drawSnapshots($("live-canvas"), msg.snapshots);
    $("live-meta").textContent = `job ${msg.id.slice(0, 8)} · ${msg.status}\n` +
      (msg.snapshots || []).map((s, i) => `env${i}: step=${s.action_step} end=${s.end}`).join("\n");
  };
  refreshJobs();
}

$("start-job").onclick = async () => {
  const job = await api("/jobs", {
    method: "POST",
    body: JSON.stringify({
      num_envs: Number($("num-envs").value),
      max_cycles: Number($("max-cycles").value),
      record: true,
      blue_behavior: "baseline1",
      red_behavior: "duck",
    }),
  });
  await refreshJobs();
  connectJob(job.id);
};

async function refreshRuns() {
  const runs = await api("/runs");
  const ul = $("run-list");
  ul.innerHTML = "";
  runs.forEach((r) => {
    const li = document.createElement("li");
    li.textContent = `${r.run_id.slice(0, 8)} · ${r.end} · ${r.total_steps} steps`;
    li.onclick = () => loadRun(r.run_id);
    ul.appendChild(li);
  });
}

async function loadRun(id) {
  state.episode = await api(`/runs/${id}`);
  state.replayIdx = 0;
  $("scrubber").max = Math.max(0, (state.episode.steps || []).length - 1);
  $("scrubber").value = 0;
  renderReplay();
}

function renderReplay() {
  const ep = state.episode;
  if (!ep || !ep.steps.length) return;
  const step = ep.steps[state.replayIdx];
  drawSnapshots($("replay-canvas"), [step.snapshot]);
  const agent = Object.keys(step.obs || {})[0];
  const bd = step.reward_breakdowns?.[agent];
  $("replay-inspect").textContent =
    `step ${step.action_step} / ${ep.meta.total_steps}\n` +
    `end=${ep.meta.end}\n` +
    `agent=${agent}\n` +
    `reward=${step.rewards?.[agent]}\n` +
    `breakdown=${JSON.stringify(bd, null, 2)}\n` +
    `own=${JSON.stringify(step.obs?.[agent]?.own, null, 2)}`;
}

$("refresh-runs").onclick = refreshRuns;
$("scrubber").oninput = (e) => {
  state.replayIdx = Number(e.target.value);
  renderReplay();
};
$("play-replay").onclick = () => {
  state.playing = !state.playing;
  $("play-replay").textContent = state.playing ? "Pause" : "Play";
};

setInterval(() => {
  if (!state.playing || !state.episode) return;
  const max = (state.episode.steps || []).length - 1;
  if (state.replayIdx >= max) {
    state.playing = false;
    $("play-replay").textContent = "Play";
    return;
  }
  state.replayIdx += 1;
  $("scrubber").value = state.replayIdx;
  renderReplay();
}, 200);

$("run-exp").onclick = async () => {
  $("exp-out").textContent = "running…";
  const out = await api("/experiment", {
    method: "POST",
    body: JSON.stringify({
      cases: Number($("exp-cases").value),
      max_cycles: Number($("exp-cycles").value),
    }),
  });
  $("exp-out").textContent = JSON.stringify(out, null, 2);
};

refreshHealth();
refreshJobs();
refreshRuns();
setInterval(refreshHealth, 5000);
