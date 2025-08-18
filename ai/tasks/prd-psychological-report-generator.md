# PRD: Psychological Test Report Generator (Mindframe)

## Introduction/Overview

Mindframe is a webhook-triggered service that transforms psychological test results into professional, ready-to-read PDF reports with engaging visuals and customized content. The system receives webhook requests from n8n (after users complete psychological tests), fetches test data from MongoDB, generates branded PDF reports with score-based interpretations, and stores them in Google Drive while saving webview links back to the database.

The system includes a Content Management System (CMS) for CRUD operations on test interpretations, allowing internal administrators to manage how test scores are interpreted and presented in the generated reports.

**Problem Solved:** Eliminates manual report generation and provides scalable, automated PDF report creation for psychological test results with consistent branding and professional presentation.

## Goals

1. **Automated Report Generation**: Generate professional PDF reports automatically upon webhook trigger from n8n
2. **Scalable Processing**: Handle up to 100 daily report generations with 10-minute SLA through asynchronous job processing
3. **Content Management**: Provide internal CMS for managing test interpretations and product configurations
4. **Secure Storage**: Store generated PDFs in Google Drive with restricted access and maintain links in MongoDB
5. **System Reliability**: Achieve 99% successful report generation rate with proper error handling and retry mechanisms

## User Stories

**As an n8n automation system**, I want to trigger report generation via webhook so that completed psychological test results are automatically converted to professional PDFs.

**As an internal administrator**, I want to manage test interpretations through a CMS so that I can update how scores are interpreted and presented in reports without requiring code changes.

**As an end customer**, I want to receive a professional PDF report of my psychological test results so that I can easily understand and share my assessment outcomes.

**As a system operator**, I want monitoring and error handling so that I can ensure reliable report generation and quickly address any issues.

## Functional Requirements

### Core Webhook Processing
1. The system must accept webhook requests from n8n with shared secret header authentication
2. The system must extract the "code" identifier from webhook payload to fetch user data
3. The system must validate that all required tests for a product are completed before generating reports
4. The system must respond with 200 OK immediately and process reports asynchronously
5. The system must provide post-completion callback to n8n with the generated PDF link

### Data Management
6. The system must connect to two separate MongoDB databases: one for fetching n8n-processed test data and one for storing Mindframe-specific data
7. The system must fetch user data, test results, and product configurations using the "code" identifier
8. The system must store generated PDF metadata including Google Drive webview links in the Mindframe database
9. The system must handle user-product entries where the same user can have multiple entries for the same or different products

### PDF Report Generation
10. The system must generate A4 portrait PDF reports in Bahasa Indonesia
11. The system must include personalized cover page, test overviews, score breakdowns, interpretation narratives, recommendations, disclaimers, and company CTA content
12. The system must apply single consistent branding across all products
13. The system must include infographics/icons as visual elements
14. The system must handle content-driven page length without artificial limits

### Content Management System
15. The system must provide web-based CMS for internal administrators only
16. The system must allow CRUD operations on score-based interpretations per test
17. The system must allow management of test definitions (scales, subscales, dimensions)
18. The system must support score range mapping (e.g., 0–20: Low, 21–40: Moderate) and multi-dimensional rules
19. The system must make interpretations globally reusable across products
20. The system must prevent overlapping score ranges and ensure complete coverage

### Google Drive Integration
21. The system must use service account authentication with shared Google Drive
22. The system must organize PDFs in per-product folders
23. The system must generate webview links restricted to specific user emails stored in MongoDB
24. The system must use naming convention: {productId}_{userId}_{timestamp}.pdf
25. The system must keep historical versions of reports

### Error Handling & Reliability
26. The system must implement job queue for asynchronous processing
27. The system must retry transient failures for Drive and database operations
28. The system must use dead-letter queue for failed jobs
29. The system must send notifications (Slack/Email/Webhook) on processing failures
30. The system must provide manual re-run capability through admin interface

## Non-Goals (Out of Scope)

1. **Scoring Logic**: Test scoring and categorization is handled by n8n; Mindframe focuses on category-based interpretation only
2. **User Authentication for End Users**: End users access reports via restricted Google Drive links, not through Mindframe login
3. **Email Notifications**: Handled by n8n workflow, not Mindframe responsibility
4. **Real-time Processing**: System uses asynchronous processing with 10-minute SLA
5. **Multi-language Support**: Initially supports Bahasa Indonesia only
6. **PDF Accessibility Features**: Alt text and high-contrast mode not required in initial version
7. **Custom Branding per Client**: Single brand application across all products

## Design Considerations

