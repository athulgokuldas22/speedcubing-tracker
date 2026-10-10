const $ = (id) => document.getElementById(id);

let sessionId = null;
let scramble = "";
let state = "idle"; // idle | running | saving
let armed = false; // true after a space keydown while idle
let startTime = 0;
let rafId = null;

function formatMs(ms) {
  if (ms === null || ms === undefined) return "DNF";
  const totalCs = Math.floor(ms / 10);
  const cs = String(totalCs % 100).padStart(2, "0");
  const totalSec = Math.floor(totalCs / 100);
  const sec = totalSec % 60;
  const min = Math.floor(totalSec / 60);
  return min > 0 ? `${min}:${String(sec).padStart(2, "0")}.${cs}` : `${sec}.${cs}`;
}

async function api(path, options = {}) {
  const response = await fetch(path, {
    headers: { "Content-Type": "application/json" },
    ...options,
  });
  if (response.status === 204) return null;
  const data = await response.json();
  if (!response.ok) throw new Error(data.error || "Request failed");
  return data;
}

function showMessage(text) {
  $("message").textContent = text;
}

async function run(action) {
  try {
    showMessage("");
    await action();
  } catch (err) {
    showMessage(err.message);
  }
}

function cell(text) {
  const td = document.createElement("td");
  td.textContent = text;
  return td;
}

function button(label, onClick) {
  const b = document.createElement("button");
  b.type = "button";
  b.textContent = label;
  b.addEventListener("click", onClick);
  return b;
}

function show(value) {
  return value === undefined ? "-" : formatMs(value);
}

function solveLabel(solve) {
  if (solve.penalty === "DNF") return "DNF";
  const text = formatMs(solve.effective_time_ms);
  return solve.penalty === "+2" ? text + "+" : text;
}

function renderStats(solves, stats) {
  const last = solves.length ? solves[solves.length - 1].effective_time_ms : undefined;
  const rows = [
    ["Single", last, stats.personal_bests.single],
    ["ao5", stats.current.ao5, stats.personal_bests.ao5],
    ["ao12", stats.current.ao12, stats.personal_bests.ao12],
    ["ao100", stats.current.ao100, stats.personal_bests.ao100],
  ];
  const body = document.querySelector("#stats-table tbody");
  body.replaceChildren();
  for (const [label, current, best] of rows) {
    const tr = document.createElement("tr");
    tr.append(cell(label), cell(show(current)), cell(show(best)));
    body.append(tr);
  }
}

function renderSolves(solves) {
  const body = document.querySelector("#solves-table tbody");
  body.replaceChildren();
  [...solves].reverse().forEach((solve, i) => {
    const tr = document.createElement("tr");
    const actions = document.createElement("td");
    actions.append(
      button("+2", () => run(() => changePenalty(solve, "+2"))),
      button("DNF", () => run(() => changePenalty(solve, "DNF"))),
      button("Delete", () => run(() => removeSolve(solve))),
    );
    tr.append(cell(String(solves.length - i)), cell(solveLabel(solve)), actions);
    body.append(tr);
  });
}

async function refresh() {
  const solves = await api(`/api/sessions/${sessionId}/solves`);
  const stats = await api(`/api/sessions/${sessionId}/stats`);
  renderSolves(solves);
  renderStats(solves, stats);
  if (stats.new_pbs.length) {
    showMessage("New personal best: " + stats.new_pbs.join(", "));
  }
}

async function changePenalty(solve, wanted) {
  // clicking the active penalty again clears it
  const penalty = solve.penalty === wanted ? "OK" : wanted;
  await api(`/api/solves/${solve.id}`, {
    method: "PATCH",
    body: JSON.stringify({ penalty }),
  });
  await refresh();
}

async function removeSolve(solve) {
  await api(`/api/solves/${solve.id}`, { method: "DELETE" });
  await refresh();
}

async function newScramble() {
  const data = await api("/api/scramble");
  scramble = data.scramble;
  $("scramble").textContent = scramble;
}

async function loadSessions(selectId) {
  let sessions = await api("/api/sessions");
  if (sessions.length === 0) {
    await api("/api/sessions", { method: "POST", body: JSON.stringify({ name: "Practice" }) });
    sessions = await api("/api/sessions");
  }
  const select = $("session-select");
  select.replaceChildren();
  for (const s of sessions) {
    const option = document.createElement("option");
    option.value = String(s.id);
    option.textContent = s.name;
    select.append(option);
  }
  sessionId = selectId ?? sessions[0].id;
  select.value = String(sessionId);
}

function tick() {
  $("timer").textContent = formatMs(performance.now() - startTime);
  rafId = requestAnimationFrame(tick);
}

function startTimer() {
  state = "running";
  startTime = performance.now();
  $("timer").classList.add("running");
  tick();
}

async function stopTimer() {
  cancelAnimationFrame(rafId);
  const elapsed = Math.max(1, Math.round(performance.now() - startTime));
  state = "saving";
  $("timer").classList.remove("running");
  $("timer").textContent = formatMs(elapsed);
  await run(async () => {
    await api(`/api/sessions/${sessionId}/solves`, {
      method: "POST",
      body: JSON.stringify({ time_ms: elapsed, scramble }),
    });
    await refresh();
    await newScramble();
  });
  state = "idle";
}

const TYPING = ["INPUT", "SELECT", "TEXTAREA", "BUTTON"];

document.addEventListener("keydown", (e) => {
  if (e.code !== "Space" || TYPING.includes(e.target.tagName)) return;
  e.preventDefault();
  if (state === "running") {
    armed = false;
    stopTimer();
  } else if (state === "idle" && !e.repeat) {
    armed = true;
  }
});

document.addEventListener("keyup", (e) => {
  if (e.code !== "Space") return;
  if (armed && state === "idle" && sessionId !== null) {
    startTimer();
  }
  armed = false;
});

$("new-session").addEventListener("click", (e) => {
  e.currentTarget.blur();
  const name = prompt("Session name?");
  if (!name) return;
  run(async () => {
    const session = await api("/api/sessions", {
      method: "POST",
      body: JSON.stringify({ name }),
    });
    await loadSessions(session.id);
    await refresh();
  });
});

$("session-select").addEventListener("change", (e) => {
  sessionId = Number(e.target.value);
  e.target.blur();
  run(refresh);
});

run(async () => {
  await loadSessions();
  await newScramble();
  await refresh();
});
