const fs=require('fs'),path=require('path'),Module=require('module');
const name=process.argv[2],tag=process.argv[3]||'after';const original=path.resolve('docs/stage8/independent-tests/'+name+'.cjs');const out=path.resolve('docs/stage8/fix-01-evidence/'+tag);fs.mkdirSync(out,{recursive:true});
let code=fs.readFileSync(original,'utf8').replaceAll("root+'/docs/stage8/independent-evidence","root+'/docs/stage8/fix-01-evidence/"+tag);
// Above replacement preserves trailing quote of original expression.
code=code.replace("fs.readFileSync(out+'/ideas-report.html','utf8')","fs.readFileSync(root+'/docs/stage8/evidence/ideas-report.html','utf8')");
const m=new Module(original,module);m.filename=original;m.paths=Module._nodeModulePaths(path.dirname(original));m._compile(code,original);
