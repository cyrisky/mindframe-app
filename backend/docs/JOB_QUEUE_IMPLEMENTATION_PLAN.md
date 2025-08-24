# Job Queue Implementation Plan
## Background Processing for PDF Generation

---

## 📋 Executive Summary

**Problem**: Our current PDF generation system processes requests immediately, which can overwhelm server resources when multiple reports are requested simultaneously.

**Solution**: Implement a job queue system that accepts all requests instantly but processes them in a controlled, organized manner.

**Business Impact**: 
- ✅ **Zero request rejections** - All n8n requests are accepted
- ✅ **Predictable performance** - Controlled resource usage
- ✅ **Better user experience** - Clear progress tracking
- ✅ **Scalable architecture** - Easy to add more processing power

---

## 🎯 What is a Job Queue?

### Simple Analogy
Think of a job queue like a **restaurant kitchen**:
- **Current system**: All orders must be cooked immediately (causes chaos during rush hour)
- **Job queue system**: Orders are taken instantly, queued up, and cooked by available chefs in order

### Technical Benefits
| Aspect               | Before (Synchronous)        | After (Job Queue)                 |
| -------------------- | --------------------------- | --------------------------------- |
| **Request Handling** | "Please wait 30 seconds..." | "Request received! Processing..." |
| **Resource Usage**   | Unpredictable spikes        | Controlled, steady usage          |
| **Failure Recovery** | Request fails completely    | Automatic retries                 |
| **Monitoring**       | Limited visibility          | Full job tracking                 |
| **Scalability**      | Hard to scale               | Easy to add workers               |

---

## 🏗️ Architecture Overview

### Current Flow (Synchronous)
```
n8n → API Request → [Wait 30s] → PDF Response
                     ↑
                Server busy/crashes = Request fails
```

### New Flow (Asynchronous with Queue & Webhook)
```
n8n → API Request → Queue Job → Immediate Response (Job ID)
                       ↓
                  Worker Process → Generate PDF → Store Result
                       ↓
                  Worker → HTTP Request to n8n → n8n Downloads PDF
```

### Key Components

1. **Job Queue** (Redis-based)
   - Stores pending PDF generation requests
   - Manages job priorities and scheduling
   - Provides persistence (survives server restarts)

2. **Worker Processes**
   - Background processes that generate PDFs
   - Configurable number (e.g., 3 concurrent workers)
   - Isolated from web requests
   - **Webhook callbacks** to n8n on completion/failure

3. **Job Status API** (Optional)
   - Allows checking job progress (backward compatibility)
   - Provides estimated completion times
   - Returns download links when complete

4. **n8n Webhook Endpoints**
   - **Success webhook**: Receives completion notifications
   - **Failure webhook**: Receives error notifications
   - **Database integration**: Retrieves PDF links using jobId

---

## 🔧 Implementation Plan

### Phase 1: Core Infrastructure (Week 1-2)

#### 1.1 Choose Job Queue Technology
**Recommendation: RQ (Redis Queue)**
- ✅ **Simple**: Easy to implement and maintain
- ✅ **Python-native**: Integrates seamlessly with our Flask backend
- ✅ **Reliable**: Battle-tested in production environments
- ✅ **Lightweight**: Minimal overhead compared to Celery

#### 1.2 Install Dependencies
```bash
# Add to requirements.txt
rq>=1.15.1           # Latest stable RQ version
redis>=8.0.0          # Latest Redis Python client (supports Redis 8.0+)
rq-dashboard>=0.6.1   # Optional: Web UI for monitoring
```

**Version Notes:**
- **Redis**: Latest redis-py (8.x) supports Redis 8.0+ with enhanced performance and security features
- **RQ**: Version 1.15+ includes improved error handling and job callbacks
- **RQ Dashboard**: Provides web interface for monitoring job queues

#### 1.3 Redis Configuration
- Use existing Redis instance (already configured for rate limiting)
- Add job queue database (separate from cache)
- Configure persistence for job reliability

