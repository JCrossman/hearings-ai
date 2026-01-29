/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        // Brand Colors
        'aer': {
          'blue': '#003366',
          'teal': '#00818a',
          'light-blue': '#e6f2f5',
          'text': '#333333',
        },
      },
      fontFamily: {
        // Clean sans-serif fonts
        sans: ['Inter', 'system-ui', 'sans-serif'],
      },
    },
  },
  plugins: [],
}
