const { createProxyMiddleware } = require('http-proxy-middleware');
var bodyParser = require('body-parser')

var restream = function(proxyReq, req, res, options) {
  if (req.body) {
      let bodyData = JSON.stringify(req.body);
      // incase if content-type is application/x-www-form-urlencoded -> we need to change to application/json
      proxyReq.setHeader('Content-Type','application/json');
      proxyReq.setHeader('Content-Length', Buffer.byteLength(bodyData));
      // stream the content
      proxyReq.write(bodyData);
  }
}

module.exports = function(app) {
  app.use(bodyParser.json());
  app.use(bodyParser.urlencoded());
  app.use(
    createProxyMiddleware('/api', {
       target: "https://localhost:5000/",
       changeOrigin: true,
       secure: false,
       onProxyReq: restream
    })
  );
};