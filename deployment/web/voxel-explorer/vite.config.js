import { readFileSync } from 'node:fs';
import { defineConfig } from 'vite';

export default defineConfig({
  base: './',
  plugins: [{
    name: 'downloadable-map',
    generateBundle() {
      this.emitFile({ type: 'asset', fileName: 'data/thais.json', source: readFileSync(new URL('./src/thais.json', import.meta.url)) });
    },
  }],
});
