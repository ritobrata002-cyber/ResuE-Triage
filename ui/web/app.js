/**
 * RescuE-Triage Web Command Center Frontend Logic
 * Live REST polling, Canvas Crisis Radar, Web Audio Siren, and DEPI Calculator.
 */

// State
let audioAlertEnabled = true;
let previousCodeRedCount = 0;
let currentCallsData = [];
let audioCtx = null;

// DOM Elements
const kpiQueued = document.getElementById('kpiQueued');
const kpiCritical = document.getElementById('kpiCritical');
const kpiAvgDepi = document.getElementById('kpiAvgDepi');
const kpiFleet = document.getElementById('kpiFleet');
const systemClock = document.getElementById('systemClock');
const triageTableBody = document.getElementById('triageTableBody');
const fleetUnitList = document.getElementById('fleetUnitList');
const radarCanvas = document.getElementById('radarCanvas');
const radarCtx = radarCanvas.getContext('2d');

// Modals
const intakeModal = document.getElementById('intakeModal');
const formulaModal = document.getElementById('formulaModal');
const benchmarkModal = document.getElementById('benchmarkModal');
const openModalCallBtn = document.getElementById('openModalCallBtn');
const closeIntakeModal = document.getElementById('closeIntakeModal');
const cancelIntakeBtn = document.getElementById('cancelIntakeBtn');
const closeFormulaModal = document.getElementById('closeFormulaModal');
const openBenchmarkBtn = document.getElementById('openBenchmarkBtn');
const closeBenchmarkModal = document.getElementById('closeBenchmarkModal');
const soundToggleBtn = document.getElementById('soundToggleBtn');

// Buttons
const dispatchTopBtn = document.getElementById('dispatchTopBtn');
const loadPresetFloodBtn = document.getElementById('loadPresetFloodBtn');
const loadPresetQuakeBtn = document.getElementById('loadPresetQuakeBtn');
const loadPresetFireBtn = document.getElementById('loadPresetFireBtn');
const streamRandomCallBtn = document.getElementById('streamRandomCallBtn');
const resetFleetBtn = document.getElementById('resetFleetBtn');

// Form elements
const intakeForm = document.getElementById('intakeForm');
const medSlider = document.getElementById('medSlider');
const envSlider = document.getElementById('envSlider');
const medValDisplay = document.getElementById('medValDisplay');
const envValDisplay = document.getElementById('envValDisplay');
const previewDepiScore = document.getElementById('previewDepiScore');
const previewCategory = document.getElementById('previewCategory');
const chkInfant = document.getElementById('chkInfant');
const chkChild = document.getElementById('chkChild');
const chkElderly = document.getElementById('chkElderly');
const chkDisabled = document.getElementById('chkDisabled');
const chkPregnant = document.getElementById('chkPregnant');

// Sound Generator using Web Audio API
function playAlertBeep(frequency = 750, type = 'sine', duration = 0.25) {
  if (!audioAlertEnabled) return;
  try {
    if (!audioCtx) audioCtx = new (window.AudioContext || window.webkitAudioContext)();
    if (audioCtx.state === 'suspended') audioCtx.resume();
    const osc = audioCtx.createOscillator();
    const gain = audioCtx.createGain();
    osc.type = type;
    osc.frequency.setValueAtTime(frequency, audioCtx.currentTime);
    gain.gain.setValueAtTime(0.12, audioCtx.currentTime);
    gain.gain.exponentialRampToValueAtTime(0.001, audioCtx.currentTime + duration);
    osc.connect(gain);
    gain.connect(audioCtx.destination);
    osc.start();
    osc.stop(audioCtx.currentTime + duration);
  } catch (e) {
    console.warn('Audio not allowed or supported:', e);
  }
}

// Toggle Sound
soundToggleBtn.addEventListener('click', () => {
  audioAlertEnabled = !audioAlertEnabled;
  soundToggleBtn.textContent = audioAlertEnabled ? '🔊 Siren: ON' : '🔇 Siren: OFF';
  soundToggleBtn.style.color = audioAlertEnabled ? '#38BDF8' : '#94A3B8';
  if (audioAlertEnabled) playAlertBeep(880, 'sine', 0.15);
});

