# PDF Job Results Schema

## Overview

This document defines the database schema for the PDF job queue system in the Mindframe application. The system uses two main collections across two MongoDB databases to manage PDF generation jobs and their results.

## Database Structure

### 1. Mindframe Database - `pdf_job_results` Collection

This collection stores detailed job execution results and metadata for PDF generation jobs.

#### Schema Structure

```json
{
  "_id": ObjectId,
  "job_id": "550e8400-e29b-41d4-a716-446655440000",
  "code": "TEST_CODE_123",
  "product_id": "minatBakatUmum",
  "status": "completed",
  "created_at": "2024-01-15T10:30:00.000Z",
  "started_at": "2024-01-15T10:30:05.000Z",
  "completed_at": "2024-01-15T10:32:15.000Z",
  "user_email": "user@example.com",
  "user_name": "John Doe",
  "pdf_filename": "psychological_report_TEST_CODE_123.pdf",
  "pdf_file_size": 2048576,
  "google_drive_file_id": "1BxiMVs0XRA5nFMdKvBdBZjgmUUqptlbs74OgvE2upms",
  "google_drive_webview_link": "https://drive.google.com/file/d/1BxiMVs0XRA5nFMdKvBdBZjgmUUqptlbs74OgvE2upms/view",
  "google_drive_folder_id": "1BxiMVs0XRA5nFMdKvBdBZjgmUUqptlbs74OgvE2upms",
  "error_message": null,
  "error_details": null,
  "retry_count": 0,
  "processing_duration": 130.5,
  "template_used": "psychological_report_v1",
  "callback_url": "https://n8n.example.com/webhook/pdf-complete",
  "callback_sent": true,
  "callback_sent_at": "2024-01-15T10:32:20.000Z",
  "metadata": {
    "worker_id": "worker-001",
    "queue_name": "pdf_generation",
    "priority": "normal"
  }
}
```

#### Field Descriptions

| Field                       | Type     | Required | Description                                                    |
| --------------------------- | -------- | -------- | -------------------------------------------------------------- |
| `_id`                       | ObjectId | Yes      | MongoDB document ID                                            |
| `job_id`                    | String   | Yes      | Unique job identifier from RQ                                  |
| `code`                      | String   | Yes      | Test code from workflow.psikotes_v2                            |
| `product_id`                | String   | Yes      | Product configuration ID                                       |
| `status`                    | Enum     | Yes      | Job status: pending, in_progress, completed, failed, cancelled |
| `created_at`                | DateTime | Yes      | Job creation timestamp                                         |
| `started_at`                | DateTime | No       | Job start timestamp                                            |
| `completed_at`              | DateTime | No       | Job completion timestamp                                       |
| `user_email`                | String   | No       | User email for Google Drive sharing                            |
| `user_name`                 | String   | No       | User name for PDF personalization                              |
| `pdf_filename`              | String   | No       | Generated PDF filename                                         |
| `pdf_file_size`             | Integer  | No       | PDF file size in bytes                                         |
| `google_drive_file_id`      | String   | No       | Google Drive file ID                                           |
| `google_drive_webview_link` | String   | No       | Google Drive webview link                                      |
| `google_drive_folder_id`    | String   | No       | Google Drive folder ID                                         |
| `error_message`             | String   | No       | Error message if job failed                                    |
| `error_details`             | Object   | No       | Detailed error information                                     |
| `retry_count`               | Integer  | Yes      | Number of retry attempts (default: 0)                          |
| `processing_duration`       | Float    | No       | Processing duration in seconds                                 |
| `template_used`             | String   | No       | Template used for PDF generation                               |
| `callback_url`              | String   | No       | n8n webhook callback URL                                       |
| `callback_sent`             | Boolean  | Yes      | Whether callback was sent successfully (default: false)        |
| `callback_sent_at`          | DateTime | No       | Callback sent timestamp                                        |
| `metadata`                  | Object   | No       | Additional job metadata                                        |

#### Indexes

```javascript
// Primary indexes for performance
db.pdf_job_results.createIndex({ "job_id": 1 }, { unique: true })
db.pdf_job_results.createIndex({ "code": 1, "product_id": 1 })
db.pdf_job_results.createIndex({ "status": 1 })
db.pdf_job_results.createIndex({ "created_at": 1 })
db.pdf_job_results.createIndex({ "user_email": 1 })

// Compound indexes for common queries
db.pdf_job_results.createIndex({ "status": 1, "created_at": 1 })
db.pdf_job_results.createIndex({ "code": 1, "product_id": 1, "status": 1 })
```

### 2. Workflow Database - `psikotes_v2` Collection Updates

