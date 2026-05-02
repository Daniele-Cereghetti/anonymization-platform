/**
 * Flusso in 3 fasi:
 *   1. /api/convert  — Upload file → testo Markdown
 *   2. /api/extract  — Estrazione entità → tabella di mappatura
 *   3. /api/anonymize — Sostituzione semantica → documento .md finale
 */

'use strict';

// ===========================================================================
// CONFIGURAZIONE
// ===========================================================================

const API_BASE_URL = 'http://localhost:8000';

// Categorie di entità da anonimizzare (da 2.1.2 della documentazione)
const CATEGORIES = [
  {
    id: 'persone_fisiche',
    label: 'Persone fisiche',
    description: 'Nomi, cognomi, soprannomi',
    icon: 'bi-person',
    color: 'danger',
  },
  {
    id: 'persone_giuridiche',
    label: 'Persone giuridiche',
    description: 'Aziende, enti, associazioni',
    icon: 'bi-building',
    color: 'warning',
  },
  {
    id: 'dati_contatto',
    label: 'Dati di contatto',
    description: 'Telefono, email, indirizzi, URL',
    icon: 'bi-telephone',
    color: 'info',
  },
  {
    id: 'identificativi',
    label: 'Identificativi univoci',
    description: 'AVS/AHV, CF, passaporto, patente',
    icon: 'bi-card-text',
    color: 'primary',
  },
  {
    id: 'dati_finanziari',
    label: 'Dati finanziari',
    description: 'IBAN, carte di credito, BIC/SWIFT',
    icon: 'bi-credit-card',
    color: 'success',
  },
  {
    id: 'dati_temporali',
    label: 'Dati temporali',
    description: 'Date di nascita, date sensibili',
    icon: 'bi-calendar-date',
    color: 'secondary',
  },
  {
    id: 'luoghi',
    label: 'Luoghi specifici',
    description: 'Domicilio, coordinate GPS, edifici',
    icon: 'bi-geo-alt',
    color: 'dark',
  },
  {
    id: 'dati_biometrici',
    label: 'Dati biometrici',
    description: 'Dati biometrici o genetici',
    icon: 'bi-fingerprint',
    color: 'danger',
  },
];

// Colori badge per categoria nella tabella
const CATEGORY_BADGE_CLASS = {
  persone_fisiche:    'bg-danger',
  persone_giuridiche: 'bg-warning text-dark',
  dati_contatto:      'bg-info text-dark',
  identificativi:     'bg-primary',
  dati_finanziari:    'bg-success',
  dati_temporali:     'bg-secondary',
  luoghi:             'bg-dark',
  dati_biometrici:    'bg-danger',
};

// ===========================================================================
// STATO APPLICAZIONE
// ===========================================================================

const state = {
  currentStep: 1,
  selectedFile: null,
  convertedText: '',          // testo .md risultato di /convert
  documentId: null,           // id restituito da /convert, riusato da /extract e /anonymize
  mappingRows: [],            // Array di {id, original, category, substitution, status}
  anonymizedText: '',         // testo .md risultato di /anonymize
  anonymizedFilename: 'documento_anonimizzato.md',
  documentType: null,         // tipo documento rilevato/forzato (cv|medical|contract|invoice|legal|letter|null)
  language: null,             // lingua rilevata dal backend (it|en|fr|de) — usata per localizzare i placeholder
};

// ===========================================================================
// UTILITIES
// ===========================================================================

function formatBytes(bytes) {
  if (bytes < 1024) return bytes + ' B';
  if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(1) + ' KB';
  return (bytes / (1024 * 1024)).toFixed(1) + ' MB';
}

function generateId() {
  return Math.random().toString(36).slice(2, 9);
}

function showToast(message, type = 'info') {
  const icons = {
    success: '<i class="bi bi-check-circle-fill text-success me-2"></i>',
    danger:  '<i class="bi bi-x-circle-fill text-danger me-2"></i>',
    warning: '<i class="bi bi-exclamation-triangle-fill text-warning me-2"></i>',
    info:    '<i class="bi bi-info-circle-fill text-primary me-2"></i>',
  };

  const toastEl = document.getElementById('toastEl');
  const toastBody = document.getElementById('toastBody');

  toastEl.className = `toast align-items-center border-0 text-bg-${type === 'info' ? 'light' : type}`;
  toastBody.innerHTML = (icons[type] || icons.info) + message;

  const toast = bootstrap.Toast.getOrCreateInstance(toastEl, { delay: 4000 });
  toast.show();
}

