# SOPHRON-CER: Detecting Lies, Bias & Misinformation on X.com

## Mission Critical: Truth in a Sea of Deception

This guide focuses on using CER-Telemetry v2.0 to identify, quantify, and track deception, implicit bias, and misinformation when your job depends on accurate information.

---

## Core Principles

### 1. Measure, Don't Assume
- Every claim is quantified with confidence intervals
- Statistical significance is required before conclusions
- Reproducibility through deterministic hashing

### 2. Detect Patterns of Deception
- Coordinated inauthentic behavior
- Bot networks and fake engagement
- Narrative manipulation
- Source credibility erosion

### 3. Track Bias Systematically
- Platform-level amplification bias
- Algorithmic recommendation bias
- Demographic representation bias
- Temporal bias (what gets memory-holed)

---

## Critical Use Cases

### Use Case 1: Fact-Checking at Scale

Verify claims being spread on X.com with statistical rigor:

```javascript
// SOPHRON-CER/examples/fact-check-pipeline.js
import { loadConfig } from '../config/schema.js';
import { createLogger } from '../lib/utils/logger.js';
import { MoltxCollector } from '../lib/collectors/moltx-collector.js';
import { PrevalenceAnalyzer } from '../lib/analyzers/prevalence-analyzer.js';
import { StatisticalAnalyzer } from '../lib/analyzers/statistical-analyzer.js';

class FactCheckPipeline {
  constructor(config, logger) {
    this.config = config;
    this.logger = logger;
    this.collector = null;
    this.analyzer = null;
    this.stats = null;
  }

  async initialize() {
    this.collector = new MoltxCollector(this.config, this.logger);
    await this.collector.initialize();
    this.analyzer = new PrevalenceAnalyzer(this.config, this.logger);
    this.stats = new StatisticalAnalyzer(this.config, this.logger);
  }

  /**
   * Analyze prevalence of a specific false claim
   * @param {string} claim - The claim to track
   * @param {Object} factCheck - Verification data
   * @returns {Object} Analysis results
   */
  async analyzeClaimSpread(claim, factCheck) {
    this.logger.info(`Analyzing claim: "${claim}"`);

    // Collect posts containing the claim
    const posts = await this.collector.fetchPaginated({
      keywords: this.extractKeywords(claim),
      platform: 'twitter',
      limit: 5000,
      includeMetrics: true
    }, 5000);

    // Classify posts by verification status
    const classified = posts.map(post => ({
      ...post,
      claimPresent: this.detectClaim(post, claim),
      claimStatus: factCheck.status, // 'false', 'misleading', 'unverified', 'true'
      verificationSource: factCheck.source,
      verificationDate: factCheck.date
    }));

    // Calculate spread metrics
    const withClaim = classified.filter(p => p.claimPresent);
    const totalImpressions = withClaim.reduce((sum, p) => sum + (p.impressions || 0), 0);
    const totalEngagement = withClaim.reduce((sum, p) => 
      sum + (p.likes || 0) + (p.retweets || 0) + (p.replies || 0), 0
    );

    // Analyze by account type
    const byAccountType = this.stratifyByAccountType(withClaim);

    // Temporal analysis - is it growing or declining?
    const temporalData = this.analyzeTemporalPattern(withClaim);
    const trendTest = this.stats.mannKendallTest(temporalData.map(d => d.count));

    // Network analysis - coordinated spreading?
    const networkMetrics = this.detectCoordination(withClaim);

    const results = {
      claim: claim,
      factCheck: factCheck,
      spread: {
        totalPosts: withClaim.length,
        totalImpressions: totalImpressions,
        totalEngagement: totalEngagement,
        prevalence: withClaim.length / posts.length,
        averageReach: totalImpressions / withClaim.length
      },
      byAccountType: byAccountType,
      temporal: {
        trend: trendTest.trend,
        significant: trendTest.significant,
        data: temporalData
      },
      coordination: networkMetrics,
      timestamp: new Date().toISOString()
    };

    // Alert if false claim is spreading
    if (factCheck.status === 'false' && trendTest.trend === 'increasing') {
      this.logger.warn(`⚠️  ALERT: False claim spreading with increasing trend`);
      this.logger.warn(`   Total reach: ${totalImpressions.toLocaleString()} impressions`);
    }

    return results;
  }

  /**
   * Compare claim spread before and after fact-check publication
   */
  async measureFactCheckImpact(claim, factCheckPublishDate) {
    const daysBefore = 7;
    const daysAfter = 7;

    // Period before fact-check
    const beforePosts = await this.collector.fetchPaginated({
      keywords: this.extractKeywords(claim),
      until: factCheckPublishDate.toISOString(),
      since: new Date(factCheckPublishDate - daysBefore * 24 * 60 * 60 * 1000).toISOString(),
      platform: 'twitter',
      limit: 2000
    }, 2000);

    // Period after fact-check
    const afterPosts = await this.collector.fetchPaginated({
      keywords: this.extractKeywords(claim),
      since: factCheckPublishDate.toISOString(),
      until: new Date(factCheckPublishDate.getTime() + daysAfter * 24 * 60 * 60 * 1000).toISOString(),
      platform: 'twitter',
      limit: 2000
    }, 2000);

    const beforeCount = beforePosts.filter(p => this.detectClaim(p, claim)).length;
    const afterCount = afterPosts.filter(p => this.detectClaim(p, claim)).length;

    // Statistical test
    const contingencyTable = [
      [beforeCount, beforePosts.length - beforeCount],
      [afterCount, afterPosts.length - afterCount]
    ];
    const chiSquare = this.stats.chiSquareTest(contingencyTable);

    const impact = {
      before: {
        posts: beforePosts.length,
        withClaim: beforeCount,
        prevalence: beforeCount / beforePosts.length
      },
      after: {
        posts: afterPosts.length,
        withClaim: afterCount,
        prevalence: afterCount / afterPosts.length
      },
      change: {
        absolute: (afterCount / afterPosts.length) - (beforeCount / beforePosts.length),
        relative: ((afterCount / afterPosts.length) / (beforeCount / beforePosts.length)) - 1,
        significant: chiSquare.significant,
        pValue: chiSquare.pValue
      }
    };

    // Effectiveness verdict
    if (impact.change.significant && impact.change.relative < -0.2) {
      this.logger.info(`✅ Fact-check was EFFECTIVE (${(impact.change.relative * 100).toFixed(1)}% reduction)`);
    } else if (impact.change.significant && impact.change.relative > 0.2) {
      this.logger.warn(`⚠️  Fact-check BACKFIRED (${(impact.change.relative * 100).toFixed(1)}% increase)`);
    } else {
      this.logger.info(`📊 Fact-check had NO SIGNIFICANT IMPACT`);
    }

    return impact;
  }

  // Helper methods
  extractKeywords(claim) {
    // Extract key terms from claim for search
    // In production: use NLP, entity extraction, etc.
    return claim.toLowerCase().split(' ')
      .filter(word => word.length > 4)
      .slice(0, 5);
  }

  detectClaim(post, claim) {
    // In production: use semantic similarity, NLP models
    const postText = post.text.toLowerCase();
    const claimText = claim.toLowerCase();
    
    // Simple keyword matching (replace with ML in production)
    const keywords = this.extractKeywords(claim);
    const matches = keywords.filter(kw => postText.includes(kw)).length;
    
    return matches >= Math.ceil(keywords.length * 0.6); // 60% keyword match
  }

  stratifyByAccountType(posts) {
    const verified = posts.filter(p => p.user.verified);
    const unverified = posts.filter(p => !p.user.verified);
    const highFollowers = posts.filter(p => p.user.followers_count > 10000);
    const mediumFollowers = posts.filter(p => p.user.followers_count > 1000 && p.user.followers_count <= 10000);
    const lowFollowers = posts.filter(p => p.user.followers_count <= 1000);

    return {
      verified: {
        count: verified.length,
        totalReach: verified.reduce((sum, p) => sum + (p.impressions || 0), 0)
      },
      unverified: {
        count: unverified.length,
        totalReach: unverified.reduce((sum, p) => sum + (p.impressions || 0), 0)
      },
      byFollowerCount: {
        high: { count: highFollowers.length, totalReach: highFollowers.reduce((sum, p) => sum + (p.impressions || 0), 0) },
        medium: { count: mediumFollowers.length, totalReach: mediumFollowers.reduce((sum, p) => sum + (p.impressions || 0), 0) },
        low: { count: lowFollowers.length, totalReach: lowFollowers.reduce((sum, p) => sum + (p.impressions || 0), 0) }
      }
    };
  }

  analyzeTemporalPattern(posts) {
    // Group by hour
    const hourly = {};
    posts.forEach(post => {
      const hour = new Date(post.created_at).getHours();
      if (!hourly[hour]) hourly[hour] = 0;
      hourly[hour]++;
    });

    return Object.entries(hourly)
      .map(([hour, count]) => ({ hour: parseInt(hour), count }))
      .sort((a, b) => a.hour - b.hour);
  }

  detectCoordination(posts) {
    // Simple coordination detection (enhance with graph analysis)
    const userPosts = {};
    const timestamps = [];

    posts.forEach(post => {
      const userId = post.user.id;
      if (!userPosts[userId]) userPosts[userId] = [];
      userPosts[userId].push(post);
      timestamps.push(new Date(post.created_at).getTime());
    });

    // Check for suspicious patterns
    const suspiciousUsers = Object.entries(userPosts)
      .filter(([_, posts]) => posts.length > 5) // Posted claim 5+ times
      .length;

    // Check for temporal clustering (many posts in short window)
    timestamps.sort((a, b) => a - b);
    let maxBurst = 0;
    const windowMs = 5 * 60 * 1000; // 5 minute window

    for (let i = 0; i < timestamps.length; i++) {
      let count = 1;
      for (let j = i + 1; j < timestamps.length; j++) {
        if (timestamps[j] - timestamps[i] <= windowMs) {
          count++;
        } else {
          break;
        }
      }
      maxBurst = Math.max(maxBurst, count);
    }

    return {
      suspiciousUsers: suspiciousUsers,
      maxBurstSize: maxBurst,
      coordinationScore: (suspiciousUsers * 0.5) + (maxBurst * 0.5), // Simple scoring
      likelyCoordinated: suspiciousUsers > 3 || maxBurst > 20
    };
  }
}

// Usage example
async function main() {
  const config = loadConfig();
  const logger = createLogger(config.logging);
  
  const pipeline = new FactCheckPipeline(config, logger);
  await pipeline.initialize();

  // Track a specific false claim
  const claim = "Vaccines cause autism in children";
  const factCheck = {
    status: 'false',
    source: 'CDC, WHO, Multiple peer-reviewed studies',
    date: new Date('2024-01-01')
  };

  const results = await pipeline.analyzeClaimSpread(claim, factCheck);
  
  console.log('\n=== Claim Analysis ===');
  console.log(`Claim: "${claim}"`);
  console.log(`Status: ${factCheck.status.toUpperCase()}`);
  console.log(`\nSpread Metrics:`);
  console.log(`  Posts: ${results.spread.totalPosts.toLocaleString()}`);
  console.log(`  Total Reach: ${results.spread.totalImpressions.toLocaleString()} impressions`);
  console.log(`  Engagement: ${results.spread.totalEngagement.toLocaleString()}`);
  console.log(`  Trend: ${results.temporal.trend}`);
  console.log(`  Coordination Detected: ${results.coordination.likelyCoordinated ? 'YES ⚠️' : 'NO'}`);

  // Measure fact-check impact
  const impact = await pipeline.measureFactCheckImpact(claim, factCheck.date);
  
  console.log('\n=== Fact-Check Impact ===');
  console.log(`Before: ${(impact.before.prevalence * 100).toFixed(2)}%`);
  console.log(`After: ${(impact.after.prevalence * 100).toFixed(2)}%`);
  console.log(`Change: ${(impact.change.relative * 100).toFixed(1)}%`);
  console.log(`Significant: ${impact.change.significant ? 'YES' : 'NO'}`);
}

main().catch(console.error);
```

