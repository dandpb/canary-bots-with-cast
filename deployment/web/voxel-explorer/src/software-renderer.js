// A real Canvas2D projection of the same cuboids used by WebGL. This deliberately
// simplifies light/shadows; it never substitutes a screenshot for the 3D scene.
const FACES = [[1, 5, 6, 2], [4, 0, 3, 7], [3, 2, 6, 7], [4, 5, 1, 0], [5, 4, 7, 6], [0, 1, 2, 3]];
const CORNERS = [-1,-1,-1, 1,-1,-1, 1,1,-1, -1,1,-1, -1,-1,1, 1,-1,1, 1,1,1, -1,1,1];
const clamp = (v, a, b) => Math.max(a, Math.min(b, v));
const srgb = v => (v <= .0031308 ? v * 12.92 : 1.055 * Math.pow(v, 1 / 2.4) - .055) * 255;
const LITTLE_ENDIAN = new Uint8Array(new Uint32Array([0x01020304]).buffer)[0] === 4;
const packedColor = (r, g, b) => LITTLE_ENDIAN ? ((255 << 24) | (b << 16) | (g << 8) | r) >>> 0 : ((r << 24) | (g << 16) | (b << 8) | 255) >>> 0;

export class SoftwareRenderer {
  constructor(THREE, { canvas } = {}) {
    this.THREE = THREE;
    this.domElement = canvas || document.createElement('canvas');
    this.context = this.domElement.getContext('2d', { alpha: false, desynchronized: true });
    if (!this.context) throw new Error('O navegador não disponibilizou o Canvas 2D.');
    this.isSoftwareRenderer = true;
    this.shadowMap = { enabled: false, type: 0, needsUpdate: false };
    this.info = { render: { calls: 0, triangles: 0 }, memory: { geometries: 0 }, software: { faces: 0, frameMs: 0, unsupportedMeshes: 0 } };
    this.toneMapping = 0; this.toneMappingExposure = 1; this.outputColorSpace = 'srgb';
    this._width = 1; this._height = 1; this._pixelRatio = 1;
    this._clearColor = new THREE.Color('#bfd0c2');
    this._fogRGB = [191, 208, 194]; this._fogKey = '';
    this._cache = new Map(); this._colorCache = new Map(); this._frame = 0;
    this._quality = 'auto'; this._faceBudget = 10000; this._pixelArea = 1.1;
    this._matrix = new THREE.Matrix4(); this._instance = new THREE.Matrix4();
    this._sunPosition = new THREE.Vector3(); this._sunTarget = new THREE.Vector3();
    this._orthographicEye = new THREE.Vector3();
    this._light = [-.44, .82, .35]; this._lastFrame = -Infinity;
    this._warnedUnsupported = false;
    this._image = null; this._depth = null; this._packed = null;
  }
  setSize(width, height, updateStyle = true) {
    this._width = Math.max(1, Math.round(width)); this._height = Math.max(1, Math.round(height));
    // Bound the CPU framebuffer independently of device DPI. CSS scales it to the viewport.
    const budget = this._quality === 'low' ? 640 * 480 : this._quality === 'high' ? 1280 * 960 : 960 * 720;
    const scale = Math.min(1, this._pixelRatio, Math.sqrt(budget / (this._width * this._height)));
    const w = Math.max(1, Math.round(this._width * scale)), h = Math.max(1, Math.round(this._height * scale));
    if (this.domElement.width !== w) this.domElement.width = w;
    if (this.domElement.height !== h) this.domElement.height = h;
    if (updateStyle) { this.domElement.style.width = `${this._width}px`; this.domElement.style.height = `${this._height}px`; }
    this._scaleX = w / this._width; this._scaleY = h / this._height;
    if (!this._image || this._image.width !== w || this._image.height !== h) {
      this._image = this.context.createImageData(w, h);
      this._packed = new Uint32Array(this._image.data.buffer, this._image.data.byteOffset, w * h);
      this._depth = new Float32Array(w * h);
    }
  }
  setPixelRatio(ratio) { this._pixelRatio = clamp(Number(ratio) || 1, .5, 1); this.setSize(this._width, this._height, false); }
  getPixelRatio() { return this._pixelRatio; }
  getSize(target) { return target.set(this._width, this._height); }
  setClearColor(value) { this._clearColor.set(value); }
  setQuality(value) {
    this._quality = ['auto', 'low', 'high'].includes(value) ? value : 'auto';
    this._faceBudget = value === 'low' ? 6500 : value === 'high' ? 14500 : 10000;
    this._pixelArea = value === 'low' ? 2.4 : value === 'high' ? .65 : 1.1;
    this.setSize(this._width, this._height, false);
  }
  dispose() { this._cache.clear(); this._colorCache.clear(); this._image = this._depth = this._packed = null; }

