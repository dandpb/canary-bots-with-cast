import * as THREE from 'three';
import { OrbitControls } from 'three/addons/controls/OrbitControls.js';
import { createPlace } from './place.js';
import { createNavigation } from './navigation.js';
import { SoftwareRenderer } from './software-renderer.js';
import { validatePlace } from './place-validation.js';
import { tiles, palette, width, scale } from './district.js';
import './style.css';
import './atlas.css';

const $=id=>document.getElementById(id), app=$('app'), canvas=$('world');
const reducedMotion=matchMedia('(prefers-reduced-motion: reduce)').matches;
const coarse=matchMedia('(pointer: coarse)').matches;
const state={mode:'tour',tourTime:0,tourPaused:false,paused:false,panel:null,loaded:false,moving:false,quality:'auto',player:{x:0,z:0,yaw:0,pitch:0},keys:new Set(),joystick:{x:0,y:0},distance:0};
let renderer,world,nav,scene,camera,orbit,sun,animationId,elapsed=0,last=0,lastMap=0,lastLocation='',toastTimer,contextLost=false,lookPointer=null,joyPointer=null,software=false;
let pois=[],tourDuration=40,tourKeys=[],chapters=[],appearance={},extent=120;
const look={x:0,y:0};
const lastView = new THREE.Matrix4(), lastProjection = new THREE.Matrix4();
let repaint = true, shadowMode = '';
function toast(message){clearTimeout(toastTimer);$('toast').textContent=message;$('toast').classList.add('show');toastTimer=setTimeout(()=>$('toast').classList.remove('show'),4000);}
function failure(error){console.error(error);$('loader').hidden=true;$('unavailable').hidden=false;app.querySelectorAll('.hud,.tour-title,.cinematic-caption').forEach(e=>e.style.display='none');}
function clearInput(){state.keys.clear();state.joystick.x=state.joystick.y=0;joyPointer=null;lookPointer=null;$('stick').style.transform='';state.moving=false;}
function exitPointer(){if(document.pointerLockElement===canvas)document.exitPointerLock();}
function setPanel(name){
  const next=state.panel===name?null:name;state.panel=next;clearInput();exitPointer();
  $('map-panel').hidden=next!=='map';$('help-panel').hidden=next!=='help';
  $('map-toggle').setAttribute('aria-expanded',String(next==='map'));$('help-toggle').setAttribute('aria-expanded',String(next==='help'));
  if(orbit)orbit.enabled=state.mode==='orbit'&&!next;
  if(next==='map')drawMap();
}
function closePanels(){if(state.panel)setPanel(state.panel);}
function setMode(mode,poi=null){
  if(!state.loaded)return;
  clearInput();closePanels();exitPointer();state.paused=false;$('paused-overlay').hidden=true;
  state.mode=mode;app.dataset.mode=mode;orbit.enabled=mode==='orbit';scene.userData.exploration.mode=mode;
  document.querySelectorAll('button[data-mode]').forEach(b=>b.setAttribute('aria-pressed',String(b.dataset.mode===mode)));
  if(mode==='tour'){
    state.tourTime=0;state.tourPaused=false;$('tour-pause').textContent='II';$('tour-pause').setAttribute('aria-label','Pausar passeio');app.classList.remove('title-faded');fitFov();updateTour(0);
  }else if(mode==='orbit'){
    fitFov();orbit.target.fromArray(world.overview.target);camera.position.fromArray(world.overview.position);orbit.update();toast(app.classList.contains('touch-enabled')?'Arraste para girar. Aproxime com dois dedos.':'Arraste para girar o diorama. Role para aproximar.');
  }else{
    const requested=poi||(state.hasWalked?state.player:world.spawn),p=nav.safePoint(requested.x,requested.z);
    if(!p){setMode('orbit');toast('Escolha outro ponto do mapa para começar.');return;}
    state.player={x:p.x,z:p.z,yaw:requested.yaw??0,pitch:requested.pitch??0};state.hasWalked=true;fitFov();updateWalk(0);canvas.focus({preventScroll:true});
    toast(app.classList.contains('touch-enabled')?'Controle à esquerda para andar; arraste à direita para olhar.':'WASD ou setas para caminhar. Arraste a cena para olhar.');
  }
  updateLocation();updateSun();
}
function setupScene(){
  const floorParam = new URLSearchParams(location.search).get('andar');
  const floor = /^(?:[0-9]|1[0-5])$/.test(floorParam ?? '') ? Number(floorParam) : 7;
  world=createPlace(THREE,floor);
  const contractErrors=validatePlace(world);if(contractErrors.length)throw new Error(contractErrors.join('\n'));
  pois=world.pois||[];appearance=world.appearance||{};
  const b=world.bounds,cx=(b.minX+b.maxX)/2,cz=(b.minZ+b.maxZ)/2;
  extent=Math.max(b.maxX-b.minX,b.maxZ-b.minZ);
  tourKeys=world.tour.keys;tourDuration=world.tour.duration??tourKeys.at(-1).t;chapters=world.tour.chapters?.length?world.tour.chapters:[{start:0,kicker:'O LUGAR',title:world.title}];
  if(tourKeys.length<2)throw new Error('Author at least two tour camera keys.');
  const forced=new URLSearchParams(location.search).get('render')==='software';
  const context=forced?null:canvas.getContext('webgl2',{antialias:true,alpha:false,powerPreference:'high-performance'});
  if(context)renderer=new THREE.WebGLRenderer({canvas,context,antialias:true,alpha:false});
  else{renderer=new SoftwareRenderer(THREE,{canvas});software=true;app.classList.add('software-mode');$('render-note').hidden=false;}
  scene=new THREE.Scene();scene.background=new THREE.Color(appearance.background||'#c7d8cb');scene.fog=new THREE.Fog(appearance.fogColor||'#cbd9c6',appearance.fogNear??extent*1.1,appearance.fogFar??extent*3);
  scene.userData.exploration={mode:'tour'};
  camera=new THREE.PerspectiveCamera(42,1,.08,appearance.far??Math.max(600,extent*6));camera.position.fromArray(world.overview.position);camera.lookAt(...world.overview.target);
  renderer.outputColorSpace=THREE.SRGBColorSpace;renderer.toneMapping=THREE.ACESFilmicToneMapping;renderer.toneMappingExposure=appearance.exposure??1.12;
  renderer.shadowMap.enabled=true;renderer.shadowMap.type=THREE.PCFShadowMap;renderer.setClearColor(appearance.background||'#c7d8cb');
  renderer.shadowMap.autoUpdate=false;
  scene.add(new THREE.HemisphereLight('#fff3da','#6e8a63',appearance.ambientIntensity??2.0));
  sun=new THREE.DirectionalLight('#ffe4b8',appearance.sunIntensity??3.1);sun.castShadow=true;sun.shadow.mapSize.set(2048,2048);sun.shadow.normalBias=.08;sun.shadow.bias=-.0002;sun.shadow.camera.near=.5;sun.shadow.camera.far=extent*4+200;
  scene.add(sun,sun.target);const fill=new THREE.DirectionalLight('#c9e1ec',.65);fill.position.set(cx+extent,extent,cz-extent);scene.add(fill);
  world.group.traverse(o=>{if(o.isMesh)for(const m of Array.isArray(o.material)?o.material:[o.material])if(m.vertexColors&&!o.geometry.getAttribute('color'))throw new Error('Vertex colors require a geometry color attribute.');});
  scene.add(world.group);nav=createNavigation(world,world.navigation||{});
  if(!nav.valid(world.spawn.x,world.spawn.z))throw new Error('Spawn must have clear, walkable footing.');
  const backdrop=new THREE.Mesh(new THREE.PlaneGeometry(extent*15,extent*15),new THREE.MeshStandardMaterial({color:appearance.floorColor||'#bfcbb3',roughness:1}));backdrop.rotation.x=-Math.PI/2;backdrop.position.set(cx,appearance.floorY??-5,cz);backdrop.receiveShadow=true;scene.add(backdrop);
  orbit=new OrbitControls(camera,canvas);orbit.enabled=false;orbit.enableDamping=true;orbit.dampingFactor=.08;orbit.minDistance=world.overview.minDistance??8;orbit.maxDistance=world.overview.maxDistance??extent*3;orbit.maxPolarAngle=Math.PI*.49;orbit.minPolarAngle=.18;orbit.enablePan=true;orbit.screenSpacePanning=false;orbit.target.fromArray(world.overview.target);
  orbit.addEventListener('change',()=>{orbit.target.x=THREE.MathUtils.clamp(orbit.target.x,b.minX,b.maxX);orbit.target.z=THREE.MathUtils.clamp(orbit.target.z,b.minZ,b.maxZ);orbit.target.y=THREE.MathUtils.clamp(orbit.target.y,0,extent*.2);});
  populateCopy();resize();setQuality('auto');buildPlaces();state.loaded=true;state.player={...world.spawn,pitch:world.spawn.pitch??0};updateSun();updateTour(0);renderer.render(scene,camera);
  $('loader').classList.add('done');setTimeout(()=>$('loader').hidden=true,650);
  if(reducedMotion || floorParam!==null){$('camera-bob').checked=!reducedMotion;setMode('orbit');}
  buildFloorAtlas(floor);
  Object.defineProperty(window,'__VOXEL_EXPLORER__',{configurable:true,value:{get state(){return {mode:state.mode,player:{...state.player},tourTime:state.tourTime,paused:state.paused,loaded:state.loaded,renderer:software?'software':'webgl'};},get stats(){return {...world.stats,drawCalls:renderer.info.render.calls,triangles:renderer.info.render.triangles};}}});
  last=performance.now();animationId=requestAnimationFrame(frame);
}
function buildFloorAtlas(current) {
  const dialog=$('floors');
  $('floor-number').textContent=String(current).padStart(2,'0');
  for(let floor=0;floor<tiles.length;floor++){
    const button=document.createElement('button'),thumb=document.createElement('canvas');
    thumb.width=thumb.height=width;
    thumb.setAttribute('aria-hidden','true');
    const ctx=thumb.getContext('2d');
    tiles[floor].forEach((row,z)=>{for(let x=0;x<width;x++){ctx.fillStyle=palette[row[x]];ctx.fillRect(x,z,1,1);}});
    const num=String(floor).padStart(2,'0');
    button.type='button';button.setAttribute('aria-label','Visitar andar '+num);
    if(floor===current){button.setAttribute('aria-current','true');}
    const label=document.createElement('span');label.textContent=num;
    button.append(thumb,label);button.addEventListener('click',()=>{
      if(floor===current){dialog.close();return;}
      const url=new URL(location.href);url.searchParams.set('andar',String(floor));location.assign(url);
    });
    $('floor-grid').append(button);
  }
  $('floor-toggle').addEventListener('click',()=>{
    closePanels();clearInput();exitPointer();dialog.showModal();state.panel='floors';
    orbit.enabled=false;
  });
  dialog.addEventListener('close',()=>{state.panel=null;clearInput();orbit.enabled=state.mode==='orbit';});
}
function populateCopy(){
  document.title=world.title+' · Lugares em Voxel';$('place-brand').textContent=world.title;$('place-subtitle').textContent=world.subtitle||'UM LUGAR EM VOXELS';
  $('intro-kicker').textContent=world.intro?.kicker||'UM NOVO PONTO DE VISTA';$('intro-title').replaceChildren();
  const lines=world.intro?.title||[world.title,'Um lugar para explorar.'];(Array.isArray(lines)?lines:[lines]).forEach((line,i)=>{if(i)$('intro-title').append(document.createElement('br'));$('intro-title').append(document.createTextNode(line));});
  $('intro-description').textContent=world.intro?.description||'Assista ao passeio e depois descubra cada caminho no seu ritmo.';$('enter-label').textContent=world.intro?.enterLabel||'Começar a caminhada';
  $('map-title').textContent=world.map?.title||'Explore '+world.title;$('fidelity-note').textContent=world.fidelityNote||'Reconstrução artística baseada em referências.';
  canvas.setAttribute('aria-label',world.title+' em três dimensões');$('minimap').setAttribute('aria-label','Mapa de '+world.title+' com sua posição');
  for(const source of world.sources||[]){if(!/^(https?:\/\/|\.\/data\/)/.test(source.url))continue;const a=document.createElement('a');a.href=source.url;a.target='_blank';a.rel='noopener noreferrer';a.textContent=source.label;$('source-links').append(a);}
  if(world.map?.attribution){const el=$('map-attribution');el.style.display='block';el.textContent=world.map.attribution;if(world.map.attributionUrl){const a=document.createElement('a');a.href=world.map.attributionUrl;a.target='_blank';a.rel='noopener noreferrer';a.textContent=world.map.attribution;el.replaceChildren(a);}}
  $('map-north').hidden=world.map?.northKnown===false;
}
function setQuality(q){state.quality=q;const low=q==='low'||(q==='auto'&&(coarse||innerWidth<700));renderer.setQuality?.(q);renderer.setPixelRatio(software?1:Math.min(devicePixelRatio,low?1.2:1.8));sun.shadow.mapSize.set(low?1024:2048,low?1024:2048);if(sun.shadow.map){sun.shadow.map.dispose();sun.shadow.map=null;}renderer.shadowMap.needsUpdate=true;resize();}
function resize(){if(!renderer)return;renderer.setSize(app.clientWidth,app.clientHeight,false);camera.aspect=app.clientWidth/app.clientHeight;fitFov();repaint=true;}
function fitFov(){const base=state.mode==='walk'?70:42;camera.fov=state.mode==='walk'?base:THREE.MathUtils.radToDeg(2*Math.atan(Math.tan(THREE.MathUtils.degToRad(base/2))*Math.max(1,1.25/camera.aspect)));camera.updateProjectionMatrix();}
function updateSun(){
  if(!sun||!world)return;
  const walk=state.mode==='walk',target=walk?[state.player.x,0,state.player.z]:world.overview.target,offset=appearance.sunOffset||[-extent*.7,extent*1.1,extent*.6];
  const mode=walk?'walk':'overview';
  if(shadowMode===mode && Math.hypot(sun.target.position.x-target[0],sun.target.position.z-target[2])<8)return;
  shadowMode=mode;renderer.shadowMap.needsUpdate=true;repaint=true;
  sun.target.position.fromArray(target);sun.position.copy(sun.target.position).add(new THREE.Vector3(...offset));
  const span=walk?(appearance.walkingShadowExtent??36):(appearance.overviewShadowExtent??extent*.7);Object.assign(sun.shadow.camera,{left:-span,right:span,top:span,bottom:-span});sun.shadow.camera.updateProjectionMatrix();
}
function updateTour(dt){
  if(!state.tourPaused&&!state.panel)state.tourTime=Math.min(tourDuration,state.tourTime+dt);
  const t=state.tourTime;let k=0;while(k<tourKeys.length-2&&t>tourKeys[k+1].t)k++;
  const a=tourKeys[k],b=tourKeys[k+1];let u=THREE.MathUtils.clamp((t-a.t)/(b.t-a.t),0,1);u=u*u*(3-2*u);
  camera.position.fromArray(a.position).lerp(new THREE.Vector3(...b.position),u);camera.lookAt(new THREE.Vector3(...a.target).lerp(new THREE.Vector3(...b.target),u));
  let ci=0;for(let i=0;i<chapters.length;i++)if(t>=chapters[i].start)ci=i;const chapter=chapters[ci];
  $('chapter-number').textContent=String(ci+1).padStart(2,'0')+' / '+String(chapters.length).padStart(2,'0');$('chapter-kicker').textContent=chapter.kicker;$('chapter-title').textContent=chapter.title;
  $('progress-fill').style.width=(t/tourDuration*100)+'%';$('tour-time').textContent=String(Math.floor(t/60)).padStart(2,'0')+':'+String(Math.floor(t%60)).padStart(2,'0');app.classList.toggle('title-faded',t>(world.intro?.fadeAfter??8));
  if(t>=tourDuration)setMode('walk',world.spawn);
}
function updateWalk(dt){
  const p=state.player;let mx=0,mz=0;
  if(!state.paused&&!state.panel){mx=(state.keys.has('KeyD')||state.keys.has('ArrowRight')?1:0)-(state.keys.has('KeyA')||state.keys.has('ArrowLeft')?1:0)+state.joystick.x;mz=(state.keys.has('KeyW')||state.keys.has('ArrowUp')?1:0)-(state.keys.has('KeyS')||state.keys.has('ArrowDown')?1:0)-state.joystick.y;}
  const len=Math.hypot(mx,mz);if(len>1){mx/=len;mz/=len;}
  const n=world.navigation||{},speed=(state.keys.has('ShiftLeft')||state.keys.has('ShiftRight')?(n.runSpeed??6.5):(n.speed??3.6))*dt;
  const dx=(Math.cos(p.yaw)*mx-Math.sin(p.yaw)*mz)*speed,dz=(-Math.sin(p.yaw)*mx-Math.cos(p.yaw)*mz)*speed;
  const ox=p.x,oz=p.z;nav.move(p,dx,dz);const distance=Math.hypot(p.x-ox,p.z-oz);state.distance+=distance;state.moving=distance>.0001;
  const bob=$('camera-bob').checked&&!reducedMotion&&state.moving?Math.sin(state.distance*6)*.028:0;
  camera.position.set(p.x,nav.groundHeight(p.x,p.z)+(n.eyeHeight??1.72)+bob,p.z);camera.rotation.order='YXZ';camera.rotation.set(p.pitch,p.yaw,0);updateSun();
}
function updateLocation(){
  if(!state.loaded)return;const p=state.mode==='walk'?state.player:camera.position;let nearest=null,distance=Infinity;
  for(const poi of pois){const d=Math.hypot(p.x-poi.x,p.z-poi.z);if(d<distance){distance=d;nearest=poi;}}
  const name=state.mode==='orbit'?world.title+' · diorama':nearest&&distance<(world.poiRadius??24)?nearest.name:world.title;
  if(name!==lastLocation){$('location-name').textContent=name;lastLocation=name;}
  if(state.mode==='walk')$('world-coords').textContent='X '+(32369+Math.round(p.x/scale))+'   Y '+(32241+Math.round(p.z/scale));
}
function frame(now){
  if(contextLost)return;const frameSeconds=Math.max(0,(now-last)/1000),dt=Math.min(frameSeconds,.1);last=now;
  if(!document.hidden&&!state.paused){
    elapsed+=dt;
    world.update?.(elapsed,dt);
    if(state.mode==='tour')updateTour(frameSeconds);
    else if(state.mode==='orbit'&&orbit.enabled)orbit.update();
    else if(state.mode==='walk')updateWalk(dt);
    camera.updateMatrixWorld();
    if(repaint || world.update || !lastView.equals(camera.matrixWorld) || !lastProjection.equals(camera.projectionMatrix)){
      renderer.render(scene,camera);
      lastView.copy(camera.matrixWorld);lastProjection.copy(camera.projectionMatrix);repaint=false;
    }
    if(now-lastMap>180){updateLocation();if(state.panel==='map')drawMap();lastMap=now;}
  }
  animationId=requestAnimationFrame(frame);
}
function drawMap(){
  const c=$('minimap').getContext('2d'),w=480,h=416,b=world.bounds,pad=22,s=Math.min((w-pad*2)/(b.maxX-b.minX),(h-pad*2)/(b.maxZ-b.minZ));
  const ox=(w-(b.maxX-b.minX)*s)/2,oz=(h-(b.maxZ-b.minZ)*s)/2,point=(x,z)=>[ox+(x-b.minX)*s,oz+(z-b.minZ)*s];
  c.fillStyle=world.map?.background||'#183d37';c.fillRect(0,0,w,h);
  for(const shape of world.map?.polygons||[]){c.beginPath();shape.points.forEach(([x,z],i)=>{const q=point(x,z);i?c.lineTo(...q):c.moveTo(...q);});c.closePath();c.fillStyle=shape.color||'#6d9252';c.fill();}
  for(const path of world.map?.paths||[]){c.beginPath();path.points.forEach(([x,z],i)=>{const q=point(x,z);i?c.lineTo(...q):c.moveTo(...q);});c.strokeStyle=path.color||'#c2b99b';c.lineWidth=Math.max(1,(path.width||2)*s);c.lineJoin='round';c.lineCap='round';c.stroke();}
  for(const p of world.map?.points||[]){const q=point(p.x,p.z);c.beginPath();c.arc(q[0],q[1],Math.max(1.5,(p.radius||1)*s),0,Math.PI*2);c.fillStyle=p.color||'#315e36';c.fill();}
  for(const poi of pois){const q=point(poi.x,poi.z);c.beginPath();c.arc(q[0],q[1],5,0,Math.PI*2);c.fillStyle='#f3d394';c.strokeStyle='#173b35';c.lineWidth=2.5;c.fill();c.stroke();}
  if(state.mode==='walk'){const p=state.player,q=point(p.x,p.z);c.save();c.translate(...q);c.rotate(-p.yaw);c.beginPath();c.moveTo(0,-11);c.lineTo(7,8);c.lineTo(0,5);c.lineTo(-7,8);c.closePath();c.fillStyle='#fff9de';c.strokeStyle='#14362e';c.lineWidth=2.5;c.fill();c.stroke();c.restore();}
}
function buildPlaces(){
  for(const poi of pois){const b=document.createElement('button');b.className='place';b.dataset.place=poi.id;const span=document.createElement('span'),strong=document.createElement('strong'),small=document.createElement('small'),arrow=document.createElement('span');strong.textContent=poi.name;small.textContent=poi.description;arrow.className='arrow-icon';span.append(strong,small);b.append(span,arrow);b.addEventListener('click',()=>{setMode('walk',poi);toast(poi.name+' · sua caminhada começa aqui.');});$('places').append(b);}
}