### Architecture
- **Backend**: Python-based service (recommended for weasyprint PDF generation)
- **Database**: Dual MongoDB setup - read from n8n database, write to Mindframe database
- **Storage**: Google Drive with service account authentication
- **Deployment**: AWS with Dokploy PaaS for CI/CD automation
- **Security**: Google Secret Manager for service account credentials

### PDF Generation
- **Library**: Weasyprint (Python) for superior PDF rendering
- **Templates**: HTML/CSS templates (hardcoded for initial products)
- **Styling**: Consistent branding with infographic elements
- **Format**: A4 portrait orientation

### CMS Interface
- **Framework**: Web-based admin interface
- **Authentication**: Internal admin access only
- **Validation**: Prevent score range overlaps and ensure complete coverage
- **Data Model**: Support for tests, interpretations, and product configurations

## Technical Considerations

### Database Schema
**N8N Database (Read-only)**:
- User-product entries with "code" identifier
- Test results with scores and categories
- User PII (name, email)

**Mindframe Database**:
- `tests`: Test definitions, scales, subscales
- `interpretations`: Score range to text mappings  
- `products`: Product configurations and test inclusions
- `pdfReports`: Generated report metadata and Drive links
- `jobQueue`: Async processing queue management

### Integration Points
- **n8n Webhook**: Shared secret authentication
- **MongoDB**: Dual database connectivity
- **Google Drive API**: Service account with restricted sharing
- **Google Secret Manager**: Credential management

### Performance & Scalability
- **Queue System**: Redis or database-backed job queue
- **Concurrency**: Handle multiple simultaneous report generations
- **Caching**: Cache interpretation data and product configurations
- **Monitoring**: Log processing times and success rates

## Success Metrics

1. **Reliability**: 99% successful report generations per day
2. **Support Reduction**: <2% support tickets related to report content issues after launch  
3. **Performance**: Report generation P95 under 10 minutes
4. **System Uptime**: Maintain service availability during peak request periods through proper queue management

## Open Questions

1. **Database Migration**: Do we need to migrate existing user-product entries to the new Mindframe database structure, or maintain the current dual-database approach?
   - *Ans*: Maintain the current dual-database approach. Duplicate user-product entries in the Mindframe database for easier migration everytime job is run.
2. **Template Versioning**: How should we handle template updates for existing products without affecting historical reports?
   - *Ans*: Maintain a separate versioning system for templates. Each product can have its own template version, and updates to a template should not affect existing reports.
   - *Ans*: Use a template engine (e.g., Jinja2) to render PDFs. This allows for easy updates to templates without breaking existing reports.
   - *Ans*: Store template files in a version-controlled repository (e.g., Git) to track changes and enable easy rollbacks.
3. **Compliance**: What specific Indonesian data protection regulations need to be considered for storing PII and psychological test results?
   - *Ans*: For now, skip this.
4. **Monitoring Stack**: Which specific logging/metrics/tracing tools should be integrated with the AWS/Dokploy deployment?
   - *Ans*: Phase 0 (now):
      - Logging: Structured JSON logs to stdout (one line per event) with fields: time, level, service, env, request_id/trace_id, code, product_id, job_id, stage, status, duration_ms, error_code. Dokploy captures container stdout; route to AWS CloudWatch at deploy time if available.
      - Correlation: Generate and propagate request_id/trace_id from webhook → job → callback; include in all logs.
      - Health: Expose /health and /ready endpoints for uptime checks.
      - No-op monitoring interface: Provide a Monitoring abstraction (span, counter, gauge) as no-op; wire real providers later without touching business logic.
      - Privacy: Never log PII (names/emails/answers); mask secrets/headers.
   - *Ans*: Phase 2 (later, after core; choose one and plug into the no-op interface):
      - Option A (AWS-native): CloudWatch Logs, CloudWatch Metrics/Alarms (via OpenTelemetry Collector), AWS X-Ray for traces.
      - Option B (SaaS-first): Sentry (errors + performance), Grafana Cloud (Prometheus metrics + Loki logs + Tempo traces) via OpenTelemetry.
      - Initial dashboards/alerts: pipeline P95 < 10m, failure rate < 1%, queue backlog/DLQ, Drive 429/403 spikes, Mongo latency, callback failures.
5. **CMS Access Control**: Should the CMS have role-based permissions (admin vs content editor) even though initially only internal administrators will use it?
   - *Ans*: Yes, but initially, only internal administrators will have access.
6. **Queue Technology**: Should we use Redis, database-backed queues, or cloud-native solutions (AWS SQS) for job processing?
   - *Ans*: Use Redis for job queueing.