  _color(rgb, fog = 0) {
    const r = clamp(Math.round(rgb[0]), 0, 255), g = clamp(Math.round(rgb[1]), 0, 255), b = clamp(Math.round(rgb[2]), 0, 255);
    const q = clamp(Math.round(fog * 16), 0, 16), key = `${r},${g},${b},${q}`;
    let result = this._colorCache.get(key);
    if (!result) {
      const f = q / 16, c = this._fogRGB;
      const red = Math.round(r + (c[0] - r) * f), green = Math.round(g + (c[1] - g) * f), blue = Math.round(b + (c[2] - b) * f);
      result = { r: red, g: green, b: blue, packed: packedColor(red, green, blue) };
      this._colorCache.set(key, result);
    }
    return result;
  }

  _record(mesh, index, world) {
    const e = world.elements, geo = mesh.geometry, size = geo.parameters || {};
    const sx = (size.width || 1) / 2, sy = (size.height || 1) / 2, sz = (size.depth || 1) / 2;
    const verts = new Float32Array(24);
    for (let j = 0; j < 8; j++) {
      const x = CORNERS[j * 3] * sx, y = CORNERS[j * 3 + 1] * sy, z = CORNERS[j * 3 + 2] * sz;
      verts[j * 3] = e[0] * x + e[4] * y + e[8] * z + e[12];
      verts[j * 3 + 1] = e[1] * x + e[5] * y + e[9] * z + e[13];
      verts[j * 3 + 2] = e[2] * x + e[6] * y + e[10] * z + e[14];
    }
    const ax = Math.hypot(e[0], e[1], e[2]) * sx, ay = Math.hypot(e[4], e[5], e[6]) * sy, az = Math.hypot(e[8], e[9], e[10]) * sz;
    const nx = [e[0] / (ax || 1) * sx, e[1] / (ax || 1) * sx, e[2] / (ax || 1) * sx];
    const ny = [e[4] / (ay || 1) * sy, e[5] / (ay || 1) * sy, e[6] / (ay || 1) * sy];
    const nz = [e[8] / (az || 1) * sz, e[9] / (az || 1) * sz, e[10] / (az || 1) * sz];
    const normals = [nx, nx.map(v => -v), ny, ny.map(v => -v), nz, nz.map(v => -v)];
    const material = Array.isArray(mesh.material) ? mesh.material[0] : mesh.material;
    const vertexColor = material.vertexColors ? geo.getAttribute('color') : null;
    // A fallback must not conceal the invalid material configuration that turns WebGL meshes black.
    if (material.vertexColors && !vertexColor) throw new Error(`Missing geometry color attribute on ${mesh.name || 'voxel mesh'}.`);
    const base = material.color || { r: 1, g: 1, b: 1 }, colors = mesh.instanceColor?.array, ci = index * 3;
    const linear = [base.r * (colors ? colors[ci] : 1), base.g * (colors ? colors[ci + 1] : 1), base.b * (colors ? colors[ci + 2] : 1)];
    const glow = material.emissiveIntensity > 0 && material.emissive && material.emissive.r + material.emissive.g + material.emissive.b > .01;
    const shades = normals.map((n, face) => {
      const tint = [1, 1, 1];
      if (vertexColor) {
        // Standard BoxGeometry stores four independent color vertices per face.
        tint.fill(0);
        for (let v = face * 4; v < face * 4 + 4; v++) {
          tint[0] += vertexColor.getX(v) / 4; tint[1] += vertexColor.getY(v) / 4; tint[2] += vertexColor.getZ(v) / 4;
        }
      }
      const dot = Math.max(0, n[0] * this._light[0] + n[1] * this._light[1] + n[2] * this._light[2]);
      const light = glow || material.isMeshBasicMaterial ? 1.03 : .56 + .40 * dot + .08 * Math.max(0, n[1]);
      return linear.map((channel, i) => srgb(channel * tint[i]) * light);
    });
    const role = mesh.userData.voxelRole || 'structure';
    const preserve = mesh.userData.voxelPreserve === true || ['structure', 'terrain', 'water', 'paving', 'glow'].includes(role);
    return {
      verts, normals, shades, material, role, preserve, x: e[12], y: e[13], z: e[14], ax, ay, az,
      radius: Math.hypot(ax, ay, az), topOnly: mesh.userData.voxelTopOnly === true,
      importance: preserve ? 7 : role === 'foliage' ? 2 : 1
    };
  }