function showLoading(message, subMessage = '') {
  document.getElementById('loadingMessage').textContent = message;
  document.getElementById('loadingSubMessage').textContent = subMessage;
  document.getElementById('loadingOverlay').classList.remove('d-none');
}

function hideLoading() {
  document.getElementById('loadingOverlay').classList.add('d-none');
}

async function apiCall(endpoint, options = {}, timeoutMs = 360000) {
  const controller = new AbortController();
  const timer = setTimeout(() => controller.abort(), timeoutMs);
  const url = `${API_BASE_URL}${endpoint}`;
  try {
    const response = await fetch(url, { ...options, signal: controller.signal });
    if (!response.ok) {
      const err = await response.json().catch(() => ({ detail: response.statusText }));
      throw new Error(err.detail || `Errore HTTP ${response.status}`);
    }
    return response.json();
  } catch (err) {
    if (err.name === 'AbortError') throw new Error('Timeout: il server non ha risposto in tempo. Riprova.');
    throw err;
  } finally {
    clearTimeout(timer);
  }
}

// ===========================================================================
// STEP NAVIGATION
// ===========================================================================

function goToStep(step) {
  [1, 2, 3].forEach(s => {
    document.getElementById(`step${s}`).classList.toggle('d-none', s !== step);
  });

  // Update step circles
  [1, 2, 3].forEach(s => {
    const circle = document.getElementById(`stepCircle${s}`);
    circle.classList.remove('active', 'completed');
    if (s < step) {
      circle.classList.add('completed');
      circle.innerHTML = '<i class="bi bi-check-lg"></i>';
    } else if (s === step) {
      circle.classList.add('active');
      const icons = ['bi-upload', 'bi-search', 'bi-file-earmark-check'];
      circle.innerHTML = `<i class="bi ${icons[s - 1]}"></i>`;
    } else {
      const icons = ['bi-upload', 'bi-search', 'bi-file-earmark-check'];
      circle.innerHTML = `<i class="bi ${icons[s - 1]}"></i>`;
    }
  });

  // Update step lines
  [1, 2].forEach(s => {
    const line = document.getElementById(`stepLine${s}`);
    line.classList.toggle('active', s < step);
  });

  state.currentStep = step;
  window.scrollTo({ top: 0, behavior: 'smooth' });
}

// ===========================================================================
// STEP 1 — INGESTIONE E NORMALIZZAZIONE
// ===========================================================================

function initDropZone() {
  const dropZone = document.getElementById('dropZone');
  const fileInput = document.getElementById('fileInput');

  dropZone.addEventListener('dragover', e => {
    e.preventDefault();
    dropZone.classList.add('drag-over');
  });

  dropZone.addEventListener('dragleave', () => {
    dropZone.classList.remove('drag-over');
  });

  dropZone.addEventListener('drop', e => {
    e.preventDefault();
    dropZone.classList.remove('drag-over');
    const file = e.dataTransfer.files[0];
    if (file) setFile(file);
  });

  dropZone.addEventListener('click', () => fileInput.click());

  fileInput.addEventListener('change', () => {
    if (fileInput.files[0]) setFile(fileInput.files[0]);
  });
}

function setFile(file) {
  const allowed = ['.pdf', '.docx', '.doc', '.txt', '.rtf', '.odt', '.html', '.htm'];
  const ext = '.' + file.name.split('.').pop().toLowerCase();

  if (!allowed.includes(ext)) {
    showToast(`Formato non supportato: ${ext}`, 'danger');
    return;
  }

  state.selectedFile = file;

  document.getElementById('fileName').textContent = file.name;
  document.getElementById('fileSize').textContent = formatBytes(file.size);
  document.getElementById('fileInfo').classList.remove('d-none');
  document.getElementById('btnConvert').disabled = false;

  // Reset preview if re-selecting
  document.getElementById('previewSection').classList.add('d-none');
  document.getElementById('markdownPreview').innerHTML = '';
  document.getElementById('rawText').textContent = '';
  state.convertedText = '';
}

function removeFile() {
  state.selectedFile = null;
  document.getElementById('fileInfo').classList.add('d-none');
  document.getElementById('btnConvert').disabled = true;
  document.getElementById('previewSection').classList.add('d-none');
  document.getElementById('fileInput').value = '';
  state.convertedText = '';
}

