export default {
  content: ["./index.html", "./src/**/*.{ts,tsx}"],
  theme: {
    extend: {
      colors: {
        ink: { 900: "#0B2D2E", 800: "#0F3D3E", 700: "#14504F", 500: "#3C6E6B" },
        coral: { DEFAULT: "#FF7A59", soft: "#FFE7DF", deep: "#E85D3A" },
        sage: { DEFAULT: "#EAF3F0", 2: "#D6E8E2" },
        leaf: { DEFAULT: "#2E8B7A", soft: "#D8F0EA" },
        sun: { DEFAULT: "#F4B942", soft: "#FFF3D6" },
        sky: { DEFAULT: "#4C8DFF", soft: "#E3EEFF" },
        plum: { DEFAULT: "#8B5CF6", soft: "#EEE8FF" },
        paper: "#F7FAF9",
      },
      fontFamily: {
        display: ["Fraunces", "Georgia", "serif"],
        sans: ["DM Sans", "Noto Sans Tamil", "system-ui", "sans-serif"],
      },
      boxShadow: {
        soft: "0 8px 30px -12px rgba(15,61,62,.25)",
        pop: "0 14px 40px -14px rgba(255,122,89,.6)",
      },
      keyframes: {
        floaty: { "0%,100%": { transform: "translateY(0)" }, "50%": { transform: "translateY(-6px)" } },
        ring: { "0%": { transform: "scale(.6)", opacity: ".6" }, "100%": { transform: "scale(1.7)", opacity: "0" } },
      },
      animation: { floaty: "floaty 4s ease-in-out infinite", ring: "ring 3.2s ease-out infinite" },
    },
  },
  plugins: [],
};