#### 1.4 Database Schema for PDF Results
```sql
-- Table to store PDF generation results
CREATE TABLE pdf_job_results (
    job_id VARCHAR(255) PRIMARY KEY,
    code VARCHAR(255) NOT NULL,
    product_id VARCHAR(255) NOT NULL,
    google_drive_link TEXT,
    status ENUM('queued', 'processing', 'completed', 'failed') DEFAULT 'queued',
    error_message TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    completed_at TIMESTAMP NULL,
    retry_count INT DEFAULT 0,
    INDEX idx_code_product (code, product_id),
    INDEX idx_status (status),
    INDEX idx_created_at (created_at)
);
```

### Phase 2: Job Queue Service (Week 2-3)

#### 2.1 Create Job Queue Service
```python
# src/services/job_queue_service.py
from rq import Queue
from redis import Redis

class JobQueueService:
    def __init__(self):
        self.redis_conn = Redis(host='localhost', port=6379, db=1)
        self.queue = Queue('pdf_generation', connection=self.redis_conn)
    
    def enqueue_pdf_generation(self, code, product_id, priority='normal', callback=None):
        """Enqueue PDF generation job with webhook callback"""
        job = self.queue.enqueue(
            'workers.pdf_worker.generate_pdf_job',
            code, product_id, callback,
            job_timeout='10m',
            retry=3,
            job_id=f"pdf_{code}_{int(time.time())}"
        )
        return job.id
    
    def get_job_status(self, job_id):
        """Get current job status - kept for backward compatibility"""
        job = self.queue.fetch_job(job_id)
        if not job:
            return None
        return {
            'job_id': job_id,
            'status': job.get_status(),
            'created_at': job.created_at,
            'started_at': job.started_at,
            'ended_at': job.ended_at
        }
    
    def get_job_result(self, job_id):
        """Get job result including Google Drive link"""
        # Query database for stored result
        return get_pdf_result_from_db(job_id)
    
    def cancel_job(self, job_id):
        """Cancel pending job"""
        job = self.queue.fetch_job(job_id)
        if job and job.get_status() == 'queued':
            job.cancel()
            return True
        return False
```

#### 2.2 Worker Implementation
```python
# workers/pdf_worker.py
import requests
from rq import get_current_job

def generate_pdf_job(code, product_id, callback_url=None):
    job = get_current_job()
    
    try:
        # Existing PDF generation logic
        pdf_result = generate_pdf(code, product_id)
        
        # Upload to Google Drive
        drive_link = upload_to_google_drive(pdf_result)
        
        # Store result in temporary database
        store_pdf_result(job.id, drive_link)
        
        # Store permanently in workflow.psikotes_v2 collection
        db.workflow.psikotes_v2.update_one(
            {'code': code, 'product_id': product_id},
            {'$set': {
                'pdf_generation': {
                    'status': 'completed',
                    'google_drive_link': drive_link,
                    'job_id': job.id,
                    'completed_at': datetime.utcnow()
                }
            }}
        )
        
        # Send success webhook to n8n
        if callback_url:
            send_success_webhook(callback_url, job.id, drive_link)
            
    except Exception as e:
        # Store failure permanently in workflow.psikotes_v2 collection
        db.workflow.psikotes_v2.update_one(
            {'code': code, 'product_id': product_id},
            {'$set': {
                'pdf_generation': {
                    'status': 'failed',
                    'error_message': str(e),
                    'job_id': job.id,
                    'failed_at': datetime.utcnow()
                }
            }}
        )
        
        # Send failure webhook to n8n
        if callback_url:
            send_failure_webhook(callback_url, job.id, str(e))
        raise

def send_success_webhook(callback_url, job_id, drive_link):
    payload = {
        "job_id": job_id,
        "status": "completed",
        "google_drive_link": drive_link,
        "completed_at": datetime.utcnow().isoformat()
    }
    requests.post(callback_url, json=payload, timeout=30)

def send_failure_webhook(callback_url, job_id, error_message):
    # Use separate failure webhook endpoint
    failure_url = callback_url.replace('/pdf-complete', '/pdf-failed')
    payload = {
        "job_id": job_id,
        "status": "failed",
        "error": error_message,
        "failed_at": datetime.utcnow().isoformat(),
        "retry_count": get_current_job().retries_left
    }
    requests.post(failure_url, json=payload, timeout=30)
```