// Live Form Preview Calculation
function updateIntakePreview() {
  const med = parseInt(medSlider.value);
  const env = parseInt(envSlider.value);
  medValDisplay.textContent = `${med} / 10`;
  envValDisplay.textContent = `${env} / 10`;

  let vulnFactor = 1.0;
  if (chkInfant.checked) vulnFactor += 1.5;
  if (chkDisabled.checked) vulnFactor += 1.5;
  if (chkElderly.checked) vulnFactor += 1.0;
  if (chkPregnant.checked) vulnFactor += 1.0;
  if (chkChild.checked) vulnFactor += 0.8;
  vulnFactor = Math.min(5.0, vulnFactor);

  const depi = (4.5 * med) + (3.0 * env) + (3.0 * vulnFactor);
  previewDepiScore.textContent = depi.toFixed(1);

  if (depi >= 75) {
    previewCategory.textContent = 'CODE RED';
    previewCategory.className = 'triage-badge badge-red';
  } else if (depi >= 55) {
    previewCategory.textContent = 'CODE ORANGE';
    previewCategory.className = 'triage-badge badge-orange';
  } else if (depi >= 35) {
    previewCategory.textContent = 'CODE YELLOW';
    previewCategory.className = 'triage-badge badge-yellow';
  } else {
    previewCategory.textContent = 'CODE GREEN';
    previewCategory.className = 'triage-badge badge-green';
  }
}

[medSlider, envSlider, chkInfant, chkChild, chkElderly, chkDisabled, chkPregnant].forEach(el => {
  el.addEventListener('input', updateIntakePreview);
});

// Modal Handlers
openModalCallBtn.addEventListener('click', () => {
  updateIntakePreview();
  intakeModal.classList.add('active');
});
closeIntakeModal.addEventListener('click', () => intakeModal.classList.remove('active'));
cancelIntakeBtn.addEventListener('click', () => intakeModal.classList.remove('active'));

closeFormulaModal.addEventListener('click', () => formulaModal.classList.remove('active'));
closeBenchmarkModal.addEventListener('click', () => benchmarkModal.classList.remove('active'));

window.addEventListener('click', (e) => {
  if (e.target === intakeModal) intakeModal.classList.remove('active');
  if (e.target === formulaModal) formulaModal.classList.remove('active');
  if (e.target === benchmarkModal) benchmarkModal.classList.remove('active');
});

// Submit Call
intakeForm.addEventListener('submit', async (e) => {
  e.preventDefault();
  const payload = {
    caller_name: document.getElementById('callerName').value,
    phone: document.getElementById('callerPhone').value,
    location: document.getElementById('callLocation').value,
    disaster_type: document.getElementById('disasterType').value,
    medical_urgency: parseInt(medSlider.value),
    environmental_hazard: parseInt(envSlider.value),
    description: document.getElementById('callNarrative').value,
    vulnerability: {
      infants: chkInfant.checked ? 1 : 0,
      children: chkChild.checked ? 1 : 0,
      elderly: chkElderly.checked ? 1 : 0,
      disabled: chkDisabled.checked ? 1 : 0,
      pregnant: chkPregnant.checked ? 1 : 0,
    }
  };

  try {
    const res = await fetch('/api/call/new', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload)
    });
    const data = await res.json();
    intakeModal.classList.remove('active');
    playAlertBeep(600, 'triangle', 0.2);
    fetchStatus();
  } catch (err) {
    alert('Error adding call: ' + err.message);
  }
});

// Dispatch Top
dispatchTopBtn.addEventListener('click', async () => {
  try {
    const res = await fetch('/api/dispatch/top', { method: 'POST' });
    const data = await res.json();
    if (data.error) {
      alert(data.error);
    } else {
      playAlertBeep(850, 'sawtooth', 0.3);
      alert(`⚡ DISPATCH SUCCESSFUL!\n\nDispatched Unit: ${data.unit.name} (${data.unit.id})\nTo Ticket: ${data.call.id}\nCaller: ${data.call.caller_name}\nLocation: ${data.call.location}\nPriority: ${data.call.current_depi} (${data.call.category})`);
      fetchStatus();
    }
  } catch (err) {
    alert('Dispatch failed: ' + err.message);
  }
});

// Scenarios
loadPresetFloodBtn.addEventListener('click', () => loadScenario('urban_flood'));
loadPresetQuakeBtn.addEventListener('click', () => loadScenario('earthquake'));
loadPresetFireBtn.addEventListener('click', () => loadScenario('highrise_fire'));

