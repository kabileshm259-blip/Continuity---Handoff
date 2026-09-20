/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    "./app/**/*.{js,ts,jsx,tsx,mdx}",
    "./pages/**/*.{js,ts,jsx,tsx,mdx}",
    "./components/**/*.{js,ts,jsx,tsx,mdx}",
  ],
  theme: {
    extend: {
      colors: {
        brand: {
          50: '#f8fafc',
          100: '#f1f5f9',
          200: '#e2e8f0',
          300: '#cbd5e1',
          400: '#94a3b8',
          500: '#64748b',
          600: '#475569',
          700: '#334155',
          800: '#1e293b',
          900: '#0f172a',
          950: '#020617',
        },
        status: {
          unresolved: {
            bg: '#fffbeb',
            text: '#b45309',
            border: '#fde68a',
            dot: '#f59e0b',
          },
          atrisk: {
            bg: '#fff7ed',
            text: '#c2410c',
            border: '#fed7aa',
            dot: '#f97316',
          },
          blocked: {
            bg: '#fff1f2',
            text: '#be123c',
            border: '#fecdd3',
            dot: '#f43f5e',
          },
          exception: {
            bg: '#faf5ff',
            text: '#7e22ce',
            border: '#e9d5ff',
            dot: '#a855f7',
          },
          overdue: {
            bg: '#fef2f2',
            text: '#b91c1c',
            border: '#fecaca',
            dot: '#ef4444',
          },
          resolved: {
            bg: '#ecfdf5',
            text: '#047857',
            border: '#a7f3d0',
            dot: '#10b981',
          }
        }
      }
    },
  },
  plugins: [],
}
