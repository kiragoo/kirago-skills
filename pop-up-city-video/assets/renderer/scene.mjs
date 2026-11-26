import * as T from './vendor/three.module.min.js';
const cfg=await fetch('./scene.json').then(r=>r.json());
const {width:W,height:H,duration:D,timing}=cfg;
document.title=cfg.title+' · Paper Atlas';
const V=(x,y,z)=>new T.Vector3(x,y,z), C=(n)=>new T.Color(n);
const ease=(a,b,t)=>T.MathUtils.smoothstep(t,a,b), lerp=T.MathUtils.lerp;
const renderer=new T.WebGLRenderer({antialias:true,preserveDrawingBuffer:true});
renderer.setSize(W,H,false);renderer.outputColorSpace=T.SRGBColorSpace;renderer.toneMapping=T.ACESFilmicToneMapping;
renderer.toneMappingExposure=1.10;renderer.shadowMap.enabled=true;renderer.shadowMap.type=T.PCFSoftShadowMap;
renderer.shadowMap.autoUpdate=false;
const view=document.querySelector('#view');view.width=W;view.height=H;
const ctx=view.getContext('2d',{alpha:false});
const scene=new T.Scene(), camera=new T.PerspectiveCamera(42,W/H,.095,180);
const M=10.8, Z=7.68, pw=M/3;
const loader=new T.TextureLoader();
const name=['map-0.jpg','map-1.jpg','map-2.jpg','desk.jpg','paper.jpg',...cfg.landmarks.map(x=>x.image),...(cfg.trees.length?['greenery.png']:[]),...(cfg.moving?['moving.png']:[])];
const A=Object.fromEntries(await Promise.all(name.map(async n=>{
 const t=await loader.loadAsync('./assets/'+n);t.colorSpace=T.SRGBColorSpace;t.anisotropy=2;return [n,t];
})));
const ambient=new T.HemisphereLight(0xeaf3dd,0x675945,2.0);scene.add(ambient);
const sun=new T.DirectionalLight(0xffdcb1,2.5);sun.position.set(-7,12,5);sun.castShadow=true;
Object.assign(sun.shadow.camera,{left:-9,right:9,top:8,bottom:-8,near:.5,far:29});
sun.shadow.mapSize.set(896,896);sun.shadow.bias=-.00029;sun.shadow.normalBias=.018;scene.add(sun);
const rim=new T.DirectionalLight(0xc4e7ff,.45);rim.position.set(6,5,-7);scene.add(rim);
const side=new T.MeshStandardMaterial({color:0xaa9171,map:A['paper.jpg'],roughness:.93});
const reverse=new T.MeshStandardMaterial({color:0xdcc8a7,map:A['paper.jpg'],roughness:.95});
const floorTex=A['desk.jpg'];floorTex.wrapS=floorTex.wrapT=T.RepeatWrapping;floorTex.repeat.set(7,7);
const desk=new T.Mesh(new T.PlaneGeometry(190,190),new T.MeshStandardMaterial({map:floorTex,color:0x9f8c77,roughness:1}));
desk.position.y=-.15;desk.rotation.x=-Math.PI/2;desk.receiveShadow=true;scene.add(desk);
function solid(geo,mat){const m=new T.Mesh(geo,mat?.isMaterial?mat:new T.MeshStandardMaterial({color:mat,roughness:.83}));m.castShadow=true;m.receiveShadow=true;return m;}
const root=new T.Group();scene.add(root);const hinges=[];
for(let i=0;i<3;i++){
 const g=new T.Group();(i?hinges[i-1]:root).add(g);g.position.x=i?pw:0;hinges.push(g);
 const surface=new T.MeshStandardMaterial({map:A['map-'+i+'.jpg'],color:0xfff3db,roughness:.95});
 const board=solid(new T.BoxGeometry(pw-.004,.077,Z),side);
 board.material=[side,side,surface,reverse,side,side];board.position.set(pw/2,-.0385,0);g.add(board);
 if(i){
  const crease=solid(new T.CylinderGeometry(.009,.009,Z-.02,6),0xbcaa87);crease.rotation.x=Math.PI/2;crease.position.y=.002;g.add(crease);
 }
}
function locate(x,z,y=0){const i=Math.min(2,Math.max(0,Math.floor((x+M/2)/pw)));return [hinges[i],V(x+M/2-i*pw,y,z)];}
function snap(x,z,y=0){const [p,v]=locate(x,z,y);const g=new T.Group();g.position.copy(v);p.add(g);return g;}
function cutout(tex,w,h,z,color,shadow=true){
 const mat=new T.MeshStandardMaterial({map:tex,color,alphaTest:.44,side:T.DoubleSide,roughness:.89,emissive:0x2d2019,emissiveIntensity:.16});
 const m=solid(new T.PlaneGeometry(w,h),mat);m.position.set(0,h*.5,z);m.castShadow=shadow;
 if(shadow)m.customDepthMaterial=new T.MeshDepthMaterial({depthPacking:T.RGBADepthPacking,map:tex,alphaTest:.44,side:T.DoubleSide});
 return m;
}
const lampFusion=new T.MeshStandardMaterial({color:0xffa75d,emissive:0xffa044,emissiveIntensity:2.5,roughness:.67});
const routeMat=new T.MeshStandardMaterial({color:0xb77741,emissive:0xffae5a,emissiveIntensity:.2,roughness:.77});
const cards=cfg.landmarks.map(k=>{
 const anchor=snap(k.x,k.z,.075);
 const support=solid(new T.BoxGeometry(k.w*.78,.030,.38),side);support.position.set(0,-.063,-.06);anchor.add(support);
 const spine=solid(new T.CylinderGeometry(.014,.014,k.w*.76,8),side);spine.rotation.z=Math.PI/2;spine.position.y=-.032;anchor.add(spine);
 const flap=new T.Group();anchor.add(flap);const tex=A[k.image];const h=k.w*tex.image.height/tex.image.width;
 const layers=[[-.194,0xb09d80],[-.085,0xd4bfa3],[.020,0xfff7ed]].map(([z,tint],i)=>{
  const part=new T.Group();const pic=cutout(tex,k.w*(i===0?.97:1),h,z,tint);part.add(pic);flap.add(part);return part;
 });
 const light=new T.PointLight(0xffa755,0,3.8,2);light.position.set(0,h*.57,.53);anchor.add(light);
 const breath=new T.PointLight(0xffb66b,0,2.9,2);breath.position.set(-k.w*.25,.18,.27);anchor.add(breath);
 const bulbs=[];for(const pos of k.bulbs){
  const b=new T.Mesh(new T.SphereGeometry(.026,8,5),lampFusion);b.position.set(pos[0]*k.w,h*pos[1],.051);flap.add(b);bulbs.push(b);
 }
 return {...k,anchor,flap,h,layers,light,breath,bulbs};
});
const willow=A['greenery.png'];
const willows=cfg.trees.map(([x,z,h],i)=>{
 const a=snap(x,z,.009), diameter=h*willow.image.width/willow.image.height;
 const stem=new T.Group();const w=cutout(willow,diameter,h,0,0xe4edd3,i%2===0);
 stem.rotation.y=i%2?.50:-.45;stem.add(w);a.add(stem);
 const depth=stem.clone();depth.rotation.y=stem.rotation.y+1.10;for(const o of depth.children){o.castShadow=false;o.receiveShadow=false;}a.add(depth);
 return {a,stem,depth};
});
const moving=cfg.moving;
let prop=null,propPath=null;
if(moving){
 const tex=A['moving.png'];propPath=new T.CatmullRomCurve3(moving.path.map(([x,z])=>V(x,.045,z)));
 prop=new T.Group();scene.add(prop);prop.add(cutout(tex,moving.width,moving.width*tex.image.height/tex.image.width,0,0xfcdfbd,false));
}
const routeCurve=cfg.landmarks.length>1 ? new T.CatmullRomCurve3(cfg.landmarks.map(({x,z})=>V(x,.023,z-.20))) : null;
const pips=hinges.map(p=>({p,data:[]}));
for(let i=0;routeCurve&&i<126;i++){
 const point=routeCurve.getPoint(i/125);const [p,loc]=locate(point.x,point.z,point.y);pips.find(g=>g.p===p).data.push([i,loc]);
}
for(const q of pips){
 q.mesh=new T.InstancedMesh(new T.SphereGeometry(.032,7,5),routeMat,q.data.length);
 q.mesh.frustumCulled=false;q.p.add(q.mesh);const tmp=new T.Object3D();
 q.data.forEach(([id,loc],i)=>{tmp.position.copy(loc);const r=id%13===0?1.2:.72;tmp.scale.set(r,.4,r);tmp.updateMatrix();q.mesh.setMatrixAt(i,tmp.matrix);});
 q.mesh.instanceMatrix.needsUpdate=true;q.mesh.count=0;
}
const overlay=document.createElement('canvas'), fog=new T.FogExp2(0x302926,.026);scene.fog=fog;
overlay.width=W;overlay.height=H;const o=overlay.getContext('2d');
const factor=H/1280, UW=W/factor;
o.setTransform(factor,0,0,factor,0,0);
const vignette=o.createRadialGradient(UW*.47,580,220,UW*.48,650,Math.max(810,UW*.60));
vignette.addColorStop(0,'rgba(14,17,20,0)');vignette.addColorStop(1,'rgba(12,16,23,.46)');
function text(x,y,s,font,color,align='center'){o.textAlign=align;o.font=font;o.fillStyle=color;o.fillText(s,x,y,align==='left'?Math.min(323,UW-105):UW-94);}
const ser=(n)=>'700 '+n+'px "Noto Serif CJK SC","Songti SC",serif';
const en='600 16px sans-serif', thin='500 17px "Noto Sans CJK SC",sans-serif';
const shot=cfg.shots.map(s=>({...s,p:s.p.map(a=>V(...a)),l:s.l.map(a=>V(...a))}));
await document.fonts.ready;
await document.fonts.load(ser(83),cfg.title+cfg.landmarks.map(x=>x.cn).join(''));
function graphic(t){
 o.clearRect(0,0,UW,1280);o.globalAlpha=1;o.fillStyle=vignette;o.fillRect(0,0,UW,1280);
 let alpha=ease(D*.005,D*.030,t)*(1-ease(timing.intro*.61,timing.intro*.87,t));
 if(alpha>0){o.globalAlpha=alpha;text(UW/2,102,'P A P E R    A T L A S',en,'#d8b787');text(UW/2,198,cfg.title,ser(83),'#fff1d0');text(UW/2,242,cfg.subtitle.toUpperCase(),en,'#e6cda4');}
 cards.forEach((k,i)=>{
  const span=Math.min(.61,(k.title[1]-k.title[0])*.24);
  const a=ease(k.title[0],k.title[0]+span,t)*(1-ease(k.title[1]-span,k.title[1],t));
  if(a<.001)return;
  o.globalAlpha=a;o.fillStyle='rgba(21,29,31,.86)';o.fillRect(52,989,Math.min(353,UW-104),131);
  o.fillStyle='#d5ac72';o.fillRect(69,1007,31,2);
  text(69,1044,String(i+1).padStart(2,'0')+'  /  '+k.en.toUpperCase(),en,'#d8b787','left');text(67,1098,k.cn,ser(38),'#fff1d0','left');
 });
 alpha=ease(timing.tail+(D-timing.tail)*.20,timing.tail+(D-timing.tail)*.40,t);
 if(alpha>0){o.globalAlpha=alpha;text(UW/2,129,cfg.closing,ser(55),'#fff0cd');text(UW/2,174,cfg.subtitle.toUpperCase()+'  /  AFTER DARK',en,'#d3b283');}
 o.globalAlpha=.78;text(UW/2,1220,cfg.mapLabel,thin,'#e2caaa');o.globalAlpha=1;
}
let oldShadow=-99;
function step(t){
 const intro=timing.intro, tail=timing.tail;
 const a=1.27*(1-ease(.08*intro,.91*intro,t)),b=-1.21*(1-ease(.11*intro,.92*intro,t)),c=.99*(1-ease(.21*intro,.95*intro,t));
 root.position.set(-pw*(Math.cos(a)+Math.cos(b)+Math.cos(c))/2,.018,0);
 hinges[0].rotation.z=a;hinges[1].rotation.z=b-a;hinges[2].rotation.z=c-b;
 cards.forEach((k,i)=>{
  const u=ease(k.rise[0],k.rise[1],t);k.anchor.visible=u>.001;
  const spring=t>k.rise[1]&&t<k.rise[1]+.64 ? Math.sin((t-k.rise[1])*13)*.051*(1-ease(k.rise[1],k.rise[1]+.64,t)):0;
  k.flap.rotation.x=-(1-u)*1.39+spring;
  k.layers.forEach((part,j)=>part.rotation.x=-(1-u)*j*.031);
  const lit=ease(k.on,k.on+1.35,t);k.light.intensity=k.intensity*lit;k.breath.intensity=k.intensity*.32*lit;
  k.bulbs.forEach((b,j)=>b.visible=t>k.on+.085*j);
 });
 willows.forEach(({a,stem,depth},i)=>{
  const d=i*.003*intro;const u=ease(.55*intro+d,.86*intro+d,t);
  a.visible=u>.005;a.scale.y=Math.max(.003,u);
  stem.rotation.z=.025*Math.sin(t*.91+i*.71);depth.rotation.z=stem.rotation.z*.72;
 });
 const nav=ease(intro,tail,t);
 pips.forEach(q=>{q.mesh.count=q.data.filter(([i])=>i/126<nav).length;});
 routeMat.emissiveIntensity=.06+ease(timing.dusk,timing.night,t)*.94;
 if(prop){
  const phase=ease(intro,tail,t);
  prop.visible=t>=intro;prop.position.copy(propPath.getPoint(phase));
  prop.position.y=.065+(moving.motion==='water'?.013*Math.sin(t*2.2):0);
  prop.rotation.set(0,.12*Math.cos(phase*6),moving.motion==='water'?.037*Math.sin(t*1.42):.013*Math.sin(t*3));
 }
 const day=ease(intro,D*.28,t);
 const dusk=ease(timing.dusk,D*.72,t), night=ease(D*.72,timing.night,t);
 ambient.intensity=lerp(lerp(1.66,2.00,day),.88,night);
 ambient.color.copy(C(0xe4eddc).lerp(C(0xffeed9),day).lerp(C(0xb8c5f0),night));
 ambient.groundColor.copy(C(0x675341).lerp(C(0x33465a),night));
 sun.intensity=lerp(2.38,.54,night);
 sun.color.copy(C(0xffe0b7).lerp(C(0xffbd92),dusk).lerp(C(0xa7bfee),night));
 sun.position.set(-6.7+2.94*dusk,11.8-3.1*dusk,5.2-2.6*night);rim.intensity=.32+.47*night;
 fog.density=.024+.008*night;fog.color.copy(C(0x352d27).lerp(C(0x14243a),night));renderer.setClearColor(fog.color,1);
 const s=shot.find(s=>t<s.end)||shot.at(-1);
 const u=ease(s.start,s.end,t);
 camera.position.copy(s.p[0]).lerp(s.p[1],u);camera.fov=lerp(s.f[0],s.f[1],u);camera.updateProjectionMatrix();
 camera.lookAt(s.l[0].clone().lerp(s.l[1],u));
 // Cache static shadow frames; refresh reliably during folds, rises and the dusk transition.
 const dynamics=t<timing.intro||t>timing.dusk&&t<timing.night||cards.some(k=>t>k.rise[0]-.1&&t<k.rise[1]+.7);
 if(dynamics||Math.abs(t-oldShadow)>.28){renderer.shadowMap.needsUpdate=true;oldShadow=t;}
 renderer.render(scene,camera);graphic(t);ctx.drawImage(renderer.domElement,0,0);ctx.drawImage(overlay,0,0);
}
window.captureFrame=(t,format='image/jpeg')=>{step(t);return view.toDataURL(format,.94).split(',')[1];};
window.ready=true;step(0);
if(new URL(location.href).searchParams.has('preview')){
 const start=performance.now();const loop=now=>{step((now-start)/1000%D);requestAnimationFrame(loop);};requestAnimationFrame(loop);
}

