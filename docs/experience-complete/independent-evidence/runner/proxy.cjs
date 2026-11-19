const http=require('http');
http.createServer((req,res)=>{const up=http.request({hostname:'web',port:3000,path:req.url,method:req.method,headers:req.headers},r=>{res.writeHead(r.statusCode,r.headers);r.pipe(res)});up.on('error',e=>{res.writeHead(502);res.end(e.message)});req.pipe(up)}).listen(3109,'0.0.0.0');
