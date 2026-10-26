// Folosit de clasament1.html si clasament2.html; proba vine din <body data-proba>.
(() => {
  const proba = Number(document.body.dataset.proba);
  const board = document.getElementById("board");
  let prev = null;   // scorurile anterioare pe echipa, ca sa evidentiem ce s-a schimbat

  Acad.connect({
    onState(st) { render(st.leaderboards[String(proba)]); },
    onStatus(ok) { document.getElementById("conn").classList.toggle("ok", ok); },
  });

  function el(tag, cls, text) {
    const n = document.createElement(tag);
    if (cls) n.className = cls;
    if (text !== undefined) n.textContent = text;
    return n;
  }

  function render(rows) {
    board.replaceChildren();
    const next = {};

    rows.forEach((r) => {
      const key = JSON.stringify(r.scores);
      next[r.team_id] = key;

      const row = el("div", "lb-row" + (r.rank && r.rank <= 3 ? " r" + r.rank : "") + (r.best === null ? " noscore" : ""));
      row.append(el("div", "rank", r.rank ?? "–"));

      const cell = el("div", "team-cell");
      const info = el("div");
      info.append(el("div", "team-name", r.name));
      if (r.country_name) info.append(el("div", "team-country", r.country_name));

      const chips = el("div", "chips");
      if (!r.scores.length) chips.append(el("span", "none", "Fără încercări"));
      r.scores.forEach((s, i) => chips.append(el("span", "chip" + (i === 0 ? " best" : ""), Acad.num(s))));
      info.append(chips);
      cell.append(Acad.flag(r.country_code), info);

      const best = el("div", "best-cell");
      best.append(el("div", "best-score", r.best === null ? "–" : Acad.num(r.best)));
      if (r.best_time !== null) best.append(el("div", "best-time", Acad.fmtTime(r.best_time)));

      row.append(cell, best);
      board.append(row);

      if (prev && prev[r.team_id] !== key) {
        row.classList.add("flash");
        setTimeout(() => row.classList.remove("flash"), 1500);
      }
    });
    prev = next;
  }
})();