async function convertDocument() {
  if (!state.selectedFile) return;

  showLoading(
    'Normalizzazione del documento in corso…',
    'Il file sorgente viene parsato (estrazione di testo, layout e tabelle) e convertito nel formato canonico Markdown utilizzato dalle fasi successive. La durata dipende dalla dimensione e dalla complessità del documento. Non chiudere la pagina.'
  );

  try {
    const formData = new FormData();
    formData.append('file', state.selectedFile);

    const result = await apiCall('/api/convert', { method: 'POST', body: formData });

    state.convertedText = result.content;
    state.documentId = result.document_id;

    // Il testo è cambiato: azzera l'estrazione precedente
    state.mappingRows = [];
    state.documentType = null;
    const docTypeSelect = document.getElementById('docTypeSelect');
    if (docTypeSelect) docTypeSelect.value = '';
    document.getElementById('mappingSection').classList.add('d-none');

    // Render markdown preview
    document.getElementById('markdownPreview').innerHTML = marked.parse(state.convertedText);
    document.getElementById('rawText').textContent = state.convertedText;
    document.getElementById('previewSection').classList.remove('d-none');

    showToast('Normalizzazione completata.', 'success');
  } catch (err) {
    showToast(`Errore nella normalizzazione: ${err.message}`, 'danger');
  } finally {
    hideLoading();
  }
}

function togglePreviewView(showRaw) {
  document.getElementById('markdownPreview').classList.toggle('d-none', showRaw);
  document.getElementById('rawPreview').classList.toggle('d-none', !showRaw);
  document.getElementById('btnViewRendered').classList.toggle('active', !showRaw);
  document.getElementById('btnViewRaw').classList.toggle('active', showRaw);
}

// ===========================================================================
// STEP 2 — ESTRAZIONE E VALIDAZIONE
// ===========================================================================

function initCategoryCheckboxes() {
  const container = document.getElementById('categoryCheckboxes');

  CATEGORIES.forEach(cat => {
    const col = document.createElement('div');
    col.className = 'col-12 col-sm-6 col-md-4 col-lg-3';

    col.innerHTML = `
      <label class="category-card d-flex align-items-start gap-2 w-100 selected" data-cat="${cat.id}">
        <input type="checkbox" class="category-checkbox form-check-input mt-0 flex-shrink-0"
               id="cat_${cat.id}" value="${cat.id}" checked />
        <div>
          <div class="d-flex align-items-center gap-1 fw-semibold" style="font-size:0.82rem;">
            <i class="bi ${cat.icon} text-${cat.color}"></i> ${cat.label}
          </div>
          <div class="text-muted" style="font-size:0.72rem;">${cat.description}</div>
        </div>
      </label>
    `;

    const card = col.querySelector('.category-card');
    const checkbox = col.querySelector('input');

    checkbox.addEventListener('change', () => {
      card.classList.toggle('selected', checkbox.checked);
    });

    card.addEventListener('click', e => {
      if (e.target !== checkbox) {
        checkbox.checked = !checkbox.checked;
        card.classList.toggle('selected', checkbox.checked);
      }
    });

    container.appendChild(col);
  });
}

function getSelectedCategories() {
  return [...document.querySelectorAll('.category-checkbox:checked')].map(cb => cb.value);
}

function selectAllCategories(select) {
  document.querySelectorAll('.category-checkbox').forEach(cb => {
    cb.checked = select;
    cb.closest('.category-card').classList.toggle('selected', select);
  });
}

