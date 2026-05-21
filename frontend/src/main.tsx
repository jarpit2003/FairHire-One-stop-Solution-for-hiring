import React from "react";
import ReactDOM from "react-dom/client";
import Lenis from "lenis";
import App from "./App";
import "./index.css";

// Lenis smooth scroll — applied to the window (default)
const lenis = new Lenis({
  duration: 1.2,
  easing: (t: number) => Math.min(1, 1.001 - Math.pow(2, -10 * t)),
  smoothWheel: true,
  wheelMultiplier: 1,
  touchMultiplier: 2,
});

// Use rAF loop instead of autoRaf so we control it
function raf(time: number) {
  lenis.raf(time);
  requestAnimationFrame(raf);
}
requestAnimationFrame(raf);

// Expose globally so RecruiterChat can reference it
(window as any).__lenis = lenis;

ReactDOM.createRoot(document.getElementById("root")!).render(
  <React.StrictMode>
    <App />
  </React.StrictMode>
);
