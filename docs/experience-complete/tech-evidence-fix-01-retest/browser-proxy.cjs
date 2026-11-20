const http = require('node:http');

const server = http.createServer((request, response) => {
  const headers = {...request.headers, host: '127.0.0.1:3120'};
  const upstream = http.request({
    hostname: 'host.docker.internal',
    port: 3120,
    method: request.method,
    path: request.url,
    headers,
  }, upstreamResponse => {
    response.writeHead(upstreamResponse.statusCode, upstreamResponse.headers);
    upstreamResponse.pipe(response);
  });
  upstream.on('error', error => {
    response.writeHead(502, {'content-type': 'text/plain'});
    response.end(error.message);
  });
  request.pipe(upstream);
});

server.listen(3120, '0.0.0.0');
