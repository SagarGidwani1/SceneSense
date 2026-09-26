/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    './app/**/*.{js,ts,jsx,tsx,mdx}',
    './components/**/*.{js,ts,jsx,tsx,mdx}',
    './lib/**/*.{js,ts,jsx,tsx,mdx}',
  ],
  theme: {
    extend: {
      colors: {
        base: '#0E0E0F',
        surface: '#151517',
        surface2: '#1B1B1E',
        line: '#26262A',
        ink: '#EDEDED',
        muted: '#8A8A90',
        accent: '#E3A34A',
        accepted: '#5FB58A',
        rejected: '#D9695F',
        warn: '#D6B25E',
      },
      fontFamily: {
        sans: ['var(--font-inter)', 'system-ui', 'sans-serif'],
        mono: ['var(--font-jbmono)', 'monospace'],
      },
      borderRadius: {
        DEFAULT: '6px',
        md: '8px',
      },
    },
  },
  plugins: [],
};
