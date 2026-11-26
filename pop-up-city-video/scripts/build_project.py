#!/usr/bin/env python3
"""Compile city metadata and generated image files to a self-contained Three.js project."""
from __future__ import annotations
import argparse
import json
import math
from pathlib import Path
import re
import shutil
import tempfile

ROOT = Path(__file__).resolve().parents[1]
ID = re.compile(r'^[a-z0-9]+(?:-[a-z0-9]+)*$')
MAP_W, MAP_D = 10.8, 7.68

def need(ok, msg):
    if not ok:
        raise ValueError(msg)

def load_json(path):
    with path.open(encoding='utf-8-sig') as f:
        return json.load(f, parse_constant=lambda v: (_ for _ in ()).throw(ValueError('invalid number: '+v)))

def finite(v):
    return type(v) in (int,float) and math.isfinite(v)

def box(v, n, bounds, where):
    need(isinstance(v,list) and len(v)==n and all(finite(z) and lo<=z<=hi for z,(lo,hi) in zip(v,bounds)),f'invalid {where}')
    return v

def label(v,where,n=96):
    need(isinstance(v,str) and 0<len(v.strip())<=n and not any(ord(c)<32 for c in v),f'invalid {where}')
    return v.strip()

def filename(v, base, where):
    need(isinstance(v,str) and Path(v).name==v and '/' not in v and chr(92) not in v and Path(v).suffix.lower() in {'.png','.jpg','.jpeg','.webp'},f'{where}: expected image filename without a directory')
    p=(base/v).resolve()
    need(p.parent==base and p.is_file(), f'{where}: file missing or outside artwork folder: {v}')
    return p

def prepare(source, dest, alpha=False, split=False):
    try:
        from PIL import Image, ImageOps
    except ImportError as e:
        raise ValueError('Pillow is required; install it in a project-local venv') from e
    with Image.open(source) as raw:
        im=ImageOps.exif_transpose(raw)
        if alpha:
            im=im.convert('RGBA'); a=im.getchannel('A')
            b=a.point(lambda v:255 if v>=130 else 0).getbbox()
            need(b is not None and sum(a.histogram()[:40])>=im.width*im.height*.01,f'{source.name}: requires meaningful transparent background')
            l,t,r,d=b
            im=im.crop((max(l-7,0),max(t-7,0),min(r+7,im.width),min(d+7,im.height)))
            im.thumbnail((1370,1370),Image.Resampling.LANCZOS)
            im.save(dest,format='PNG')
        elif split:
            im=im.convert('RGB')
            # Retain the whole artwork and apply the board aspect in one predictable resample.
            im=im.resize((2160,1536),Image.Resampling.LANCZOS)
            for i in range(3):
                im.crop((i*720,0,(i+1)*720,1536)).save(dest/f'map-{i}.jpg',quality=92,subsampling=0)
        else:
            im=im.convert('RGB');im.thumbnail((1200,1200),Image.Resampling.LANCZOS);im.save(dest,quality=92)
        return im.size

