const themeToggle = document.getElementById("theme-toggle");
const appTheme = localStorage.getItem("theme") || "dark";
applyTheme(appTheme);

themeToggle.addEventListener("click", ()=> {
  const n = document.body.getAttribute("data-theme")==="light"?"dark":"light";
  applyTheme(n);
});

function applyTheme(t){
  document.body.setAttribute("data-theme", t);
  localStorage.setItem("theme", t);
  themeToggle.textContent = t==="light"?"🌞":"🌙";
}

window.addEventListener("load", ()=> {
  const s = document.getElementById("splash");
  setTimeout(()=> s.style.opacity="0", 400);
  setTimeout(()=> s.remove(), 900);
});

/* PLAYER */
const player = document.getElementById("player");
const toggle = document.getElementById("play-toggle");
toggle.addEventListener("click", ()=> {
  if(player.paused) { player.play(); toggle.textContent="Pause"; }
  else { player.pause(); toggle.textContent="Play"; }
});

/* PROGRAMM */
fetch("data/programm.json")
  .then(r=>r.json())
  .then(list=>{
    document.getElementById("programm").innerHTML =
      list.map(e=>`<div>${e.time} — ${e.title}</div>`).join("");
  });

/* MEDIATHEK */
fetch("data/mediathek.json")
  .then(r=>r.json())
  .then(list=>{
    document.getElementById("mediathek").innerHTML =
      list.map(e=>`<div>${e.date} – ${e.title}</div>`).join("");
  });

/* SERVICE WORKER */
if('serviceWorker' in navigator){
  navigator.serviceWorker.register("service-worker.js");
}