async function extractEntities() {
  const categories = getSelectedCategories();

  if (categories.length === 0) {
    showToast('Selezionare almeno una categoria di entità.', 'warning');
    return;
  }

  // Nascondi i risultati precedenti prima di mostrare il loading
  document.getElementById('mappingSection').classList.add('d-none');

  showLoading(
    'Riconoscimento entità (NER) in corso…',
    'Il modello LLM locale sta analizzando il testo per identificare entità nominative (PII) appartenenti alle categorie selezionate e proporre i relativi placeholder. L\'inferenza avviene interamente in locale, senza invio dati a servizi esterni; il tempo richiesto dipende dalla lunghezza del documento e dalle risorse hardware disponibili. Non chiudere la pagina.'
  );

  try {
    const payload = { document_id: state.documentId, categories };
    if (state.documentType) {
      payload.document_type = state.documentType;
    }
    const result = await apiCall('/api/extract', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload),
    });

    // Sync detected document type with the dropdown (only when the user
    // hasn't forced an override — in that case keep their choice visible).
    state.documentType = result.document_type || state.documentType || null;
    state.language = result.language || null;
    const docTypeSelect = document.getElementById('docTypeSelect');
    if (docTypeSelect) {
      docTypeSelect.value = state.documentType || '';
    }

    // Build mapping rows. Il backend pre-computa il placeholder finale
    // (con il ruolo del proprietario, es. [DATA_NASCITA_CANDIDATO_1]) e lo
    // restituisce in entity.proposed_replacement.  Lo usiamo come default
    // per la sostituzione mostrata in tabella; il fallback su entity_type
    // copre solo il caso in cui il backend non lo abbia popolato.
    const fallbackCounters = {};
    state.mappingRows = (result.entities || []).map(e => {
      let substitution = e.proposed_replacement;
      if (!substitution) {
        const label = (e.entity_type || e.category || 'entita').toUpperCase();
        fallbackCounters[label] = (fallbackCounters[label] || 0) + 1;
        substitution = `[${label}_${fallbackCounters[label]}]`;
      }
      return {
        id: generateId(),
        original: e.value,
        category: e.category,
        entity_type: e.entity_type,
        semantic_role: e.semantic_role || null,
        substitution,
        status: 'proposed',   // proposed | accepted | removed
      };
    });

    renderMappingTable();
    document.getElementById('mappingSection').classList.remove('d-none');

    if (state.mappingRows.length === 0) {
      document.getElementById('mappingEmpty').classList.remove('d-none');
      document.getElementById('mappingTable').classList.add('d-none');
    } else {
      document.getElementById('mappingEmpty').classList.add('d-none');
      document.getElementById('mappingTable').classList.remove('d-none');
    }

    showToast(`${state.mappingRows.length} entità rilevate.`, 'success');
  } catch (err) {
    showToast(`Errore nel riconoscimento entità: ${err.message}`, 'danger');
  } finally {
    hideLoading();
  }
}

function renderMappingTable() {
  const tbody = document.getElementById('mappingTableBody');
  tbody.innerHTML = '';

  state.mappingRows.forEach(row => {
    const tr = document.createElement('tr');
    tr.id = `row_${row.id}`;
    tr.className = `row-${row.status}`;

    const catLabel = CATEGORIES.find(c => c.id === row.category)?.label || row.category;
    const badgeClass = CATEGORY_BADGE_CLASS[row.category] || 'bg-secondary';
    const isRemoved = row.status === 'removed';
    const roleCell = row.semantic_role
      ? `<span class="badge bg-light text-dark border" style="font-size:0.68rem;">${escapeHtml(row.semantic_role)}</span>`
      : `<span class="text-muted small">&mdash;</span>`;

    tr.innerHTML = `
      <td>
        <span class="entity-text">${escapeHtml(row.original)}</span>
      </td>
      <td>
        <span class="badge ${badgeClass}" style="font-size:0.7rem;">${escapeHtml(catLabel)}</span>
      </td>
      <td>${roleCell}</td>
      <td>
        <span class="substitution-display">${escapeHtml(row.substitution)}</span>
      </td>
      <td>${statusBadge(row.status)}</td>
      <td>
        ${isRemoved
          ? `<button class="btn btn-sm btn-outline-secondary" onclick="restoreRow('${row.id}')" title="Reintroduci entità">
               <i class="bi bi-arrow-counterclockwise"></i>
             </button>`
          : `<button class="btn btn-sm btn-outline-success me-1" onclick="acceptRow('${row.id}')" title="Accetta placeholder">
               <i class="bi bi-check-lg"></i>
             </button>
             <button class="btn btn-sm btn-outline-danger" onclick="removeRow('${row.id}')" title="Scarta entità">
               <i class="bi bi-x-lg"></i>
             </button>`
        }
      </td>
    `;

    tbody.appendChild(tr);
  });

  updateMappingStats();
}

function statusBadge(status) {
  const map = {
    proposed: '<span class="badge bg-warning text-dark">In attesa</span>',
    accepted: '<span class="badge bg-success">Accettata</span>',
    removed:  '<span class="badge bg-danger">Scartata</span>',
  };
  return map[status] || '';
}