#### 2.3 Job Status Tracking
- **Queued**: Job accepted, waiting for processing
- **Processing**: Worker is generating PDF
- **Completed**: PDF ready for download
- **Failed**: Error occurred, retry available
- **Cancelled**: Job cancelled by user

### Phase 3: API Integration (Week 3-4)

#### 3.1 New API Endpoints

**Submit PDF Generation Job**
```http
POST /api/reports/generate-async
Content-Type: application/json

{
  "code": "rb5YrWGWJXOHoj6r",
  "productId": "minatBakatUmum",
  "priority": "normal",
  "callback": "https://n8n.example.com/webhook/pdf-complete"
}

Response:
{
  "job_id": "pdf_gen_abc123",
  "status": "queued",
  "estimated_completion": "2024-01-15T10:35:00Z",
  "position_in_queue": 3
}
```

**Payload Structure:**
- `code` (required): Report identifier
- `productId` (required): Product identifier
- `priority` (optional): "high", "normal", "low" (default: "normal")
- `callback` (optional): n8n webhook URL for completion notification

**Check Job Status**
```http
GET /api/jobs/{job_id}

Response:
{
  "job_id": "pdf_gen_abc123",
  "status": "processing",
  "progress": 65,
  "estimated_completion": "2024-01-15T10:33:00Z",
  "created_at": "2024-01-15T10:30:00Z",
  "started_at": "2024-01-15T10:31:00Z"
}
```

**Download Completed PDF**
```http
GET /api/jobs/{job_id}/download

Response: PDF file or redirect to storage URL
```

#### 3.2 Backward Compatibility
- Keep existing synchronous endpoint for simple use cases
- Add timeout protection (max 60 seconds)
- Automatically queue long-running requests

### Phase 4: Worker Management (Week 4-5)

#### 4.1 Worker Configuration
```python
# config/job_queue.py
class JobQueueConfig:
    CONCURRENT_WORKERS = 3          # Max simultaneous PDF generations
    MAX_QUEUE_SIZE = 1000           # Prevent memory issues
    JOB_TIMEOUT = 300               # 5 minutes per PDF
    RETRY_ATTEMPTS = 3              # Auto-retry failed jobs
    CLEANUP_COMPLETED_AFTER = 3600  # 1 hour retention
```

#### 4.2 Worker Process Management
```bash
# Start workers
python -m workers.pdf_worker

# Or use supervisor for production
[program:pdf_worker]
command=python -m workers.pdf_worker
numprocs=3
autostart=true
autorestart=true
```

#### 4.3 Health Monitoring
- Worker heartbeat tracking
- Queue length monitoring
- Failed job alerting
- Performance metrics

### Phase 5: n8n Integration (Week 5-6)

#### 5.1 n8n Workflow Updates

**Webhook Pattern (Recommended)**
```
1. HTTP Request → Submit PDF job (with callback URL)
2. Webhook Node → Wait for completion notification
3. Extract jobId/Google Drive link from webhook payload
4. HTTP Request → Get PDF link from database (if jobId received)
5. HTTP Request → Download PDF from Google Drive
```

**Worker Callback Payloads:**

*Success Callback:*
```json
{
  "job_id": "pdf_gen_abc123",
  "status": "completed",
  "google_drive_link": "https://drive.google.com/file/d/1abc123/view",
  "completed_at": "2024-01-15T10:35:00Z"
}
```

