import survey from './thais.json' with {type:'json'};

export const tiles = survey.floors.map(f => f.rows);
export const width = survey.width;
export const scale = 1.7;
export const local = index => (index - width / 2) * scale;
export const indexOf = n => Math.floor(n / scale + width / 2 + .5);
export const read = (rows, x, z) => rows?.[z]?.[x] || ' ';
export const walkable = t => '.pgm+swi'.includes(t);
export const palette = {
  ' ': '#1c3534', '.':'#b6ad97', '#':'#a8684c', 'g':'#83a75d', 'T':'#396849',
  'm':'#b5c67b','p':'#ac855f','r':'#956d53','~':'#478e94','+':'#efbf5e',
  'b':'#828a87','s':'#d7bf8f','l':'#e18243','w':'#dedfd0','i':'#b3d8d5',
};
export function random(x,z,k=0) {
  let h=Math.imul(x+731,73856093)^Math.imul(z+917,19349663)^Math.imul(k+11,83492791);
  h=Math.imul(h^(h>>>16),0x45d9f3b); return ((h^(h>>>16))>>>0)/4294967296;
}
export function strips(rows, visit){
  rows.forEach((row,z)=>{
    for(let x=0;x<width;){
      const t=row[x]; let end=x+1;
      while(end<width && row[end]===t) end++;
      if(t!==' ') visit(x,end,z,t);
      x=end;
    }
  });
}
export function closest(rows, x, z, used=[]) {
  let best=null, distance=Infinity;
  rows.forEach((row,j)=>{for(let i=0;i<width;i++){
    if(!walkable(row[i]) || used.some(p=>Math.hypot(local(i)-p.x,local(j)-p.z)<scale*2)) continue;
    if(![[1,0],[-1,0],[0,1],[0,-1]].some(([dx,dz])=>walkable(read(rows,i+dx,j+dz)))) continue;
    const d=(i-x)**2+(j-z)**2;
    if(d<distance){distance=d;best={x:local(i),z:local(j)};}
  }});
  return best;
}
export function roofShapes(rows) {
  const groups = new Int32Array(width*width).fill(-1);
  const depth = new Uint8Array(width*width).fill(99);
  const directions=[[1,0],[-1,0],[0,1],[0,-1]];
  for(let z=0;z<width;z++)for(let x=0;x<width;x++){
    const id=z*width+x;
    if(rows[z][x]===' '||groups[id]>=0)continue;
    const component=[id], border=[];
    groups[id]=id;
    for(let n=0;n<component.length;n++){
      const k=component[n],cx=k%width,cz=Math.floor(k/width);
      for(const [dx,dz] of directions){
        const nx=cx+dx,nz=cz+dz,j=nz*width+nx;
        if(read(rows,nx,nz)===' '){if(depth[k]!==0){depth[k]=0;border.push(k);}continue;}
        if(groups[j]===-1){groups[j]=id;component.push(j);}
      }
    }
    for(let n=0;n<border.length;n++){
      const k=border[n],cx=k%width,cz=Math.floor(k/width);
      for(const [dx,dz] of directions){
        const nx=cx+dx,nz=cz+dz,j=nz*width+nx;
        if(nx<0||nx>=width||nz<0||nz>=width||groups[j]!==id||depth[j]<=depth[k]+1)continue;
        depth[j]=depth[k]+1;border.push(j);
      }
    }
  }
  return {groups,depth};
}
