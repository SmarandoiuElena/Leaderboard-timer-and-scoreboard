(() => {
  const $ = (id) => document.getElementById(id);
  let st = null;            // ultima stare de la server
  let offset = 0;
  let lastTeam;             // echipa activa la starea anterioara (undefined = inca nimic primit)
  let pendingSave = null;   // {proba, count} cat timp asteptam confirmarea unui scor trimis

  const link = Acad.connect({
    onState(s) {
      st = s;
      offset = s.server_time - Date.now() / 1000;
      document.body.dataset.proba = s.active.proba;

      // Scor salvat cu succes -> golim formularul. Echipa schimbata -> la fel.
      if (pendingSave && s.counts[pendingSave.proba] > pendingSave.count) {
        resetForm();
        pendingSave = null;
      } else if (lastTeam !== undefined && lastTeam !== s.active.team_id) {
        resetForm();
      }
      lastTeam = s.active.team_id;
      render();
    },
    onStatus(ok) { $("conn").classList.toggle("ok", ok); },
    onError(msg) { pendingSave = null; Acad.toast(msg); },
  });

  function el(tag, cls, text) {
    const n = document.createElement(tag);
    if (cls) n.className = cls;
    if (text !== undefined) n.textContent = text;
    return n;
  }

  // ---------------------------------------------------------------- randare
  function render() {
    const a = st.active;
    const stopped = st.timer.state === "stopped";

    document.querySelectorAll(".seg-btn").forEach((b) => {
      b.classList.toggle("on", Number(b.dataset.proba) === a.proba);
      b.disabled = !stopped;
    });

    renderDropdown(stopped);

    $("start").disabled = st.timer.state === "running" || a.team_id === null;
    $("start").textContent = st.timer.state === "paused" ? "Reia" : "Start";
    $("pause").disabled = st.timer.state !== "running";
    $("saveBtn").disabled = a.team_id === null;

    $("recentTitle").textContent = "Ultimele încercări · " + Acad.probaTitle(a.proba);
    renderRecent();
    updateTotal();
  }

  function teamLine(team) {
    const frag = document.createDocumentFragment();
    frag.append(Acad.flag(team.country_code), el("span", "", team.name));
    if (team.country_name) frag.append(el("small", "", team.country_name));
    return frag;
  }

  function renderDropdown(stopped) {
    const btn = $("ddBtn");
    const team = st.teams.find((t) => t.id === st.active.team_id);
    btn.disabled = !stopped;
    btn.replaceChildren();
    if (team) btn.append(teamLine(team));
    else btn.append(el("span", "ph", "Alege echipa…"));

    const list = $("ddList");
    list.replaceChildren();
    st.teams.forEach((t) => {
      const li = el("li", "dd-item" + (t.id === st.active.team_id ? " sel" : ""));
      li.append(teamLine(t));
      li.onclick = () => {
        list.hidden = true;
        link.send({ action: "set_team", team_id: t.id });
      };
      list.append(li);
    });
  }

  function renderRecent() {
    const p = st.active.proba;
    const ul = $("recent");
    ul.replaceChildren();
    const rows = st.attempts[String(p)];
    if (!rows.length) {
      ul.append(el("li", "empty", "Nicio încercare încă."));
      return;
    }
    rows.forEach((a) => {
      const team = st.teams.find((t) => t.id === a.team_id);
      const li = el("li");
      li.append(Acad.flag(team ? team.country_code : "xx"));

      const info = el("div", "info");
      info.append(el("div", "", team ? team.name : "Echipă ștearsă"));
      let detail;
      if (p === 1) {
        const cps = [1, 2, 3, 4, 5].filter((i) => a["cp" + i]).join(", ") || "–";
        detail = `CP: ${cps} · viteză ${Acad.num(a.speed_points)}`;
      } else {
        detail = `control ${Acad.num(a.control_points)} · viteză ${Acad.num(a.speed_points)}`;
      }
      if (a.time_s !== null) detail += ` · ${Acad.fmtTime(a.time_s)}`;
      detail += ` · ${a.timestamp.slice(11, 16)}`;
      info.append(el("small", "", detail));

      const del = el("button", "del", "✕");
      del.title = "Șterge încercarea";
      del.onclick = () => {
        const name = team ? team.name : "echipa";
        if (confirm(`Ștergi încercarea ${name} (${Acad.num(a.total)} p)?`)) {
          link.send({ action: "delete_attempt", proba: p, id: a.id });
        }
      };
      li.append(info, el("div", "tot", Acad.num(a.total)), del);
      ul.append(li);
    });
  }

  // ---------------------------------------------------------------- formular
  const cpButtons = [...document.querySelectorAll(".cp")];
  const inputs = ["p1speed", "p2control", "p2speed"].map($);

  function resetForm() {
    cpButtons.forEach((b) => b.classList.remove("on"));
    inputs.forEach((i) => { i.value = ""; });
    updateTotal();
  }

  function val(input) { return parseFloat(input.value) || 0; }

  function updateTotal() {
    const p = st ? st.active.proba : 1;
    let total;
    if (p === 1) total = cpButtons.filter((b) => b.classList.contains("on")).length * 10 + val($("p1speed"));
    else total = val($("p2control")) + val($("p2speed"));
    $("total").textContent = Acad.num(total);
  }

  cpButtons.forEach((b) => b.addEventListener("click", () => { b.classList.toggle("on"); updateTotal(); }));
  inputs.forEach((i) => i.addEventListener("input", updateTotal));

  function save() {
    const a = st.active;
    if (a.team_id === null) return Acad.toast("Alege o echipă.");

    const fields = a.proba === 1
      ? [["p1speed", "Punctaj viteză", 50]]
      : [["p2control", "Punctaj control"], ["p2speed", "Punctaj viteză (grosime linie)"]];
    for (const [id, label, max] of fields) {
      const raw = $(id).value;
      if (raw === "") return Acad.toast(`Completează: ${label}.`);
      const n = Number(raw);
      if (!Number.isFinite(n)) return Acad.toast(`${label}: valoare invalidă.`);
      if (n < 0) return Acad.toast(`${label} nu poate fi negativ.`);
      if (max !== undefined && n > max) return Acad.toast(`${label} nu poate depăși ${max}.`);
    }

    let payload;
    if (a.proba === 1) {
      payload = {
        action: "save", proba: 1, team_id: a.team_id,
        checkpoints: cpButtons.map((b) => b.classList.contains("on")),
        speed_points: $("p1speed").value,
      };
    } else {
      payload = {
        action: "save", proba: 2, team_id: a.team_id,
        control_points: $("p2control").value,
        speed_points: $("p2speed").value,
      };
    }

    const team = st.teams.find((t) => t.id === a.team_id);
    const time = Acad.elapsed(st, offset);
    const wasRunning = st.timer.state === "running";
    if (wasRunning) link.send({ action: "pause" });
    
    const msg = `${Acad.probaTitle(a.proba)}\n${team.name}\nTotal: ${$("total").textContent} p`
      + (time > 0 ? `\nTimp: ${Acad.fmtTime(time)}` : "") + "\n\nSalvezi încercarea?";

    if (!confirm(msg)) {
      if (wasRunning) link.send({ action: "start" });
        return;
    }

    pendingSave = { proba: a.proba, count: st.counts[String(a.proba)] };
    link.send(payload);
  }

  // ---------------------------------------------------------------- evenimente
  document.querySelectorAll(".seg-btn").forEach((b) =>
    b.addEventListener("click", () => link.send({ action: "set_proba", proba: Number(b.dataset.proba) })));
  $("start").onclick = () => link.send({ action: "start" });
  $("pause").onclick = () => link.send({ action: "pause" });
  $("reset").onclick = () => link.send({ action: "reset" });
  $("saveBtn").onclick = save;

  $("ddBtn").onclick = (e) => { e.stopPropagation(); $("ddList").hidden = !$("ddList").hidden; };
  document.addEventListener("click", () => { $("ddList").hidden = true; });

  setInterval(() => {
    if (!st) return;
    const c = $("clock");
    c.textContent = Acad.fmtTime(Acad.elapsed(st, offset));
    c.className = "mini-clock " + st.timer.state;
  }, 50);
})();
