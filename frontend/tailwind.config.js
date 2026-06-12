/** @type {import('tailwindcss').Config} */
export default {
  darkMode: "class",
  content: ["./index.html", "./src/**/*.{ts,tsx}"],
  theme: {
    extend: {
      colors: {
        ink: "#102027",
        flood: "#0077b6",
        aqua: "#00a6a6",
        land: "#588157"
      }
    }
  },
  plugins: []
};
