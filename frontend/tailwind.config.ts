/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    "./src/pages/**/*.{js,ts,jsx,tsx,mdx}",
    "./src/components/**/*.{js,ts,jsx,tsx,mdx}",
    "./src/app/**/*.{js,ts,jsx,tsx,mdx}",
  ],
  theme: {
    extend: {
      colors: {
        hz: {
          navy: "#0F2A47",
          teal: "#14B8A6",
          "teal-deep": "#0F766E",
          "teal-bright": "#2DD4BF",
          midnight: "#0B1220",
          slate: "#5B6B7F",
          mist: "#9AA8BA",
          ice: "#F4F8FB",
        },
        slate: {
          50: "#F4F8FB",
          100: "#F4F8FB",
          200: "#E4EBF1",
          300: "#9AA8BA",
          400: "#5B6B7F",
          500: "#5B6B7F",
          600: "#5B6B7F",
          700: "#0F2A47",
          800: "#0F2A47",
          900: "#0B1220",
          950: "#0B1220",
        },
      },
      fontFamily: {
        sans: ["Inter", "ui-sans-serif", "system-ui", "sans-serif"],
      },
    },
  },
  plugins: [],
};
