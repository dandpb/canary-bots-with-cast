// Keep authoring errors out of both the browser runtime and offline checks.
export function validatePlace(place) {
  const errors = [], fail = message => errors.push(message);
  const finite = Number.isFinite;
  const vector = (value, size) => Array.isArray(value) && value.length === size && Array.from(value).every(finite);
  const nonempty = value => typeof value === 'string' && value.trim().length > 0;
  if (!place || typeof place !== 'object') return ['Place must be an object.'];
  if (!nonempty(place.title)) fail('Place title must be a nonempty string.');
  if (!place.group?.isObject3D) fail('Place group must be a Three Object3D.');
  const bounds = place.bounds;
  if (!bounds || !['minX', 'maxX', 'minZ', 'maxZ'].every(k => finite(bounds[k])) || bounds.minX >= bounds.maxX || bounds.minZ >= bounds.maxZ) fail('Bounds must be finite and ordered.');
  for (const name of ['isWalkable', 'groundHeight']) if (typeof place[name] !== 'function') fail(name + ' must be a function.');
  if (place.metersPerUnit !== undefined && (!finite(place.metersPerUnit) || place.metersPerUnit <= 0)) fail('metersPerUnit must be positive.');
  const start = (point, label) => {
    if (!point || !finite(point.x) || !finite(point.z) || !finite(point.yaw)) fail(label + ' needs finite x, z and yaw.');
    if (point?.pitch !== undefined && !finite(point.pitch)) fail(label + ' pitch must be finite.');
  };
  start(place.spawn, 'Spawn');
  if (place.pois !== undefined && !Array.isArray(place.pois)) fail('POIs must be an array.');
  else {
    const ids = new Set();
    for (const [i, poi] of (place.pois || []).entries()) {
      start(poi, 'POI ' + i);
      if (!nonempty(poi?.id) || ids.has(poi.id)) fail('POI ' + i + ' needs a unique nonempty id.');
      if (!nonempty(poi?.name)) fail('POI ' + i + ' needs a name.');
      ids.add(poi?.id);
    }
  }
  const overview = place.overview;
  if (!overview || !vector(overview.position, 3) || !vector(overview.target, 3)) fail('Overview position and target must each contain exactly three finite numbers.');
  for (const key of ['minDistance', 'maxDistance']) if (overview?.[key] !== undefined && (!finite(overview[key]) || overview[key] <= 0)) fail('Overview ' + key + ' must be positive.');
  if (overview?.minDistance !== undefined && overview?.maxDistance !== undefined && overview.minDistance >= overview.maxDistance) fail('Overview zoom limits must be ordered.');
  const tour = place.tour, keys = tour?.keys, duration = tour?.duration ?? (Array.isArray(keys) ? keys.at(-1)?.t : undefined);
  if (!finite(duration) || duration <= 0) fail('Tour duration must be positive and finite.');
  if (!Array.isArray(keys) || keys.length < 2) fail('Tour needs at least two camera keys.');
  else {
    for (let i = 0; i < keys.length; i++) {
      const key = keys[i];
      if (!finite(key?.t) || (i > 0 && key.t <= keys[i - 1]?.t)) fail('Tour key times must be finite and strictly increasing: ' + i);
      if (!vector(key?.position, 3) || !vector(key?.target, 3)) fail('Tour key ' + i + ' position and target must each contain exactly three finite numbers.');
    }
    if (keys[0]?.t !== 0 || keys.at(-1)?.t !== duration) fail('Tour must run from t=0 through its duration.');
  }
  if (tour?.chapters !== undefined) {
    if (!Array.isArray(tour.chapters)) fail('Tour chapters must be an array.');
    else for (const [i, chapter] of tour.chapters.entries()) {
      if (!finite(chapter?.start) || chapter.start < 0 || chapter.start >= duration || (i === 0 && chapter.start !== 0) || (i > 0 && chapter.start <= tour.chapters[i - 1]?.start)) fail('Invalid chapter start: ' + i);
      if (!nonempty(chapter?.kicker) || !nonempty(chapter?.title)) fail('Chapter ' + i + ' needs kicker and title.');
    }
  }
  for (const key of ['radius', 'speed', 'runSpeed', 'eyeHeight', 'safeSearchRadius']) if (place.navigation?.[key] !== undefined && (!finite(place.navigation[key]) || place.navigation[key] <= 0)) fail('Navigation ' + key + ' must be positive.');
  if (place.navigation?.maxStep !== undefined && (!finite(place.navigation.maxStep) || place.navigation.maxStep < 0)) fail('Navigation maxStep must be nonnegative.');
  for (const name of ['colliders', 'walkSurfaces']) {
    if (place[name] !== undefined && !Array.isArray(place[name])) fail(name + ' must be an array.');
    else for (const [i, box] of (place[name] || []).entries()) if (!box || !['minX', 'maxX', 'minZ', 'maxZ'].every(k => finite(box[k])) || box.minX >= box.maxX || box.minZ >= box.maxZ || (name === 'walkSurfaces' && !finite(box.y))) fail('Invalid ' + name + ' entry: ' + i);
  }
  if (!place.map || typeof place.map !== 'object') fail('Place needs a map object.');
  else {
    for (const [name, minimum] of [['polygons', 3], ['paths', 2]]) {
      const shapes = place.map[name];
      if (shapes !== undefined && !Array.isArray(shapes)) fail('Map ' + name + ' must be an array.');
      else for (const [i, shape] of (shapes || []).entries()) if (!Array.isArray(shape?.points) || shape.points.length < minimum || !shape.points.every(p => vector(p, 2))) fail('Invalid map ' + name + ' entry: ' + i);
    }
    if (place.map.points !== undefined && !Array.isArray(place.map.points)) fail('Map points must be an array.');
    else for (const [i, point] of (place.map.points || []).entries()) if (!finite(point?.x) || !finite(point?.z)) fail('Invalid map point: ' + i);
  }
  return errors;
}