*Failure Callback (separate webhook):*
```json
{
  "job_id": "pdf_gen_abc123",
  "status": "failed",
  "error": "Template not found",
  "failed_at": "2024-01-15T10:35:00Z",
  "retry_count": 2
}
```

#### 5.2 n8n Webhook Configuration

**Required n8n Webhook Endpoints:**

1. **Success Webhook**: `/webhook/pdf-complete`
   - Receives job completion notifications
   - Extracts Google Drive link or jobId
   - Triggers PDF download workflow

2. **Failure Webhook**: `/webhook/pdf-failed`
   - Receives job failure notifications
   - Handles error logging and notifications
   - Can trigger retry workflows if needed

**n8n Workflow Structure:**
```
[HTTP Request] → Submit PDF Job
       ↓
[Webhook Wait] → Listen for completion
       ↓
[Switch Node] → Check if Google Drive link or jobId
       ↓
[HTTP Request] → Get PDF link from DB (if jobId)
       ↓
[HTTP Request] → Download PDF from Google Drive
```

#### 5.3 Error Handling in n8n
- **Webhook timeout**: 30-minute maximum wait time
- **Failure webhook**: Separate endpoint for job failures
- **Retry logic**: Automatic retries handled by RQ worker
- **Fallback**: Manual job status check if webhook fails
- **Dead letter queue**: Failed jobs moved to separate queue for investigation

---

## 📊 Configuration & Monitoring

### Resource Allocation

| Environment     | Workers | Queue Size | Timeout |
| --------------- | ------- | ---------- | ------- |
| **Development** | 2       | 100        | 300s    |
| **Staging**     | 3       | 500        | 300s    |
| **Production**  | 5       | 1000       | 600s    |

### Priority Levels

| Priority   | Use Case                  | Queue Position |
| ---------- | ------------------------- | -------------- |
| **High**   | Urgent reports, VIP users | Front of queue |
| **Normal** | Regular reports           | Standard order |
| **Low**    | Batch operations, testing | Back of queue  |

### Monitoring Dashboard

**Key Metrics to Track:**
- Queue length (current pending jobs)
- Average processing time
- Success/failure rates
- Worker utilization
- Memory/CPU usage per worker

**Alerts:**
- Queue length > 100 jobs
- Worker failure rate > 5%
- Average processing time > 5 minutes
- No workers available

---

## 🚀 Deployment Strategy

### Rollout Plan

#### Week 1-2: Infrastructure Setup
- [ ] Install and configure Redis for job queue
- [ ] Implement basic job queue service
- [ ] Create worker process framework
- [ ] Set up monitoring

#### Week 3-4: API Development
- [ ] Implement async PDF generation endpoints
- [ ] Add job status tracking
- [ ] Create download mechanism
- [ ] Add comprehensive error handling
- [ ] Implement webhook callback system
- [ ] Create database schema for PDF results

#### Week 5-6: Integration & Testing
- [ ] Update n8n workflows with webhook endpoints
- [ ] Configure success and failure webhook handlers
- [ ] Test webhook reliability and error handling
- [ ] Conduct load testing
- [ ] Performance optimization
- [ ] Documentation updates

#### Week 7: Production Deployment
- [ ] Deploy to staging environment
- [ ] User acceptance testing
- [ ] Production deployment
- [ ] Monitor and optimize

### Risk Mitigation

| Risk               | Impact | Mitigation                         |
| ------------------ | ------ | ---------------------------------- |
| **Redis failure**  | High   | Redis clustering, backup instances |
| **Worker crashes** | Medium | Auto-restart, health checks        |
| **Queue overflow** | Medium | Queue size limits, alerting        |
| **Job failures**   | Low    | Automatic retries, error logging   |

---

## 💰 Cost-Benefit Analysis

### Implementation Costs
- **Development time**: 6-7 weeks
- **Infrastructure**: Minimal (uses existing Redis)
- **Maintenance**: Low (simple architecture)

