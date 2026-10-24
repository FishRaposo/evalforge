/** @type {import('next').NextConfig} */
const connected = process.env.EVALFORGE_CONNECTED_BUILD === 'true';
module.exports = { ...(connected ? {} : {output: 'export'}), distDir: process.env.NEXT_DIST_DIR || (connected ? 'dist-connected' : 'dist') };