The existing `workflow.psikotes_v2` collection will be updated to include PDF generation status for permanent storage.

#### New Fields Added

```json
{
  // ... existing fields ...
  "pdf_generation": {
    "status": "completed",
    "job_id": "550e8400-e29b-41d4-a716-446655440000",
    "google_drive_link": "https://drive.google.com/file/d/1BxiMVs0XRA5nFMdKvBdBZjgmUUqptlbs74OgvE2upms/view",
    "created_at": "2024-01-15T10:30:00.000Z",
    "completed_at": "2024-01-15T10:32:15.000Z",
    "error_message": null,
    "product_configs": [
      {
        "product_id": "minatBakatUmum",
        "status": "completed",
        "job_id": "550e8400-e29b-41d4-a716-446655440000",
        "google_drive_link": "https://drive.google.com/file/d/1BxiMVs0XRA5nFMdKvBdBZjgmUUqptlbs74OgvE2upms/view",
        "completed_at": "2024-01-15T10:32:15.000Z"
      }
    ]
  }
}
```

#### Field Descriptions for PDF Generation

| Field                              | Type     | Description                                      |
| ---------------------------------- | -------- | ------------------------------------------------ |
| `pdf_generation.status`            | String   | Overall PDF generation status                    |
| `pdf_generation.job_id`            | String   | Latest job ID (for single product)               |
| `pdf_generation.google_drive_link` | String   | Latest Google Drive link (for single product)    |
| `pdf_generation.created_at`        | DateTime | First PDF generation request                     |
| `pdf_generation.completed_at`      | DateTime | Latest completion timestamp                      |
| `pdf_generation.error_message`     | String   | Latest error message if any                      |
| `pdf_generation.product_configs`   | Array    | Array of product-specific PDF generation results |

## Usage Patterns

### 1. Job Submission

```python
# Create new job result record
job_result = PDFJobResult(
    job_id=job.id,
    code="TEST_CODE_123",
    product_id="minatBakatUmum",
    user_email="user@example.com",
    callback_url="https://n8n.example.com/webhook/pdf-complete"
)

# Store in pdf_job_results collection
job_result_service.create_job_result(job_result)
```

### 2. Job Status Updates

```python
# Mark job as started
job_result_service.mark_job_as_started(job_id)

# Mark job as completed
job_result_service.mark_job_as_completed(
    job_id=job_id,
    pdf_filename="report.pdf",
    pdf_file_size=2048576,
    google_drive_file_id="1BxiMVs0XRA5nFMdKvBdBZjgmUUqptlbs74OgvE2upms",
    google_drive_webview_link="https://drive.google.com/file/d/1BxiMVs0XRA5nFMdKvBdBZjgmUUqptlbs74OgvE2upms/view"
)

# Update workflow.psikotes_v2 collection
workflow_collection.update_one(
    {"code": code},
    {"$set": {
        "pdf_generation.status": "completed",
        "pdf_generation.job_id": job_id,
        "pdf_generation.google_drive_link": google_drive_link,
        "pdf_generation.completed_at": datetime.utcnow()
    }}
)
```

### 3. Job Queries

```python
# Get job by job ID
job_result = job_result_service.get_job_result_by_job_id(job_id)

# Get latest job for code and product
job_result = job_result_service.get_job_result_by_code_and_product(code, product_id)

# Get all pending jobs
pending_jobs = job_result_service.get_jobs_by_status(JobStatus.PENDING)
```

## Data Lifecycle

### 1. Job Creation
- Job record created in `pdf_job_results` with status "pending"
- Job submitted to Redis queue

### 2. Job Processing
- Status updated to "in_progress" when worker starts
- PDF generated and uploaded to Google Drive
- Status updated to "completed" with results

### 3. Permanent Storage
- Results stored in `workflow.psikotes_v2` collection
- Webhook callback sent to n8n

### 4. Cleanup
- Old job records (30+ days) automatically cleaned up
- Failed jobs retained for debugging

## Error Handling

### Job Failures
- Status set to "failed" with error details
- Retry mechanism with configurable limits
- Error details stored for debugging

### Data Consistency
- Atomic updates to prevent race conditions
- Rollback mechanisms for failed operations
- Monitoring and alerting for data inconsistencies

## Performance Considerations

### Indexing Strategy
- Primary indexes on frequently queried fields
- Compound indexes for complex queries
- TTL indexes for automatic cleanup

### Query Optimization
- Use projection to limit returned fields
- Implement pagination for large result sets
- Cache frequently accessed data

### Monitoring
- Track job processing times
- Monitor queue lengths and worker performance
- Alert on high failure rates or long processing times