/** Shared cuboid authoring helpers. One world unit normally represents one metre. */
export function createVoxelKit(THREE, { name = 'Voxel place' } = {}) {
  const group = new THREE.Group();
  group.name = name;
  const colliders = [], walkSurfaces = [], batches = new Map();
  const roles = new Set(['terrain', 'paving', 'water', 'structure', 'foliage', 'detail', 'glow']);
  const counts = { voxels: 0, trees: 0, benches: 0, lamps: 0 };
  let result = null;

  const finite = (...values) => values.every(Number.isFinite);
  function requireOpen() {
    if (result) throw new Error('Add geometry before calling voxel kit finalize().');
  }
  function collider(x, z, w, d, rotation = 0) {
    const c = Math.abs(Math.cos(rotation)), s = Math.abs(Math.sin(rotation));
    const hx = (w * c + d * s) / 2, hz = (w * s + d * c) / 2;
    colliders.push({ minX: x - hx, maxX: x + hx, minZ: z - hz, maxZ: z + hz });
  }

  /** options: role, glow, rotation (yaw radians), collide, keep (retain silhouette). */
  function box(x, y, z, w, h, d, color, options = {}) {
    requireOpen();
    const { role = 'structure', glow = false, rotation = 0, collide = false, keep = false } = options;
    if (!finite(x, y, z, w, h, d, rotation) || w <= 0 || h <= 0 || d <= 0) {
      throw new TypeError('Voxel coordinates and dimensions must be finite; dimensions must be positive.');
    }
    if (!roles.has(role)) throw new TypeError(`Unknown voxel role: ${role}`);
    const tint = new THREE.Color(color);
    if (!finite(tint.r, tint.g, tint.b) || Math.min(tint.r, tint.g, tint.b) < 0) {
      throw new TypeError('Voxel color must have finite, nonnegative channels.');
    }
    const emissive = glow || role === 'glow';
    const key = `${role}:${emissive ? 1 : 0}:${keep ? 1 : 0}`;
    if (!batches.has(key)) batches.set(key, { role, glow: emissive, keep, boxes: [] });
    batches.get(key).boxes.push({ x, y, z, w, h, d, rotation, tint });
    counts.voxels++;
    if (collide) collider(x, z, w, d, rotation);
  }

  /** Draw a continuous path from [x,z] pairs or {x,z} points. y is its centre. */
  function path(points, width, color = '#c5b99b', y = .025) {
    requireOpen();
    if (!Array.isArray(points) || points.length < 2 || !finite(width, y) || width <= 0) {
      throw new TypeError('A path needs at least two points and a positive finite width.');
    }
    const xy = p => Array.isArray(p) ? { x: p[0], z: p[1] } : p;
    for (let i = 1; i < points.length; i++) {
      const a = xy(points[i - 1]), b = xy(points[i]);
      if (!a || !b || !finite(a.x, a.z, b.x, b.z)) throw new TypeError('Path points need finite x,z coordinates.');
      const dx = b.x - a.x, dz = b.z - a.z, length = Math.hypot(dx, dz);
      if (length < .0001) continue;
      box((a.x + b.x) / 2, y, (a.z + b.z) / 2, width, .06, length + .08, color,
        { role: 'paving', rotation: Math.atan2(dx, dz) });
      if (i < points.length - 1) box(b.x, y, b.z, width, .06, width, color, { role: 'paving' });
    }
  }

  /** options: height, crownWidth, trunkWidth, baseY, foliage, trunkColor, collide. */
  function tree(x, z, options = {}) {
    const {
      height = 6, crownWidth = height * .65, trunkWidth = Math.max(.28, height * .065),
      baseY = 0, foliage = ['#527743', '#678b4c', '#7b9a56'], trunkColor = '#6f5138', collide = true
    } = options;
    if (!finite(height, crownWidth, trunkWidth, baseY) || Math.min(height, crownWidth, trunkWidth) <= 0) {
      throw new TypeError('Tree dimensions must be positive and finite.');
    }
    const palette = Array.isArray(foliage) ? foliage : [foliage];
    if (!palette.length) throw new TypeError('Tree foliage palette cannot be empty.');
    box(x, baseY + height * .30, z, trunkWidth, height * .60, trunkWidth, trunkColor,
      { role: 'structure', collide });
    // A retained central canopy prevents whole trees turning into bare trunks at low detail.
    box(x, baseY + height * .70, z, crownWidth * .72, height * .43, crownWidth * .72,
      palette[0], { role: 'foliage', keep: true });
    for (let i = 0; i < 8; i++) {
      const angle = i * Math.PI / 4, offset = crownWidth * .28;
      box(x + Math.cos(angle) * offset, baseY + height * (.65 + (i % 3) * .035),
        z + Math.sin(angle) * offset, crownWidth * .49, height * .29, crownWidth * .49,
        palette[i % palette.length], { role: 'foliage' });
    }
    box(x, baseY + height * .925, z, crownWidth * .49, height * .15, crownWidth * .49,
      palette[palette.length - 1], { role: 'foliage' });
    counts.trees++;
  }

  /** options: baseY, width, woodColor, metalColor, collide. Faces local -Z. */
  function bench(x, z, yaw = 0, options = {}) {
    const { baseY = 0, width = 1.9, woodColor = '#9b7048', metalColor = '#374640', collide = true } = options;
    const c = Math.cos(yaw), s = Math.sin(yaw);
    const part = (lx, y, lz, w, h, d, color, role = 'structure') =>
      box(x + lx * c + lz * s, baseY + y, z - lx * s + lz * c, w, h, d, color, { role, rotation: yaw });
    for (const dx of [-width * .33, width * .33]) {
      part(dx, .28, 0, .12, .56, .62, metalColor);
      part(dx, .79, .24, .10, .88, .10, metalColor);
    }
    for (const dz of [-.2, 0, .2]) part(0, .57, dz, width, .12, .16, woodColor);
    for (const y of [.83, 1.06]) part(0, y, .28, width, .18, .11, woodColor);
    if (collide) collider(x, z, width, .72, yaw);
    counts.benches++;
  }

  /** options: height, baseY, ironColor, lightColor, collide. */
  function lamp(x, z, options = {}) {
    const { height = 3.5, baseY = 0, ironColor = '#35453e', lightColor = '#ffdc8d', collide = true } = options;
    box(x, baseY + .12, z, .38, .24, .38, ironColor, { collide });
    box(x, baseY + height / 2, z, .12, height, .12, ironColor);
    box(x, baseY + height, z, .40, .52, .40, lightColor, { role: 'glow' });
    for (const y of [height - .30, height + .30]) box(x, baseY + y, z, .53, .09, .53, ironColor);
    for (const dx of [-.19, .19]) for (const dz of [-.19, .19]) {
      box(x + dx, baseY + height, z + dz, .045, .6, .045, ironColor, { role: 'detail' });
    }
    counts.lamps++;
  }

  function finalize() {
    if (result) return result;
    const geometry = new THREE.BoxGeometry(1, 1, 1);
    const matrix = new THREE.Matrix4(), position = new THREE.Vector3(), scale = new THREE.Vector3();
    const rotation = new THREE.Quaternion(), axis = new THREE.Vector3(0, 1, 0);
    for (const batch of batches.values()) {
      // Per-instance tint is independent of geometry vertex colors. BoxGeometry has no color attribute.
      const material = new THREE.MeshStandardMaterial({
        color: 0xffffff, roughness: batch.role === 'water' ? .3 : .92, metalness: 0,
        ...(batch.glow ? { emissive: '#ffd495', emissiveIntensity: .7 } : {}),
        ...(batch.role === 'water' ? { transparent: true, opacity: .82, depthWrite: false } : {})
      });
      const mesh = new THREE.InstancedMesh(geometry, material, batch.boxes.length);
      mesh.name = `${name} · ${batch.role} (${batch.boxes.length})`;
      mesh.userData.voxelRole = batch.role;
      mesh.userData.voxelPreserve = batch.keep || ['structure', 'terrain', 'paving', 'water', 'glow'].includes(batch.role);
      batch.boxes.forEach((b, i) => {
        position.set(b.x, b.y, b.z); scale.set(b.w, b.h, b.d);
        rotation.setFromAxisAngle(axis, b.rotation); matrix.compose(position, rotation, scale);
        mesh.setMatrixAt(i, matrix); mesh.setColorAt(i, b.tint);
      });
      mesh.instanceMatrix.needsUpdate = true;
      mesh.instanceColor.needsUpdate = true;
      mesh.castShadow = !['terrain', 'paving', 'water', 'glow'].includes(batch.role);
      mesh.receiveShadow = batch.role !== 'glow';
      mesh.computeBoundingSphere(); group.add(mesh);
    }
    result = { group, colliders, walkSurfaces, stats: { ...counts, batches: batches.size, colliders: colliders.length, walkSurfaces: walkSurfaces.length } };
    return result;
  }
  return { group, colliders, walkSurfaces, box, path, tree, bench, lamp, finalize };
}
