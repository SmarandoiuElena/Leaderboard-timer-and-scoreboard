(() => {
  let st = null;     // ultima stare primita de la server
  let offset = 0;    // ceas server - ceas client

  const clock = document.getElementById("clock");
  const statusEl = document.getElementById("status");
  const teamEl = document.getElementById("team");
  const pill = document.getElementById("pill");

  const STATUS = { stopped: "Pregătit", running: "În desfășurare", paused: "Pauză" };

  Acad.connect({
    onState(s) {
      st = s;
      offset = s.server_time - Date.now() / 1000;
      renderStatic();
    },
    onStatus(ok) { document.getElementById("conn").classList.toggle("ok", ok); },
  });

  function renderStatic() {
    const p = st.active.proba;
    document.body.dataset.proba = p;
    pill.textContent = Acad.probaTitle(p);
    statusEl.textContent = STATUS[st.timer.state];

    teamEl.replaceChildren();
    const team = st.teams.find((t) => t.id === st.active.team_id);
    teamEl.classList.toggle("none", !team);
    if (!team) {
      teamEl.textContent = "Nicio echipă selectată";
    } else {
      const name = document.createElement("span");
      name.textContent = team.name;
      teamEl.append(Acad.flag(team.country_code), name);
      if (team.country_name) {
        const c = document.createElement("small");
        c.textContent = team.country_name;
        teamEl.append(c);
      }
    }
  }

  setInterval(() => {
    if (!st) return;
    clock.textContent = Acad.fmtTime(Acad.elapsed(st, offset));
    clock.className = "clock " + st.timer.state;
  }, 50);
})();
