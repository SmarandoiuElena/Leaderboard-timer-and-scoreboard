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

    // Steag emoji din codul de tara (ISO 3166, ex. ro -> 🇷🇴). Cod lipsa sau "xx" -> 🏳️
  function flag(code) {
    const span = document.createElement("span");
    span.className = "flag";
    const c = (code || "").toLowerCase();
    span.textContent = /^[a-z]{2}$/.test(c) && c !== "xx"
      ? String.fromCodePoint(...[...c.toUpperCase()].map((ch) => 0x1F1E6 + ch.charCodeAt(0) - 65))
      : "🏳️";
    return span;
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
