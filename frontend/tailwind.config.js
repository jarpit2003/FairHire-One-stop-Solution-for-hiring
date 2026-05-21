/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      fontFamily: {
        sans: ["DM Sans", "ui-sans-serif", "system-ui", "-apple-system", "sans-serif"],
      },
      colors: {
        brand: {
          50:  "#ecfdf5",
          100: "#d1fae5",
          200: "#a7f3d0",
          400: "#34d399",
          500: "#10b981",
          600: "#059669",
          700: "#047857",
        },
      },
      boxShadow: {
        card:   "0 1px 2px rgba(0,0,0,0.35), 0 6px 20px rgba(0,0,0,0.28), 0 0 0 1px rgba(255,255,255,0.07)",
        glow:   "0 0 28px rgba(16,185,129,0.35)",
        "glow-sm": "0 0 14px rgba(16,185,129,0.25)",
      },
      backdropBlur: {
        xs: "4px",
      },
    },
  },
  plugins: [],
}