function updateMappingStats() {
  const total    = state.mappingRows.length;
  const accepted = state.mappingRows.filter(r => r.status === 'accepted').length;
  const removed  = state.mappingRows.filter(r => r.status === 'removed').length;
  const proposed = state.mappingRows.filter(r => r.status === 'proposed').length;
  const validated = accepted + removed;

  document.getElementById('mappingStats').textContent =
    `${total} entità rilevate · ${accepted} accettate · ${removed} scartate · ${proposed} in attesa di validazione`;

  const pct = total > 0 ? (validated / total) * 100 : 0;
  document.getElementById('validationProgress').style.width = `${pct}%`;

  // Enable "next" only if all rows have a decision
  document.getElementById('btnToStep3').disabled = proposed > 0;

  if (proposed > 0) {
    document.getElementById('btnToStep3').title = `${proposed} entità ancora in attesa di validazione`;
  } else {
    document.getElementById('btnToStep3').title = '';
  }
}

// --- Row actions ---

function acceptRow(id) {
  const row = state.mappingRows.find(r => r.id === id);
  if (!row) return;
  row.status = 'accepted';
  renderMappingTable();
}

function removeRow(id) {
  const row = state.mappingRows.find(r => r.id === id);
  if (!row) return;
  row.status = 'removed';
  renderMappingTable();
}

function restoreRow(id) {
  const row = state.mappingRows.find(r => r.id === id);
  if (!row) return;
  row.status = 'proposed';
  renderMappingTable();
}

function acceptAllRows() {
  state.mappingRows.forEach(row => {
    if (row.status !== 'removed') row.status = 'accepted';
  });
  renderMappingTable();
}

function removeAllRows() {
  state.mappingRows.forEach(row => {
    row.status = 'removed';
  });
  renderMappingTable();
}

// ===========================================================================
// STEP 3 — ANONIMIZZAZIONE E DOWNLOAD
// ===========================================================================

function buildSummary() {
  const rows    = state.mappingRows;
  const accepted = rows.filter(r => r.status === 'accepted').length;
  const removed  = rows.filter(r => r.status === 'removed').length;
  const active   = accepted;

  const summaryEl = document.getElementById('summaryStats');
  summaryEl.innerHTML = `
    <div class="col-6 col-md-3">
      <div class="text-center p-2 rounded bg-white">
        <div class="fs-4 fw-bold text-success">${accepted}</div>
        <div class="small text-muted">Accettate</div>
      </div>
    </div>
    <div class="col-6 col-md-3">
      <div class="text-center p-2 rounded bg-white">
        <div class="fs-4 fw-bold text-danger">${removed}</div>
        <div class="small text-muted">Rimosse</div>
      </div>
    </div>
    <div class="col-6 col-md-3">
      <div class="text-center p-2 rounded bg-white">
        <div class="fs-4 fw-bold text-dark">${active}</div>
        <div class="small text-muted">Placeholder attivi</div>
      </div>
    </div>
  `;
}

async function anonymizeDocument() {
  const activeEntities = state.mappingRows
    .filter(r => r.status === 'accepted')
    .map(r => ({
      value: r.original,
      category: r.category,
      entity_type: r.entity_type,
      semantic_role: r.semantic_role,
    }));

  showLoading(
    'Redazione del documento in corso…',
    'Il modello LLM locale applica i placeholder approvati al testo originale, preservando struttura e formattazione Markdown. Al termine la mappa di sostituzione viene eliminata dalla memoria del processo: l\'operazione è irreversibile e i valori originali non saranno più recuperabili. Non chiudere la pagina.'
  );

  try {
    const result = await apiCall('/api/anonymize', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ document_id: state.documentId, entities: activeEntities, language: state.language }),
    });

    state.anonymizedText = result.anonymized_content;

    // Aggiorna le sostituzioni preview con quelle reali calcolate dal backend
    if (Array.isArray(result.mappings)) {
      const byOriginal = new Map(result.mappings.map(m => [m.original, m]));
      state.mappingRows.forEach(row => {
        const m = byOriginal.get(row.original);
        if (m) {
          row.substitution = m.replacement;
          if (m.semantic_role) row.semantic_role = m.semantic_role;
        }
      });
      renderMappingTable();
    }

    // Render anonymized preview
    document.getElementById('anonymizedPreview').innerHTML = marked.parse(state.anonymizedText);
    document.getElementById('anonymizedRawText').textContent = state.anonymizedText;
    document.getElementById('resultSection').classList.remove('d-none');

    // Scroll to result
    document.getElementById('resultSection').scrollIntoView({ behavior: 'smooth', block: 'start' });

    showToast('Redazione completata.', 'success');
  } catch (err) {
    showToast(`Errore nella redazione: ${err.message}`, 'danger');
  } finally {
    hideLoading();
  }
}

