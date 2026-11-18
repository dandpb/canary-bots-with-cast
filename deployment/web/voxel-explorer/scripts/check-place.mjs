import * as THREE from 'three';
import {createPlace} from '../src/place.js';
import {createNavigation} from '../src/navigation.js';
import {validatePlace} from '../src/place-validation.js';
for(let floor=0;floor<16;floor++){
const place=createPlace(THREE,floor), failures=validatePlace(place), warnings=[];
if(failures.length){console.log(JSON.stringify({place:place?.title,failures,warnings},null,2));process.exit(1);}
const fail=m=>failures.push(m);
const nav=createNavigation(place,place.navigation||{});
let batches=0,instances=0;const solids=[];
const matrix=new THREE.Matrix4(), instance=new THREE.Matrix4();
place.update?.(0,0);place.group.updateMatrixWorld(true);
place.group.traverse(mesh=>{
  if(!mesh.isMesh)return;
  for(const material of Array.isArray(mesh.material)?mesh.material:[mesh.material]){
    if(material.vertexColors&&!mesh.geometry.getAttribute('color'))fail('Material requires missing vertex colors: '+mesh.name);
    if(material.color&&![material.color.r,material.color.g,material.color.b].every(Number.isFinite))fail('Nonfinite material color: '+mesh.name);
  }
  const count=mesh.isInstancedMesh?mesh.count:1;
  if(mesh.isInstancedMesh){batches++;instances+=count;const c=mesh.instanceColor;if(!c||c.count<count||!c.array.every(v=>Number.isFinite(v)&&v>=0))fail('Invalid instance color buffer: '+mesh.name);}
  for(let i=0;i<count;i++){
    if(mesh.isInstancedMesh){mesh.getMatrixAt(i,instance);matrix.multiplyMatrices(mesh.matrixWorld,instance);}else matrix.copy(mesh.matrixWorld);
    const e=matrix.elements;if(!e.every(Number.isFinite)||matrix.determinant()<=0){fail('Invalid transform: '+mesh.name);continue;}
    if(mesh.geometry.type!=='BoxGeometry'||mesh.userData.voxelRole==='water')continue;
    const {width=1,height=1,depth=1}=mesh.geometry.parameters;
    const ax=(Math.abs(e[0])*width+Math.abs(e[4])*height+Math.abs(e[8])*depth)/2;
    const ay=(Math.abs(e[1])*width+Math.abs(e[5])*height+Math.abs(e[9])*depth)/2;
    const az=(Math.abs(e[2])*width+Math.abs(e[6])*height+Math.abs(e[10])*depth)/2;
    solids.push({x:e[12],y:e[13],z:e[14],ax,ay,az,w:width/2,h:height/2,d:depth/2,inv:matrix.clone().invert(),name:mesh.name});
  }
});
for(const p of [{id:'spawn',...place.spawn},...(place.pois||[])])if(!nav.valid(p.x,p.z))fail('Unsafe starting point: '+p.id+' ('+p.x+', '+p.z+')');
const keys=place.tour?.keys||[],duration=place.tour?.duration??keys.at(-1)?.t;
if(keys.length<2||keys[0]?.t!==0||keys.at(-1)?.t!==duration)fail('Tour must run from t=0 through its duration.');
for(let i=0;i<keys.length;i++)if(![keys[i].t,...keys[i].position,...keys[i].target].every(Number.isFinite)||(i&&keys[i].t<=keys[i-1].t))fail('Invalid tour key '+i);
const p=new THREE.Vector3(),local=new THREE.Vector3();let cameraSamples=0;
const sampleCount=Math.min(3000,Math.ceil(duration/.2));
for(let sample=0;sample<=sampleCount;sample++){
  const t=sample/sampleCount*duration;
  let k=0;while(k<keys.length-2&&t>keys[k+1].t)k++;
  const a=keys[k],b=keys[k+1];let u=Math.max(0,Math.min(1,(t-a.t)/(b.t-a.t)));u=u*u*(3-2*u);
  p.fromArray(a.position).lerp(new THREE.Vector3(...b.position),u);cameraSamples++;
  for(const box of solids){if(Math.abs(p.x-box.x)>box.ax+.06||Math.abs(p.y-box.y)>box.ay+.06||Math.abs(p.z-box.z)>box.az+.06)continue;
    local.copy(p).applyMatrix4(box.inv);if(Math.abs(local.x)<box.w&&Math.abs(local.y)<box.h&&Math.abs(local.z)<box.d){fail('Tour camera enters geometry at '+t.toFixed(1)+'s: '+box.name);break;}}
}
const end=keys.at(-1)?.position,eye=place.navigation?.eyeHeight??1.72;
if(end&&Math.hypot(end[0]-place.spawn.x,end[2]-place.spawn.z)>.2)warnings.push('Tour ends away from spawn; transition will teleport.');
if(end&&Math.abs(end[1]-(nav.groundHeight(place.spawn.x,place.spawn.z)+eye))>.3)warnings.push('Tour final camera height differs from walking height.');
console.log(JSON.stringify({place:place.title,batches,instances,points:(place.pois||[]).length,cameraSamples,failures:[...new Set(failures)],warnings},null,2));
if(failures.length)process.exitCode=1;
}