  _meshRecords(mesh) {
    const material = Array.isArray(mesh.material) ? mesh.material[0] : mesh.material;
    const signature = [mesh.matrixWorld.elements.join(','), mesh.count || 0, mesh.geometry.uuid,
      mesh.instanceMatrix?.version || 0, mesh.instanceColor?.version || 0, material.version,
      material.color?.getHex(), material.emissive?.getHex(), material.emissiveIntensity,
      material.vertexColors, mesh.geometry.getAttribute('color')?.version || 0,
      mesh.userData.voxelRole, mesh.userData.voxelPreserve, mesh.userData.voxelTopOnly, this._light.join(',')].join('|');
    const previous = this._cache.get(mesh.id);
    if (previous?.signature === signature) return previous.records;
    const records = [];
    if (mesh.isInstancedMesh) {
      for (let i = 0; i < mesh.count; i++) {
        this._instance.fromArray(mesh.instanceMatrix.array, i * 16);
        this._matrix.multiplyMatrices(mesh.matrixWorld, this._instance);
        records.push(this._record(mesh, i, this._matrix));
      }
    } else records.push(this._record(mesh, 0, mesh.matrixWorld));
    this._cache.set(mesh.id, { records, signature });
    return records;
  }

  _projectPolygon(vertices, indices, view, near, fx, fy, cx, cy, perspective, far = Infinity) {
    const points = indices.map(n => {
      const j = n * 3, x = vertices[j], y = vertices[j + 1], z = vertices[j + 2];
      return [view[0] * x + view[4] * y + view[8] * z + view[12],
        view[1] * x + view[5] * y + view[9] * z + view[13],
        -(view[2] * x + view[6] * y + view[10] * z + view[14])];
    });
    const clipDepth = (input, boundary, keepGreater) => {
      const output = [];
      for (let i = 0; i < input.length; i++) {
        const a = input[i], b = input[(i + 1) % input.length];
        const ia = keepGreater ? a[2] >= boundary : a[2] <= boundary, ib = keepGreater ? b[2] >= boundary : b[2] <= boundary;
        if (ia) output.push(a);
        if (ia !== ib) { const t = (boundary - a[2]) / (b[2] - a[2]); output.push([a[0] + (b[0] - a[0]) * t, a[1] + (b[1] - a[1]) * t, boundary]); }
      }
      return output;
    };
    const nearClipped = clipDepth(points, near, true);
    const clipped = Number.isFinite(far) ? clipDepth(nearClipped, far, false) : nearClipped;
    if (clipped.length < 3) return null;
    const coords = [], depths = []; let depth = 0, minX = Infinity, minY = Infinity, maxX = -Infinity, maxY = -Infinity;
    for (const p of clipped) {
      const inv = perspective ? 1 / p[2] : 1, x = cx + p[0] * fx * inv, y = cy - p[1] * fy * inv;
      if (!Number.isFinite(x) || !Number.isFinite(y)) return null;
      coords.push(x, y); depths.push(perspective ? inv : -p[2]);
      depth += p[2]; minX = Math.min(minX, x); maxX = Math.max(maxX, x); minY = Math.min(minY, y); maxY = Math.max(maxY, y);
    }
    if (maxX < 0 || minX > this._width || maxY < 0 || minY > this._height) return null;
    return { coords, depths, depth: depth / clipped.length,
      area: Math.max(0, Math.min(maxX, this._width) - Math.max(minX, 0)) * Math.max(0, Math.min(maxY, this._height) - Math.max(minY, 0)) };
  }

