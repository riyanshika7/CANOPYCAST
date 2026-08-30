/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        nature: {
          900: '#14532d',
          800: '#166534',
          600: '#16a34a',
          500: '#22c55e',
          300: '#86efac',
          100: '#dcfce7',
          bg: '#F8FAF7',
          surface: '#F1F7F2',
          text: '#17231B',
          secText: '#647067',
          mutedText: '#87928B',
        }
      },
      fontFamily: {
        sans: ['Plus Jakarta Sans', 'Inter', 'sans-serif'],
      }
    },
  },
  plugins: [],
};