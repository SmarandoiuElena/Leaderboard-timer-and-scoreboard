// Pagina de administrare: tabele editabile pentru incercari (proba 1 / 2) si echipe.
// Datele vin prin /api (REST); WebSocket-ul e folosit doar ca sa stim cand s-a schimbat ceva.
(() => {
  const $ = (id) => document.getElementById(id);
  const CPS = [1, 2, 3, 4, 5];

  let tab = "1";          // "1" | "2" | "teams"
  let teams = [];
  let rows = [];          // incercarile probei curente, sau echipele
  let editing = null;     // null | { id } ; id === null = rand nou, inca nesalvat

  function el(tag, cls, text) {
    const n = document.createElement(tag);
    if (cls) n.className = cls;
    if (text !== undefined) n.textContent = text;
    return n;
  }

  async function api(method, url, body) {
    const res = await fetch(url, {
      method,
      headers: body ? { "Content-Type": "application/json" } : {},
      body: body ? JSON.stringify(body) : undefined,
    });
    if (res.status === 204) return null;
    const data = await res.json().catch(() => ({}));
    if (!res.ok) throw new Error(typeof data.detail === "string" ? data.detail : "Eroare la server.");
    return data;
  }

  // ---------------------------------------------------------------- date
  async function load() {
    try {
      teams = await api("GET", "/api/teams");
      rows = tab === "teams" ? teams : await api("GET", `/api/attempts/${tab}`);
      render();
    } catch (e) { Acad.toast(e.message); }
  }

  async function run(promise) {            // executa o actiune; la eroare arata mesajul si ramane in editare
    try { await promise; editing = null; await load(); }
    catch (e) { Acad.toast(e.message); }
  }

  Acad.connect({
    // Cineva (arbitrul, alt admin) a schimbat ceva. Nu reincarcam cat editam, ca sa nu pierdem ce scriem.
    onState() { if (!editing) load(); },
    onStatus(ok) { $("conn").classList.toggle("ok", ok); },
  });

  // ---------------------------------------------------------------- tabel
  function td(content, cls) {
    const c = el("td", cls || "");
    if (content instanceof Node) c.append(content);
    else if (content !== undefined) c.textContent = content;
    return c;
  }

  function header(labels) {
    const tr = el("tr");
    labels.forEach(([text, cls]) => tr.append(Object.assign(el("th", cls || ""), { textContent: text })));
    return tr;
  }

  function actions(buttons) {
    const box = el("div", "acts");
    buttons.forEach(([text, cls, fn]) => {
      const b = el("button", cls, text);
      b.type = "button";
      b.onclick = fn;
      box.append(b);
    });
    return td(box);
  }

  function teamName(id) {
    const t = teams.find((x) => x.id === id);
    return t ? t.name : "Echipă ștearsă";
  }

  function teamCell(id) {
    const t = teams.find((x) => x.id === id);
    const c = td("", "team");
    c.append(Acad.flag(t ? t.country_code : "xx"), t ? t.name : "Echipă ștearsă");
    return c;
  }

  function numInput(value, cls, step = "any") {
    const i = el("input", cls || "");
    i.type = "number"; i.min = "0"; i.step = step; i.inputMode = "decimal";
    i.value = value ?? "";
    return i;
  }

  function stamp(a) { return a.timestamp ? a.timestamp.slice(5, 16) : ""; }

  // ---- incercari
  function attemptHeader(p) {
    return header(p === 1
      ? [["Echipă"], ...CPS.map((i) => ["CP" + i]), ["Viteză (0–50)", "num"], ["Total", "num"], ["Timp (s)", "num"], ["Salvat"], [""]]
      : [["Echipă"], ["Control", "num"], ["Viteză (grosime linie)", "num"], ["Total", "num"], ["Timp (s)", "num"], ["Salvat"], [""]]);
  }

  function attemptRow(p, a) {
    const tr = el("tr");
    tr.append(teamCell(a.team_id));
    if (p === 1) {
      CPS.forEach((i) => tr.append(td(a["cp" + i] ? "✓" : "–", a["cp" + i] ? "" : "muted")));
      tr.append(td(Acad.num(a.speed_points), "num"));
    } else {
      tr.append(td(Acad.num(a.control_points), "num"), td(Acad.num(a.speed_points), "num"));
    }
    tr.append(
      td(Acad.num(a.total), "num tot"),
      td(a.time_s === null ? "–" : Acad.num(a.time_s), "num"),
      td(stamp(a), "muted"),
      actions([
        ["Editează", "", () => { editing = { id: a.id }; render(); }],
        ["Șterge", "del", () => {
          if (confirm(`Ștergi încercarea ${teamName(a.team_id)} (${Acad.num(a.total)} p)?`))
            run(api("DELETE", `/api/attempts/${p}/${a.id}`));
        }],
      ]),
    );
    return tr;
  }

  function attemptEditRow(p, a) {         // a = incercarea existenta, sau null pentru una noua
    const tr = el("tr", "editing");

    const sel = el("select");
    if (!a) sel.append(Object.assign(el("option"), { value: "", textContent: "Alege echipa…" }));
    teams.forEach((t) => sel.append(Object.assign(el("option"), { value: t.id, textContent: t.name })));
    sel.value = a ? a.team_id : "";
    tr.append(td(sel));

    const boxes = [], f = {};
    if (p === 1) {
      CPS.forEach((i) => {
        const c = el("input"); c.type = "checkbox"; c.checked = !!(a && a["cp" + i]);
        boxes.push(c); tr.append(td(c));
      });
      f.speed = numInput(a ? a.speed_points : "", "short");
      tr.append(td(f.speed, "num"));
    } else {
      f.control = numInput(a ? a.control_points : "", "short");
      f.speed = numInput(a ? a.speed_points : "", "short");
      tr.append(td(f.control, "num"), td(f.speed, "num"));
    }

    const total = td("", "num tot");
    const recompute = () => {
      const v = (i) => parseFloat(i.value) || 0;
      const t = p === 1 ? boxes.filter((b) => b.checked).length * 10 + v(f.speed) : v(f.control) + v(f.speed);
      total.textContent = Acad.num(t);
    };
    [...boxes, f.control, f.speed].filter(Boolean).forEach((i) => i.addEventListener("input", recompute));
    recompute();

    f.time = numInput(a && a.time_s !== null ? a.time_s : "", "short", "0.1");
    tr.append(total, td(f.time, "num"), td(a ? stamp(a) : "nou", "muted"));

    const save = () => {
      const body = { team_id: sel.value === "" ? null : Number(sel.value), time_s: f.time.value, speed_points: f.speed.value };
      if (p === 1) body.checkpoints = boxes.map((b) => b.checked);
      else body.control_points = f.control.value;
      run(a ? api("PUT", `/api/attempts/${p}/${a.id}`, body) : api("POST", `/api/attempts/${p}`, body));
    };
    tr.append(actions([["Salvează", "save", save], ["Anulează", "", () => { editing = null; render(); }]]));
    return tr;
  }

  // ---- echipe
  function teamHeader() { return header([["Echipă"], ["Cod țară"], ["Țară"], [""]]); }

  function teamRow(t) {
    const tr = el("tr");
    tr.append(teamCell(t.id), td(t.country_code === "xx" ? "–" : t.country_code, "muted"), td(t.country_name || "–", "muted"),
      actions([
        ["Editează", "", () => { editing = { id: t.id }; render(); }],
        ["Șterge", "del", () => { if (confirm(`Ștergi echipa ${t.name}?`)) run(api("DELETE", `/api/teams/${t.id}`)); }],
      ]));
    return tr;
  }

  function teamEditRow(t) {
    const tr = el("tr", "editing");
    const text = (v, ph) => { const i = el("input"); i.type = "text"; i.value = v || ""; i.placeholder = ph; return i; };
    const name = text(t && t.name, "Nume echipă");
    const code = text(t && t.country_code !== "xx" ? t.country_code : "", "ro"); code.maxLength = 2; code.className = "short";
    const country = text(t && t.country_name, "România");
    const save = () => {
      const body = { name: name.value, country_code: code.value, country_name: country.value };
      run(t ? api("PUT", `/api/teams/${t.id}`, body) : api("POST", "/api/teams", body));
    };
    tr.append(td(name), td(code), td(country),
      actions([["Salvează", "save", save], ["Anulează", "", () => { editing = null; render(); }]]));
    return tr;
  }

  // ---------------------------------------------------------------- randare
  function render() {
    const isTeams = tab === "teams";
    const p = Number(tab);
    document.body.dataset.proba = tab === "1" ? "1" : "2";
    document.querySelectorAll(".tab").forEach((b) => b.classList.toggle("on", b.dataset.tab === tab));
    $("title").textContent = isTeams ? "Echipe" : `${Acad.probaTitle(p)} · încercări`;
    $("addBtn").textContent = isTeams ? "+ Echipă nouă" : "+ Încercare nouă";
    $("addBtn").disabled = !!editing;

    const table = $("table");
    table.replaceChildren();
    const head = el("thead"), body = el("tbody");
    head.append(isTeams ? teamHeader() : attemptHeader(p));

    if (editing && editing.id === null) body.append(isTeams ? teamEditRow(null) : attemptEditRow(p, null));
    rows.forEach((r) => {
      const isEdit = editing && editing.id === r.id;
      if (isTeams) body.append(isEdit ? teamEditRow(r) : teamRow(r));
      else body.append(isEdit ? attemptEditRow(p, r) : attemptRow(p, r));
    });
    if (!rows.length && !editing) {
      const tr = el("tr"), c = td(isTeams ? "Nicio echipă." : "Nicio încercare încă.", "empty");
      c.colSpan = 12; tr.append(c); body.append(tr);
    }
    table.append(head, body);
  }

  document.querySelectorAll(".tab").forEach((b) => b.addEventListener("click", () => {
    if (tab === b.dataset.tab) return;
    tab = b.dataset.tab; editing = null; rows = []; render(); load();
  }));
  $("addBtn").onclick = () => { editing = { id: null }; render(); };

  render();
  load();
})();
