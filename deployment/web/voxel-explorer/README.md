# Thais em voxel

Explorador local do centro de Thais, construído com a skill **Lugares em Voxel**. Abra **Passeio** para um percurso de 24 segundos, arraste o **Diorama** para girar a cidade ou escolha **Caminhar**. O botão **Andar** abre os 16 recortes. O **Mapa** mostra a posição do jogador e os pontos de partida do andar atual.

## Executar

Com Node.js 22.12 ou posterior, na pasta deste arquivo:

```sh
npm ci
npm run check
npm run build
npm run preview -- --host 127.0.0.1 --port 8176 --strictPort
```

Abra [o explorador](http://127.0.0.1:8176/). Para abrir diretamente o subsolo, use [andar 08](http://127.0.0.1:8176/?andar=8). O [modo de compatibilidade](http://127.0.0.1:8176/?render=software) desenha a mesma geometria em Canvas 2D.

## Cartografia

O recorte inclui as casas X 32329 a 32408 e Y 32201 a 32280 nos 16 PNGs do World Map. Um pixel representa uma casa e mede 1,7 unidade na cena. A origem e os hashes dos arquivos estão em [thais.json](src/thais.json). Para reproduzir a extração com Python e Pillow, execute `python scripts/crop-thais.py`.

O templo e o depot usam as posições do [cadastro do Canary](../../../data/bot/authored/city_pois.csv). A alameda e os jardins descrevem padrões visíveis no minimapa. Fachadas, cores de materiais, alturas e coberturas são interpretações. Na superfície, os volumes usam os pisos superiores alinhados. A troca de andar é feita pelo seletor.

Dados cartográficos do projeto [TibiaMaps](https://github.com/tibiamaps/tibia-map-data), com [licença MIT](public/data/LICENSE-map.txt).

## Interface
- `[index.html]` / `[vite.config.js]` / `[package.json:scripts]` — Vite frontend build (`npm run check`, `npm run build`, `npm run preview`) supporting URL parameters `?andar=<0..15>` and `?render=software`.
- Subdirectories:
  - `src`: [`./src/README.md`](./src/README.md) — Voxel scene builder, district map data (`thais.json`), WebGL/Canvas2D software renderer, navigation, and place validation.
  - `scripts`: [`./scripts/README.md`](./scripts/README.md) — Map cropping (`crop-thais.py`) and place validation CLI (`check-place.mjs`).

## Invariants
- The cropped Thais region covers exact map coordinates `X 32329..32408` and `Y 32201..32280` across 16 floors (`0..15`), with 1 pixel = 1 tile = `1.7` scene units, verified against source hashes in `src/thais.json` (`[scripts/check-place.mjs]`).
- `?render=software` renders the same district geometry via 2D Canvas (`SoftwareRenderer`) when WebGL is unavailable.

## Side Effects
- `npm run build` outputs bundled static assets into `dist/`; `scripts/crop-thais.py` writes cropped floor PNGs and updates `src/thais.json` hashes.

## Verification
- Run: `npm run check && npm run build`

