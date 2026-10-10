const theme = require('../../themes/blist/assets/css/tailwind.config.js');
module.exports = {
  ...theme,
  purge: {
    enabled: process.env.HUGO_ENVIRONMENT === 'production',
    content: ['layouts/**/*.html', 'themes/blist/layouts/**/*.html',
      'content/**/*.md', 'content/**/*.html', 'assets/js/**/*.js', 'config.toml'],
  },
};