async function loadScenario(preset) {
  await fetch('/api/scenario/load', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ preset })
  });
  playAlertBeep(520, 'sine', 0.25);
  fetchStatus();
}

streamRandomCallBtn.addEventListener('click', async () => {
  await fetch('/api/call/random', { method: 'POST' });
  playAlertBeep(700, 'sine', 0.15);
  fetchStatus();
});

resetFleetBtn.addEventListener('click', async () => {
  if (confirm('Reset entire triage queue and fleet state?')) {
    await fetch('/api/reset', { method: 'POST' });
    fetchStatus();
  }
});

// Benchmark modal
openBenchmarkBtn.addEventListener('click', async () => {
  benchmarkModal.classList.add('active');
  document.getElementById('benchmarkLoading').style.display = 'block';
  document.getElementById('benchmarkContent').style.display = 'none';

  try {
    const res = await fetch('/api/benchmark');
    const data = await res.json();
    const tbody = document.getElementById('benchmarkTableBody');
    tbody.innerHTML = '';

    for (const [key, val] of Object.entries(data.benchmark)) {
      const row = document.createElement('tr');
      row.innerHTML = `
        <td><strong>${key}</strong></td>
        <td>${val.Heap_Insert_Total_Sec.toFixed(5)}s</td>
        <td>${val.Heap_Extract100_Sec.toFixed(5)}s</td>
        <td>${val.Naive_Extract100_Sec.toFixed(5)}s</td>
        <td><strong style="color: #38BDF8;">${val.Heap_Speedup_Factor}x faster</strong></td>
      `;
      tbody.appendChild(row);
    }

    document.getElementById('benchmarkLoading').style.display = 'none';
    document.getElementById('benchmarkContent').style.display = 'block';
  } catch (err) {
    alert('Benchmark error: ' + err.message);
  }
});

// Inspect Formula Breakdown
window.inspectFormula = function(callId) {
  const call = currentCallsData.find(c => c.id === callId);
  if (!call) return;

  const content = document.getElementById('formulaModalContent');
  const b = call.breakdown || {};

  content.innerHTML = `
    <div style="background: rgba(0,0,0,0.4); padding: 14px; border-radius: 8px; border: 1px solid rgba(255,255,255,0.08);">
      <div style="font-size: 11px; color: #94A3B8;">INCIDENT TICKET: ${call.id}</div>
      <div style="font-size: 18px; font-weight: 700; color: white; margin: 4px 0;">${call.caller_name} &bull; ${call.location}</div>
      <div style="font-size: 12px; color: #38BDF8;">Context: ${call.disaster_type}</div>
    </div>

    <div style="display: flex; justify-content: space-between; align-items: center; background: rgba(255,255,255,0.02); padding: 12px; border-radius: 8px;">
      <div>
        <div style="font-size: 11px; color: #94A3B8;">CALCULATED DEPI INDEX</div>
        <div style="font-size: 28px; font-weight: 800; font-family: 'JetBrains Mono'; color: #38BDF8;">${call.current_depi.toFixed(2)} / 100</div>
      </div>
      <div>
        <span class="triage-badge ${call.category === 'CODE_RED' ? 'badge-red' : (call.category === 'CODE_ORANGE' ? 'badge-orange' : (call.category === 'CODE_YELLOW' ? 'badge-yellow' : 'badge-green'))}">
          ${call.category}
        </span>
      </div>
    </div>

    <div style="background: rgba(0,0,0,0.3); padding: 14px; border-radius: 8px; border: 1px solid rgba(255,255,255,0.06);">
      <h4 style="font-size: 12px; color: #F1F5F9; margin-bottom: 8px; text-transform: uppercase;">Mathematical Formulation:</h4>
      <div style="font-family: 'JetBrains Mono'; font-size: 12px; color: #FBBF24; margin-bottom: 12px;">
        ${b.formula_expression || 'DEPI = (4.5×M) + (3.0×H) + (3.0×V) + f(Δt)'}
      </div>

      <div style="display: grid; grid-template-columns: 1fr auto; row-gap: 8px; font-size: 12px;">
        <span style="color: #94A3B8;">1. Medical Urgency (4.5 × ${call.medical_urgency}):</span>
        <strong style="color: #EF4444;">+ ${(b.medical_component || 0).toFixed(2)} pts</strong>

        <span style="color: #94A3B8;">2. Environmental Hazard (3.0 × ${call.environmental_hazard}):</span>
        <strong style="color: #F97316;">+ ${(b.environmental_component || 0).toFixed(2)} pts</strong>

        <span style="color: #94A3B8;">3. Vulnerability Multiplier (3.0 × ${(call.vulnerability_score || 1).toFixed(2)}):</span>
        <strong style="color: #A855F7;">+ ${(b.vulnerability_component || 0).toFixed(2)} pts</strong>

        <span style="color: #94A3B8;">4. Dynamic Wait Aging Bonus (f(Δt = ${call.wait_time_minutes}m)):</span>
        <strong style="color: #10B981;">+ ${(b.wait_time_component || 0).toFixed(2)} pts</strong>
      </div>
    </div>

    <div style="font-size: 12px; color: #94A3B8; font-style: italic;">
      "${call.description || 'No additional narrative logged.'}"
    </div>
  `;

  formulaModal.classList.add('active');
};

