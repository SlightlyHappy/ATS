/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    "./src/**/*.{js,jsx,ts,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        'bear-red': '#960303',
        'bear-gold': '#FFD700',
      }
    },
  },
  plugins: [],
}