---

### Use Case 2: Bot Detection & Inauthentic Behavior

Identify and quantify bot networks and coordinated inauthentic behavior:

```javascript
// SOPHRON-CER/examples/bot-detection.js
class BotDetector {
  constructor(config, logger) {
    this.config = config;
    this.logger = logger;
    this.collector = null;
  }

  async initialize() {
    this.collector = new MoltxCollector(this.config, this.logger);
    await this.collector.initialize();
  }

  /**
   * Detect bot-like behavior patterns
   */
  async detectBots(topic, sampleSize = 5000) {
    this.logger.info(`Detecting bots discussing: ${topic}`);

    const posts = await this.collector.fetchPaginated({
      keywords: [topic],
      platform: 'twitter',
      limit: sampleSize,
      includeMetrics: true,
      includeUserHistory: true // Get user's posting history
    }, sampleSize);

    const users = this.extractUniqueUsers(posts);
    const suspiciousUsers = [];

    for (const user of users) {
      const userPosts = posts.filter(p => p.user.id === user.id);
      const score = this.calculateBotScore(user, userPosts);

      if (score.totalScore > 0.7) { // 70% confidence threshold
        suspiciousUsers.push({
          ...user,
          botScore: score.totalScore,
          reasons: score.reasons,
          postCount: userPosts.length
        });
      }
    }

    // Calculate bot prevalence
    const botPrevalence = suspiciousUsers.length / users.length;
    const botPostPrevalence = suspiciousUsers.reduce((sum, u) => sum + u.postCount, 0) / posts.length;

    // Network analysis - find clusters
    const clusters = this.findBotClusters(suspiciousUsers, posts);

    const results = {
      topic: topic,
      totalUsers: users.length,
      totalPosts: posts.length,
      suspiciousUsers: suspiciousUsers.length,
      botPrevalence: {
        byAccount: botPrevalence,
        byPost: botPostPrevalence
      },
      clusters: clusters,
      topBots: suspiciousUsers.slice(0, 10).map(u => ({
        username: u.username,
        score: u.botScore,
        posts: u.postCount,
        reasons: u.reasons
      }))
    };

    this.logger.warn(`⚠️  Bot Detection Results:`);
    this.logger.warn(`   ${suspiciousUsers.length}/${users.length} suspicious accounts (${(botPrevalence * 100).toFixed(1)}%)`);
    this.logger.warn(`   ${(botPostPrevalence * 100).toFixed(1)}% of posts from likely bots`);

    return results;
  }

  calculateBotScore(user, userPosts) {
    const reasons = [];
    let score = 0;

    // Check 1: Account age vs activity
    const accountAge = Date.now() - new Date(user.created_at).getTime();
    const daysOld = accountAge / (24 * 60 * 60 * 1000);
    const postsPerDay = userPosts.length / Math.max(daysOld, 1);

    if (postsPerDay > 50) {
      score += 0.3;
      reasons.push(`High frequency: ${postsPerDay.toFixed(0)} posts/day`);
    }

    // Check 2: Default profile image
    if (user.profile_image_url?.includes('default_profile')) {
      score += 0.2;
      reasons.push('Default profile image');
    }

    // Check 3: Username pattern (random characters)
    const randomPattern = /^[a-zA-Z]+[0-9]{8,}$/; // name followed by 8+ digits
    if (randomPattern.test(user.username)) {
      score += 0.2;
      reasons.push('Random username pattern');
    }

    // Check 4: Low follower/following ratio
    const ratio = user.followers_count / Math.max(user.following_count, 1);
    if (ratio < 0.1 && user.following_count > 100) {
      score += 0.15;
      reasons.push(`Low follower ratio: ${ratio.toFixed(2)}`);
    }

    // Check 5: Repetitive content
    const uniqueTexts = new Set(userPosts.map(p => p.text.toLowerCase().trim())).size;
    const repetitionRatio = uniqueTexts / userPosts.length;
    if (repetitionRatio < 0.3 && userPosts.length > 5) {
      score += 0.25;
      reasons.push(`Repetitive content: ${(repetitionRatio * 100).toFixed(0)}% unique`);
    }

    // Check 6: Temporal clustering (all posts in short bursts)
    const timestamps = userPosts.map(p => new Date(p.created_at).getTime()).sort();
    let inBursts = 0;
    const burstWindow = 60 * 1000; // 1 minute

    for (let i = 1; i < timestamps.length; i++) {
      if (timestamps[i] - timestamps[i-1] < burstWindow) {
        inBursts++;
      }
    }

    if (inBursts / userPosts.length > 0.7) {
      score += 0.2;
      reasons.push('Clustered posting pattern');
    }

    return {
      totalScore: Math.min(score, 1.0), // Cap at 1.0
      reasons: reasons
    };
  }

  extractUniqueUsers(posts) {
    const userMap = new Map();
    posts.forEach(post => {
      if (!userMap.has(post.user.id)) {
        userMap.set(post.user.id, post.user);
      }
    });
    return Array.from(userMap.values());
  }

  findBotClusters(suspiciousUsers, posts) {
    // Simple clustering based on timing and content similarity
    const clusters = [];
    const processed = new Set();

    suspiciousUsers.forEach(user => {
      if (processed.has(user.id)) return;

      const userPosts = posts.filter(p => p.user.id === user.id);
      const cluster = [user];
      processed.add(user.id);

      // Find similar users
      suspiciousUsers.forEach(otherUser => {
        if (processed.has(otherUser.id)) return;

        const otherPosts = posts.filter(p => p.user.id === otherUser.id);
        
        // Check similarity
        const similarity = this.calculateSimilarity(userPosts, otherPosts);
        
        if (similarity > 0.7) {
          cluster.push(otherUser);
          processed.add(otherUser.id);
        }
      });

      if (cluster.length > 1) {
        clusters.push({
          size: cluster.length,
          users: cluster.map(u => u.username),
          totalPosts: cluster.reduce((sum, u) => 
            sum + posts.filter(p => p.user.id === u.id).length, 0
          )
        });
      }
    });

    return clusters.sort((a, b) => b.size - a.size);
  }

  calculateSimilarity(posts1, posts2) {
    // Simple text similarity (enhance with embeddings in production)
    const texts1 = posts1.map(p => p.text.toLowerCase());
    const texts2 = posts2.map(p => p.text.toLowerCase());

    let matches = 0;
    texts1.forEach(t1 => {
      texts2.forEach(t2 => {
        if (t1 === t2) matches++;
      });
    });

    return matches / Math.max(texts1.length, texts2.length);
  }
}

// Usage
const detector = new BotDetector(config, logger);
await detector.initialize();

const results = await detector.detectBots('#election2024', 10000);

console.log('\n=== Bot Detection Report ===');
console.log(`Topic: ${results.topic}`);
console.log(`Bot Prevalence: ${(results.botPrevalence.byAccount * 100).toFixed(1)}% of accounts`);
console.log(`Bot Posts: ${(results.botPrevalence.byPost * 100).toFixed(1)}% of posts`);
console.log(`\nLargest Clusters:`);
results.clusters.slice(0, 5).forEach((cluster, i) => {
  console.log(`  ${i+1}. ${cluster.size} accounts, ${cluster.totalPosts} posts`);
});
```

