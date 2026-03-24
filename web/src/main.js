/**
 * Lucas' Game — HTML+JS web version
 * Copyright (c) 2025 Gregory R. Warnes — MIT License
 *
 * State machine:
 *   TITLE   — title screen visible, waiting for first interaction
 *   PLAYING — game loop active, key presses update display and play tones
 */

// ─── State ────────────────────────────────────────────────────────────────────

let state = "TITLE"; // "TITLE" | "PLAYING"
let audioCtx = null;

// C-major scale frequencies matching the Python version exactly
const C_MAJOR = [261.63, 293.66, 329.63, 349.23, 392.0, 440.0, 493.88, 523.25];

// ─── DOM references ───────────────────────────────────────────────────────────

const titleScreen  = document.getElementById("title-screen");
const gameScreen   = document.getElementById("game-screen");
const keyWrapper   = document.getElementById("key-wrapper");
const keyLabel     = document.getElementById("key-label");
const waitingHint  = document.getElementById("waiting-hint");

// ─── Key name mapping ─────────────────────────────────────────────────────────
// Mirrors Python get_key_name() using event.key values from the KeyboardEvent API.

const KEY_MAP = {
  " ":           "Space",
  Enter:         "Return",
  Escape:        "Esc",
  Backspace:     "Backspace",
  Tab:           "Tab",
  Delete:        "Delete",
  Insert:        "Insert",
  Home:          "Home",
  End:           "End",
  PageUp:        "Page Up",
  PageDown:      "Page Down",
  ArrowUp:       "↑",
  ArrowDown:     "↓",
  ArrowLeft:     "←",
  ArrowRight:    "→",
  Shift:         "Shift",
  Control:       "Ctrl",
  Alt:           "Alt",
  Meta:          "Command",
  CapsLock:      "Caps Lock",
  F1:  "F1",  F2:  "F2",  F3:  "F3",  F4:  "F4",
  F5:  "F5",  F6:  "F6",  F7:  "F7",  F8:  "F8",
  F9:  "F9",  F10: "F10", F11: "F11", F12: "F12",
  F13: "F13", F14: "F14", F15: "F15",
};

function getKeyName(event) {
  const k = event.key;
  if (k in KEY_MAP) return KEY_MAP[k];
  // Single printable character — uppercase it
  if (k.length === 1) return k.toUpperCase();
  // Fallback — return event.key as-is
  return k;
}

// ─── Color ───────────────────────────────────────────────────────────────────

function clamp(v, lo, hi) {
  return Math.max(lo, Math.min(hi, v));
}

function generateColor() {
  return {
    r: Math.floor(Math.random() * 256),
    g: Math.floor(Math.random() * 256),
    b: Math.floor(Math.random() * 256),
  };
}

function rgb({ r, g, b }) {
  return `rgb(${r}, ${g}, ${b})`;
}

function shadowColor({ r, g, b }) {
  return `rgb(${clamp(r - 50, 0, 255)}, ${clamp(g - 50, 0, 255)}, ${clamp(b - 50, 0, 255)})`;
}

function borderColor({ r, g, b }) {
  return `rgb(${clamp(r + 50, 0, 255)}, ${clamp(g + 50, 0, 255)}, ${clamp(b + 50, 0, 255)})`;
}

// ─── Font scaling ─────────────────────────────────────────────────────────────
// Sets the largest font-size (in px) that fits the key-label inside 90% of the
// key-wrapper width, starting from 60% of the wrapper height.

function scaleFontSize() {
  const maxW  = keyWrapper.clientWidth  * 0.9;
  const startH = keyWrapper.clientHeight * 0.6;
  let size = startH;

  keyLabel.style.fontSize = `${size}px`;

  // Shrink until the text fits horizontally
  while (keyLabel.scrollWidth > maxW && size > 12) {
    size -= 4;
    keyLabel.style.fontSize = `${size}px`;
  }
}

// ─── Rendering ────────────────────────────────────────────────────────────────

function applyKeyPress(keyName, color) {
  // Hide the waiting hint once a real key has been pressed
  if (waitingHint) waitingHint.style.display = "none";

  // Background
  document.body.style.backgroundColor = rgb(color);

  // Key wrapper colors / shadows
  keyWrapper.style.backgroundColor = rgb(color);
  keyWrapper.style.boxShadow = [
    `10px 10px 0 ${shadowColor(color)}`,          // drop shadow (matches Python)
    `0 0 0 5px ${borderColor(color)}`,            // simulated border via outline shadow
  ].join(", ");

  // Label text
  keyLabel.textContent = keyName;

  // Scale font to fit
  scaleFontSize();
}

// ─── Audio ────────────────────────────────────────────────────────────────────

function initAudio() {
  if (audioCtx) return;
  try {
    audioCtx = new (window.AudioContext || window.webkitAudioContext)();
  } catch (e) {
    console.warn("Web Audio API not available:", e);
  }
}

function playTone(freq) {
  if (!audioCtx) return;
  // Resume suspended context (browser may suspend after inactivity/backgrounding)
  audioCtx.resume().then(() => {
    try {
      const now  = audioCtx.currentTime;
      const osc  = audioCtx.createOscillator();
      const gain = audioCtx.createGain();

      osc.type            = "sine";
      osc.frequency.value = freq;

      // 10 ms fade-in, hold, 10 ms fade-out — matches Python envelope
      gain.gain.setValueAtTime(0,   now);
      gain.gain.linearRampToValueAtTime(1, now + 0.01);
      gain.gain.setValueAtTime(1,         now + 0.99);
      gain.gain.linearRampToValueAtTime(0, now + 1.0);

      osc.connect(gain);
      gain.connect(audioCtx.destination);

      osc.start(now);
      osc.stop(now + 1.0);
    } catch (e) {
      console.warn("Could not play tone:", e);
    }
  }).catch((e) => console.warn("AudioContext resume failed:", e));
}

function playRandomTone() {
  const freq = C_MAJOR[Math.floor(Math.random() * C_MAJOR.length)];
  playTone(freq);
}

// ─── Game start ───────────────────────────────────────────────────────────────

function startGame(firstEvent) {
  state = "PLAYING";

  // Initialise audio — must be inside a user gesture
  initAudio();

  // Request true fullscreen (best effort; may be denied by browser policy)
  document.documentElement.requestFullscreen().catch(() => {});

  // Swap screens
  titleScreen.style.display = "none";
  gameScreen.style.display  = "flex";

  // Process the triggering key/click as the first game action
  if (firstEvent) {
    const keyName = getKeyName(firstEvent);
    const color   = generateColor();
    applyKeyPress(keyName, color);
    playRandomTone();
  }
}

// ─── Event listeners ─────────────────────────────────────────────────────────

document.addEventListener("keydown", (event) => {
  if (state === "TITLE") {
    event.preventDefault();
    startGame(event);
    return;
  }

  if (state === "PLAYING") {
    event.preventDefault();
    const keyName = getKeyName(event);
    const color   = generateColor();
    applyKeyPress(keyName, color);
    playRandomTone();
  }
});

titleScreen.addEventListener("click", () => {
  if (state === "TITLE") {
    startGame(null);
  }
});

// Re-scale when window is resized during gameplay
window.addEventListener("resize", () => {
  if (state === "PLAYING" && keyLabel.textContent) {
    scaleFontSize();
  }
});
