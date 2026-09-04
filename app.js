/**
 * VoiceERP Copilot — Core Application State & Logic Engine
 * Architecture:
 *   Step 1: Audio Capture & Web Speech / Whisper Transcription
 *   Step 2: AI Intent & Entity Extraction (GPT-4o / Claude Engine)
 *   Step 3: ERP REST API & Webhook Payload Generator
 *   Step 4: Live ERP Database & Audit Ledger Updates
 */

(function () {
  'use strict';

  // =========================================================================
  // Initial Demo State & Master Data
  // =========================================================================
  const state = {
    // Current Active Pipeline Step (1, 2, 3, 4)
    activeStep: 1,
    
    // Recording & Web Speech
    isRecording: false,
    recognition: null,
    recordingStartTime: null,
    timerInterval: null,
    audioContext: null,
    analyser: null,
    animFrameId: null,

    // Current Active Input & Extraction
    currentTranscript: '',
    parsedData: null,
    confidenceScore: 98.4,
    
    // Configurations
    selectedERP: 'netsuite', // sap, netsuite, odoo, dynamics, custom
    sttProvider: 'webspeech',
    llmProvider: 'gpt4o',
    webhookUrl: 'https://api.netsuite.com/v1/inventory/receive',
    apiKey: '',

    // Master Inventory Ledger
    inventory: [
      { sku: 'SKU-10492', item: 'Steel Nails (3-inch)', qty: 150, unit: 'boxes', location: 'Main Warehouse - Bay 1A', vendor: 'Vendor A', updated: '2026-07-22 08:30' },
      { sku: 'SKU-48201', item: 'Ergonomic Office Chair', qty: 45, unit: 'units', location: 'Chicago Store', vendor: 'Steelcase Inc.', updated: '2026-07-21 14:15' },
      { sku: 'SKU-99302', item: 'A4 Printing Paper (80gsm)', qty: 320, unit: 'reams', location: 'Supply Depot 2', vendor: 'Office Supplies Co', updated: '2026-07-20 11:00' },
      { sku: 'SKU-57311', item: 'Stainless Steel Screws', qty: 1200, unit: 'units', location: 'Main Warehouse - Bay 3B', vendor: 'Fastenal Inc.', updated: '2026-07-19 16:40' }
    ],

    // Active Purchase Orders (POs)
    purchaseOrders: [
      { po: 'PO-1234', vendor: 'Vendor A', item: 'Steel Nails (3-inch)', ordered: 200, received: 150, status: 'PARTIAL' },
      { po: 'PO-5678', vendor: 'Steelcase Inc.', item: 'Ergonomic Office Chair', ordered: 50, received: 45, status: 'PARTIAL' },
      { po: 'PO-9012', vendor: 'Fastenal Inc.', item: 'Stainless Steel Screws', ordered: 2000, received: 1200, status: 'PARTIAL' }
    ],

    // Audit Log History
    auditLogs: []
  };

  // Quick Preset Sample Transcripts
  const PRESET_TRANSCRIPTS = {
    receive_nails: "Receive fifty boxes of steel nails from Vendor A on Purchase Order 1234.",
    transfer_chairs: "Transfer 20 Ergonomic Chairs from Warehouse North to Chicago Store.",
    requisition_paper: "Create purchase requisition for 100 reams of A4 Paper from Office Supplies Co.",
    audit_screws: "Log inventory count 450 units of Stainless Screws at Bay 3-B."
  };

  // ERP Endpoints Mapping
  const ERP_ENDPOINTS = {
    sap: 'https://sap-s4hana.enterprise.internal/sap/bc/rest/inventory/receive',
    netsuite: 'https://api.netsuite.com/v1/inventory/receive',
    odoo: 'https://odoo-erp.company.org/api/v17/stock.move/create',
    dynamics: 'https://dynamics.microsoft.com/api/data/v9.2/inventory_entries',
    custom: 'https://api.custom-webhook.com/erp/v1/ingest'
  };

  // =========================================================================
  // DOM Element Selectors
  // =========================================================================
  const DOM = {
    // Header & Selectors
    erpSelect: document.getElementById('erp-system-select'),
    btnSettingsToggle: document.getElementById('btn-settings-toggle'),
    systemStatus: document.getElementById('system-status-indicator'),
    
    // Step Nodes
    stepNode1: document.getElementById('step-node-1'),
    stepNode2: document.getElementById('step-node-2'),
    stepNode3: document.getElementById('step-node-3'),
    stepNode4: document.getElementById('step-node-4'),

    // Voice Studio Elements
    btnPushToTalk: document.getElementById('btn-push-to-talk'),
    micIconMain: document.getElementById('mic-icon-main'),
    micStatusLabel: document.getElementById('mic-status-label'),
    recordingTimer: document.getElementById('recording-timer'),
    waveformCanvas: document.getElementById('waveform-canvas'),
    transcriptInput: document.getElementById('transcript-input-text'),
    transcriptCharCount: document.getElementById('transcript-char-count'),
    btnClearTranscript: document.getElementById('btn-clear-transcript'),
    btnProcessAI: document.getElementById('btn-process-ai'),
    presetChips: document.querySelectorAll('.preset-chip'),

    // AI Parsing Elements
    aiPlaceholder: document.getElementById('ai-placeholder'),
    parsedFieldsForm: document.getElementById('parsed-fields-form'),
    fieldIntentBadge: document.getElementById('field-intent-badge'),
    inputItem: document.getElementById('input-field-item'),
    inputQty: document.getElementById('input-field-qty'),
    inputUnit: document.getElementById('input-field-unit'),
    inputVendor: document.getElementById('input-field-vendor'),
    inputPO: document.getElementById('input-field-po'),
    inputLocation: document.getElementById('input-field-location'),
    confidenceBarFill: document.getElementById('confidence-bar-fill'),
    confidenceVal: document.getElementById('confidence-val'),
    btnPushERP: document.getElementById('btn-push-erp'),
    aiModelBadge: document.getElementById('ai-model-badge'),

    // API Inspector Elements
    apiEndpointUrl: document.getElementById('api-endpoint-url'),
    httpStatusBadge: document.getElementById('http-status-badge'),
    apiJsonCode: document.getElementById('api-json-code'),
    btnCopyJson: document.getElementById('btn-copy-json'),

    // ERP Dashboard & Tables
    inventoryTableBody: document.getElementById('inventory-table-body'),
    poCardsGrid: document.getElementById('po-cards-grid'),
    auditLogList: document.getElementById('audit-log-list'),
    auditCountBadge: document.getElementById('audit-count-badge'),
    statTotalSkus: document.getElementById('stat-total-skus'),
    statOpenPos: document.getElementById('stat-open-pos'),
    statVoiceEntries: document.getElementById('stat-voice-entries'),
    btnResetDemo: document.getElementById('btn-reset-demo'),

    // Settings Modal
    settingsModal: document.getElementById('settings-modal'),
    btnCloseModal: document.getElementById('btn-close-modal'),
    btnSaveSettings: document.getElementById('btn-save-settings'),
    settingStt: document.getElementById('setting-stt-provider'),
    settingLlm: document.getElementById('setting-llm-provider'),
    settingApiKey: document.getElementById('setting-api-key'),
    settingWebhookUrl: document.getElementById('setting-webhook-url'),

    // Toast Container
    toastContainer: document.getElementById('toast-container')
  };

  // =========================================================================
  // Initialize Application
  // =========================================================================
  function init() {
    // Initialize Lucide SVG Icons
    if (window.lucide) {
      window.lucide.createIcons();
    }

    setupSpeechRecognition();
    setupCanvasVisualizer();
    bindEvents();
    renderInventoryTable();
    renderPOCards();
    renderAuditLogs();
    updateStepProgress(1);
  }

  // =========================================================================
  // Step 1: Web Speech API & Canvas Visualizer
  // =========================================================================
  function setupSpeechRecognition() {
    const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
    if (SpeechRecognition) {
      state.recognition = new SpeechRecognition();
      state.recognition.continuous = true;
      state.recognition.interimResults = true;
      state.recognition.lang = 'en-US';

      state.recognition.onstart = function () {
        state.isRecording = true;
        updateRecordingUI(true);
        startTimer();
      };

      state.recognition.onresult = function (event) {
        let transcript = '';
        for (let i = event.resultIndex; i < event.results.length; i++) {
          transcript += event.results[i][0].transcript;
        }
        DOM.transcriptInput.value = transcript;
        updateCharCount();
      };

      state.recognition.onerror = function (event) {
        console.warn('Speech recognition error:', event.error);
        if (event.error !== 'no-speech') {
          showToast('Speech recognition notice: ' + event.error, 'error');
        }
        stopRecording();
      };

      state.recognition.onend = function () {
        if (state.isRecording) {
          stopRecording();
        }
      };
    } else {
      console.log('Web Speech API not supported. Falling back to simulated audio studio.');
    }
  }

  function toggleRecording() {
    if (state.isRecording) {
      stopRecording();
    } else {
      startRecording();
    }
  }

  function startRecording() {
    if (state.recognition) {
      try {
        state.recognition.start();
      } catch (err) {
        console.warn('Recognition start failed, stopping first:', err);
        stopRecording();
      }
    } else {
      // Simulated mic recording fallback
      state.isRecording = true;
      updateRecordingUI(true);
      startTimer();
      showToast('Recording audio... (Speak into your mic)', 'success');
      
      // Simulate live typing after 2 seconds if user stays silent
      setTimeout(() => {
        if (state.isRecording && !DOM.transcriptInput.value.trim()) {
          DOM.transcriptInput.value = "Receive fifty boxes of steel nails from Vendor A on Purchase Order 1234.";
          updateCharCount();
        }
      }, 2500);
    }
  }

  function stopRecording() {
    state.isRecording = false;
    if (state.recognition) {
      try { state.recognition.stop(); } catch (e) {}
    }
    updateRecordingUI(false);
    stopTimer();
    
    // Auto-process with AI if transcript is available
    if (DOM.transcriptInput.value.trim().length > 5) {
      processTranscriptWithAI();
    }
  }

  function updateRecordingUI(recording) {
    if (recording) {
      DOM.btnPushToTalk.classList.add('recording');
      DOM.micStatusLabel.textContent = 'Listening... Click again to stop & process';
      DOM.micStatusLabel.style.color = '#ef4444';
      updateStepProgress(1);
    } else {
      DOM.btnPushToTalk.classList.remove('recording');
      DOM.micStatusLabel.textContent = 'Tap Microphone to Speak or Select a Preset Command';
      DOM.micStatusLabel.style.color = '#9ca3af';
    }
  }

  function startTimer() {
    state.recordingStartTime = Date.now();
    DOM.recordingTimer.textContent = '00:00';
    clearInterval(state.timerInterval);
    state.timerInterval = setInterval(() => {
      const elapsedSec = Math.floor((Date.now() - state.recordingStartTime) / 1000);
      const mins = String(Math.floor(elapsedSec / 60)).padStart(2, '0');
      const secs = String(elapsedSec % 60).padStart(2, '0');
      DOM.recordingTimer.textContent = `${mins}:${secs}`;
    }, 1000);
  }

  function stopTimer() {
    clearInterval(state.timerInterval);
  }

  // Audio Canvas Visualizer
  function setupCanvasVisualizer() {
    const canvas = DOM.waveformCanvas;
    if (!canvas) return;
    const ctx = canvas.getContext('2d');
    let phase = 0;

    function drawWave() {
      ctx.clearRect(0, 0, canvas.width, canvas.height);
      ctx.lineWidth = 2;

      const numBars = 45;
      const barWidth = 4;
      const gap = (canvas.width - numBars * barWidth) / (numBars + 1);

      for (let i = 0; i < numBars; i++) {
        const x = gap + i * (barWidth + gap);
        let height = 8;

        if (state.isRecording) {
          // Dynamic wave based on sine math
          const factor = Math.sin(phase + i * 0.2) * 0.5 + 0.5;
          height = 12 + factor * 55;
        } else {
          height = 6 + Math.sin(i * 0.3) * 4;
        }

        const y = (canvas.height - height) / 2;

        const gradient = ctx.createLinearGradient(0, y, 0, y + height);
        if (state.isRecording) {
          gradient.addColorStop(0, '#ef4444');
          gradient.addColorStop(1, '#3b82f6');
        } else {
          gradient.addColorStop(0, '#3b82f6');
          gradient.addColorStop(1, '#6366f1');
        }

        ctx.fillStyle = gradient;
        ctx.beginPath();
        ctx.roundRect(x, y, barWidth, height, 2);
        ctx.fill();
      }

      phase += 0.08;
      state.animFrameId = requestAnimationFrame(drawWave);
    }

    drawWave();
  }

  // =========================================================================
  // Step 2: AI Intent & Entity Extraction Engine (GPT-4o Simulation)
  // =========================================================================
  function processTranscriptWithAI() {
    const rawText = DOM.transcriptInput.value.trim();
    if (!rawText) {
      showToast('Please provide or speak an audio transcript first', 'error');
      return;
    }

    updateStepProgress(2);
    showToast('Processing transcript with AI LLM Engine...', 'success');

    // Simulate LLM Processing Delay (350ms for snappy feel)
    setTimeout(() => {
      const parsed = extractIntentAndEntities(rawText);
      state.parsedData = parsed;
      state.confidenceScore = (94.5 + Math.random() * 5).toFixed(1);

      // Populate Extracted UI Fields
      DOM.fieldIntentBadge.textContent = formatIntentLabel(parsed.intent);
      DOM.inputItem.value = parsed.item || '';
      DOM.inputQty.value = parsed.quantity || 0;
      DOM.inputUnit.value = parsed.unit || 'units';
      DOM.inputVendor.value = parsed.vendor || 'N/A';
      DOM.inputPO.value = parsed.poNumber || 'N/A';
      DOM.inputLocation.value = parsed.warehouse || 'Main Warehouse - Bay 1A';

      DOM.confidenceBarFill.style.width = `${state.confidenceScore}%`;
      DOM.confidenceVal.textContent = `${state.confidenceScore}%`;

      DOM.aiPlaceholder.classList.add('hidden');
      DOM.parsedFieldsForm.classList.remove('hidden');

      // Automatically generate Step 3 REST API preview
      generateAPIPayload(parsed);

      showToast('AI Intent & Entities Extracted successfully!', 'success');
    }, 400);
  }

  /**
   * Rule-based & LLM extraction algorithm simulating GPT-4o structured JSON response
   */
  function extractIntentAndEntities(text) {
    const lower = text.toLowerCase();
    
    // Intent Classification
    let intent = 'GOODS_RECEIPT';
    if (lower.includes('transfer') || lower.includes('move')) {
      intent = 'STOCK_TRANSFER';
    } else if (lower.includes('requisition') || lower.includes('create po') || lower.includes('purchase requisition')) {
      intent = 'PURCHASE_REQUISITION';
    } else if (lower.includes('count') || lower.includes('audit') || lower.includes('stocktaking')) {
      intent = 'INVENTORY_AUDIT';
    }

    // Number / Quantity Extraction
    let quantity = 50;
    const numberWords = {
      'one': 1, 'two': 2, 'ten': 10, 'twenty': 20, 'fifty': 50,
      'hundred': 100, 'two hundred': 200, 'four hundred': 400, 'four hundred fifty': 450
    };
    
    // Match digits e.g. "50 boxes" or "450"
    const digitMatch = text.match(/\b(\d+)\b/);
    if (digitMatch) {
      quantity = parseInt(digitMatch[1], 10);
    } else {
      for (const [word, val] of Object.entries(numberWords)) {
        if (lower.includes(word)) {
          quantity = val;
          break;
        }
      }
    }

    // Unit of Measure Extraction
    let unit = 'units';
    if (lower.includes('box') || lower.includes('boxes')) unit = 'boxes';
    else if (lower.includes('ream') || lower.includes('reams')) unit = 'reams';
    else if (lower.includes('unit') || lower.includes('units')) unit = 'units';
    else if (lower.includes('carton') || lower.includes('cartons')) unit = 'cartons';

    // Item Extraction
    let item = 'Steel Nails (3-inch)';
    if (lower.includes('nail') || lower.includes('nails')) item = 'Steel Nails (3-inch)';
    else if (lower.includes('chair') || lower.includes('chairs')) item = 'Ergonomic Office Chair';
    else if (lower.includes('paper') || lower.includes('a4')) item = 'A4 Printing Paper (80gsm)';
    else if (lower.includes('screw') || lower.includes('screws')) item = 'Stainless Steel Screws';

    // Vendor / Supplier Extraction
    let vendor = 'Vendor A';
    if (lower.includes('steelcase')) vendor = 'Steelcase Inc.';
    else if (lower.includes('office supplies')) vendor = 'Office Supplies Co';
    else if (lower.includes('fastenal')) vendor = 'Fastenal Inc.';
    else if (lower.includes('vendor a')) vendor = 'Vendor A';

    // PO Number Extraction
    let poNumber = 'PO-1234';
    const poMatch = text.match(/\b(po|purchase order|order)?\s*#?\s*(\d{4,6})\b/i);
    if (poMatch) {
      poNumber = `PO-${poMatch[2]}`;
    }

    // Warehouse / Location
    let warehouse = 'Main Warehouse - Bay 1A';
    if (lower.includes('chicago')) warehouse = 'Chicago Store';
    else if (lower.includes('north')) warehouse = 'Warehouse North';
    else if (lower.includes('supply depot')) warehouse = 'Supply Depot 2';
    else if (lower.includes('bay 3') || lower.includes('bay 3-b')) warehouse = 'Main Warehouse - Bay 3B';

    return {
      intent,
      item,
      quantity,
      unit,
      vendor,
      poNumber,
      warehouse,
      timestamp: new Date().toISOString()
    };
  }

  function formatIntentLabel(intent) {
    switch (intent) {
      case 'GOODS_RECEIPT': return '📦 Goods Receipt';
      case 'STOCK_TRANSFER': return '🔄 Stock Transfer';
      case 'PURCHASE_REQUISITION': return '🛒 Purchase Requisition';
      case 'INVENTORY_AUDIT': return '📋 Inventory Audit';
      default: return intent;
    }
  }

  // =========================================================================
  // Step 3: ERP REST API & Webhook Payload Generator
  // =========================================================================
  function generateAPIPayload(data) {
    updateStepProgress(3);

    const erpSystemName = DOM.erpSelect.options[DOM.erpSelect.selectedIndex].text;
    const endpoint = ERP_ENDPOINTS[state.selectedERP] || state.webhookUrl;

    DOM.apiEndpointUrl.textContent = endpoint;

    const payloadObj = {
      system: erpSystemName,
      endpoint: endpoint,
      payload: {
        intent: data.intent,
        poNumber: data.poNumber,
        vendor: data.vendor,
        item: data.item,
        quantity: data.quantity,
        unit: data.unit,
        warehouse: data.warehouse
      },
      metadata: {
        source: "VoiceERP_Copilot_STT",
        confidence: `${state.confidenceScore}%`,
        timestamp: new Date().toISOString()
      }
    };

    DOM.apiJsonCode.textContent = JSON.stringify(payloadObj, null, 2);
  }

  // =========================================================================
  // Step 4: Push to ERP Database & Render Tables
  // =========================================================================
  function pushDataToERP() {
    if (!state.parsedData) {
      showToast('No parsed data available to push', 'error');
      return;
    }

    // Read updated values from user input fields (Human in the Loop approval)
    const finalData = {
      intent: state.parsedData.intent,
      item: DOM.inputItem.value.trim() || state.parsedData.item,
      quantity: parseInt(DOM.inputQty.value, 10) || state.parsedData.quantity,
      unit: DOM.inputUnit.value.trim() || state.parsedData.unit,
      vendor: DOM.inputVendor.value.trim() || state.parsedData.vendor,
      poNumber: DOM.inputPO.value.trim() || state.parsedData.poNumber,
      warehouse: DOM.inputLocation.value.trim() || state.parsedData.warehouse
    };

    // Update Master Inventory Ledger
    let existingItem = state.inventory.find(i => i.item.toLowerCase().includes(finalData.item.toLowerCase().split(' ')[0]));
    
    if (existingItem) {
      if (finalData.intent === 'GOODS_RECEIPT' || finalData.intent === 'PURCHASE_REQUISITION') {
        existingItem.qty += finalData.quantity;
      } else if (finalData.intent === 'INVENTORY_AUDIT') {
        existingItem.qty = finalData.quantity;
      }
      existingItem.location = finalData.warehouse;
      existingItem.updated = formatCurrentDateTime();
      existingItem.justUpdated = true;
    } else {
      const newSku = `SKU-${Math.floor(10000 + Math.random() * 90000)}`;
      existingItem = {
        sku: newSku,
        item: finalData.item,
        qty: finalData.quantity,
        unit: finalData.unit,
        location: finalData.warehouse,
        vendor: finalData.vendor,
        updated: formatCurrentDateTime(),
        justUpdated: true
      };
      state.inventory.unshift(existingItem);
    }

    // Update PO Ledger
    const targetPO = state.purchaseOrders.find(p => p.po === finalData.poNumber);
    if (targetPO) {
      targetPO.received = Math.min(targetPO.ordered, targetPO.received + finalData.quantity);
      targetPO.status = targetPO.received >= targetPO.ordered ? 'FULFILLED' : 'PARTIAL';
    }

    // Append to Audit Logs
    state.auditLogs.unshift({
      id: `TXN-${Math.floor(100000 + Math.random() * 900000)}`,
      intent: finalData.intent,
      transcript: DOM.transcriptInput.value,
      item: finalData.item,
      qty: finalData.quantity,
      unit: finalData.unit,
      po: finalData.poNumber,
      time: formatCurrentDateTime()
    });

    updateStepProgress(4);
    renderInventoryTable();
    renderPOCards();
    renderAuditLogs();

    showToast(`Successfully pushed to ${DOM.erpSelect.options[DOM.erpSelect.selectedIndex].text}! Transaction ID: TXN-${Math.floor(100000 + Math.random() * 900000)}`, 'success');
  }

  function renderInventoryTable() {
    const tbody = DOM.inventoryTableBody;
    tbody.innerHTML = '';

    state.inventory.forEach(row => {
      const tr = document.createElement('tr');
      if (row.justUpdated) {
        tr.classList.add('row-updated');
        setTimeout(() => row.justUpdated = false, 2500);
      }

      tr.innerHTML = `
        <td class="sku-code">${row.sku}</td>
        <td><strong>${row.item}</strong></td>
        <td class="qty-badge">${row.qty}</td>
        <td>${row.unit}</td>
        <td>${row.location}</td>
        <td>${row.vendor}</td>
        <td style="font-family: var(--font-mono); font-size: 0.76rem; color: var(--text-muted);">${row.updated}</td>
      `;
      tbody.appendChild(tr);
    });

    DOM.statTotalSkus.textContent = state.inventory.length;
    DOM.statVoiceEntries.textContent = state.auditLogs.length;
  }

  function renderPOCards() {
    const container = DOM.poCardsGrid;
    container.innerHTML = '';

    state.purchaseOrders.forEach(po => {
      const card = document.createElement('div');
      card.className = 'po-card';
      const pct = Math.round((po.received / po.ordered) * 100);

      card.innerHTML = `
        <div class="po-card-header">
          <span class="po-number">${po.po}</span>
          <span class="badge-neutral">${po.status}</span>
        </div>
        <div class="po-vendor">${po.vendor} — ${po.item}</div>
        <div class="po-progress-row">
          <span>Received: ${po.received} / ${po.ordered}</span>
          <span style="font-weight: 700;">${pct}%</span>
        </div>
        <div class="progress-bar-bg" style="width: 100%; margin-top: 0.3rem;">
          <div class="progress-bar-fill" style="width: ${pct}%;"></div>
        </div>
      `;
      container.appendChild(card);
    });

    const openCount = state.purchaseOrders.filter(p => p.status !== 'FULFILLED').length;
    DOM.statOpenPos.textContent = openCount;
  }

  function renderAuditLogs() {
    const list = DOM.auditLogList;
    list.innerHTML = '';

    if (state.auditLogs.length === 0) {
      list.innerHTML = `
        <div class="empty-audit-message">
          <i data-lucide="inbox"></i>
          <p>No voice entries processed yet. Record your voice or select a preset command to test!</p>
        </div>
      `;
      if (window.lucide) window.lucide.createIcons();
      DOM.auditCountBadge.textContent = '0 Logged Actions';
      return;
    }

    state.auditLogs.forEach(log => {
      const item = document.createElement('div');
      item.className = 'audit-item';
      item.innerHTML = `
        <div class="audit-item-top">
          <span class="audit-action-tag">${formatIntentLabel(log.intent)}</span>
          <span class="audit-time">${log.time}</span>
        </div>
        <div class="audit-transcript">"${log.transcript}"</div>
        <div class="audit-payload-summary">➜ Updated: ${log.qty} ${log.unit} of ${log.item} (${log.po})</div>
      `;
      list.appendChild(item);
    });

    DOM.auditCountBadge.textContent = `${state.auditLogs.length} Logged Actions`;
  }

  function updateStepProgress(stepNum) {
    state.activeStep = stepNum;
    const nodes = [DOM.stepNode1, DOM.stepNode2, DOM.stepNode3, DOM.stepNode4];

    nodes.forEach((node, idx) => {
      if (!node) return;
      node.classList.remove('active', 'completed');
      if (idx + 1 === stepNum) {
        node.classList.add('active');
      } else if (idx + 1 < stepNum) {
        node.classList.add('completed');
      }
    });
  }

  // =========================================================================
  // Helper Utilities & Event Listeners
  // =========================================================================
  function bindEvents() {
    // Mic Button
    DOM.btnPushToTalk.addEventListener('click', toggleRecording);

    // Clear Transcript
    DOM.btnClearTranscript.addEventListener('click', () => {
      DOM.transcriptInput.value = '';
      updateCharCount();
      DOM.aiPlaceholder.classList.remove('hidden');
      DOM.parsedFieldsForm.classList.add('hidden');
      updateStepProgress(1);
    });

    // Transcript Input typing
    DOM.transcriptInput.addEventListener('input', updateCharCount);

    // Process AI Button
    DOM.btnProcessAI.addEventListener('click', processTranscriptWithAI);

    // Push to ERP Button
    DOM.btnPushERP.addEventListener('click', pushDataToERP);

    // Preset Chips
    DOM.presetChips.forEach(chip => {
      chip.addEventListener('click', () => {
        const presetKey = chip.getAttribute('data-preset');
        if (PRESET_TRANSCRIPTS[presetKey]) {
          DOM.transcriptInput.value = PRESET_TRANSCRIPTS[presetKey];
          updateCharCount();
          processTranscriptWithAI();
        }
      });
    });

    // ERP Selector Change
    DOM.erpSelect.addEventListener('change', (e) => {
      state.selectedERP = e.target.value;
      if (state.parsedData) {
        generateAPIPayload(state.parsedData);
      }
    });

    // Copy JSON Button
    DOM.btnCopyJson.addEventListener('click', () => {
      const code = DOM.apiJsonCode.textContent;
      navigator.clipboard.writeText(code).then(() => {
        showToast('JSON Payload copied to clipboard!', 'success');
      });
    });

    // Settings Modal
    DOM.btnSettingsToggle.addEventListener('click', () => {
      DOM.settingsModal.classList.remove('hidden');
    });
    DOM.btnCloseModal.addEventListener('click', () => {
      DOM.settingsModal.classList.add('hidden');
    });
    DOM.btnSaveSettings.addEventListener('click', () => {
      state.sttProvider = DOM.settingStt.value;
      state.llmProvider = DOM.settingLlm.value;
      state.apiKey = DOM.settingApiKey.value.trim();
      state.webhookUrl = DOM.settingWebhookUrl.value.trim();

      DOM.aiModelBadge.innerHTML = `<i data-lucide="cpu"></i> ${DOM.settingLlm.options[DOM.settingLlm.selectedIndex].text}`;
      if (window.lucide) window.lucide.createIcons();

      DOM.settingsModal.classList.add('hidden');
      showToast('Settings saved successfully!', 'success');
    });

    // Reset Demo Data
    DOM.btnResetDemo.addEventListener('click', () => {
      state.auditLogs = [];
      renderInventoryTable();
      renderPOCards();
      renderAuditLogs();
      showToast('Demo data reset to default state.', 'success');
    });
  }

  function updateCharCount() {
    const len = DOM.transcriptInput.value.length;
    DOM.transcriptCharCount.textContent = `${len} character${len === 1 ? '' : 's'}`;
  }

  function formatCurrentDateTime() {
    const now = new Date();
    const yyyy = now.getFullYear();
    const mm = String(now.getMonth() + 1).padStart(2, '0');
    const dd = String(now.getDate()).padStart(2, '0');
    const hh = String(now.getHours()).padStart(2, '0');
    const min = String(now.getMinutes()).padStart(2, '0');
    return `${yyyy}-${mm}-${dd} ${hh}:${min}`;
  }

  function showToast(message, type = 'success') {
    const toast = document.createElement('div');
    toast.className = `toast ${type}`;
    toast.innerHTML = `
      <i data-lucide="${type === 'success' ? 'check-circle' : 'alert-circle'}"></i>
      <span>${message}</span>
    `;
    DOM.toastContainer.appendChild(toast);
    if (window.lucide) window.lucide.createIcons();

    setTimeout(() => {
      toast.style.opacity = '0';
      toast.style.transform = 'translateX(100%)';
      setTimeout(() => toast.remove(), 300);
    }, 3500);
  }

  // Initialize on DOM Ready
  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init);
  } else {
    init();
  }

})();
