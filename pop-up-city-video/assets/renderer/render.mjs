import {createServer} from 'node:http';
import {readFile,writeFile,mkdir} from 'node:fs/promises';
import {resolve,extname,dirname,join} from 'node:path';
import {fileURLToPath} from 'node:url';
import {spawn} from 'node:child_process';
import {once} from 'node:events';
import {createRequire} from 'node:module';
const {chromium}=createRequire(import.meta.url)('playwright');
const root=dirname(fileURLToPath(import.meta.url));
const cfg=JSON.parse(await readFile(join(root,'scene.json'),'utf8'));
const {width,height,fps,duration,slug}=cfg;
const mime={'.html':'text/html','.mjs':'text/javascript','.js':'text/javascript','.json':'application/json','.png':'image/png','.jpg':'image/jpeg'};
const server=createServer(async(req,res)=>{
 try{
  const url=new URL(req.url,'http://127.0.0.1');
  const p=resolve(root,'.'+(url.pathname==='/'?'/index.html':url.pathname));
  if(!p.startsWith(root+'/'))throw Error('outside root');
  const b=await readFile(p);res.writeHead(200,{'content-type':mime[extname(p)]||'application/octet-stream'});res.end(b);
 }catch(e){res.writeHead(404);res.end('not found');}
});
await new Promise(r=>server.listen(0,'127.0.0.1',r));
const link='http://127.0.0.1:'+server.address().port;
const args=['--no-sandbox','--use-gl=angle','--use-angle=swiftshader','--enable-unsafe-swiftshader','--disable-dev-shm-usage','--ignore-gpu-blocklist','--num-raster-threads=2'];
const out=join(root,'output');await mkdir(out,{recursive:true});
async function pageUse(task){
 const browser=await chromium.launch({executablePath:process.env.CHROME_PATH||undefined,headless:true,args});
 try {
  const page=await browser.newPage({viewport:{width,height}});
  page.on('pageerror',e=>console.error('PAGE ERROR',e));
  page.on('response',r=>{if(r.status()>=400&&r.url().includes('127.0.0.1')&&!r.url().endsWith('favicon.ico'))console.error(r.status(),r.url());});
  await page.goto(link);
  await page.waitForFunction(()=>window.ready,{},{timeout:60000});
  const grab=async(t,format)=>Buffer.from(await page.evaluate(([s,f])=>window.captureFrame(s,f),[t,format]),'base64');
  return await task(grab);
 }finally{await browser.close();}
}
function proc(args,pipe=false){
 const p=spawn('ffmpeg',['-hide_banner','-v','error','-y',...args],{stdio:[pipe?'pipe':'ignore','inherit','inherit']});
 p.stdin?.on('error',console.error);
 return [p,once(p,'close').then(([code])=>{if(code!==0)throw Error('ffmpeg '+code)})];
}
async function chunk(i,lo,hi){
 await pageUse(async grab=>{
  const file=join(out,prefix+'-part'+i+'.mp4');
  const [p,done]=proc(['-f','image2pipe','-framerate',String(fps),'-i','-','-an','-c:v','libx264','-preset','fast','-crf','18','-pix_fmt','yuv420p','-threads','2','-movflags','+faststart',file],true);
  try{
   for(let k=lo;k<hi;k++){
    if(!p.stdin.write(await grab(k/fps,'image/jpeg')))await once(p.stdin,'drain');
    if((k-lo)%100===0)console.log('Part '+i+': '+(k-lo)+' / '+(hi-lo));
   }
  }finally{p.stdin.end();}
  await done;
 });
}
const mode=process.argv[2]||'preview';
const prefix=mode==='clip' ? slug+'-clip-'+process.argv.slice(3,5).join('-') : slug+'-paper-atlas';
try{
 if(mode==='video'||mode==='clip'){
  const start=mode==='clip'?Number(process.argv[3]):0, end=mode==='clip'?Number(process.argv[4]):duration;
  if(!(Number.isInteger(start)&&Number.isInteger(end)&&0<=start&&start<end&&end<=duration))throw Error('Use clip <startWholeSecond> <endWholeSecond>, within the project duration');
  const workers=Math.max(1,Math.min(3,end-start,Math.round(Number(process.env.RENDER_WORKERS)||2)));
  await Promise.all(Array.from({length:workers},(_,i)=>chunk(i,(start+Math.ceil(i*(end-start)/workers))*fps,(start+Math.ceil((i+1)*(end-start)/workers))*fps)));
  const list=Array.from({length:workers},(_,i)=>'file '+prefix+'-part'+i+'.mp4').join('\n')+'\n';await writeFile(join(out,prefix+'-parts.txt'),list);
  const [p,done]=proc(['-f','concat','-safe','1','-i',join(out,prefix+'-parts.txt'),'-c','copy','-movflags','+faststart',join(out,prefix+'.mp4')]);await done;
  console.log('FINAL '+join(out,prefix+'.mp4'));
 }else if(mode==='preview'){
  const times=process.argv.slice(3).length?process.argv.slice(3).map(Number):cfg.previewTimes;
  if(times.some(t=>!Number.isFinite(t)||t<0||t>=duration))throw Error('Preview timestamps must be in [0, duration)');
  await pageUse(async grab=>{for(let i=0;i<times.length;i++)await writeFile(join(out,'key-'+String(i).padStart(2,'0')+'.jpg'),await grab(times[i],'image/jpeg'))});
  console.log('Keyframes ready');
 }else throw Error('Use preview, clip or video');
}finally{server.close();}
