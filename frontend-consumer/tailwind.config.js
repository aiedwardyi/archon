/** @type {import('tailwindcss').Config} */
export default {
  content: ['./index.html', './index.tsx', './App.tsx', './components/**/*.{ts,tsx}', './pages/**/*.{ts,tsx}', './hooks/**/*.{ts,tsx}', './services/**/*.{ts,tsx}'],
  darkMode: 'class',
  theme: {
    extend: {
      fontFamily: {
        sans: ['Aptos', '"Segoe UI Variable Text"', '"Segoe UI"', 'sans-serif'],
        mono: ['"Cascadia Code"', '"IBM Plex Mono"', '"SFMono-Regular"', 'monospace'],
      },
      boxShadow: {
        soft: '0 24px 60px rgba(15, 23, 42, 0.08)',
      },
    },
  },
  plugins: [],
};