---

### Use Case 3: Source Credibility Tracking

Track which sources are being cited and their credibility distribution:

```javascript
// SOPHRON-CER/examples/source-credibility.js
class SourceCredibilityTracker {
  constructor(config, logger, credibilityDB) {
    this.config = config;
    this.logger = logger;
    this.collector = null;
    this.credibilityDB = credibilityDB; // Database of source credibility ratings
  }

  async initialize() {
    this.collector = new MoltxCollector(this.config, this.logger);
    await this.collector.initialize();
  }

  /**
   * Analyze what sources are being shared and their credibility
   */
  async analyzeSourceDistribution(topic, timeWindow) {
    this.logger.info(`Analyzing source credibility for: ${topic}`);

    const posts = await this.collector.fetchPaginated({
      keywords: [topic],
      platform: 'twitter',
      since: new Date(Date.now() - timeWindow).toISOString(),
      limit: 10000,
      includeUrls: true
    }, 10000);

    // Extract all URLs
    const urlData = [];
    posts.forEach(post => {
      if (post.urls && post.urls.length > 0) {
        post.urls.forEach(url => {
          urlData.push({
            url: url,
            post: post,
            domain: this.extractDomain(url)
          });
        });
      }
    });

    // Count by domain
    const domainCounts = {};
    urlData.forEach(item => {
      if (!domainCounts[item.domain]) {
        domainCounts[item.domain] = {
          count: 0,
          posts: [],
          totalReach: 0
        };
      }
      domainCounts[item.domain].count++;
      domainCounts[item.domain].posts.push(item.post);
      domainCounts[item.domain].totalReach += (item.post.impressions || 0);
    });

    // Rate each domain
    const ratedDomains = Object.entries(domainCounts).map(([domain, data]) => {
      const rating = this.credibilityDB.getRating(domain);
      return {
        domain: domain,
        count: data.count,
        totalReach: data.totalReach,
        credibility: rating.score,
        category: rating.category, // 'high', 'medium', 'low', 'unreliable', 'unknown'
        bias: rating.bias, // 'left', 'center', 'right', 'unknown'
        factualReporting: rating.factualReporting // 'high', 'mostly-factual', 'mixed', 'low'
      };
    });

    // Calculate distributions
    const totalShares = ratedDomains.reduce((sum, d) => sum + d.count, 0);
    const totalReach = ratedDomains.reduce((sum, d) => sum + d.totalReach, 0);

    const byCredibility = this.groupBy(ratedDomains, 'category');
    const byBias = this.groupBy(ratedDomains, 'bias');
    const byFactual = this.groupBy(ratedDomains, 'factualReporting');

    const results = {
      topic: topic,
      analysis: {
        totalPosts: posts.length,
        postsWithUrls: posts.filter(p => p.urls && p.urls.length > 0).length,
        totalShares: totalShares,
        totalReach: totalReach,
        uniqueDomains: Object.keys(domainCounts).length
      },
      credibilityDistribution: this.calculateDistribution(byCredibility, totalShares, totalReach),
      biasDistribution: this.calculateDistribution(byBias, totalShares, totalReach),
      factualDistribution: this.calculateDistribution(byFactual, totalShares, totalReach),
      topSources: ratedDomains.sort((a, b) => b.count - a.count).slice(0, 20),
      unreliableSources: ratedDomains.filter(d => d.category === 'unreliable').sort((a, b) => b.totalReach - a.totalReach),
      unknownSources: ratedDomains.filter(d => d.category === 'unknown').sort((a, b) => b.count - a.count).slice(0, 10)
    };

    // Alert on high unreliable content
    const unreliableShare = results.credibilityDistribution.unreliable?.shareOfTotal || 0;
    if (unreliableShare > 0.15) {
      this.logger.warn(`⚠️  HIGH UNRELIABLE SOURCE USAGE: ${(unreliableShare * 100).toFixed(1)}%`);
    }

    return results;
  }

  extractDomain(url) {
    try {
      const parsed = new URL(url);
      return parsed.hostname.replace('www.', '');
    } catch {
      return 'unknown';
    }
  }

  groupBy(items, field) {
    const groups = {};
    items.forEach(item => {
      const key = item[field] || 'unknown';
      if (!groups[key]) groups[key] = [];
      groups[key].push(item);
    });
    return groups;
  }

  calculateDistribution(groups, totalShares, totalReach) {
    const dist = {};
    Object.entries(groups).forEach(([key, items]) => {
      const shares = items.reduce((sum, item) => sum + item.count, 0);
      const reach = items.reduce((sum, item) => sum + item.totalReach, 0);
      
      dist[key] = {
        count: items.length,
        shares: shares,
        shareOfTotal: shares / totalShares,
        reach: reach,
        reachOfTotal: reach / totalReach,
        avgReach: reach / shares
      };
    });
    return dist;
  }
}

// Credibility database (in production, use MediaBias/FactCheck.org API or similar)
class CredibilityDatabase {
  constructor() {
    this.ratings = {
      // High credibility
      'apnews.com': { score: 0.95, category: 'high', bias: 'center', factualReporting: 'high' },
      'reuters.com': { score: 0.95, category: 'high', bias: 'center', factualReporting: 'high' },
      'bbc.com': { score: 0.90, category: 'high', bias: 'center', factualReporting: 'high' },
      'npr.org': { score: 0.88, category: 'high', bias: 'center', factualReporting: 'high' },
      
      // Medium credibility
      'cnn.com': { score: 0.70, category: 'medium', bias: 'left', factualReporting: 'mostly-factual' },
      'foxnews.com': { score: 0.65, category: 'medium', bias: 'right', factualReporting: 'mixed' },
      
      // Low credibility
      'infowars.com': { score: 0.15, category: 'unreliable', bias: 'right', factualReporting: 'low' },
      'naturalnews.com': { score: 0.10, category: 'unreliable', bias: 'right', factualReporting: 'low' },
      
      // Add more as needed
    };
  }

  getRating(domain) {
    return this.ratings[domain] || { 
      score: 0.5, 
      category: 'unknown', 
      bias: 'unknown', 
      factualReporting: 'unknown' 
    };
  }
}

// Usage
const credibilityDB = new CredibilityDatabase();
const tracker = new SourceCredibilityTracker(config, logger, credibilityDB);
await tracker.initialize();

const results = await tracker.analyzeSourceDistribution(
  '#climatechange',
  7 * 24 * 60 * 60 * 1000 // 7 days
);

console.log('\n=== Source Credibility Analysis ===');
console.log(`\nCredibility Distribution:`);
Object.entries(results.credibilityDistribution).forEach(([category, data]) => {
  console.log(`  ${category}: ${(data.shareOfTotal * 100).toFixed(1)}% of shares, ${(data.reachOfTotal * 100).toFixed(1)}% of reach`);
});

console.log(`\nTop Unreliable Sources:`);
results.unreliableSources.slice(0, 5).forEach((source, i) => {
  console.log(`  ${i+1}. ${source.domain}: ${source.count} shares, ${source.totalReach.toLocaleString()} reach`);
});
```

