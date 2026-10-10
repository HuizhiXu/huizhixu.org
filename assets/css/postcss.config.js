const path = require('path');
const root = path.resolve(__dirname, '../..');
module.exports = {
  plugins: [
    require('postcss-import')({ path: [root, path.join(root, 'themes/blist')] }),
    require('tailwindcss')(path.join(__dirname, 'tailwind.config.js')),
    require('autoprefixer')(),
  ],
};
