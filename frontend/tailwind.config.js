/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    "./app/**/*.{js,jsx}",
    "./components/**/*.{js,jsx}",
    "./lib/**/*.{js,jsx}",
  ],
  theme: {
    extend: {
      colors: {
        "bg-primary": "#0A0A0F",
        "bg-surface": "#111118",
        "bg-surface-2": "#16161F",
        "accent-indigo": "#6C63FF",
        "accent-cyan": "#00D9FF",
        "accent-green": "#00FF88",
        "text-primary": "#F0F0FF",
        "text-secondary": "#8888AA",
        "border-dark": "#1E1E2E",
      },
      fontFamily: {
        sans: ["Inter", "sans-serif"],
      },
      animation: {
        "pulse-slow": "pulse 3s ease-in-out infinite",
      },
    },
  },
  plugins: [],
};