  _rasterFace(face) {
    // Reciprocal camera depth is linear across a projected planar face. A depth
    // buffer resolves occlusion per pixel, so neither terrain roles nor the
    // average depth of a large ground polygon can cover a nearer building.
    const width = this._image.width, height = this._image.height;
    const p = face.coords, q = face.depths, n = q.length, xs = [], ys = [];
    let minY = Infinity, maxY = -Infinity;
    for (let i = 0; i < n; i++) {
      xs.push(p[i * 2] * this._scaleX); ys.push(p[i * 2 + 1] * this._scaleY);
      minY = Math.min(minY, ys[i]); maxY = Math.max(maxY, ys[i]);
    }
    const rowStart = Math.max(0, Math.ceil(minY - .5)), rowEnd = Math.min(height - 1, Math.ceil(maxY - .5) - 1);
    const color = face.color, opacity = clamp(face.opacity ?? 1, 0, 1), pixels = this._image.data;
    const opaque = opacity >= .999, writesDepth = face.depthWrite !== false;
    if (opacity <= 0) return;
    for (let y = rowStart; y <= rowEnd; y++) {
      const sampleY = y + .5; let left = Infinity, right = -Infinity, leftQ = 0, rightQ = 0;
      for (let i = 0; i < n; i++) {
        const j = (i + 1) % n, ay = ys[i], by = ys[j];
        if (!((ay <= sampleY && by > sampleY) || (by <= sampleY && ay > sampleY))) continue;
        const t = (sampleY - ay) / (by - ay), x = xs[i] + (xs[j] - xs[i]) * t, depth = q[i] + (q[j] - q[i]) * t;
        if (x < left) { left = x; leftQ = depth; }
        if (x > right) { right = x; rightQ = depth; }
      }
      if (!(right > left)) continue;
      const xStart = Math.max(0, Math.ceil(left - .5)), xEnd = Math.min(width - 1, Math.ceil(right - .5) - 1);
      const dq = (rightQ - leftQ) / (right - left);
      let depth = leftQ + (xStart + .5 - left) * dq, index = y * width + xStart;
      for (let x = xStart; x <= xEnd; x++, index++, depth += dq) {
        if (depth <= this._depth[index]) continue;
        if (opaque) this._packed[index] = color.packed;
        else {
          const offset = index * 4, rest = 1 - opacity;
          pixels[offset] = color.r * opacity + pixels[offset] * rest;
          pixels[offset + 1] = color.g * opacity + pixels[offset + 1] * rest;
          pixels[offset + 2] = color.b * opacity + pixels[offset + 2] * rest;
        }
        if (writesDepth) this._depth[index] = depth;
      }
    }
  }