def plan(source, art, project):
    need(isinstance(source,dict),'city config must be a JSON object')
    work=project/'assets';work.mkdir(exist_ok=True)
    duration=source.get('duration',50); fps=source.get('fps',24)
    need(type(duration)==int and 8<=duration<=180,'duration must be 8–180 whole seconds')
    need(type(fps)==int and 12<=fps<=60,'fps must be an integer from 12 to 60')
    presets={'9:16':(720,1280),'16:9':(1280,720),'1:1':(960,960),'4:5':(864,1080),'3:4':(900,1200)}
    ratio=source.get('aspect','9:16')
    need(ratio in presets,'aspect must be 9:16, 16:9, 1:1, 4:5 or 3:4')
    w,h=presets[ratio]
    size=source.get('size')
    if size is not None:
        need(isinstance(size,list) and len(size)==2 and all(type(v)==int and 480<=v<=2160 and v%2==0 for v in size),'size must be two even dimensions, 480–2160')
        need(size[0]*h==size[1]*w,'size must match aspect')
        w,h=size
    slug=source.get('slug')
    need(isinstance(slug,str) and len(slug)<=48 and ID.fullmatch(slug),'slug must use lowercase letters/digits separated by hyphens')
    title=label(source.get('title'),'title',28)
    subtitle=label(source.get('subtitle',slug.replace('-',' ')),'subtitle',50)
    closing=label(source.get('closing',title+' · 夜色'),'closing',36)
    credit=label(source.get('mapLabel','AI 纸艺地图 / 非导航底图'),'mapLabel',60)
    objs=source.get('landmarks')
    need(isinstance(objs,list) and 1<=len(objs)<=8,'landmarks must have 1–8 entries, in visit order')
    need(duration >= 2*len(objs)+5,'increase duration or reduce the landmark count; each needs a readable beat')
    media=source.get('art')
    need(isinstance(media,dict),'expected art object with map, desk and paper filenames')
    prepare(filename(media.get('map'),art,'art.map'),work,split=True)
    for k in ('desk','paper'):
        prepare(filename(media.get(k),art,'art.'+k),work/(k+'.jpg'))
    rows=[]; seen=set()
    intro=max(2.5,duration*.14); finale=max(2.,duration*.12); tail=duration-finale
    beat=(tail-intro)/len(objs)
    wide = w >= h
    full_end=[.14,10.3,10.1] if wide else [.14,17.8,17.5]
    opening=[[1.15,7.0,7.3],[1.7,9.4,9.75]] if wide else [[1.45,10.7,10.3],[2.3,14.3,13.7]]
    shots=[dict(start=0,end=intro,p=opening,l=[[0,.60,0],[0,.16,0]],f=[47,49] if wide else [50,52])]
    marks=[intro*.30,intro*.87]
    for i, o in enumerate(objs):
        need(isinstance(o,dict),f'landmark {i+1} must be an object')
        k=o.get('id')
        need(isinstance(k,str) and len(k)<=40 and ID.fullmatch(k) and k not in seen,'landmark ids must be distinct lowercase slugs')
        seen.add(k)
        x,z=box(o.get('at'),2,[(-4.65,4.65),(-3.02,3.02)],k+'.at')
        width=o.get('width',2.45)
        need(finite(width) and .55<=width<=4.,k+'.width outside .55–4.0')
        path='landmark-'+k+'.png'
        iw,ih=prepare(filename(o.get('image'),art,k+'.image'),work/path,alpha=True)
        width=min(width,2.8*iw/ih)
        point_h=width*ih/iw
        start=intro+i*beat; end=intro+(i+1)*beat if i+1<len(objs) else tail
        lamps=o.get('lamps',[[-.18,.45],[.16,.45]])
        need(isinstance(lamps,list) and len(lamps)<=8,k+'.lamps must have 0–8 coordinates')
        for v in lamps: box(v,2,[(-.48,.48),(.08,.95)],k+'.lamps')
        on=duration*(.76+.13*(i+1)/len(objs)) if i+1<len(objs) else min(end-beat*.20,max(start+beat*.50,duration*.78))
        rows.append(dict(id=k,image=path,cn=label(o.get('name'),k+'.name',35),
          en=label(o.get('subtitle',k.replace('-',' ')),k+'.subtitle',60),
          x=x,z=z,w=width,rise=[start+beat*.08,start+beat*.44],
          title=[start+beat*.44,end-.12],on=on,intensity=3.55,bulbs=lamps))
        angle=(-1 if i%2==0 else 1)
        vertical=max(2.4,point_h*.90+1.45)
        distance=5.25+max(0,width-2.50)*.64+max(0,point_h-1.9)*.35
        target=max(.52,point_h*.52)
        shots.append(dict(start=start,end=end,
          p=[[x-angle*1.9,vertical+.32,z+distance+.48],[x+angle*.88,vertical,z+distance]],
          l=[[x,target*.88,z],[x,target,z]],
          f=[46,44]))
        marks.extend([start+beat*.32,start+beat*.68])
    prev=shots[-1]
    shots.append(dict(start=tail,end=duration,p=[prev['p'][1],full_end],l=[prev['l'][1],[0,.32,0]],f=[prev['f'][1],45 if wide else 50]))
    marks.extend([tail+finale*.42,duration-.15])
    custom=source.get('shots')
    if custom is not None:
        need(isinstance(custom,list) and len(custom)>0,'shots must be a non-empty array')
        stop=0
        for i,s in enumerate(custom):
            need(isinstance(s,dict) and s.get('start')==stop and finite(s.get('end')) and stop<s['end']<=duration,f'shots[{i}] is not contiguous')
            stop=s['end']
            for k in ('p','l'):
                need(isinstance(s.get(k),list) and len(s[k])==2,f'shots[{i}].{k} needs two xyz vectors')
                for v in s[k]:box(v,3,[(-45,45),(-3,48),(-50,50)],'shot '+k)
            box(s.get('f'),2,[(20,90)]*2,'shot FOV')
        need(stop==duration,'shots must end at duration')
        shots=custom
    trees=[]
    greenery=media.get('greenery')
    if greenery is not None:
        at=source.get('greenery',[])
        need(isinstance(at,list) and len(at)<=40,'greenery must contain at most 40 points')
        for v in at:trees.append(box(v,3,[(-5.2,5.2),(-3.65,3.65),(.18,1.7)],'greenery point'))
        if trees:prepare(filename(greenery,art,'art.greenery'),work/'greenery.png',alpha=True)
    prop=None
    if source.get('moving') is not None:
        m=source['moving']
        need(isinstance(m,dict),'moving must be an object')
        path=m.get('path')
        need(isinstance(path,list) and 2<=len(path)<=24,'moving.path must have 2–24 points')
        for v in path:box(v,2,[(-5.2,5.2),(-3.65,3.65)],'moving point')
        width=m.get('width',.9);need(finite(width) and .15<=width<=2.8,'moving.width outside .15–2.8')
        mode=m.get('motion','ground')
        need(mode in ('ground','water'),'moving.motion must be ground or water')
        prepare(filename(m.get('image'),art,'moving.image'),work/'moving.png',alpha=True)
        prop=dict(path=path,width=width,motion=mode)
    return dict(slug=slug,title=title,subtitle=subtitle,closing=closing,mapLabel=credit,width=w,height=h,fps=fps,duration=duration,
                landmarks=rows,trees=trees,moving=prop,shots=shots,previewTimes=marks,
                timing=dict(intro=intro,tail=tail,dusk=duration*.59,night=duration*.92))

def main():
    a=argparse.ArgumentParser(description=__doc__)
    a.add_argument('--city',type=Path,required=True)
    a.add_argument('--art',type=Path,required=True)
    a.add_argument('--out',type=Path,required=True)
    args=a.parse_args()
    dest=args.out.resolve()
    if dest.exists():a.error('target exists; use a new output directory')
    try:
        art=args.art.resolve(strict=True)
        source=load_json(args.city)
        dest.parent.mkdir(parents=True,exist_ok=True)
        with tempfile.TemporaryDirectory(prefix='.popup-build-',dir=dest.parent) as temp:
            p=Path(temp)/'project'
            shutil.copytree(ROOT/'assets'/'renderer',p)
            render=plan(source,art,p)
            (p/'scene.json').write_text(json.dumps(render,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
            shutil.copy2(args.city,p/'city.input.json')
            p.rename(dest)
    except (ValueError,OSError,TypeError) as e:a.error(str(e))
    print(dest)

if __name__=='__main__':main()

