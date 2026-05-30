import fs from 'fs';
import path from 'path';

export class CERExportIngest {
  constructor(config = {}, logger = console) {
    this.config = config;
    this.logger = logger;
  }

  ingestJsonl(inputPath, context = {}) {
    const resolved = path.resolve(inputPath);
    const lines = fs.readFileSync(resolved, 'utf8').split(/\r?\n/).filter(Boolean);
    const records = lines.map(line => JSON.parse(line));

    const counts = {};
    const runIds = new Set();
    const recordTypes = new Set();
    const riskFlags = [];

    for (const record of records) {
      const type = record.record_type || 'unknown';
      counts[type] = (counts[type] || 0) + 1;
      recordTypes.add(type);
      if (record.run_id) runIds.add(record.run_id);
      if (type === 'data_issue' && record.payload?.details) {
        riskFlags.push(record.payload.details);
      }
    }

    const summary = {
      valid: records.length > 0,
      contractVersion: records[0]?.contract_version || null,
      schemaVersion: records[0]?.schema_version || null,
      runIds: [...runIds],
      recordTypes: [...recordTypes],
      counts,
      riskFlags: [...new Set(riskFlags)].sort(),
      source: resolved,
      context
    };

    return {
      records,
      summary,
      timestamp: Date.now()
    };
  }

  ingestAndWrite(inputPath, outputDir, context = {}) {
    const result = this.ingestJsonl(inputPath, context);
    const runId = context.runId || `cer_export_ingest_${result.timestamp}`;
    const targetDir = path.resolve(outputDir, runId);
    fs.mkdirSync(targetDir, { recursive: true });

    const meta = {
      kind: 'cer_export_ingest_v0.1',
      runId,
      generatedAt: new Date(result.timestamp).toISOString(),
      summary: result.summary,
      context
    };

    fs.writeFileSync(path.join(targetDir, 'meta.json'), JSON.stringify(meta, null, 2));
    fs.writeFileSync(path.join(targetDir, 'records.json'), JSON.stringify(result.records, null, 2));
    fs.writeFileSync(path.join(targetDir, 'summary.json'), JSON.stringify(result.summary, null, 2));

    return {
      ...result,
      runId,
      outputDir: targetDir
    };
  }
}

export function createCERExportIngest(config = {}, logger) {
  return new CERExportIngest(config, logger);
}
