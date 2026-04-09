# Performance Checklist

Pre-merge and pre-launch performance verification. Use alongside the main `performance-optimization` skill.

## Core Web Vitals

- [ ] LCP (Largest Contentful Paint) ≤ 2.5s
- [ ] INP (Interaction to Next Paint) ≤ 200ms
- [ ] CLS (Cumulative Layout Shift) ≤ 0.1
- [ ] TTFB (Time to First Byte) ≤ 800ms
- [ ] Lighthouse Performance score ≥ 90

## Bundle and Assets

- [ ] Initial JS bundle < 200KB gzipped
- [ ] Total CSS < 50KB gzipped
- [ ] Web fonts < 100KB total; `font-display: swap` set
- [ ] Above-the-fold images < 200KB each; appropriately sized
- [ ] Code splitting at route level (lazy loading non-critical routes)
- [ ] Tree-shaking confirmed (no dead code in production bundle)
- [ ] Source maps excluded from production deployment

## Images

- [ ] Modern formats used (WebP/AVIF with fallback)
- [ ] Explicit `width` and `height` set (prevents CLS)
- [ ] Above-the-fold images: `fetchpriority="high"`, no `loading="lazy"`
- [ ] Below-the-fold images: `loading="lazy"` and `decoding="async"`
- [ ] Responsive images with `srcset` and `sizes` for variable viewports
- [ ] No images wider than their display container

## Rendering

- [ ] No long tasks > 50ms on main thread (check Performance trace)
- [ ] No layout thrashing (read-then-write cycles on DOM geometry)
- [ ] CSS animations use `transform` and `opacity` only (compositor-friendly)
- [ ] `will-change` used sparingly and only on elements that actually animate
- [ ] React: no unnecessary re-renders (check React Profiler)
- [ ] React: `React.memo` applied to expensive pure components
- [ ] React: stable references for objects/arrays passed as props

## Data Fetching

- [ ] No N+1 query patterns (use joins, includes, or batch loading)
- [ ] All list endpoints paginated with a max page size
- [ ] No unbounded data fetching (`SELECT *` without `LIMIT`)
- [ ] Critical queries have covering indexes
- [ ] `EXPLAIN ANALYZE` run on new or modified queries
- [ ] Connection pool sized appropriately for expected concurrency

## Caching

- [ ] Static assets served with `Cache-Control: public, max-age=31536000, immutable`
- [ ] Content-hashed filenames for cache busting
- [ ] API responses cached where appropriate (`Cache-Control`, ETags, or application cache)
- [ ] CDN configured for static assets and (optionally) API edge caching
- [ ] No stale cache invalidation issues (test with cache-clearing flows)

## Network

- [ ] HTTP/2 or HTTP/3 enabled
- [ ] `dns-prefetch` and `preconnect` for critical third-party origins
- [ ] Third-party scripts deferred or async; non-critical ones lazy-loaded
- [ ] No render-blocking resources in the critical path
- [ ] API responses compressed (gzip/brotli)

## Backend

- [ ] No synchronous I/O in request handlers
- [ ] Timeouts set on all outbound HTTP calls and database queries
- [ ] Memory usage stable under load (no leaks in heap snapshots)
- [ ] CPU profiling shows no hotspots in business logic
- [ ] Background jobs offloaded from request cycle (queues, workers)

## Monitoring and Regression Prevention

- [ ] RUM (Real User Monitoring) tracking Core Web Vitals in production
- [ ] Performance budgets enforced in CI (`bundlesize`, `lhci`, or equivalent)
- [ ] Alerts configured for P95 latency and error rate regressions
- [ ] Before/after measurements documented for any optimization change

## Quick Commands

```bash
# Bundle analysis
npx vite-bundle-visualizer        # Vite
npx webpack-bundle-analyzer       # Webpack

# Lighthouse CI
npx lhci autorun

# Database query analysis
EXPLAIN ANALYZE SELECT ...;

# Node.js profiling
node --prof app.js
node --prof-process isolate-*.log > profile.txt
```

## Anti-Patterns to Flag

| Anti-Pattern | Quick Check |
|---|---|
| N+1 queries | Count SQL queries per API call in dev logs |
| Unbounded lists | Search for `findMany()` without `take`/`limit` |
| Blocking main thread | Check for synchronous file I/O or heavy computation in handlers |
| Missing pagination | Every list endpoint must accept `page`/`limit` params |
| Inline critical CSS missing | Check if LCP element depends on external CSS |
| Over-fetching | API returns fields the client never uses |
