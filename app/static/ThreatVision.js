/**
 * ThreatVision.js
 * Core client-side logic for the surveillance system.
 * ML model via TensorFlow.js (COCO-SSD) + custom threat scoring.
 * Persistent storage via localStorage.
 */

const TV = (() => {

  // ─── CONSTANTS ─────────────────────────────────────────────────────────────
  const STORAGE_KEY = 'ThreatVision_v1';
  const ALERT_STORAGE_KEY = 'ThreatVision_alerts_v1';
  const CAM_STORAGE_KEY = 'ThreatVision_cameras_v1';

  // How threat levels map to entity classes detected by COCO-SSD
  const ENTITY_THREAT_MAP = {
    person:       { base: 0.4, label: 'Person' },
    car:          { base: 0.25, label: 'Vehicle' },
    truck:        { base: 0.35, label: 'Heavy Vehicle' },
    motorcycle:   { base: 0.35, label: 'Motorcycle' },
    bicycle:      { base: 0.2, label: 'Bicycle' },
    backpack:     { base: 0.3, label: 'Bag/Backpack' },
    handbag:      { base: 0.2, label: 'Handbag' },
    suitcase:     { base: 0.25, label: 'Luggage' },
    knife:        { base: 0.85, label: '⚠ Knife' },
    scissors:     { base: 0.6,  label: 'Sharp Object' },
    cell_phone:   { base: 0.1,  label: 'Mobile Device' },
    laptop:       { base: 0.1,  label: 'Electronic Device' },
    default:      { base: 0.15, label: 'Unknown Object' },
  };

  const THREAT_LEVELS = [
    { label: 'NONE',     min: 0,    max: 0.15, color: '#00ff88', cssClass: 'threat-none' },
    { label: 'LOW',      min: 0.15, max: 0.35, color: '#44ccff', cssClass: 'threat-low' },
    { label: 'MEDIUM',   min: 0.35, max: 0.60, color: '#ffaa00', cssClass: 'threat-medium' },
    { label: 'HIGH',     min: 0.60, max: 0.80, color: '#ff6600', cssClass: 'threat-high' },
    { label: 'CRITICAL', min: 0.80, max: 1.01, color: '#ff2244', cssClass: 'threat-critical' },
  ];

  // ─── STATE ──────────────────────────────────────────────────────────────────
  const state = {
    model: null,
    modelLoading: false,
    modelLoaded: false,
    cameras: [],           // loaded from storage
    alerts: [],            // loaded from storage
    detectionLog: [],      // loaded from storage
    activeCamera: null,
    streams: {},           // cameraId → MediaStream
    animFrames: {},        // cameraId → requestAnimationFrame id
    detectionIntervals: {},
    systemThreat: 0,       // aggregate 0-1
    alertCount: 0,
  };

  // ─── STORAGE ────────────────────────────────────────────────────────────────
  const Storage = {
    load() {
      try {
        const raw = localStorage.getItem(STORAGE_KEY);
        if (raw) Object.assign(state, JSON.parse(raw));
      } catch(e) {}
      try {
        state.alerts = JSON.parse(localStorage.getItem(ALERT_STORAGE_KEY) || '[]');
      } catch(e) { state.alerts = []; }
      try {
        state.cameras = JSON.parse(localStorage.getItem(CAM_STORAGE_KEY) || '[]');
      } catch(e) { state.cameras = []; }

      // Rebuild alert count
      state.alertCount = state.alerts.filter(a => !a.acknowledged).length;
    },

    save() {
      try {
        const minimal = {
          systemThreat: state.systemThreat,
          detectionLog: state.detectionLog.slice(-500), // keep last 500
        };
        localStorage.setItem(STORAGE_KEY, JSON.stringify(minimal));
        localStorage.setItem(ALERT_STORAGE_KEY, JSON.stringify(state.alerts.slice(-200)));
        localStorage.setItem(CAM_STORAGE_KEY, JSON.stringify(state.cameras));
      } catch(e) {}
    },

    clear() {
      localStorage.removeItem(STORAGE_KEY);
      localStorage.removeItem(ALERT_STORAGE_KEY);
      localStorage.removeItem(CAM_STORAGE_KEY);
    }
  };

  // ─── THREAT UTILS ───────────────────────────────────────────────────────────
  const Threat = {
    classify(score) {
      return THREAT_LEVELS.find(l => score >= l.min && score < l.max) || THREAT_LEVELS[0];
    },

    computeFromDetections(detections) {
      if (!detections || detections.length === 0) return 0;
      let maxThreat = 0;
      let accumulator = 0;

      detections.forEach(d => {
        const key = d.class?.replace(/ /g, '_').toLowerCase();
        const entry = ENTITY_THREAT_MAP[key] || ENTITY_THREAT_MAP.default;
        const entityThreat = entry.base * d.score;
        accumulator += entityThreat * 0.5;
        if (entityThreat > maxThreat) maxThreat = entityThreat;
      });

      // Weighted: max is dominant factor
      const raw = maxThreat * 0.7 + Math.min(accumulator, 0.5) * 0.3;
      // Crowd factor: more entities = higher threat
      const crowdBoost = Math.min(detections.length / 10, 0.2);
      return Math.min(raw + crowdBoost, 1.0);
    },

    colorForScore(score) {
      return this.classify(score).color;
    },

    labelForScore(score) {
      return this.classify(score).label;
    },

    cssForScore(score) {
      return this.classify(score).cssClass;
    }
  };

  // ─── ML MODEL ───────────────────────────────────────────────────────────────
  const Model = {
    async load(onProgress) {
      if (state.modelLoaded) return state.model;
      if (state.modelLoading) {
        // wait for it
        return new Promise(resolve => {
          const check = setInterval(() => {
            if (state.modelLoaded) { clearInterval(check); resolve(state.model); }
          }, 200);
        });
      }

      state.modelLoading = true;
      onProgress && onProgress('Loading COCO-SSD model...');

      // Load TF.js + COCO-SSD from CDN if not present
      await this._ensureScripts();

      state.model = await cocoSsd.load({ base: 'mobilenet_v2' });
      state.modelLoaded = true;
      state.modelLoading = false;
      onProgress && onProgress('Model ready');
      return state.model;
    },

    async _ensureScripts() {
      const scripts = [
        { id: 'tf-js', src: 'https://cdn.jsdelivr.net/npm/@tensorflow/tfjs@4.15.0/dist/tf.min.js' },
        { id: 'coco-ssd', src: 'https://cdn.jsdelivr.net/npm/@tensorflow-models/coco-ssd@2.2.3/dist/coco-ssd.min.js' },
      ];

      for (const s of scripts) {
        if (!document.getElementById(s.id)) {
          await new Promise((resolve, reject) => {
            const el = document.createElement('script');
            el.id = s.id;
            el.src = s.src;
            el.onload = resolve;
            el.onerror = reject;
            document.head.appendChild(el);
          });
        }
      }
    },

    async detect(imageElement) {
      if (!state.model) return [];
      try {
        return await state.model.detect(imageElement);
      } catch(e) {
        return [];
      }
    }
  };

  // ─── CAMERA MANAGEMENT ──────────────────────────────────────────────────────
  const Camera = {
    getAll() { return state.cameras; },

    get(id) { return state.cameras.find(c => c.id === id); },

    add(data) {
      const cam = {
        id: 'cam_' + Date.now(),
        name: data.name || 'Camera',
        location: data.location || '',
        type: data.type || 'webcam',
        status: 'offline',
        threatScore: null,
        threatLabel: null,
        detectedEntities: [],
        lastSeen: null,
        totalDetections: 0,
        createdAt: new Date().toISOString(),
      };
      state.cameras.push(cam);
      Storage.save();
      return cam;
    },

    update(id, data) {
      const idx = state.cameras.findIndex(c => c.id === id);
      if (idx !== -1) {
        state.cameras[idx] = { ...state.cameras[idx], ...data };
        Storage.save();
        return state.cameras[idx];
      }
    },

    remove(id) {
      Camera.stopStream(id);
      state.cameras = state.cameras.filter(c => c.id !== id);
      Storage.save();
    },

    async startStream(cameraId) {
      const cam = Camera.get(cameraId);
      if (!cam) return null;

      try {
        const stream = await navigator.mediaDevices.getUserMedia({
          video: { width: { ideal: 1280 }, height: { ideal: 720 }, facingMode: 'environment' },
          audio: false,
        });
        state.streams[cameraId] = stream;
        Camera.update(cameraId, { status: 'online', lastSeen: new Date().toISOString() });
        return stream;
      } catch(e) {
        Camera.update(cameraId, { status: 'error' });
        throw e;
      }
    },

    stopStream(cameraId) {
      if (state.streams[cameraId]) {
        state.streams[cameraId].getTracks().forEach(t => t.stop());
        delete state.streams[cameraId];
      }
      if (state.animFrames[cameraId]) {
        cancelAnimationFrame(state.animFrames[cameraId]);
        delete state.animFrames[cameraId];
      }
      Camera.update(cameraId, { status: 'offline' });
    },

    getStream(cameraId) {
      return state.streams[cameraId];
    }
  };

  // ─── DETECTION LOOP ─────────────────────────────────────────────────────────
  const Detection = {
    async startLoop(cameraId, videoEl, overlayCanvas) {
      const ctx = overlayCanvas.getContext('2d');

      const loop = async () => {
        if (!videoEl || videoEl.readyState < 2) {
          state.animFrames[cameraId] = requestAnimationFrame(loop);
          return;
        }

        // Sync canvas size
        overlayCanvas.width = videoEl.videoWidth || overlayCanvas.clientWidth;
        overlayCanvas.height = videoEl.videoHeight || overlayCanvas.clientHeight;

        const detections = await Model.detect(videoEl);
        const threatScore = Threat.computeFromDetections(detections);

        // Update camera state
        const prevCam = Camera.get(cameraId);
        const entities = detections.map(d => {
          const key = d.class?.replace(/ /g, '_').toLowerCase();
          const meta = ENTITY_THREAT_MAP[key] || ENTITY_THREAT_MAP.default;
          return {
            class: d.class,
            label: meta.label,
            confidence: d.score,
            bbox: d.bbox,
          };
        });

        Camera.update(cameraId, {
          threatScore,
          threatLabel: Threat.labelForScore(threatScore),
          detectedEntities: entities,
          lastSeen: new Date().toISOString(),
          totalDetections: (prevCam?.totalDetections || 0) + entities.length,
          status: 'online',
        });

        // Log detections
        if (entities.length > 0) {
          Detection.logEntities(cameraId, entities, threatScore);
        }

        // Check for high-threat alert
        if (threatScore >= 0.6) {
          Alerts.raiseAlert(cameraId, threatScore, entities);
        }

        // Draw overlay
        Detection.drawOverlay(ctx, overlayCanvas, detections, threatScore);

        // Update system-wide threat
        Detection.updateSystemThreat();

        // Next frame (throttle to ~5fps for performance)
        setTimeout(() => {
          state.animFrames[cameraId] = requestAnimationFrame(loop);
        }, 200);
      };

      state.animFrames[cameraId] = requestAnimationFrame(loop);
    },

    drawOverlay(ctx, canvas, detections, threatScore) {
      ctx.clearRect(0, 0, canvas.width, canvas.height);

      detections.forEach(d => {
        const [x, y, w, h] = d.bbox;
        const key = d.class?.replace(/ /g, '_').toLowerCase();
        const meta = ENTITY_THREAT_MAP[key] || ENTITY_THREAT_MAP.default;
        const entityThreat = meta.base * d.score;
        const color = Threat.colorForScore(entityThreat);

        // Draw bounding box
        ctx.strokeStyle = color;
        ctx.lineWidth = 1.5;
        ctx.strokeRect(x, y, w, h);

        // Corner marks
        const cs = 10;
        ctx.lineWidth = 3;
        [[x,y],[x+w,y],[x,y+h],[x+w,y+h]].forEach(([cx,cy]) => {
          ctx.beginPath();
          ctx.moveTo(cx - (cx<x+w/2?0:cs), cy);
          ctx.lineTo(cx + (cx<x+w/2?cs:0), cy);
          ctx.moveTo(cx, cy - (cy<y+h/2?0:cs));
          ctx.lineTo(cx, cy + (cy<y+h/2?cs:0));
          ctx.stroke();
        });

        // Label bg
        const label = `${meta.label} ${(d.score * 100).toFixed(0)}%`;
        ctx.font = '11px "Share Tech Mono", monospace';
        const tw = ctx.measureText(label).width;
        ctx.fillStyle = 'rgba(0,0,0,0.7)';
        ctx.fillRect(x, y - 20, tw + 10, 18);
        ctx.fillStyle = color;
        ctx.fillText(label, x + 5, y - 6);
      });
    },

    logEntities(cameraId, entities, threatScore) {
      const cam = Camera.get(cameraId);
      const entry = {
        id: 'log_' + Date.now() + '_' + Math.random().toString(36).slice(2,6),
        cameraId,
        cameraName: cam?.name || cameraId,
        timestamp: new Date().toISOString(),
        entities: entities.map(e => e.label),
        entityCount: entities.length,
        threatScore,
        threatLabel: Threat.labelForScore(threatScore),
      };

      // Deduplicate: don't log if same camera logged within 3s
      const last = state.detectionLog[state.detectionLog.length - 1];
      if (last && last.cameraId === cameraId && (Date.now() - new Date(last.timestamp)) < 3000) return;

      state.detectionLog.push(entry);
      if (state.detectionLog.length > 500) state.detectionLog.shift();
      Storage.save();

      // Dispatch event for live UI
      document.dispatchEvent(new CustomEvent('tv:detection', { detail: entry }));
    },

    updateSystemThreat() {
      const online = state.cameras.filter(c => c.status === 'online' && c.threatScore !== null);
      if (online.length === 0) { state.systemThreat = 0; return; }
      const max = Math.max(...online.map(c => c.threatScore));
      const avg = online.reduce((s, c) => s + c.threatScore, 0) / online.length;
      state.systemThreat = max * 0.7 + avg * 0.3;
      document.dispatchEvent(new CustomEvent('tv:systemThreat', { detail: state.systemThreat }));
    }
  };

  // ─── ALERTS ─────────────────────────────────────────────────────────────────
  const Alerts = {
    raiseAlert(cameraId, threatScore, entities) {
      const cam = Camera.get(cameraId);
      // Don't duplicate within 10s for same camera
      const recent = state.alerts.find(a =>
        a.cameraId === cameraId && !a.acknowledged &&
        (Date.now() - new Date(a.timestamp)) < 10000
      );
      if (recent) return;

      const alert = {
        id: 'alert_' + Date.now(),
        cameraId,
        cameraName: cam?.name || cameraId,
        timestamp: new Date().toISOString(),
        threatScore,
        threatLabel: Threat.labelForScore(threatScore),
        entities: entities.map(e => e.label),
        acknowledged: false,
      };

      state.alerts.unshift(alert);
      if (state.alerts.length > 200) state.alerts.pop();
      state.alertCount = state.alerts.filter(a => !a.acknowledged).length;
      Storage.save();

      // Play alert sound
      Alerts.playBeep(threatScore);

      document.dispatchEvent(new CustomEvent('tv:alert', { detail: alert }));
    },

    acknowledge(alertId) {
      const alert = state.alerts.find(a => a.id === alertId);
      if (alert) {
        alert.acknowledged = true;
        state.alertCount = state.alerts.filter(a => !a.acknowledged).length;
        Storage.save();
        document.dispatchEvent(new CustomEvent('tv:alertAck', { detail: alertId }));
      }
    },

    acknowledgeAll() {
      state.alerts.forEach(a => a.acknowledged = true);
      state.alertCount = 0;
      Storage.save();
      document.dispatchEvent(new CustomEvent('tv:alertsCleared'));
    },

    getAll() { return state.alerts; },
    getUnacked() { return state.alerts.filter(a => !a.acknowledged); },
    getCount() { return state.alertCount; },

    playBeep(threatScore) {
      try {
        const ctx = new (window.AudioContext || window.webkitAudioContext)();
        const osc = ctx.createOscillator();
        const gain = ctx.createGain();
        osc.connect(gain);
        gain.connect(ctx.destination);
        osc.type = 'square';
        osc.frequency.value = threatScore > 0.8 ? 880 : 440;
        gain.gain.value = 0.1;
        osc.start();
        osc.stop(ctx.currentTime + (threatScore > 0.8 ? 0.3 : 0.15));
      } catch(e) {}
    }
  };

  // ─── UI HELPERS ─────────────────────────────────────────────────────────────
  const UI = {
    formatTime(isoStr) {
      if (!isoStr) return '—';
      const d = new Date(isoStr);
      return d.toLocaleTimeString('en-US', { hour12: false });
    },

    formatDateTime(isoStr) {
      if (!isoStr) return '—';
      const d = new Date(isoStr);
      return d.toLocaleString('en-US', { hour12: false, month: 'short', day: '2-digit', hour: '2-digit', minute: '2-digit', second: '2-digit' });
    },

    threatBadge(score, label) {
      const css = Threat.cssForScore(score ?? 0);
      const lbl = label || (score !== null && score !== undefined ? Threat.labelForScore(score) : '—');
      return `<span class="threat-badge ${css}">${lbl}</span>`;
    },

    threatBar(score) {
      if (score === null || score === undefined) {
        return `<div class="threat-meter"><div class="threat-meter-fill" style="width:0%"></div></div>`;
      }
      const pct = (score * 100).toFixed(1);
      const color = Threat.colorForScore(score);
      return `<div class="threat-meter">
        <div class="threat-meter-fill" style="width:${pct}%;background:${color}"></div>
      </div>`;
    },

    updateClock() {
      const el = document.getElementById('tv-clock');
      const de = document.getElementById('tv-date');
      if (!el) return;
      const now = new Date();
      el.textContent = now.toLocaleTimeString('en-US', { hour12: false });
      if (de) de.textContent = now.toLocaleDateString('en-US', { weekday: 'short', year: 'numeric', month: 'short', day: '2-digit' });
    },

    updateBadge() {
      const badge = document.getElementById('alert-badge');
      if (!badge) return;
      const count = Alerts.getCount();
      badge.textContent = count;
      badge.style.display = count > 0 ? 'inline' : 'none';
    },
  };

  // ─── INIT ───────────────────────────────────────────────────────────────────
  function init() {
    Storage.load();
    setInterval(UI.updateClock, 1000);
    UI.updateClock();
    UI.updateBadge();

    // Listen for alert events to update badge
    document.addEventListener('tv:alert', UI.updateBadge);
    document.addEventListener('tv:alertAck', UI.updateBadge);
    document.addEventListener('tv:alertsCleared', UI.updateBadge);
  }

  // ─── PUBLIC API ─────────────────────────────────────────────────────────────
  return {
    init,
    state,
    Storage,
    Threat,
    Model,
    Camera,
    Detection,
    Alerts,
    UI,
    THREAT_LEVELS,
    ENTITY_THREAT_MAP,
  };
})();

// Auto-init when DOM ready
if (document.readyState === 'loading') {
  document.addEventListener('DOMContentLoaded', TV.init);
} else {
  TV.init();
}
