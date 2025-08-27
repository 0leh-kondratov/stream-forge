const http = require('http');
const url = require('url');
const pino = require('pino');

const projectID = process.env.GCP_PROJECT_ID;
const service = process.env.K_SERVICE || 'sample-logger-node';
const version = process.env.K_REVISION || '1.0.0';

const logger = pino({
  messageKey: 'message',
  formatters: {
    level(label) {
      // Map pino levels to GCP severity
      const pinoLevelToGcpSeverity = {
        trace: 'DEBUG',
        debug: 'DEBUG',
        info: 'INFO',
        warn: 'WARNING',
        error: 'ERROR',
        fatal: 'CRITICAL',
      };
      return { severity: pinoLevelToGcpSeverity[label] || 'INFO' };
    },
  },
});

if (!projectID) {
  logger.warn("GCP_PROJECT_ID environment variable not set. Trace correlation will be affected.");
}

const server = http.createServer((req, res) => {
  const startTime = Date.now();
  const parsedUrl = url.parse(req.url, true);
  const traceHeader = req.headers['x-cloud-trace-context'];

  const baseLog = {
    service,
    version,
    env: process.env.APP_ENV || 'dev',
    tenant: process.env.TENANT || 'default',
    request_id: req.headers['x-request-id'],
    http_method: req.method,
    http_path: parsedUrl.pathname,
  };

  // Add trace context for Cloud Trace correlation
  if (traceHeader && projectID) {
    const [traceId, spanId] = traceHeader.split('/');
    baseLog['logging.googleapis.com/trace'] = `projects/${projectID}/traces/${traceId}`;
    if (spanId) {
      baseLog['logging.googleapis.com/spanId'] = spanId.split(';')[0];
    }
  }

  if (parsedUrl.pathname === '/healthz') {
    res.writeHead(200);
    res.end('ok');
    logger.debug(baseLog, 'Health check successful');
    return;
  }

  if (parsedUrl.query.error === 'true') {
    res.writeHead(500);
    res.end('Internal Server Error');
    const latencyMs = Date.now() - startTime;
    logger.error({ ...baseLog, status: 500, latency_ms: latencyMs }, 'Simulated internal server error');
  } else {
    res.writeHead(200);
    res.end('Work done successfully');
    const latencyMs = Date.now() - startTime;
    logger.info({ ...baseLog, status: 200, latency_ms: latencyMs }, 'Request processed successfully');
  }
});

server.listen(8080, () => {
  logger.info(`Server listening on port 8080`);
});