function bindInput(){
  $('enter').addEventListener('click',()=>setMode('walk'));
  document.querySelectorAll('button[data-mode]').forEach(b=>b.addEventListener('click',()=>setMode(b.dataset.mode)));
  $('map-toggle').addEventListener('click',()=>setPanel('map'));$('help-toggle').addEventListener('click',()=>setPanel('help'));
  document.querySelectorAll('[data-close]').forEach(b=>b.addEventListener('click',()=>closePanels()));
  $('return-start').addEventListener('click',()=>setMode('walk',world.spawn));
  $('tour-pause').addEventListener('click',()=>{state.tourPaused=!state.tourPaused;$('tour-pause').textContent=state.tourPaused?'▷':'II';$('tour-pause').setAttribute('aria-label',state.tourPaused?'Continuar passeio':'Pausar passeio');});
  $('quality').addEventListener('change',e=>setQuality(e.target.value));
  $('touch-mode').checked=coarse;app.classList.toggle('touch-enabled',coarse);
  $('touch-mode').addEventListener('change',e=>{app.classList.toggle('touch-enabled',e.target.checked);clearInput();});
  $('retry').addEventListener('click',()=>location.reload());
  $('retry-software').addEventListener('click',()=>{const url=new URL(location.href);url.searchParams.set('render','software');location.href=url.href;});
  $('fullscreen').addEventListener('click',async()=>{try{if(document.fullscreenElement)await document.exitFullscreen();else if(app.requestFullscreen)await app.requestFullscreen();else toast('Use a opção Tela cheia do seu navegador.');}catch{toast('A tela cheia não está disponível neste navegador.');}});
  $('lock-mouse').addEventListener('click',async()=>{if(state.mode!=='walk')return;try{if(canvas.requestPointerLock)await canvas.requestPointerLock();else toast('Arraste a cena para olhar ao redor.');}catch{toast('Arraste a cena para olhar ao redor.');}});
  document.addEventListener('pointerlockchange',()=>{$('lock-mouse').textContent=document.pointerLockElement===canvas?'Esc para liberar o mouse':'Ativar mouse livre';clearInput();});
  document.addEventListener('pointerlockerror',()=>toast('Você pode arrastar a cena para olhar ao redor.'));
  const relevant=new Set(['KeyW','KeyA','KeyS','KeyD','ArrowUp','ArrowDown','ArrowLeft','ArrowRight','ShiftLeft','ShiftRight']);
  window.addEventListener('keydown',e=>{
    if($('floors').open)return;
    if(['INPUT','SELECT','TEXTAREA'].includes(e.target.tagName))return;
    if(e.code==='Escape'){closePanels();clearInput();exitPointer();return;}
    if(e.code==='KeyM'&&!e.repeat){e.preventDefault();setPanel('map');return;}
    if(relevant.has(e.code)&&state.mode==='walk'&&!state.panel&&!state.paused){e.preventDefault();state.keys.add(e.code);}
  });
  window.addEventListener('keyup',e=>state.keys.delete(e.code));
  canvas.addEventListener('pointerdown',e=>{
    if(state.mode!=='walk'||state.panel||state.paused)return;if(e.button!==0)return;
    lookPointer=e.pointerId;look.x=e.clientX;look.y=e.clientY;canvas.setPointerCapture(e.pointerId);canvas.focus({preventScroll:true});
  });
  window.addEventListener('pointermove',e=>{
    if(state.mode!=='walk'||state.panel||state.paused)return;
    const locked=document.pointerLockElement===canvas;
    if(!locked&&lookPointer!==e.pointerId)return;
    const dx=locked?e.movementX:e.clientX-look.x,dy=locked?e.movementY:e.clientY-look.y;
    if(Math.abs(dx)>500||Math.abs(dy)>500)return;
    state.player.yaw-=dx*.003;state.player.pitch=THREE.MathUtils.clamp(state.player.pitch-dy*.003,-1.2,1.2);look.x=e.clientX;look.y=e.clientY;
  });
  const releaseLook=e=>{if(lookPointer===e.pointerId)lookPointer=null;};window.addEventListener('pointerup',releaseLook);window.addEventListener('pointercancel',releaseLook);
  canvas.addEventListener('contextmenu',e=>e.preventDefault());
  $('joystick').addEventListener('pointerdown',e=>{if(state.mode!=='walk'||state.panel)return;e.preventDefault();e.stopPropagation();joyPointer=e.pointerId;$('joystick').setPointerCapture(e.pointerId);updateStick(e);});
  $('joystick').addEventListener('pointermove',e=>{if(e.pointerId===joyPointer){e.preventDefault();updateStick(e);}});
  const endStick=e=>{if(e.pointerId!==joyPointer)return;joyPointer=null;state.joystick.x=state.joystick.y=0;$('stick').style.transform='';};
  $('joystick').addEventListener('pointerup',endStick);$('joystick').addEventListener('pointercancel',endStick);$('joystick').addEventListener('lostpointercapture',endStick);
  window.addEventListener('resize',resize);
  document.addEventListener('visibilitychange',()=>{clearInput();last=performance.now();});
  window.addEventListener('blur',()=>{clearInput();if(state.mode==='walk'&&state.loaded){state.paused=true;$('paused-overlay').hidden=false;exitPointer();}});
  $('resume').addEventListener('click',()=>{state.paused=false;$('paused-overlay').hidden=true;canvas.focus({preventScroll:true});last=performance.now();});
  canvas.addEventListener('webglcontextlost',e=>{e.preventDefault();contextLost=true;cancelAnimationFrame(animationId);clearInput();$('graphics-recovery').hidden=false;});
  canvas.addEventListener('webglcontextrestored',()=>location.reload());
  $('recover-graphics').addEventListener('click',()=>{const url=new URL(location.href);url.searchParams.set('render','software');location.href=url.href;});
}
function updateStick(e){const r=$('joystick').getBoundingClientRect();let x=e.clientX-r.left-r.width/2,y=e.clientY-r.top-r.height/2;const limit=r.width*.32,len=Math.hypot(x,y);if(len>limit){x*=limit/len;y*=limit/len;}state.joystick.x=x/limit;state.joystick.y=y/limit;$('stick').style.transform=`translate(${x}px,${y}px)`;}
bindInput();requestAnimationFrame(()=>{try{setupScene();}catch(e){failure(e);}});
