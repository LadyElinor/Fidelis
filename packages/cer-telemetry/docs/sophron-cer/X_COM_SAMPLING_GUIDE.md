# SOPHRON-CER Usage Guide: Sampling from X.com

A comprehensive guide to using the CER-Telemetry v2.0 pipeline for analyzing content from X.com (Twitter), with practical examples and best practices.

## Table of Contents

1. [Quick Start](#quick-start)
2. [Basic Sampling](#basic-sampling)
3. [Advanced Analysis](#advanced-analysis)
4. [Real-World Examples](#real-world-examples)
5. [Configuration for X.com](#configuration-for-xcom)
6. [Common Patterns](#common-patterns)
7. [Troubleshooting](#troubleshooting)

---

## Quick Start

### Prerequisites

```bash
# From the OpenClaw workspace root:
cd SOPHRON-CER

# Install dependencies
npm install

# Set up your X.com API credentials
cp .env.example .env
# Edit .env with your credentials
```

### Your First Analysis

```bash
# From the OpenClaw workspace root:
cd SOPHRON-CER

# Run a basic analysis with 1000 samples
node src/cli.js analyze --max-samples 1000

# View the results (OpenClaw workspace root)
cd ..
ls -l outputs/
```

---

## Basic Sampling

### Example 1: Simple Prevalence Analysis

Analyze the prevalence of certain characteristics in X.com posts:

```javascript
// SOPHRON-CER/examples/basic-xcom-analysis.js
import { loadConfig } from '../config/schema.js';
import { createLogger } from '../lib/utils/logger.js';
import { MoltxCollector } from '../lib/collectors/moltx-collector.js';
import { PrevalenceAnalyzer } from '../lib/analyzers/prevalence-analyzer.js';

async function basicAnalysis() {
  const config = loadConfig();
  const logger = createLogger(config.logging);

  // Initialize collector for X.com data
  const collector = new MoltxCollector(config, logger);
  await collector.initialize();

  // Fetch posts from the last 24 hours
  const posts = await collector.fetchPaginated({
    since: new Date(Date.now() - 24 * 60 * 60 * 1000).toISOString(),
    platform: 'twitter'
  }, 1000);

  logger.info(`Collected ${posts.length} posts`);

  // Run prevalence analysis
  const analyzer = new PrevalenceAnalyzer(config, logger);
  const results = analyzer.analyze(posts);

  // Display summary
  console.log('\n=== Analysis Summary ===');
  console.log(`Total Posts: ${results.summary.totalPosts}`);
  console.log(`Analyzed Blocks: ${results.summary.totalBlocks}`);
  console.log(`Overall Prevalence: ${(results.summary.overallPrevalence * 100).toFixed(2)}%`);
  console.log(`95% CI: [${(results.summary.confidenceInterval.lower * 100).toFixed(2)}%, ${(results.summary.confidenceInterval.upper * 100).toFixed(2)}%]`);

  return results;
}

basicAnalysis().catch(console.error);
```

**Run it:**
```bash
node examples/basic-xcom-analysis.js
```

---

### Example 2: Time-Based Sampling

Sample posts across different time periods:

```javascript
// SOPHRON-CER/examples/temporal-sampling.js
import { MoltxCollector } from '../lib/collectors/moltx-collector.js';
import { PrevalenceAnalyzer } from '../lib/analyzers/prevalence-analyzer.js';
import { loadConfig } from '../config/schema.js';
import { createLogger } from '../lib/utils/logger.js';

async function temporalSampling() {
  const config = loadConfig();
  const logger = createLogger(config.logging);
  const collector = new MoltxCollector(config, logger);
  await collector.initialize();

  // Define time blocks (hourly over 24 hours)
  const timeBlocks = [];
  const now = Date.now();
  
  for (let i = 0; i < 24; i++) {
    const blockEnd = now - (i * 60 * 60 * 1000);
    const blockStart = blockEnd - (60 * 60 * 1000);
    
    timeBlocks.push({
      name: `Hour_${23 - i}`,
      start: new Date(blockStart),
      end: new Date(blockEnd)
    });
  }

  // Sample each time block
  const results = [];
  for (const block of timeBlocks) {
    logger.info(`Sampling ${block.name}...`);
    
    const posts = await collector.fetchPaginated({
      since: block.start.toISOString(),
      until: block.end.toISOString(),
      platform: 'twitter'
    }, 100); // 100 posts per hour

    results.push({
      block: block.name,
      timestamp: block.start,
      sampleSize: posts.length,
      posts: posts
    });
  }

  // Analyze temporal trends
  const analyzer = new PrevalenceAnalyzer(config, logger);
  const analysis = analyzer.analyze(
    results.flatMap(r => r.posts),
    results.map(r => ({ id: r.block, posts: r.posts }))
  );

  console.log('\n=== Temporal Analysis ===');
  analysis.blockAnalysis.forEach(block => {
    console.log(`${block.blockId}: ${block.sampleSize} posts, prevalence: ${(block.prevalence * 100).toFixed(2)}%`);
  });

  return analysis;
}

temporalSampling().catch(console.error);
```

---

### Example 3: Topic-Based Sampling

Sample and analyze posts by topic or hashtag:

```javascript
// SOPHRON-CER/examples/topic-sampling.js
async function topicSampling() {
  const config = loadConfig();
  const logger = createLogger(config.logging);
  const collector = new MoltxCollector(config, logger);
  await collector.initialize();

  // Define topics to analyze
  const topics = [
    { name: 'AI', keywords: ['#AI', '#MachineLearning', '#DeepLearning'] },
    { name: 'Climate', keywords: ['#ClimateChange', '#Environment', '#Sustainability'] },
    { name: 'Politics', keywords: ['#Politics', '#Election2024', '#Policy'] },
    { name: 'Sports', keywords: ['#Sports', '#NFL', '#NBA'] }
  ];

  const topicResults = [];

  for (const topic of topics) {
    logger.info(`Sampling topic: ${topic.name}`);
    
    // Fetch posts matching topic keywords
    const posts = await collector.fetchPaginated({
      keywords: topic.keywords,
      platform: 'twitter',
      limit: 500
    }, 500);

    topicResults.push({
      topic: topic.name,
      keywords: topic.keywords,
      sampleSize: posts.length,
      posts: posts
    });
  }

  // Compare prevalence across topics
  const analyzer = new PrevalenceAnalyzer(config, logger);
  
  console.log('\n=== Topic-Based Analysis ===');
  topicResults.forEach(result => {
    const analysis = analyzer.analyze(result.posts);
    console.log(`\nTopic: ${result.topic}`);
    console.log(`  Sample Size: ${result.sampleSize}`);
    console.log(`  Prevalence: ${(analysis.summary.overallPrevalence * 100).toFixed(2)}%`);
    console.log(`  95% CI: [${(analysis.summary.confidenceInterval.lower * 100).toFixed(2)}%, ${(analysis.summary.confidenceInterval.upper * 100).toFixed(2)}%]`);
  });

  return topicResults;
}
```

---

## Advanced Analysis

### Example 4: Statistical Comparison

Compare prevalence between different user groups:

```javascript
// SOPHRON-CER/examples/user-group-comparison.js
import { StatisticalAnalyzer } from '../lib/analyzers/statistical-analyzer.js';

async function compareUserGroups() {
  const config = loadConfig();
  const logger = createLogger(config.logging);
  const collector = new MoltxCollector(config, logger);
  await collector.initialize();

  // Define user groups
  const groups = [
    { name: 'Verified', filter: { verified: true } },
    { name: 'Unverified', filter: { verified: false } },
    { name: 'HighFollowers', filter: { minFollowers: 10000 } },
    { name: 'LowFollowers', filter: { maxFollowers: 1000 } }
  ];

  const groupData = [];

  for (const group of groups) {
    const posts = await collector.fetchPaginated({
      ...group.filter,
      platform: 'twitter',
      limit: 1000
    }, 1000);

    groupData.push({
      group: group.name,
      posts: posts,
      positives: posts.filter(p => p.hasTargetCharacteristic).length,
      total: posts.length
    });
  }

  // Statistical comparison
  const stats = new StatisticalAnalyzer(config, logger);

  console.log('\n=== User Group Comparison ===\n');
  
  // Chi-square test for independence
  const contingencyTable = [
    [groupData[0].positives, groupData[0].total - groupData[0].positives],
    [groupData[1].positives, groupData[1].total - groupData[1].positives]
  ];
  
  const chiSquare = stats.chiSquareTest(contingencyTable);
  console.log('Verified vs Unverified:');
  console.log(`  Chi-square: ${chiSquare.chiSquare.toFixed(3)}`);
  console.log(`  p-value: ${chiSquare.pValue.toFixed(4)}`);
  console.log(`  Significant: ${chiSquare.significant ? 'YES' : 'NO'}`);

  // Effect size (Cohen's h)
  const p1 = groupData[2].positives / groupData[2].total;
  const p2 = groupData[3].positives / groupData[3].total;
  const effect = stats.cohensH(p1, p2);
  
  console.log('\nHigh vs Low Followers:');
  console.log(`  Prevalence (High): ${(p1 * 100).toFixed(2)}%`);
  console.log(`  Prevalence (Low): ${(p2 * 100).toFixed(2)}%`);
  console.log(`  Cohen's h: ${effect.h.toFixed(3)} (${effect.interpretation})`);

  return { groupData, statistics: { chiSquare, effect } };
}
```

---

### Example 5: Weighted Analysis by Engagement

Weight prevalence estimates by post impressions/engagement:

```javascript
// SOPHRON-CER/examples/weighted-analysis.js
async function weightedAnalysis() {
  const config = loadConfig();
  const logger = createLogger(config.logging);
  const collector = new MoltxCollector(config, logger);
  await collector.initialize();

  // Fetch posts with engagement metrics
  const posts = await collector.fetchPaginated({
    platform: 'twitter',
    includeMetrics: true,
    limit: 2000
  }, 2000);

  const analyzer = new PrevalenceAnalyzer(config, logger);
  
  // Unweighted analysis
  const unweighted = analyzer.analyze(posts);
  
  // Weighted by impressions
  const weightedByImpressions = analyzer.analyze(posts, null, {
    weightField: 'impressions'
  });
  
  // Weighted by engagement (likes + retweets + replies)
  const postsWithEngagement = posts.map(p => ({
    ...p,
    totalEngagement: (p.likes || 0) + (p.retweets || 0) + (p.replies || 0)
  }));
  
  const weightedByEngagement = analyzer.analyze(postsWithEngagement, null, {
    weightField: 'totalEngagement'
  });

  console.log('\n=== Weighted vs Unweighted Analysis ===\n');
  
  console.log('Unweighted:');
  console.log(`  Prevalence: ${(unweighted.summary.overallPrevalence * 100).toFixed(2)}%`);
  console.log(`  95% CI: [${(unweighted.summary.confidenceInterval.lower * 100).toFixed(2)}%, ${(unweighted.summary.confidenceInterval.upper * 100).toFixed(2)}%]`);
  
  console.log('\nWeighted by Impressions:');
  console.log(`  Prevalence: ${(weightedByImpressions.summary.overallPrevalence * 100).toFixed(2)}%`);
  console.log(`  95% CI: [${(weightedByImpressions.summary.confidenceInterval.lower * 100).toFixed(2)}%, ${(weightedByImpressions.summary.confidenceInterval.upper * 100).toFixed(2)}%]`);
  
  console.log('\nWeighted by Engagement:');
  console.log(`  Prevalence: ${(weightedByEngagement.summary.overallPrevalence * 100).toFixed(2)}%`);
  console.log(`  95% CI: [${(weightedByEngagement.summary.confidenceInterval.lower * 100).toFixed(2)}%, ${(weightedByEngagement.summary.confidenceInterval.upper * 100).toFixed(2)}%]`);

  return { unweighted, weightedByImpressions, weightedByEngagement };
}
```

---

## Real-World Examples

### Example 6: Misinformation Detection

Analyze prevalence of potentially misleading content:

```javascript
// SOPHRON-CER/examples/misinformation-detection.js
async function analyzeMinformation() {
  const config = loadConfig();
  const logger = createLogger(config.logging);
  const collector = new MoltxCollector(config, logger);
  await collector.initialize();

  // Fetch posts about a specific topic
  const posts = await collector.fetchPaginated({
    keywords: ['#ClimateChange', 'global warming', 'climate crisis'],
    platform: 'twitter',
    limit: 5000
  }, 5000);

  // Classify posts (this would use your classification logic)
  const classifiedPosts = posts.map(post => ({
    ...post,
    hasTargetCharacteristic: classifyAsMisinformation(post), // Your classification function
    metadata: {
      confidence: getClassificationConfidence(post),
      reasons: getClassificationReasons(post)
    }
  }));

  // Analyze with stratification by account type
  const blocks = [
    { 
      id: 'verified', 
      posts: classifiedPosts.filter(p => p.user.verified) 
    },
    { 
      id: 'unverified', 
      posts: classifiedPosts.filter(p => !p.user.verified) 
    },
    { 
      id: 'high_followers', 
      posts: classifiedPosts.filter(p => p.user.followers_count > 10000) 
    },
    { 
      id: 'low_followers', 
      posts: classifiedPosts.filter(p => p.user.followers_count <= 10000) 
    }
  ];

  const analyzer = new PrevalenceAnalyzer(config, logger);
  const results = analyzer.analyze(classifiedPosts, blocks);

  // Generate comprehensive report
  const reporter = new OutputReporter(config, logger);
  await reporter.writeOutputs(results, {
    runId: `misinformation_${Date.now()}`,
    description: 'Climate change misinformation prevalence analysis',
    topic: 'ClimateChange',
    dateRange: {
      start: new Date(Date.now() - 7 * 24 * 60 * 60 * 1000),
      end: new Date()
    }
  });

  return results;
}

// Helper functions (implement based on your needs)
function classifyAsMisinformation(post) {
  // Your classification logic here
  // Could use keywords, ML models, fact-checking APIs, etc.
  return false; // placeholder
}

function getClassificationConfidence(post) {
  return 0.5; // placeholder
}

function getClassificationReasons(post) {
  return []; // placeholder
}
```

---

### Example 7: Trend Detection Over Time

Detect changes in prevalence patterns:

```javascript
// SOPHRON-CER/examples/trend-detection.js
import { StatisticalAnalyzer } from '../lib/analyzers/statistical-analyzer.js';

async function detectTrends() {
  const config = loadConfig();
  const logger = createLogger(config.logging);
  const collector = new MoltxCollector(config, logger);
  await collector.initialize();

  // Collect daily samples over 30 days
  const dailyData = [];
  const daysToAnalyze = 30;

  for (let i = 0; i < daysToAnalyze; i++) {
    const dayEnd = Date.now() - (i * 24 * 60 * 60 * 1000);
    const dayStart = dayEnd - (24 * 60 * 60 * 1000);

    logger.info(`Collecting data for day ${i + 1}/${daysToAnalyze}`);

    const posts = await collector.fetchPaginated({
      since: new Date(dayStart).toISOString(),
      until: new Date(dayEnd).toISOString(),
      platform: 'twitter',
      limit: 500
    }, 500);

    const prevalence = posts.filter(p => p.hasTargetCharacteristic).length / posts.length;

    dailyData.push({
      day: daysToAnalyze - i,
      date: new Date(dayStart),
      sampleSize: posts.length,
      prevalence: prevalence
    });
  }

  // Sort by day (oldest to newest)
  dailyData.sort((a, b) => a.day - b.day);

  // Mann-Kendall trend test
  const stats = new StatisticalAnalyzer(config, logger);
  const prevalenceSeries = dailyData.map(d => d.prevalence);
  const trendTest = stats.mannKendallTest(prevalenceSeries);

  console.log('\n=== Trend Analysis (30 Days) ===\n');
  console.log(`Trend Direction: ${trendTest.trend}`);
  console.log(`Kendall's Tau: ${trendTest.tau.toFixed(4)}`);
  console.log(`Z-score: ${trendTest.Z.toFixed(3)}`);
  console.log(`Statistically Significant: ${trendTest.significant ? 'YES' : 'NO'}`);

  // Display daily prevalence
  console.log('\nDaily Prevalence:');
  dailyData.forEach(d => {
    console.log(`  Day ${d.day}: ${(d.prevalence * 100).toFixed(2)}% (n=${d.sampleSize})`);
  });

  // Generate visualization-ready data
  const outputData = {
    trendAnalysis: trendTest,
    dailyData: dailyData,
    summary: {
      startDate: dailyData[0].date,
      endDate: dailyData[dailyData.length - 1].date,
      meanPrevalence: prevalenceSeries.reduce((a, b) => a + b) / prevalenceSeries.length,
      trend: trendTest.trend
    }
  };

  // Save results
  const fs = require('fs').promises;
  await fs.writeFile(
    'outputs/trend_analysis.json',
    JSON.stringify(outputData, null, 2)
  );

  return outputData;
}
```

---

### Example 8: A/B Testing Content Moderation

Test effectiveness of moderation strategies:

```javascript
// SOPHRON-CER/examples/ab-test-moderation.js
async function testModerationStrategies() {
  const config = loadConfig();
  const logger = createLogger(config.logging);
  const collector = new MoltxCollector(config, logger);
  await collector.initialize();

  // Collect posts from two experimental groups
  const controlGroup = await collector.fetchPaginated({
    experimentGroup: 'control',
    platform: 'twitter',
    limit: 2000
  }, 2000);

  const treatmentGroup = await collector.fetchPaginated({
    experimentGroup: 'treatment',
    platform: 'twitter',
    limit: 2000
  }, 2000);

  // Analyze each group
  const analyzer = new PrevalenceAnalyzer(config, logger);
  const controlResults = analyzer.analyze(controlGroup);
  const treatmentResults = analyzer.analyze(treatmentGroup);

  // Statistical comparison
  const stats = new StatisticalAnalyzer(config, logger);
  
  const controlPrevalence = controlResults.summary.overallPrevalence;
  const treatmentPrevalence = treatmentResults.summary.overallPrevalence;
  
  // Effect size
  const effect = stats.cohensH(controlPrevalence, treatmentPrevalence);
  
  // Hypothesis test
  const contingencyTable = [
    [
      controlGroup.filter(p => p.hasTargetCharacteristic).length,
      controlGroup.length - controlGroup.filter(p => p.hasTargetCharacteristic).length
    ],
    [
      treatmentGroup.filter(p => p.hasTargetCharacteristic).length,
      treatmentGroup.length - treatmentGroup.filter(p => p.hasTargetCharacteristic).length
    ]
  ];
  
  const chiSquare = stats.chiSquareTest(contingencyTable);

  console.log('\n=== A/B Test Results ===\n');
  
  console.log('Control Group:');
  console.log(`  Prevalence: ${(controlPrevalence * 100).toFixed(2)}%`);
  console.log(`  Sample Size: ${controlGroup.length}`);
  console.log(`  95% CI: [${(controlResults.summary.confidenceInterval.lower * 100).toFixed(2)}%, ${(controlResults.summary.confidenceInterval.upper * 100).toFixed(2)}%]`);
  
  console.log('\nTreatment Group:');
  console.log(`  Prevalence: ${(treatmentPrevalence * 100).toFixed(2)}%`);
  console.log(`  Sample Size: ${treatmentGroup.length}`);
  console.log(`  95% CI: [${(treatmentResults.summary.confidenceInterval.lower * 100).toFixed(2)}%, ${(treatmentResults.summary.confidenceInterval.upper * 100).toFixed(2)}%]`);
  
  console.log('\nComparison:');
  console.log(`  Absolute Difference: ${((treatmentPrevalence - controlPrevalence) * 100).toFixed(2)} percentage points`);
  console.log(`  Relative Change: ${(((treatmentPrevalence / controlPrevalence) - 1) * 100).toFixed(2)}%`);
  console.log(`  Cohen's h: ${effect.h.toFixed(3)} (${effect.interpretation})`);
  console.log(`  p-value: ${chiSquare.pValue.toFixed(4)}`);
  console.log(`  Statistically Significant: ${chiSquare.significant ? 'YES' : 'NO'}`);

  return {
    control: controlResults,
    treatment: treatmentResults,
    comparison: { effect, chiSquare }
  };
}
```

---

## Configuration for X.com

### Custom Configuration File

Create `SOPHRON-CER/config/xcom.json`:

```json
{
  "api": {
    "baseUrl": "https://api.x.com/v2",
    "timeout": 30000,
    "retryAttempts": 3,
    "retryDelay": 1000,
    "rateLimit": {
      "maxRequests": 300,
      "windowMs": 900000
    }
  },
  "sampling": {
    "minSampleSize": 200,
    "maxSampleSize": 10000,
    "defaultSampleSize": 1000,
    "stratificationMethod": "proportional"
  },
  "analysis": {
    "confidenceLevel": 0.95,
    "minBlockSize": 50,
    "enableWeighting": true,
    "weightField": "impressions"
  },
  "privacy": {
    "enablePiiDetection": true,
    "kAnonymity": 5,
    "redactUserIds": true,
    "hashSensitiveFields": true
  },
  "output": {
    "formats": ["json", "csv", "html"],
    "includeRawData": false,
    "prettify": true
  }
}
```

### Load Custom Configuration

```javascript
import { loadConfig } from './config/schema.js';

const config = loadConfig({
  configPath: './config/xcom.json'
});
```

---

## Common Patterns

### Pattern 1: Batch Processing

Process large datasets in manageable batches:

```javascript
async function batchProcess() {
  const config = loadConfig();
  const logger = createLogger(config.logging);
  const collector = new MoltxCollector(config, logger);
  await collector.initialize();

  const batchSize = 1000;
  const totalBatches = 10;
  const allResults = [];

  for (let i = 0; i < totalBatches; i++) {
    logger.info(`Processing batch ${i + 1}/${totalBatches}`);
    
    const posts = await collector.fetchPaginated({
      platform: 'twitter',
      offset: i * batchSize,
      limit: batchSize
    }, batchSize);

    // Process batch
    const analyzer = new PrevalenceAnalyzer(config, logger);
    const results = analyzer.analyze(posts);
    
    allResults.push(results);

    // Rate limiting: wait between batches
    if (i < totalBatches - 1) {
      await new Promise(resolve => setTimeout(resolve, 2000));
    }
  }

  // Aggregate results
  const aggregated = aggregateResults(allResults);
  return aggregated;
}

function aggregateResults(results) {
  // Combine multiple analysis results
  const totalPosts = results.reduce((sum, r) => sum + r.summary.totalPosts, 0);
  const totalPositives = results.reduce((sum, r) => 
    sum + (r.summary.overallPrevalence * r.summary.totalPosts), 0
  );

  return {
    totalPosts,
    aggregatedPrevalence: totalPositives / totalPosts,
    batchResults: results
  };
}
```

---

### Pattern 2: Continuous Monitoring

Set up continuous data collection:

```javascript
// SOPHRON-CER/examples/continuous-monitor.js
class ContinuousMonitor {
  constructor(config, logger) {
    this.config = config;
    this.logger = logger;
    this.collector = null;
    this.analyzer = null;
    this.isRunning = false;
  }

  async initialize() {
    this.collector = new MoltxCollector(this.config, this.logger);
    await this.collector.initialize();
    this.analyzer = new PrevalenceAnalyzer(this.config, this.logger);
  }

  async start(intervalMinutes = 60) {
    this.isRunning = true;
    this.logger.info(`Starting continuous monitoring (interval: ${intervalMinutes} minutes)`);

    while (this.isRunning) {
      try {
        await this.collectAndAnalyze();
        
        // Wait for next interval
        await new Promise(resolve => 
          setTimeout(resolve, intervalMinutes * 60 * 1000)
        );
      } catch (error) {
        this.logger.error('Error in monitoring cycle:', error);
        // Continue monitoring despite errors
        await new Promise(resolve => setTimeout(resolve, 60000)); // Wait 1 minute on error
      }
    }
  }

  async collectAndAnalyze() {
    const timestamp = new Date().toISOString();
    this.logger.info(`Collection cycle started at ${timestamp}`);

    // Fetch recent posts
    const posts = await this.collector.fetchPaginated({
      since: new Date(Date.now() - 60 * 60 * 1000).toISOString(), // Last hour
      platform: 'twitter',
      limit: 500
    }, 500);

    // Analyze
    const results = this.analyzer.analyze(posts);

    // Save results with timestamp
    const fs = require('fs').promises;
    const outputPath = `outputs/monitoring/results_${Date.now()}.json`;
    await fs.writeFile(outputPath, JSON.stringify({
      timestamp,
      results,
      sampleSize: posts.length
    }, null, 2));

    this.logger.info(`Cycle complete. Prevalence: ${(results.summary.overallPrevalence * 100).toFixed(2)}%`);

    // Check for alerts
    this.checkAlerts(results);
  }

  checkAlerts(results) {
    const threshold = 0.10; // 10% prevalence threshold
    
    if (results.summary.overallPrevalence > threshold) {
      this.logger.warn(`⚠️  ALERT: Prevalence (${(results.summary.overallPrevalence * 100).toFixed(2)}%) exceeds threshold (${threshold * 100}%)`);
      // Send notification, email, etc.
    }
  }

  stop() {
    this.isRunning = false;
    this.logger.info('Stopping continuous monitoring');
  }
}

// Usage
const monitor = new ContinuousMonitor(config, logger);
await monitor.initialize();
monitor.start(60); // Run every 60 minutes
```

---

### Pattern 3: Privacy-Preserving Analysis

Ensure privacy compliance:

```javascript
// SOPHRON-CER/examples/privacy-preserving.js
import { PiiDetector } from '../lib/utils/pii-detector.js';

async function privacyPreservingAnalysis() {
  const config = loadConfig({
    privacy: {
      enablePiiDetection: true,
      kAnonymity: 10,
      redactUserIds: true
    }
  });

  const logger = createLogger(config.logging);
  const collector = new MoltxCollector(config, logger);
  await collector.initialize();

  // Fetch posts
  const posts = await collector.fetchPaginated({
    platform: 'twitter',
    limit: 1000
  }, 1000);

  // Detect and redact PII
  const piiDetector = new PiiDetector(config, logger);
  const cleanPosts = posts.map(post => {
    const findings = piiDetector.scanObject(post);
    
    if (findings.length > 0) {
      logger.warn(`PII detected in post ${post.id}: ${findings.length} instances`);
      return piiDetector.redactObject(post);
    }
    
    return post;
  });

  // Ensure k-anonymity
  const blocks = enforceKAnonymity(cleanPosts, config.privacy.kAnonymity);

  // Analyze with privacy guarantees
  const analyzer = new PrevalenceAnalyzer(config, logger);
  const results = analyzer.analyze(cleanPosts, blocks);

  // Remove small groups to maintain k-anonymity
  results.blockAnalysis = results.blockAnalysis.filter(
    block => block.sampleSize >= config.privacy.kAnonymity
  );

  return results;
}

function enforceKAnonymity(posts, k) {
  // Group posts by sensitive attributes
  const groups = {};
  
  posts.forEach(post => {
    const key = `${post.user.location}_${post.user.verified}`;
    if (!groups[key]) groups[key] = [];
    groups[key].push(post);
  });

  // Return only groups meeting k-anonymity
  return Object.entries(groups)
    .filter(([_, posts]) => posts.length >= k)
    .map(([key, posts]) => ({
      id: key,
      posts: posts
    }));
}
```

---

## Troubleshooting

### Common Issues

#### Issue 1: Rate Limiting

```javascript
// Handle rate limiting gracefully
async function handleRateLimiting() {
  const collector = new MoltxCollector(config, logger);
  
  try {
    const posts = await collector.fetchPaginated({
      platform: 'twitter',
      limit: 10000
    }, 10000);
  } catch (error) {
    if (error.statusCode === 429) {
      const retryAfter = error.headers['retry-after'] || 60;
      logger.warn(`Rate limited. Waiting ${retryAfter} seconds...`);
      await new Promise(resolve => setTimeout(resolve, retryAfter * 1000));
      // Retry
      return handleRateLimiting();
    }
    throw error;
  }
}
```

#### Issue 2: Invalid Data

```javascript
// Validate and clean data
function validatePosts(posts) {
  return posts.filter(post => {
    // Required fields
    if (!post.id || !post.text || !post.created_at) {
      logger.warn(`Skipping invalid post: ${post.id}`);
      return false;
    }
    
    // Data quality checks
    if (post.text.length === 0) {
      logger.warn(`Skipping empty post: ${post.id}`);
      return false;
    }
    
    return true;
  });
}
```

#### Issue 3: Memory Issues with Large Datasets

```javascript
// Use streaming for large datasets
async function* streamPosts(collector, totalPosts) {
  const batchSize = 1000;
  let offset = 0;

  while (offset < totalPosts) {
    const batch = await collector.fetchPaginated({
      platform: 'twitter',
      offset: offset,
      limit: batchSize
    }, batchSize);

    yield batch;
    offset += batchSize;
  }
}

// Usage
for await (const batch of streamPosts(collector, 50000)) {
  // Process each batch independently
  const results = analyzer.analyze(batch);
  await saveBatchResults(results);
}
```

---

## Next Steps

1. **Explore Advanced Features**: Check `SOPHRON-CER/docs/ARXIV_RESEARCH_GUIDE.md` for research-backed methodologies
2. **Custom Collectors**: Implement custom data collectors for specific X.com endpoints
3. **Visualization**: Create dashboards using the HTML reports
4. **Integration**: Connect to monitoring systems and alerting platforms
5. **Scaling**: Deploy on cloud infrastructure for continuous monitoring

## Additional Resources

- [API Documentation](https://github.com/LadyElinor/SOPHRON-CER/blob/main/README.md)
- [Configuration Schema](https://github.com/LadyElinor/SOPHRON-CER/blob/main/config/schema.js)
- [Statistical Methods](https://github.com/LadyElinor/SOPHRON-CER/blob/main/lib/analyzers/statistical-analyzer.js)

---

**Note**: This guide assumes you have proper API access to X.com. Ensure you comply with X.com's Terms of Service and API usage policies when collecting data.
