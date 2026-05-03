/** @type {import('tailwindcss').Config} */
export default {
  content: ['./index.html', './src/**/*.{js,ts,jsx,tsx}'],
  theme: {
    extend: {
      colors: {
        primary: {
          50:  '#eef3fb',
          100: '#d5e2f5',
          200: '#adc5eb',
          300: '#7fa3df',
          400: '#4f7ed1',
          500: '#2563c0',
          600: '#1a4fa0',
          700: '#1b4f8a',
          800: '#173f70',
          900: '#10305a',
        },
        secondary: {
          50:  '#fef8ec',
          100: '#fdecc8',
          200: '#fbd58e',
          300: '#f9bd54',
          400: '#f7a420',
          500: '#d4820a',
          600: '#b06a07',
          700: '#8c5305',
          800: '#683e04',
          900: '#452902',
        },
        accent: {
          50:  '#eaf5ed',
          100: '#c6e5cc',
          200: '#8dcc9d',
          300: '#55b36e',
          400: '#339950',
          500: '#2d7a3c',
          600: '#226030',
          700: '#174823',
          800: '#0d3017',
          900: '#04180a',
        },
      },
      fontFamily: {
        sans: ['Inter', 'system-ui', '-apple-system', 'Segoe UI', 'sans-serif'],
      },
      boxShadow: {
        card: '0 2px 8px rgba(0,0,0,0.07)',
        'card-hover': '0 6px 20px rgba(0,0,0,0.12)',
      },
    },
  },
  plugins: [],
}
