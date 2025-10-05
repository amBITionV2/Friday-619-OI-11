const API = {
  start: '/start_orb',
  stop: '/stop_orb',
  status: '/status',
};

const toggleBtn = document.getElementById('toggle-btn');
const statusText = document.getElementById('status-text');
const orb = document.getElementById('orb');

let isOn = false;

async function setStatus(s) { statusText.textContent = s; }

async function startOrb() {
  setStatus('starting...');
  const res = await fetch(API.start, { method: 'POST' });
  const j = await res.json();
  if (j.success) {
    isOn = true;
    toggleBtn.classList.remove('off');
    toggleBtn.classList.add('on');
    toggleBtn.textContent = 'Stop FRIDAY';
    orb.style.animationPlayState = 'running';
    setStatus('running');
  } else setStatus('error');
}

async function stopOrb() {
  setStatus('stopping...');
  const res = await fetch(API.stop, { method: 'POST' });
  const j = await res.json();
  if (j.success) {
    isOn = false;
    toggleBtn.classList.remove('on');
    toggleBtn.classList.add('off');
    toggleBtn.textContent = 'Start FRIDAY';
    orb.style.animationPlayState = 'paused';
    setStatus('stopped');
  } else setStatus('error');
}

toggleBtn.addEventListener('click', () => {
  if (isOn) stopOrb(); else startOrb();
});

// Initialize orb animation as paused
orb.style.animationPlayState = 'paused';