### Benefits
- **Reliability**: 99.9% request acceptance rate
- **Performance**: Predictable response times
- **Scalability**: Easy horizontal scaling
- **User Experience**: No more "server busy" errors
- **Monitoring**: Full visibility into PDF generation

### ROI Calculation
- **Current**: 5% request failures during peak times
- **After**: <0.1% request failures
- **Business impact**: Improved customer satisfaction, reduced support tickets

---

## 🔄 Migration Strategy

### Gradual Rollout

1. **Phase 1**: Deploy job queue alongside existing system
2. **Phase 2**: Route 10% of traffic to job queue
3. **Phase 3**: Gradually increase to 50%, then 100%
4. **Phase 4**: Remove old synchronous endpoints

### Fallback Plan
- Keep synchronous endpoints active during transition
- Feature flag to switch between systems
- Rollback procedure documented

---

## 📚 Success Metrics

### Technical Metrics
- **Request acceptance rate**: >99.9%
- **Average processing time**: <2 minutes
- **Queue processing rate**: >95% within SLA
- **System uptime**: >99.5%

### Business Metrics
- **Customer satisfaction**: Reduced complaints about "server busy"
- **Support tickets**: 50% reduction in PDF-related issues
- **System reliability**: Predictable performance during peak usage

---

## 🎯 Next Steps

1. **Review this plan** with product and engineering teams
2. **Approve technical approach** and timeline
3. **Assign development resources** (1-2 developers)
4. **Set up project tracking** and milestones
5. **Begin Phase 1 implementation**

---

## 📞 Questions for Product Review

1. **Timeline**: Is the 6-7 week timeline acceptable for the webhook-based implementation?
2. **Webhook Reliability**: Are you comfortable with n8n receiving webhook callbacks instead of polling?
3. **Failure Handling**: How should we handle cases where webhook delivery fails to n8n?
4. **Payload Options**: ✅ **RESOLVED** - Workers will send jobIds for database lookup
5. **Priorities**: ✅ **RESOLVED** - Single user priority for now, can be extended later
6. **Retention**: ✅ **RESOLVED** - PDFs stored permanently in Google Drive. Job results will be stored in `workflow.psikotes_v2` collection for permanent access, separate from temporary job queue data
7. **Monitoring**: What level of visibility do you need into the queue status?
8. **n8n Configuration**: ✅ **RESOLVED** - You will handle the webhook endpoint setup in n8n

## 🔄 Key Changes in This Update

### Architectural Improvements
1. **Webhook-Based Flow**: Shifted from polling to push-based notifications
2. **Dual Webhook Endpoints**: Separate success and failure callback handling
3. **Minimal Payload Structure**: Streamlined job submission with essential fields only
4. **Permanent Storage Strategy**: Job results stored in `workflow.psikotes_v2` collection for permanent access

### Technical Updates
5. **Latest Redis Version**: Updated to Redis `>=8.0.0` (version 8.2.1) with enhanced performance and security
6. **Python 3.13 Support**: Added official support for Python 3.13.6
7. **Database Integration**: Dual storage approach - temporary job tracking and permanent result storage
8. **Enhanced Worker Implementation**: Comprehensive webhook callback system with permanent data persistence
9. **Detailed n8n Workflow**: Complete webhook endpoint configuration

### Operational Enhancements
10. **Enhanced Error Handling**: Multiple fallback mechanisms and retry strategies
11. **JobId-Based Lookup**: Workers send job IDs for database lookup instead of direct links
12. **Single Priority Level**: Simplified priority system for current single-user scenario
13. **Permanent PDF Access**: Google Drive links stored permanently in main workflow collection
14. **Self-Managed n8n Setup**: Clear ownership of webhook endpoint configuration

This updated plan provides a complete roadmap for implementing the webhook-based job queue system with the latest Redis version, permanent storage solution, and comprehensive error handling.

---

*This document will be updated based on feedback and implementation progress.*