  render(scene, camera) {
    const start = performance.now();
    if (start - this._lastFrame < 28) return; // Presentation capped near 30fps; simulation remains independent.
    this._lastFrame = start;
    scene.updateMatrixWorld(true); camera.updateMatrixWorld(true); camera.matrixWorldInverse.copy(camera.matrixWorld).invert();
    const view = camera.matrixWorldInverse.elements, projection = camera.projectionMatrix.elements;
    const perspective = camera.isPerspectiveCamera === true, near = Math.max(.01, camera.near || .1);
    if (!perspective) camera.getWorldDirection(this._orthographicEye).negate();
    const fx = projection[0] * this._width / 2, fy = projection[5] * this._height / 2, cx = this._width / 2, cy = this._height / 2;
    const exploration = scene.userData.exploration || {}, walking = exploration.mode === 'walk';
    const configuredDistance = Number.isFinite(exploration.viewDistance) && exploration.viewDistance > 0 ? exploration.viewDistance : camera.far;
    const maxDistance = Math.min(camera.far || Infinity, configuredDistance || Infinity);
    const background = scene.background?.isColor ? scene.background : this._clearColor;
    const fogColor = scene.fog?.color || background;
    const fogKey = fogColor.getHexString();
    if (fogKey !== this._fogKey) { this._fogKey = fogKey; this._fogRGB = [srgb(fogColor.r), srgb(fogColor.g), srgb(fogColor.b)]; this._colorCache.clear(); }
    const fogAt = depth => {
      if (!scene.fog) return 0;
      if (scene.fog.isFogExp2) return clamp(1 - Math.exp(-(scene.fog.density ** 2) * depth ** 2), 0, 1);
      const t = clamp((depth - scene.fog.near) / Math.max(.001, scene.fog.far - scene.fog.near), 0, 1);
      return t * t * (3 - 2 * t);
    };
    let firstSun;
    scene.traverseVisible(o => { if (!firstSun && o.isDirectionalLight) firstSun = o; });
    if (firstSun) {
      firstSun.getWorldPosition(this._sunPosition); firstSun.target.getWorldPosition(this._sunTarget);
      this._sunPosition.sub(this._sunTarget).normalize();
      this._light = this._sunPosition.toArray().map(v => Math.round(v * 1000) / 1000);
    }
    const lists = [], planes = []; let unsupported = 0;
    scene.traverseVisible(o => {
      if (!o.isMesh || !o.geometry) return;
      if (o.geometry.type === 'PlaneGeometry') planes.push(o);
      else if (o.geometry.type === 'BoxGeometry') lists.push(this._meshRecords(o));
      else unsupported++;
    });
    if (unsupported && !this._warnedUnsupported) {
      console.warn('Compatibility renderer supports BoxGeometry and PlaneGeometry; other geometry needs an explicit fallback.');
      this._warnedUnsupported = true;
    }
    if (!this._image) this.setSize(this._width, this._height, false);
    this._packed.fill(this._color([srgb(background.r), srgb(background.g), srgb(background.b)]).packed);
    this._depth.fill(-Infinity);
    let calls = 0, triangles = 0;
    const essential = [], optional = [];
    for (const plane of planes) {
      const attr = plane.geometry.attributes.position, m = plane.matrixWorld.elements, verts = [];
      for (let i = 0; i < 4; i++) {
        const x = attr.getX(i), y = attr.getY(i), z = attr.getZ(i);
        verts.push(m[0] * x + m[4] * y + m[8] * z + m[12], m[1] * x + m[5] * y + m[9] * z + m[13], m[2] * x + m[6] * y + m[10] * z + m[14]);
      }
      const face = this._projectPolygon(verts, [0, 1, 3, 2], view, near, fx, fy, cx, cy, perspective, maxDistance);
      if (face) {
        const color = plane.material.color || background;
        face.color = this._color([srgb(color.r), srgb(color.g), srgb(color.b)], fogAt(face.depth));
        face.opacity = plane.material.transparent ? plane.material.opacity : 1; face.depthWrite = plane.material.depthWrite;
        essential.push(face);
      }
    }
    // Project essential geometry first. When it fills the detail budget, the
    // optional faces would all be discarded, so avoid projecting them at all.
    for (const preservePass of [true, false]) {
      if (!preservePass && essential.length >= this._faceBudget) break;
      for (const records of lists) for (const r of records) {
      if (r.preserve !== preservePass) continue;
      const vx = view[0] * r.x + view[4] * r.y + view[8] * r.z + view[12], vy = view[1] * r.x + view[5] * r.y + view[9] * r.z + view[13];
      const depth = -(view[2] * r.x + view[6] * r.y + view[10] * r.z + view[14]), radius = r.radius;
      if (depth + radius < near || depth - radius > maxDistance) continue;
      if (perspective && (Math.abs(vx) - radius > (depth + radius) * this._width / (2 * fx) || Math.abs(vy) - radius > (depth + radius) * this._height / (2 * fy))) continue;
      const dx = camera.position.x - r.x, dy = camera.position.y - r.y, dz = camera.position.z - r.z;
      const cubeFaces = []; let maxFaceArea = 0;
      for (let f = 0; f < 6; f++) {
        if (r.topOnly && f !== 2) continue;
        const n = r.normals[f], half = f < 2 ? r.ax : f < 4 ? r.ay : r.az;
        const facing = perspective ? n[0] * dx + n[1] * dy + n[2] * dz - half :
          n[0] * this._orthographicEye.x + n[1] * this._orthographicEye.y + n[2] * this._orthographicEye.z;
        if (facing <= .0001) continue;
        const poly = this._projectPolygon(r.verts, FACES[f], view, near, fx, fy, cx, cy, perspective, maxDistance);
        if (!poly) continue;
        poly.color = this._color(r.shades[f], fogAt(poly.depth));
        poly.opacity = r.material.transparent ? r.material.opacity : 1;
        poly.depthWrite = r.material.depthWrite;
        cubeFaces.push(poly); maxFaceArea = Math.max(maxFaceArea, poly.area);
      }
      if (!cubeFaces.length) continue;
      if (r.preserve) essential.push(...cubeFaces);
      else if (maxFaceArea >= this._pixelArea * (walking ? .8 : 1)) optional.push({ faces: cubeFaces, score: maxFaceArea * r.importance });
      }
    }
    // Structural solids always survive LOD. Detail uses whole cubes, never disconnected faces.
    optional.sort((a, b) => b.score - a.score);
    const faces = essential;
    for (const candidate of optional) if (faces.length + candidate.faces.length <= this._faceBudget) faces.push(...candidate.faces);
    const opaque = [], transparent = [];
    for (const face of faces) (face.opacity >= .999 ? opaque : transparent).push(face);
    opaque.sort((a, b) => a.depth - b.depth);
    transparent.sort((a, b) => b.depth - a.depth);
    for (const face of [...opaque, ...transparent]) { this._rasterFace(face); calls++; triangles += face.depths.length - 2; }
    this.context.putImageData(this._image, 0, 0);
    const elapsed = performance.now() - start;
    Object.assign(this.info.render, { calls, triangles });
    this.info.memory.geometries = lists.length + planes.length;
    Object.assign(this.info.software, { faces: faces.length, frameMs: Math.round(elapsed), unsupportedMeshes: unsupported });
    this._frame++;
    if (this._quality === 'auto' && this._frame % 45 === 0) {
      if (elapsed > 46) { this._faceBudget = Math.max(6500, this._faceBudget - 700); this._pixelArea = Math.min(3, this._pixelArea + .2); }
      else if (elapsed < 22) { this._faceBudget = Math.min(11500, this._faceBudget + 400); this._pixelArea = Math.max(.8, this._pixelArea - .1); }
    }
    if (this._colorCache.size > 16000) this._colorCache.clear();
  }
}
