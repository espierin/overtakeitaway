const test=require('node:test'),assert=require('node:assert/strict'),vm=require('node:vm'),fs=require('node:fs');
const context={window:{}};vm.runInNewContext(fs.readFileSync('_development/assets/goat-parameters.js','utf8'),context);
const {sampleCurvePath,curveLabelLayout}=context.window.goatParameters;

test('collision geometry follows the rendered cubic between its endpoints',()=>{
 const points=sampleCurvePath('M0,0C0,100 100,100 100,0');
 assert.ok(points.length>60);
 assert.ok(Math.abs(Math.max(...points.map(p=>p.y))-75)<.05);
 assert.ok(points.some(p=>p.x>40&&p.x<60&&p.y>70));
 for(let i=1;i<points.length;i++)assert.ok(Math.hypot(points[i].x-points[i-1].x,points[i].y-points[i-1].y)<3.1);
});

function checkLayout(curves){
 const bounds={left:0,right:800,top:0,bottom:300},layout=curveLabelLayout(curves,bounds);
 assert.equal(layout.length,curves.length);
 assert.equal(JSON.stringify(curveLabelLayout(curves,bounds)),JSON.stringify(layout));
 for(const label of layout){
  const b=label.box;
  assert.ok(b.x>=0&&b.x+b.w<=800&&b.y>=0&&b.y+b.h<=300);
  assert.ok(Math.hypot(label.point.x-label.leader.x,label.point.y-label.leader.y)<=100);
  for(const curve of curves)for(const run of curve.runs)for(const point of run)assert.ok(!(point.x>b.x-3&&point.x<b.x+b.w+3&&point.y>b.y-3&&point.y<b.y+b.h+3),label.id+' overlaps '+curve.id);
 }
 for(let i=0;i<layout.length;i++)for(let j=0;j<i;j++){const a=layout[i].box,b=layout[j].box;assert.ok(a.x>=b.x+b.w||b.x>=a.x+a.w||a.y>=b.y+b.h||b.y>=a.y+a.h);}
 return layout;
}

test('labels avoid their own and every other crossing curve without a right-hand column',()=>{
 const paths=['M10,135C190,10 610,280 790,130','M10,140C250,280 500,10 790,145','M10,145C250,20 500,15 790,70','M10,138C260,180 520,240 790,250'];
 checkLayout(paths.map((path,i)=>({id:'driver'+i,width:166,runs:[sampleCurvePath(path)]})));
});

test('coincident starts get separate readable labels with short leaders',()=>{
 const curves=Array.from({length:4},(_,i)=>({id:'driver'+i,width:160,runs:[sampleCurvePath('M10,150L790,150')]}));
 const layout=checkLayout(curves);
 assert.ok(layout.every(label=>label.separated===false)); // No unique point: omit misleading markers.
});

test('marker anchors move beyond a shared curve section before attaching a label',()=>{
 const curves=[
  {id:'a',width:160,runs:[sampleCurvePath('M10,150L350,150C480,150 600,30 790,30')]},
  {id:'b',width:160,runs:[sampleCurvePath('M10,150L350,150C480,150 600,270 790,270')]}
 ];
 const layout=checkLayout(curves);
 for(const label of layout){assert.equal(label.separated,true);assert.ok(label.point.x>350);for(const other of curves){if(other.id===label.id)continue;const distance=Math.min(...other.runs.flat().map(p=>Math.hypot(p.x-label.point.x,p.y-label.point.y)));assert.ok(distance>=8);}}
});
