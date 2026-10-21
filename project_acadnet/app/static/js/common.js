// Cod comun tuturor paginilor: conexiune WebSocket, formatare, steaguri, notificari.
const Acad = (() => {
  const PROBA = {
    1: { name: "Proba 1", label: "Viteză" },
    2: { name: "Proba 2", label: "Control" },
  };

  // Conectare cu reconectare automata. Serverul trimite {type:"state",...} sau {type:"error",message}.
  function connect({ onState, onStatus, onError } = {}) {
    let ws = null;

    function open() {
      const proto = location.protocol === "https:" ? "wss" : "ws";
      ws = new WebSocket(`${proto}://${location.host}/ws`);
      ws.onopen = () => onStatus && onStatus(true);
      ws.onclose = () => { onStatus && onStatus(false); setTimeout(open, 2000); };
      ws.onmessage = (e) => {
        const msg = JSON.parse(e.data);
        if (msg.type === "error") onError ? onError(msg.message) : toast(msg.message);
        else onState && onState(msg);
      };
    }
    open();

    return {
      send(obj) {
        if (ws && ws.readyState === WebSocket.OPEN) ws.send(JSON.stringify(obj));
        else toast("Nu există conexiune cu serverul.");
      },
    };
  }

  function fmtTime(s) {
    if (s === null || s === undefined) return "–";
    const tenths = Math.floor(s * 10);              // trunchiem la zecimi
    const m = Math.floor(tenths / 600);
    const sec = (tenths % 600) / 10;
    return String(m).padStart(2, "0") + ":" + sec.toFixed(1).padStart(4, "0");
  }

  // Timpul scurs, calculat din starea serverului (offset = ceas server - ceas client)
  function elapsed(st, offset) {
    const t = st.timer;
    let e = t.elapsed_before_pause;
    if (t.state === "running") e += Date.now() / 1000 + offset - t.start;
    return Math.max(0, e);
  }

  function num(v) { return String(+Number(v).toFixed(2)); }

  function probaTitle(p) { return `${PROBA[p].name} · ${PROBA[p].label}`; }

  // Steag: static/flags/<cod>.svg, apoi .png, apoi dreptunghi alb (xx.svg)
  function flag(code) {
    const img = document.createElement("img");
    img.className = "flag";
    img.alt = "";
    const c = /^[a-z]{2}$/.test((code || "").toLowerCase()) ? code.toLowerCase() : "xx";
    const tries = [`/static/flags/${c}.svg`, `/static/flags/${c}.png`, "/static/flags/xx.svg"];
    let i = 0;
    img.src = tries[0];
    img.onerror = () => { if (++i < tries.length) img.src = tries[i]; else img.onerror = null; };
    return img;
  }

  let toastEl = null, toastTimer = null;
  function toast(msg) {
    if (!toastEl) {
      toastEl = document.createElement("div");
      toastEl.className = "toast";
      toastEl.hidden = true;
      document.body.appendChild(toastEl);
    }
    toastEl.textContent = msg;
    toastEl.hidden = false;
    clearTimeout(toastTimer);
    toastTimer = setTimeout(() => { toastEl.hidden = true; }, 4500);
  }

  return { PROBA, connect, fmtTime, elapsed, num, probaTitle, flag, toast };
})();