// Resolve Incident
window.resolveCall = async function(callId) {
  await fetch('/api/call/resolve', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ call_id: callId })
  });
  fetchStatus();
};

// Fetch Main Status
async function fetchStatus() {
  try {
    const res = await fetch('/api/status');
    const data = await res.json();

    // KPIs
    kpiQueued.textContent = data.summary.queued_count;
    kpiCritical.textContent = data.summary.code_red_critical;
    kpiAvgDepi.textContent = data.summary.avg_depi_score.toFixed(1);
    systemClock.textContent = `CLOCK: ${data.clock}`;

    const availUnits = data.units.filter(u => u.status === 'AVAILABLE').length;
    kpiFleet.textContent = `${availUnits} / ${data.units.length}`;

    // Alert sound on new Code Red
    if (data.summary.code_red_critical > previousCodeRedCount) {
      playAlertBeep(920, 'sawtooth', 0.4);
    }
    previousCodeRedCount = data.summary.code_red_critical;

    // Combine queued + dispatched
    currentCallsData = [...data.queued, ...data.dispatched];

    // Render Table
    renderTable(currentCallsData);

    // Render Fleet
    renderFleet(data.units);

    // Render Canvas Radar
    drawRadar(currentCallsData);

  } catch (err) {
    console.warn('Status poll warning:', err);
  }
}

function renderTable(calls) {
  triageTableBody.innerHTML = '';
  if (calls.length === 0) {
    triageTableBody.innerHTML = `<tr><td colspan="12" style="text-align: center; color: #64748B; padding: 24px;">No active distress calls in triage. Queue idle.</td></tr>`;
    return;
  }

  calls.forEach((c, idx) => {
    const tr = document.createElement('tr');
    if (c.category === 'CODE_RED') tr.className = 'tier-red';
    else if (c.category === 'CODE_ORANGE') tr.className = 'tier-orange';

    const badgeClass = c.category === 'CODE_RED' ? 'badge-red' : (
      c.category === 'CODE_ORANGE' ? 'badge-orange' : (
        c.category === 'CODE_YELLOW' ? 'badge-yellow' : 'badge-green'
      )
    );

    const isDispatched = c.status === 'DISPATCHED';

    tr.innerHTML = `
      <td><strong>${idx + 1}</strong></td>
      <td><span style="font-family: 'JetBrains Mono'; font-size: 11px;">${c.id}</span></td>
      <td class="depi-score-cell">${c.current_depi.toFixed(1)}</td>
      <td><span class="triage-badge ${badgeClass}">${c.category.replace('_', ' ')}</span></td>
      <td class="caller-cell">
        <span class="caller-name">${c.caller_name}</span>
        <span class="caller-loc">📍 ${c.location}</span>
      </td>
      <td><span style="font-size: 12px;">${c.disaster_type}</span></td>
      <td><strong style="color: #EF4444;">${c.medical_urgency}</strong></td>
      <td><strong style="color: #F97316;">${c.environmental_hazard}</strong></td>
      <td>${c.vulnerability_score ? c.vulnerability_score.toFixed(1) : '1.0'}</td>
      <td><span style="font-family: 'JetBrains Mono';">${c.wait_time_minutes}m</span></td>
      <td>
        <span style="font-size: 11px; font-weight: 700; color: ${isDispatched ? '#F59E0B' : '#38BDF8'};">
          ${isDispatched ? '🚑 DISPATCHED' : '⏳ QUEUED'}
        </span>
      </td>
      <td>
        <div style="display: flex; gap: 4px;">
          <button class="btn-icon" onclick="inspectFormula('${c.id}')" title="Inspect Formula Breakdown">🔍</button>
          <button class="btn-icon" onclick="resolveCall('${c.id}')" title="Resolve Incident" style="color: #10B981;">✅</button>
        </div>
      </td>
    `;
    triageTableBody.appendChild(tr);
  });
}

