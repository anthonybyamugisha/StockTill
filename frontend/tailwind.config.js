/** @type {import('tailwindcss').Config} */
export default {
  content: ['./index.html', './src/**/*.{js,ts,jsx,tsx}'],
  theme: {
    extend: {
      colors: {
        primary: {
          50: '#eff6ff',
          100: '#dbeafe',
          200: '#bfdbfe',
          300: '#93c5fd',
          400: '#60a5fa',
          500: '#0078d4',
          600: '#106ebe',
          700: '#005a9e',
          800: '#004578',
          900: '#003052',
        },
        surface: {
          50: '#f3f2f1',
          100: '#e1dfdd',
          200: '#c8c6c4',
          300: '#a19f9d',
          400: '#797775',
          500: '#605e5c',
          600: '#323130',
          700: '#1b1a19',
        },
        success: '#107c10',
        warning: '#ffb900',
        error: '#d13438',
      },
      fontFamily: {
        sans: ['"Segoe UI"', 'system-ui', '-apple-system', 'sans-serif'],
      },
      boxShadow: {
        card: '0 1.6px 3.6px 0 rgba(0,0,0,.132), 0 .3px .9px 0 rgba(0,0,0,.108)',
        modal: '0 32px 64px 0 rgba(0,0,0,.24), 0 2px 8px 0 rgba(0,0,0,.16)',
        nav: '0 2px 4px 0 rgba(0,0,0,.08)',
      },
    },
  },
  plugins: [],
};
