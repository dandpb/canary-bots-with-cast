import {local, palette, random, read, roofShapes, scale, strips, tiles, width} from './district.js';

const storey=3.4;
const masonry=['#dfc392','#dfbf89','#ebcf9e','#d0af80'];
const paving=['#c5bea9','#bcb69f','#cfc7b2','#b5ae97'];
const roofs=[['#a85735','#bb6742','#b35d3c'],['#814b3c','#a35c48','#93513e'],['#52827a','#5d8b80','#4a776f'],['#a9653d','#c58050','#b97448']];
const trim='#735942', stone='#9b907b';
const pick=(items,n)=>items[Math.min(items.length-1,Math.floor(n*items.length))];

function wall(kit,rows,x,z,h,roofAbove){
  const X=local(x),Z=local(z);
  const same=(a,b)=>read(rows,a,b)==='#';
  const east=same(x+1,z)||same(x-1,z), south=same(x,z+1)||same(x,z-1);
  const w=east?scale:scale*.64,d=south?scale:scale*.64, height=roofAbove?storey:storey*.88;
  const tint=pick(masonry,random(Math.floor(x/5),Math.floor(z/5)));
  kit.box(X,h+height/2,Z,w,height,d,tint);
  kit.box(X,h+.23,Z,w+.08,.45,d+.08,stone);
  kit.box(X,h+height-.13,Z,w+.12,.26,d+.12,trim);
  if(east===south)return;
  const face=(a,y,width_,height_,out,color,role='detail')=>{
    kit.box(X+(south?out:a),h+y,Z+(south?a:out),south?.10:width_,height_,south?width_:.10,color,{role});
  };
  const along=east?x:z,thick=(east?d:w)/2;
  if(along%4===0){
    for(const sign of [-1,1])face(0,height/2,.18,height-.32,sign*(thick+.035),trim);
  }else if(along%3===0){
    for(const sign of [-1,1]){
      face(0,1.65,.72,1.1,sign*(thick+.055),'#614e3b');
      face(0,1.65,.48,.83,sign*(thick+.102),random(x,z)>.79?'#efb96d':'#476562');
      face(0,1.03,.86,.12,sign*(thick+.13),stone);
    }
  }
}
function ground(kit,rows,floor){
  strips(rows,(start,end,z,t)=>{
    // Merge slabs of the same material, retaining paths one tile wide.
    for(let x=start;x<end;){
      const next=Math.min(end,x+3+Math.floor(random(x,z)*4)),len=next-x;
      const X=(local(x)+local(next-1))/2,Z=local(z);
      const water=t==='~', material=t==='#'?paving[1]:t==='.'?pick(paving,random(x,z)):palette[t];
      kit.box(X,water?-.25:-.14,Z,len*scale,.28,scale,material,{role:water?'water':'terrain'});
      if(floor!==7) kit.box(X,-.62,Z,len*scale,.74,scale,'#897a65',{role:'terrain'});
      x=next;
    }
  });
  if(floor===7){
    const center=-scale/2, span=width*scale;
    kit.box(center,-1.05,center,span,1.62,span,'#8b785c',{role:'terrain'});
    kit.box(center,-2.07,center,span+.28,.44,span+.28,'#675c4a',{role:'terrain'});
    kit.box(center,-2.52,center,span+.52,.48,span+.52,'#aa9471',{role:'terrain'});
  }
}
function roofing(kit,rows,above,roof,h,layer){
  for(let z=0;z<width;z++){
    for(let x=0;x<width;){
      if(rows[z][x]===' '||read(above,x,z)!==' '){x++;continue;}
      const k=z*width+x,group=roof.groups[k],depth=Math.min(roof.depth[k],8);
      let end=x+1;
      while(end<width && end-x<5 && rows[z][end]!==' ' && read(above,end,z)===' ' &&
        roof.groups[z*width+end]===group && Math.min(roof.depth[z*width+end],8)===depth)end++;
      const colors=roofs[Math.floor(random(group,0,layer)*roofs.length)];
      const tint=pick(colors,random(Math.floor(x/4),z,group));
      const height=.37+depth*.84;
      kit.box((local(x)+local(end-1))/2,h+height/2,local(z),(end-x)*scale,height,scale,tint);
      x=end;
    }
  }
}
export function buildDistrict(kit,floor){
  const rows=tiles[floor];ground(kit,rows,floor);
  for(let layer=floor;layer>=(floor===7?0:floor);layer--){
    const story=tiles[layer],above=tiles[layer-1],h=(floor-layer)*storey;
    const facades=floor===7 && layer<7;
    const roof=facades?roofShapes(story):null;
    if(facades){
      strips(story,(start,end,z)=>kit.box((local(start)+local(end-1))/2,h-.12,local(z),(end-start)*scale,.24,scale,'#937c62',{role:'paving'}));
      roofing(kit,story,above,roof,h,layer);
    }
    for(let z=0;z<width;z++)for(let x=0;x<width;x++){
      const t=story[z][x];if(t===' ')continue;
      const X=local(x),Z=local(z),aboveTile=read(above,x,z),upper=aboveTile!==' ';
      const r=random(x,z);
      if(t==='#' && (!facades||upper))wall(kit,story,x,z,h,upper);
      if(layer!==floor)continue;
      if(t==='T' && r>.21){
        kit.tree(X,Z,{height:3.9+r*2.4,crownWidth:2.1+r*.65,trunkWidth:.35,foliage:['#3d6749','#618754','#86a661']});
      }else if((t==='g'||t==='m')&&r>.94){
        kit.box(X,.17,Z,.38,.32,.37,'#658d52',{role:'foliage'});
        if(r>.973)kit.box(X,.4,Z,.22,.18,.22,'#e8ba67',{role:'detail'});
      }else if(t==='r'||t==='b'){
        kit.box(X,.42+(r*.25),Z,scale,.84+r*.5,scale,t==='r'?'#8f6144':'#767971');
      }else if(t==='+'){
        for(let step=0;step<3;step++)kit.box(X,.045+step*.045,Z+(step-1)*.42,1.26,.09+step*.09,.42,'#cda260',{role:'paving'});
      }else if(t==='~' && r>.79){
        kit.box(X,-.06,Z,.74,.045,.10,'#a6c7b3',{role:'detail'});
      }else if(t==='.' && !upper && r>.72){
        kit.box(X,.012,Z,1.38,.024,.055,'#a69e8d',{role:'detail'});
      }
    }
  }
}
