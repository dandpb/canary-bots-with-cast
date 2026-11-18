import {createVoxelKit} from './voxel-kit.js';
import {buildDistrict} from './architecture.js';
import {width, scale, tiles, local, indexOf, read, walkable, closest, strips, palette} from './district.js';

const anchors=[
  ['templo','Templo de Thais','O templo que ancora as coordenadas do mapa.',0,0,Math.PI],
  ['alameda','Alameda norte','O caminho entre duas fileiras de árvores.',0,-17,Math.PI],
  ['depot','Rua do depot','Acesso ao depósito, ao norte do templo.',-4,-26,-Math.PI/2],
  ['jardins','Jardins do templo','A faixa verde junto à rua transversal.',8,6,Math.PI/2],
];
const pad = floor => String(floor).padStart(2,'0');
const name = f => f===7?'Superfície':f<7?'Piso superior':'Subsolo';

export function createPlace(THREE,floor=7){
  const rows=tiles[floor],kit=createVoxelKit(THREE,{name:'Thais'});
  buildDistrict(kit,floor);
  const polygons=[];
  let minX=Infinity,maxX=-Infinity,minZ=Infinity,maxZ=-Infinity;
  strips(rows,(start,end,z,t)=>{
    const x1=local(start)-scale/2,x2=local(end)-scale/2,z1=local(z)-scale/2,z2=z1+scale;
    minX=Math.min(minX,x1);maxX=Math.max(maxX,x2);minZ=Math.min(minZ,z1);maxZ=Math.max(maxZ,z2);
    polygons.push({color:palette[t],points:[[x1,z1],[x2,z1],[x2,z2],[x1,z2]]});
  });
  const pois=[];
  const candidates=floor===7?anchors:[
    ['entrada','Ponto de chegada','Trecho mais próximo do centro do recorte.',0,0,0],
    ['norte','Trecho norte','Piso mapeado no sentido norte.',0,-30,Math.PI],
    ['sul','Trecho sul','Piso mapeado no sentido sul.',0,30,0],
    ['leste','Trecho leste','Piso mapeado no sentido leste.',30,0,Math.PI/2],
  ];
  for(const [id,name,description,dx,dz,yaw] of candidates){
    const pos=closest(rows,width/2+dx,width/2+dz,pois);
    if(!pos)continue;
    let facing=yaw;
    if(floor!==7){
      let best=-1;
      for(const angle of [yaw,0,Math.PI/2,Math.PI,-Math.PI/2]){
        let clear=0;
        for(let n=1;n<=10;n++){
          if(!walkable(read(rows,indexOf(pos.x)-Math.round(Math.sin(angle))*n,indexOf(pos.z)-Math.round(Math.cos(angle))*n)))break;
          clear++;
        }
        if(clear>best){best=clear;facing=angle;}
      }
    }
    pois.push({id,name,description,yaw:facing,...pos});
  }
  // Start on the open avenue, clear of roofs for the final camera descent.
  const spawn={...(floor===7?pois[1]:pois[0])};
  const span=Math.max(14,maxX-minX,maxZ-minZ);
  const cx=(maxX+minX)/2,cz=(maxZ+minZ)/2;
  const overview={position:[cx+span*.72,span*.72,cz+span*.96],target:[cx, floor===7?2:0,cz],minDistance:4,maxDistance:span*3.2};
  const fromRoof=floor===7?35:Math.max(10,span*.38);
  const look=[spawn.x-Math.sin(spawn.yaw)*10,1.72,spawn.z-Math.cos(spawn.yaw)*10];
  const title=floor===7?'Thais':'Thais · '+pad(floor);
  const mapSource='http://127.0.0.1:8080/plugins/worldmap/static/floors/floor-'+pad(floor)+'.png';
  return {...kit.finalize(),title,subtitle:'ATLAS DE TIBIA · '+name(floor).toUpperCase(),floor,metersPerUnit:1,
    bounds:{minX,maxX,minZ,maxZ},groundHeight:()=>0,
    isWalkable:(x,z)=>walkable(read(rows,indexOf(x),indexOf(z))),spawn,pois,poiRadius:9,overview,
    navigation:{radius:.28,eyeHeight:1.72,speed:4.2,runSpeed:7.2},
    tour:{duration:24,keys:[
      {t:0,position:overview.position,target:overview.target},
      {t:9,position:[cx+span*.32,Math.max(fromRoof,span*.39),cz+span*.44],target:[cx,1,cz]},
      {t:16,position:[spawn.x,fromRoof,spawn.z],target:[look[0],3,look[2]]},
      {t:24,position:[spawn.x,1.72,spawn.z],target:look}],
      chapters:[{start:0,kicker:'VISTA GERAL',title:floor===7?'Centro de Thais':name(floor)+' · '+pad(floor)},
        {start:10,kicker:'APROXIMAÇÃO',title:floor===7?'O eixo do templo':'O traçado deste piso'},
        {start:17,kicker:'A PÉ',title:spawn.name}]},
    intro:{kicker:'TIBIA / '+name(floor).toUpperCase()+' '+pad(floor),title:[floor===7?'Thais':name(floor)+' '+pad(floor)],
      description:floor===7?'Do templo ao depot, explore o centro da cidade em três dimensões.':'Explore a parte deste andar registrada sob as mesmas coordenadas de Thais.',
      enterLabel:'Entrar na caminhada',fadeAfter:7},
    appearance:{background:'#d5decd',floorColor:'#bdc7ad',fogColor:'#d7dfcd',fogNear:span*1.5,fogFar:span*4,floorY:-3.65,ambientIntensity:1.65,sunIntensity:2.75,exposure:1.03},
    map:{title:'Mapa de Thais',northKnown:true,polygons,background:'#203832',attribution:'TibiaMaps · minimapa',attributionUrl:'https://tibiamaps.io/'},
    fidelityNote:'Recorte de 80 × 80 casas, centrado no templo (32369, 32241). Cada pixel mantém sua posição nos 16 andares. Alturas, fachadas e telhados são interpretações artísticas. Andares são visitados pelo seletor.',
    sources:[{label:'PNG original deste andar',url:mapSource},{label:'Dados derivados dos 16 andares (JSON)',url:'./data/thais.json'},
      {label:'TibiaMaps · origem dos mapas',url:'https://github.com/tibiamaps/tibia-map-data'},{label:'Licença dos mapas',url:'./data/LICENSE-map.txt'}]};
}
