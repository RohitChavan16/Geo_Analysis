/** @type {import('tailwindcss').Config} */
export default {
  darkMode: 'class',
  content: ['./index.html', './src/**/*.{js,ts,jsx,tsx}'],
  theme: {
    extend: {
      colors: {
        ink: '#0b1220',
        slateblue: '#3957ff',
        mint: '#00c48c',
        rose: '#e85d75',
        amber: '#f59e0b',
      },
      boxShadow: {
        soft: '0 10px 30px rgba(2, 8, 23, 0.08)',
      },
      backgroundImage: {
        'dash-gradient': 'radial-gradient(circle at 20% 20%, rgba(57,87,255,0.18), transparent 35%), radial-gradient(circle at 80% 0%, rgba(0,196,140,0.16), transparent 30%)',
      },
    },
  },
  plugins: [],
}
