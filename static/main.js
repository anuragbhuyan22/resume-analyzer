/* static/main.js — Upload page logic */

const zone      = document.getElementById('uploadZone');
const fileInput = document.getElementById('fileInput');
const browseBtn = document.getElementById('browseBtn');
const overlay   = document.getElementById('overlay');
const toast     = document.getElementById('toast');
const toastMsg  = document.getElementById('toastMsg');
const preview   = document.getElementById('filePreview');
const fileLabel = document.getElementById('fileName');
const stepEl    = document.getElementById('overlayStep');

let selectedFile = null;

// ── Browse button ──────────────────────────────────────────────────────────
browseBtn.addEventListener('click', (e) => {
  e.stopPropagation();
  fileInput.click();
});

// ── Click on zone ──────────────────────────────────────────────────────────
zone.addEventListener('click', () => fileInput.click());

// ── File selected via dialog ───────────────────────────────────────────────
fileInput.addEventListener('change', () => {
  if (fileInput.files.length) handleFile(fileInput.files[0]);
});

// ── Drag & Drop ────────────────────────────────────────────────────────────
zone.addEventListener('dragover', (e) => {
  e.preventDefault();
  zone.classList.add('drag-over');
});
zone.addEventListener('dragleave', () => zone.classList.remove('drag-over'));
zone.addEventListener('drop', (e) => {
  e.preventDefault();
  zone.classList.remove('drag-over');
  const file = e.dataTransfer.files[0];
  if (file) handleFile(file);
});

// ── Handle selected file ───────────────────────────────────────────────────
function handleFile(file) {
  const ext = file.name.split('.').pop().toLowerCase();
  if (!['pdf', 'docx'].includes(ext)) {
    showToast('Only PDF and DOCX files are supported.');
    return;
  }
  if (file.size > 16 * 1024 * 1024) {
    showToast('File too large. Maximum size is 16 MB.');
    return;
  }
  selectedFile = file;
  fileLabel.textContent = `${file.name} (${formatBytes(file.size)})`;
  preview.style.display = 'flex';
  
  // Start upload immediately for a smoother feel
  setTimeout(() => uploadFile(file), 400);
}

// ── Upload ─────────────────────────────────────────────────────────────────
async function uploadFile(file) {
  showOverlay();

  const steps = [
    'Parsing document layers…',
    'Executing NLP analysis…',
    'Mapping skills index…',
    'Synthesizing role matches…',
    'Finalizing report…',
  ];
  let stepIdx = 0;
  const stepTimer = setInterval(() => {
    if (stepIdx < steps.length - 1) stepEl.textContent = steps[++stepIdx];
  }, 1000);

  const formData = new FormData();
  formData.append('resume', file);

  try {
    const res  = await fetch('/upload', { method: 'POST', body: formData });
    const data = await res.json();

    clearInterval(stepTimer);

    if (!res.ok || data.error) {
      hideOverlay();
      showToast(data.error || 'Analysis failed. Please try again.');
      return;
    }

    // Smooth redirect
    setTimeout(() => {
      window.location.href = `/results/${data.id}`;
    }, 500);

  } catch (err) {
    clearInterval(stepTimer);
    hideOverlay();
    showToast('Network error. Please check your connection.');
  }
}

// ── Overlay helpers ────────────────────────────────────────────────────────
function showOverlay() {
  overlay.classList.add('active');
  stepEl.textContent = 'Parsing document layers…';
}
function hideOverlay() { overlay.classList.remove('active'); }

// ── Toast helper ───────────────────────────────────────────────────────────
function showToast(msg) {
  toastMsg.textContent = msg;
  toast.classList.add('active');
  setTimeout(() => toast.classList.remove('active'), 5000);
}

// ── Format bytes ───────────────────────────────────────────────────────────
function formatBytes(bytes) {
  if (bytes < 1024)       return bytes + ' B';
  if (bytes < 1048576)    return (bytes / 1024).toFixed(1) + ' KB';
  return (bytes / 1048576).toFixed(1) + ' MB';
}