---

## Critical Implementation Notes

### 1. Ground Truth Required

The system can measure and track, but YOU must provide ground truth:

- **Fact-check data**: Integrate with FactCheck.org, Snopes, PolitiFact APIs
- **Credibility ratings**: Use MediaBias/FactCheck.org or build your own
- **Classification models**: Train or use existing models for content classification

### 2. Statistical Rigor

Always include:
- Confidence intervals on all prevalence estimates
- Effect sizes for comparisons
- Multiple testing correction when doing many comparisons
- Clear documentation of assumptions

### 3. Privacy & Ethics

- Never doxx individuals
- Use k-anonymity for small groups
- Redact PII automatically
- Focus on patterns, not individuals

### 4. Reproducibility

- Hash all configurations
- Version all code
- Archive all data
- Document all manual classifications

---

## Production Deployment

### Real-Time Monitoring Dashboard

```javascript
// SOPHRON-CER/examples/monitoring-dashboard.js
class TruthMonitoringDashboard {
  async monitorInRealTime(topics, alertThresholds) {
    const monitors = topics.map(topic => ({
      topic: topic,
      factChecker: new FactCheckPipeline(config, logger),
      botDetector: new BotDetector(config, logger),
      sourceTracker: new SourceCredibilityTracker(config, logger, credibilityDB)
    }));

    // Initialize all
    await Promise.all(monitors.map(m => 
      Promise.all([
        m.factChecker.initialize(),
        m.botDetector.initialize(),
        m.sourceTracker.initialize()
      ])
    ));

    // Run continuous monitoring
    setInterval(async () => {
      for (const monitor of monitors) {
        try {
          // Check for misinformation
          const claims = await this.detectActiveClaims(monitor.topic);
          for (const claim of claims) {
            const analysis = await monitor.factChecker.analyzeClaimSpread(
              claim.text,
              claim.factCheck
            );
            
            if (analysis.spread.totalReach > alertThresholds.reachThreshold &&
                analysis.factCheck.status === 'false') {
              this.sendAlert({
                type: 'MISINFORMATION_SPREAD',
                topic: monitor.topic,
                claim: claim.text,
                reach: analysis.spread.totalReach
              });
            }
          }

          // Check for bot activity
          const botResults = await monitor.botDetector.detectBots(monitor.topic);
          if (botResults.botPrevalence.byPost > alertThresholds.botThreshold) {
            this.sendAlert({
              type: 'BOT_ACTIVITY_HIGH',
              topic: monitor.topic,
              prevalence: botResults.botPrevalence.byPost
            });
          }

          // Check source credibility
          const sourceResults = await monitor.sourceTracker.analyzeSourceDistribution(
            monitor.topic,
            60 * 60 * 1000 // Last hour
          );
          
          const unreliableShare = sourceResults.credibilityDistribution.unreliable?.shareOfTotal || 0;
          if (unreliableShare > alertThresholds.unreliableThreshold) {
            this.sendAlert({
              type: 'UNRELIABLE_SOURCES_HIGH',
              topic: monitor.topic,
              unreliableShare: unreliableShare
            });
          }

        } catch (error) {
          logger.error(`Error monitoring ${monitor.topic}:`, error);
        }
      }
    }, 5 * 60 * 1000); // Every 5 minutes
  }

  async detectActiveClaims(topic) {
    // Implement claim detection logic
    // Could use trending phrases, fact-check API queries, etc.
    return [];
  }

  sendAlert(alert) {
    // Send to Slack, email, PagerDuty, etc.
    logger.warn(`🚨 ALERT: ${alert.type} - ${JSON.stringify(alert)}`);
  }
}
```

---

## Bottom Line

This system gives you:

1. **Quantified Truth**: Not opinions, but measured prevalence with confidence intervals
2. **Early Warning**: Detect coordinated lies before they spread
3. **Source Accountability**: Track who's spreading what
4. **Reproducible Results**: Same inputs = same outputs, always

But remember: **The system measures. You decide what's true.** Feed it good ground truth data, and it will help you track deception at scale.
