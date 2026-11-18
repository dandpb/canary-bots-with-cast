/** Pedestrian navigation over an authored terrain function and axis-aligned obstacle proxies. */
export function createNavigation(place, { radius = .28, maxStep = .45, safeSearchRadius = 16 } = {}) {
  if (![radius, maxStep, safeSearchRadius].every(Number.isFinite) || radius <= 0 || maxStep < 0 || safeSearchRadius < 0) {
    throw new TypeError('Navigation requires a positive radius and nonnegative finite limits.');
  }
  if (typeof place.isWalkable !== 'function' || typeof place.groundHeight !== 'function') {
    throw new TypeError('Place must supply isWalkable(x,z) and groundHeight(x,z).');
  }
  const colliders = place.colliders || [], surfaces = place.walkSurfaces || [];
  const buckets = new Map(), bucketSize = Math.max(4, radius * 8), bounds = place.bounds;
  if (bounds && (![bounds.minX, bounds.maxX, bounds.minZ, bounds.maxZ].every(Number.isFinite) || bounds.minX >= bounds.maxX || bounds.minZ >= bounds.maxZ)) {
    throw new TypeError('Place bounds must be finite and enclose an area.');
  }
  for (const b of [...colliders, ...surfaces]) {
    if (![b.minX, b.maxX, b.minZ, b.maxZ].every(Number.isFinite) || b.minX > b.maxX || b.minZ > b.maxZ) {
      throw new TypeError('Navigation boxes must have finite, ordered bounds.');
    }
  }
  for (const s of surfaces) if (!Number.isFinite(s.y)) throw new TypeError('Walk surfaces need a finite elevation.');
  for (const b of colliders) {
    for (let x = Math.floor((b.minX - radius) / bucketSize); x <= Math.floor((b.maxX + radius) / bucketSize); x++) {
      for (let z = Math.floor((b.minZ - radius) / bucketSize); z <= Math.floor((b.maxZ + radius) / bucketSize); z++) {
        const key = `${x},${z}`;
        if (!buckets.has(key)) buckets.set(key, []);
        buckets.get(key).push(b);
      }
    }
  }
  function surfaceAt(x, z) {
    let highest = null;
    for (const s of surfaces) {
      if (x >= s.minX && x <= s.maxX && z >= s.minZ && z <= s.maxZ && (!highest || s.y > highest.y)) highest = s;
    }
    return highest;
  }
  function inside(x, z) {
    return !bounds || (x >= bounds.minX && x <= bounds.maxX && z >= bounds.minZ && z <= bounds.maxZ);
  }
  function supported(x, z) {
    return inside(x, z) && (!!surfaceAt(x, z) || !!place.isWalkable(x, z));
  }
  function groundHeight(x, z) {
    const surface = surfaceAt(x, z), terrain = place.groundHeight(x, z);
    // Negative elevations are valid. A bridge/deck overrides lower terrain, not higher terrain.
    return surface ? Math.max(surface.y, Number.isFinite(terrain) && place.isWalkable(x, z) ? terrain : -Infinity) : terrain;
  }
  const footprint = [[0, 0], [1, 0], [-1, 0], [0, 1], [0, -1],
    [Math.SQRT1_2, Math.SQRT1_2], [-Math.SQRT1_2, Math.SQRT1_2],
    [Math.SQRT1_2, -Math.SQRT1_2], [-Math.SQRT1_2, -Math.SQRT1_2]];
  function valid(x, z) {
    if (!Number.isFinite(x) || !Number.isFinite(z)) return false;
    if (!supported(x, z)) return false;
    const height = groundHeight(x, z);
    if (!Number.isFinite(height)) return false;
    for (const [dx, dz] of footprint) {
      const px = x + dx * radius, pz = z + dz * radius;
      if (!supported(px, pz)) return false;
      const edgeHeight = groundHeight(px, pz);
      if (!Number.isFinite(edgeHeight) || Math.abs(edgeHeight - height) > maxStep + 1e-6) return false;
    }
    for (const b of buckets.get(`${Math.floor(x / bucketSize)},${Math.floor(z / bucketSize)}`) || []) {
      const cx = Math.max(b.minX, Math.min(x, b.maxX)), cz = Math.max(b.minZ, Math.min(z, b.maxZ));
      if ((x - cx) ** 2 + (z - cz) ** 2 < radius ** 2) return false;
    }
    return true;
  }
  function safePoint(x, z) {
    if (!Number.isFinite(x) || !Number.isFinite(z)) return null;
    if (valid(x, z)) return { x, z };
    const increment = Math.max(.15, radius);
    for (let r = increment; r <= safeSearchRadius; r += increment) {
      const count = Math.max(16, Math.ceil(2 * Math.PI * r / increment));
      for (let i = 0; i < count; i++) {
        const angle = i * 2 * Math.PI / count, nx = x + Math.cos(angle) * r, nz = z + Math.sin(angle) * r;
        if (valid(nx, nz)) return { x: nx, z: nz };
      }
    }
    return null;
  }
  function move(state, dx, dz) {
    if (!state || ![state.x, state.z, dx, dz].every(Number.isFinite)) return false;
    const distance = Math.hypot(dx, dz);
    // Bad frame data must not produce an unbounded substep loop or teleport.
    const stepSize = Math.min(.12, radius * .5), steps = Math.ceil(distance / stepSize);
    if (!Number.isFinite(steps) || steps > 4096) return false;
    const startX = state.x, startZ = state.z;
    function canMove(x, z) {
      if (!valid(x, z)) return false;
      const currentY = groundHeight(state.x, state.z), nextY = groundHeight(x, z);
      return Number.isFinite(currentY) && Math.abs(nextY - currentY) <= maxStep + 1e-6;
    }
    for (let i = 0; i < steps; i++) {
      if (canMove(state.x + dx / steps, state.z)) state.x += dx / steps;
      if (canMove(state.x, state.z + dz / steps)) state.z += dz / steps;
    }
    return state.x !== startX || state.z !== startZ;
  }
  return { valid, safePoint, move, groundHeight, surfaceAt, colliders, radius };
}
