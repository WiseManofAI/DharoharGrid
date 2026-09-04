/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{js,jsx}"],
  theme: {
    extend: {
      colors: {
        void: "#050507",
        panel: "rgba(18, 18, 22, 0.45)",
        "panel-solid": "#0d0e12",
        hairline: "rgba(255, 255, 255, 0.08)",
        "hairline-strong": "rgba(255, 255, 255, 0.16)",
        gold: "#e2b357",
        violet: "#a78bfa",
        signal: "#ef4444",
      },
      fontFamily: {
        sans: [
          "-apple-system",
          "BlinkMacSystemFont",
          '"Segoe UI"',
          "Roboto",
          "sans-serif",
        ],
      },
      backdropBlur: {
        glass: "16px",
      },
      boxShadow: {
        glass: "0 30px 60px rgba(0, 0, 0, 0.45)",
      },
    },
  },
  plugins: [],
};
