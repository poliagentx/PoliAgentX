/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    "../templates/**/*.{html,js}",   
    "../../templates/**/*.{html,js}",
    "./static/src/**/*.{js,jsx,ts,tsx}", 
  ],
  theme: {
    extend: {
  
     
    },
  },
  plugins: [
    require("@tailwindcss/forms"),
    require("@tailwindcss/typography"),
    require("@tailwindcss/aspect-ratio"),
  ],
};