function renderFleet(units) {
  fleetUnitList.innerHTML = '';
  units.forEach(u => {
    const isAvail = u.status === 'AVAILABLE';
    const div = document.createElement('div');
    div.className = 'fleet-unit-card';
    div.innerHTML = `
      <div>
        <div class="fleet-name">${u.name} (${u.id})</div>
        <div class="fleet-type">${u.type}</div>
      </div>
      <div>
        <span class="fleet-badge ${isAvail ? 'fleet-ready' : 'fleet-deployed'}">
          ${isAvail ? 'READY' : 'DEPLOYED'}
        </span>
      </div>
    `;
    fleetUnitList.appendChild(div);
  });
}

// Draw Crisis Radar Canvas
let radarAngle = 0;
function drawRadar(calls) {
  const w = radarCanvas.width;
  const h = radarCanvas.height;
  const cx = w / 2;
  const cy = h / 2;
  const r = Math.min(cx, cy) - 15;

  radarCtx.fillStyle = '#080D17';
  radarCtx.fillRect(0, 0, w, h);

  // Concentric Rings
  radarCtx.strokeStyle = 'rgba(56, 189, 248, 0.15)';
  radarCtx.lineWidth = 1;
  for (let i = 1; i <= 3; i++) {
    radarCtx.beginPath();
    radarCtx.arc(cx, cy, (r / 3) * i, 0, Math.PI * 2);
    radarCtx.stroke();
  }

  // Crosshairs
  radarCtx.beginPath();
  radarCtx.moveTo(cx, cy - r);
  radarCtx.lineTo(cx, cy + r);
  radarCtx.moveTo(cx - r, cy);
  radarCtx.lineTo(cx + r, cy);
  radarCtx.stroke();

  // Sweeping Radar Line
  radarAngle += 0.04;
  radarCtx.strokeStyle = 'rgba(56, 189, 248, 0.4)';
  radarCtx.lineWidth = 2;
  radarCtx.beginPath();
  radarCtx.moveTo(cx, cy);
  radarCtx.lineTo(cx + r * Math.cos(radarAngle), cy + r * Math.sin(radarAngle));
  radarCtx.stroke();

  // Plot Incident Markers
  calls.forEach((c, i) => {
    const hash = (c.id.charCodeAt(5) || 1) * 37 + (i * 59);
    const angle = (hash % 360) * (Math.PI / 180);
    const dist = 30 + ((hash * 13) % (r - 40));

    const px = cx + dist * Math.cos(angle);
    const py = cy + dist * Math.sin(angle);

    let color = '#10B981';
    let dotRadius = 4;
    if (c.category === 'CODE_RED') {
      color = '#EF4444';
      dotRadius = 6;
      // Pulsing outer halo for red
      radarCtx.beginPath();
      radarCtx.arc(px, py, dotRadius + 4 + Math.sin(radarAngle * 3) * 2, 0, Math.PI * 2);
      radarCtx.fillStyle = 'rgba(239, 68, 68, 0.3)';
      radarCtx.fill();
    } else if (c.category === 'CODE_ORANGE') {
      color = '#F97316';
      dotRadius = 5;
    } else if (c.category === 'CODE_YELLOW') {
      color = '#FBBF24';
    }

    radarCtx.beginPath();
    radarCtx.arc(px, py, dotRadius, 0, Math.PI * 2);
    radarCtx.fillStyle = color;
    radarCtx.fill();
  });
}

// Initial status fetch and polling every 1.5 seconds
fetchStatus();
setInterval(fetchStatus, 1500);