function downloadAnonymized() {
  if (!state.anonymizedText) return;
  const blob = new Blob([state.anonymizedText], { type: 'text/markdown;charset=utf-8' });
  const url = URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url;
  a.download = state.anonymizedFilename;
  document.body.appendChild(a);
  a.click();
  document.body.removeChild(a);
  URL.revokeObjectURL(url);
}

function toggleAnonymizedView(showRaw) {
  document.getElementById('anonymizedPreview').classList.toggle('d-none', showRaw);
  document.getElementById('anonymizedRawPreview').classList.toggle('d-none', !showRaw);
  document.getElementById('btnViewAnonymizedRendered').classList.toggle('active', !showRaw);
  document.getElementById('btnViewAnonymizedRaw').classList.toggle('active', showRaw);
}

function startOver() {
  // Reset state
  state.selectedFile = null;
  state.convertedText = '';
  state.mappingRows = [];
  state.anonymizedText = '';
  state.documentType = null;
  const docTypeSelect = document.getElementById('docTypeSelect');
  if (docTypeSelect) docTypeSelect.value = '';

  // Reset UI
  removeFile();
  document.getElementById('mappingSection').classList.add('d-none');
  document.getElementById('resultSection').classList.add('d-none');
  document.getElementById('fileInput').value = '';

  goToStep(1);
}

// ===========================================================================
// HTML ESCAPING
// ===========================================================================

function escapeHtml(str) {
  return String(str)
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
    .replace(/'/g, '&#039;');
}

// ===========================================================================
// INIT
// ===========================================================================

document.addEventListener('DOMContentLoaded', () => {

  // --- Drop zone ---
  initDropZone();

  // --- Category checkboxes ---
  initCategoryCheckboxes();

  // --- Step 1 events ---
  document.getElementById('btnRemoveFile').addEventListener('click', removeFile);
  document.getElementById('btnConvert').addEventListener('click', convertDocument);
  document.getElementById('btnViewRendered').addEventListener('click', () => togglePreviewView(false));
  document.getElementById('btnViewRaw').addEventListener('click', () => togglePreviewView(true));

  document.getElementById('btnToStep2').addEventListener('click', () => {
    if (!state.convertedText) {
      showToast('Eseguire prima la normalizzazione del documento.', 'warning');
      return;
    }
    goToStep(2);
  });

  // --- Step 2 events ---
  document.getElementById('btnBackToStep1').addEventListener('click', () => goToStep(1));
  document.getElementById('btnSelectAll').addEventListener('click', () => selectAllCategories(true));
  document.getElementById('btnDeselectAll').addEventListener('click', () => selectAllCategories(false));
  document.getElementById('btnExtract').addEventListener('click', extractEntities);
  document.getElementById('btnAcceptAll').addEventListener('click', acceptAllRows);
  document.getElementById('btnRemoveAll').addEventListener('click', removeAllRows);

  // Document type override: re-run extraction with the chosen type so the
  // SemanticRoleService produces role labels appropriate for that document.
  document.getElementById('docTypeSelect').addEventListener('change', (ev) => {
    const newType = ev.target.value || null;
    if (newType === state.documentType) return;
    state.documentType = newType;
    if (state.documentId) {
      extractEntities();
    }
  });

  document.getElementById('btnToStep3').addEventListener('click', () => {
    const proposed = state.mappingRows.filter(r => r.status === 'proposed').length;
    if (proposed > 0) {
      showToast(`${proposed} entità ancora in attesa di validazione.`, 'warning');
      return;
    }
    buildSummary();
    goToStep(3);
  });

  // --- Step 3 events ---
  document.getElementById('btnBackToStep2').addEventListener('click', () => {
    document.getElementById('resultSection').classList.add('d-none');
    goToStep(2);
  });
  document.getElementById('btnAnonymize').addEventListener('click', anonymizeDocument);
  document.getElementById('btnViewAnonymizedRendered').addEventListener('click', () => toggleAnonymizedView(false));
  document.getElementById('btnViewAnonymizedRaw').addEventListener('click', () => toggleAnonymizedView(true));
  document.getElementById('btnDownload').addEventListener('click', downloadAnonymized);
  document.getElementById('btnStartOver').addEventListener('click', startOver);

});

// Make row-action functions accessible from inline onclick handlers
window.acceptRow  = acceptRow;
window.removeRow  = removeRow;
window.restoreRow = restoreRow;
