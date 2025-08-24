"""Report service for managing psychological reports"""

import os
import logging
from typing import Dict, Any, List, Optional, Union
from datetime import datetime, timedelta
from pathlib import Path
import uuid
from enum import Enum
import time

from ..models.report_model import (
    PsychologicalReport, ReportType, ReportStatus, TestResult, 
    ClientInformation
)
from ..models.user_model import User
from ..utils.logging_utils import LoggingUtils

logger = LoggingUtils.get_logger(__name__)


class ReportService:
    """Service for psychological report management"""
    
    def __init__(self):
        self.db_service = None
        self.pdf_service = None
        self.template_service = None
        self.storage_service = None
        self.email_service = None
        self.auth_service = None
        self._initialized = False
    
    def initialize(self, db_service=None, pdf_service=None, 
                   template_service=None, storage_service=None,
                   email_service=None, auth_service=None) -> bool:
        """Initialize report service"""
        start_time = time.time()
        try:
            # Set service dependencies
            self.db_service = db_service
            self.pdf_service = pdf_service
            self.template_service = template_service
            self.storage_service = storage_service
            self.email_service = email_service
            self.auth_service = auth_service
            
            self._initialized = True
            
            initialization_time = time.time() - start_time
            logger.info("Report service initialized successfully", extra={
                'service': 'report_service',
                'initialization_time_ms': round(initialization_time * 1000, 2),
                'dependencies_count': sum(1 for dep in [db_service, pdf_service, template_service, 
                                                       storage_service, email_service, auth_service] if dep is not None)
            })
            return True
            
        except Exception as e:
            logger.error("Failed to initialize report service", extra={
                'service': 'report_service',
                'error': str(e),
                'error_type': type(e).__name__,
                'initialization_time_ms': round((time.time() - start_time) * 1000, 2)
            })
            return False
    
    def health_check(self) -> Dict[str, Any]:
        """Perform report service health check"""
        try:
            health_info = {
                "status": "healthy",
                "database_available": False,
                "pdf_service_available": False,
                "template_service_available": False,
                "storage_available": False,
                "email_available": False,
                "auth_available": False,
                "timestamp": datetime.utcnow().isoformat()
            }
            
            # Check service dependencies
            if self.db_service:
                try:
                    db_health = self.db_service.health_check()
                    health_info["database_available"] = db_health.get("status") == "healthy"
                except Exception as e:
                    health_info["database_error"] = str(e)
            
            if self.pdf_service:
                try:
                    pdf_health = self.pdf_service.health_check()
                    health_info["pdf_service_available"] = pdf_health.get("status") == "healthy"
                except Exception as e:
                    health_info["pdf_service_error"] = str(e)
            
            if self.template_service:
                try:
                    template_health = self.template_service.health_check()
                    health_info["template_service_available"] = template_health.get("status") == "healthy"
                except Exception as e:
                    health_info["template_service_error"] = str(e)
            
            if self.storage_service:
                try:
                    storage_health = self.storage_service.health_check()
                    health_info["storage_available"] = storage_health.get("status") == "healthy"
                except Exception as e:
                    health_info["storage_error"] = str(e)
            
            if self.email_service:
                try:
                    email_health = self.email_service.health_check()
                    health_info["email_available"] = email_health.get("status") == "healthy"
                except Exception as e:
                    health_info["email_error"] = str(e)
            
            if self.auth_service:
                try:
                    auth_health = self.auth_service.health_check()
                    health_info["auth_available"] = auth_health.get("status") == "healthy"
                except Exception as e:
                    health_info["auth_error"] = str(e)
            
            return health_info
            
        except Exception as e:
            return {
                "status": "error",
                "message": f"Report service health check failed: {str(e)}",
                "timestamp": datetime.utcnow().isoformat()
            }
    
    def create_report(self, report_data: Dict[str, Any], 
                     user_id: str = None) -> Dict[str, Any]:
        """Create a new psychological report"""
        start_time = time.time()
        report_id = None
        
        # Create contextual logger for this operation
        context_logger = LoggingUtils.get_contextual_logger('report_service.create', {
            'operation': 'create_report',
            'user_id': user_id,
            'report_type': report_data.get('report_type'),
            'client_name': report_data.get('client_information', {}).get('name')
        })
        
        context_logger.info("Starting report creation")
        
        try:
            # Create report object
            report = PsychologicalReport(**report_data)
            report.created_by = user_id
            report.created_at = datetime.utcnow()
            report.updated_at = datetime.utcnow()
            report.status = ReportStatus.DRAFT
            
            # Validate report data
            validation_start = time.time()
            validation_result = self._validate_report_data(report)
            validation_time = time.time() - validation_start
            
            if not validation_result["valid"]:
                context_logger.warning("Report validation failed", extra={
                    'validation_error': validation_result['error'],
                    'validation_time_ms': round(validation_time * 1000, 2)
                })
                return {
                    "success": False,
                    "error": f"Report validation failed: {validation_result['error']}",
                    "error_type": "validation"
                }
            
            context_logger.debug("Report validation successful", extra={
                'validation_time_ms': round(validation_time * 1000, 2)
            })
            
            # Save to database
            if self.db_service:
                try:
                    db_start = time.time()
                    result = self.db_service.create_document(
                        "psychological_reports", report.to_dict()
                    )
                    report.id = str(result.inserted_id)
                    report_id = report.id
                    db_time = time.time() - db_start
                    
                    context_logger.debug("Report saved to database", extra={
                        'report_id': report_id,
                        'database_time_ms': round(db_time * 1000, 2)
                    })
                    
                except Exception as e:
                    context_logger.error("Failed to save report to database", extra={
                        'error': str(e),
                        'error_type': type(e).__name__,
                        'database_time_ms': round((time.time() - db_start) * 1000, 2)
                    })
                    return {
                        "success": False,
                        "error": str(e),
                        "error_type": "database"
                    }
            
            total_time = time.time() - start_time
            context_logger.info("Report created successfully", extra={
                'report_id': report_id,
                'total_time_ms': round(total_time * 1000, 2),
                'validation_time_ms': round(validation_time * 1000, 2)
            })
            
            return {
                "success": True,
                "report": report.to_dict()
            }
            
        except Exception as e:
            logger.error(f"Error creating report: {e}")
            return {
                "success": False,
                "error": str(e),
                "error_type": "unexpected"
            }
    
    def get_report(self, report_id: str, user_id: str = None) -> Optional[Dict[str, Any]]:
        """Get report by ID"""
        if not self.db_service:
            return None
        
        try:
            report_doc = self.db_service.find_one(
                "psychological_reports", {"_id": report_id}
            )
            
            if not report_doc:
                return None
            
            # Check access permissions
            if user_id and not self._check_report_access(report_doc, user_id):
                logger.warning(f"User {user_id} attempted to access report {report_id} without permission")
                return None
            
            return report_doc
            
        except Exception as e:
            logger.error(f"Error getting report: {e}")
            return None
    
    def list_reports(self, user_id: str = None, status: str = None,
                    report_type: str = None, client_name: str = None,
                    limit: int = 50, skip: int = 0) -> List[Dict[str, Any]]:
        """List reports with filtering"""
        if not self.db_service:
            return []
        
        try:
            query = {}
            
            # Filter by user access
            if user_id:
                query["$or"] = [
                    {"created_by": user_id},
                    {"authorized_viewers": user_id},
                    {"professional_information.psychologist_id": user_id}
                ]
            
            # Filter by status
            if status:
                query["status"] = status
            
            # Filter by report type
            if report_type:
                query["report_type"] = report_type
            
            # Filter by client name (case-insensitive partial match)
            if client_name:
                query["client_information.full_name"] = {
                    "$regex": client_name,
                    "$options": "i"
                }
            
            reports = self.db_service.find(
                "psychological_reports", query, limit=limit, skip=skip,
                sort=[("updated_at", -1)]
            )
            
            return list(reports)
            
        except Exception as e:
            logger.error(f"Error listing reports: {e}")
            return []
    
    def update_report(self, report_id: str, update_data: Dict[str, Any],
                     user_id: str = None) -> Dict[str, Any]:
        """Update report"""
        try:
            # Get existing report
            existing_report = self.get_report(report_id, user_id)
            if not existing_report:
                return {
                    "success": False,
                    "error": "Report not found or access denied",
                    "error_type": "not_found"
                }
            
            # Check edit permissions
            if user_id and not self._check_report_edit_access(existing_report, user_id):
                return {
                    "success": False,
                    "error": "Permission denied",
                    "error_type": "permission"
                }
            
            # Validate update data
            if "client_information" in update_data or "test_results" in update_data:
                # Create temporary report object for validation
                temp_report_data = existing_report.copy()
                temp_report_data.update(update_data)
                temp_report = PsychologicalReport(**temp_report_data)
                
                validation_result = self._validate_report_data(temp_report)
                if not validation_result["valid"]:
                    return {
                        "success": False,
                        "error": f"Report validation failed: {validation_result['error']}",
                        "error_type": "validation"
                    }
            
            # Set update timestamp
            update_data["updated_at"] = datetime.utcnow()
            update_data["last_modified_by"] = user_id
            
            # Update in database
            if self.db_service:
                result = self.db_service.update_document(
                    "psychological_reports",
                    {"_id": report_id},
                    {"$set": update_data}
                )
                
                if result.modified_count == 0:
                    return {
                        "success": False,
                        "error": "Report not updated",
                        "error_type": "database"
                    }
            
            # Get updated report
            updated_report = self.get_report(report_id, user_id)
            
            logger.info(f"Updated report: {report_id}")
            
            return {
                "success": True,
                "report": updated_report
            }
            
        except Exception as e:
            logger.error(f"Error updating report: {e}")
            return {
                "success": False,
                "error": str(e),
                "error_type": "unexpected"
            }
    
    def delete_report(self, report_id: str, user_id: str = None) -> Dict[str, Any]:
        """Delete report"""
        try:
            # Get existing report
            existing_report = self.get_report(report_id, user_id)
            if not existing_report:
                return {
                    "success": False,
                    "error": "Report not found or access denied",
                    "error_type": "not_found"
                }
            
            # Check delete permissions (only creator can delete)
            if user_id and existing_report.get("created_by") != user_id:
                return {
                    "success": False,
                    "error": "Permission denied",
                    "error_type": "permission"
                }
            
            # Delete associated PDF file if exists
            if existing_report.get("pdf_file_path") and self.storage_service:
                try:
                    self.storage_service.delete_file(existing_report["pdf_file_path"])
                except Exception as e:
                    logger.warning(f"Failed to delete PDF file: {e}")
            
            # Delete from database
            if self.db_service:
                result = self.db_service.delete_document(
                    "psychological_reports", {"_id": report_id}
                )
                
                if result.deleted_count == 0:
                    return {
                        "success": False,
                        "error": "Report not deleted",
                        "error_type": "database"
                    }
            
            logger.info(f"Deleted report: {report_id}")
            
            return {"success": True}
            
        except Exception as e:
            logger.error(f"Error deleting report: {e}")
            return {
                "success": False,
                "error": str(e),
                "error_type": "unexpected"
            }
    
    def generate_report_pdf(self, report_id: str, user_id: str = None,
                           template_name: str = "psychological_report",
                           send_email: bool = False) -> Dict[str, Any]:
        """Generate PDF for psychological report"""
        try:
            # Get report
            report_doc = self.get_report(report_id, user_id)
            if not report_doc:
                return {
                    "success": False,
                    "error": "Report not found or access denied",
                    "error_type": "not_found"
                }
            
            # Check if PDF service is available
            if not self.pdf_service:
                return {
                    "success": False,
                    "error": "PDF service not available",
                    "error_type": "service_unavailable"
                }
            
            # Update PDF generation status
            if self.db_service:
                self.db_service.update_document(
                    "psychological_reports",
                    {"_id": report_id},
                    {"$set": {"pdf_generation_status": "generating"}}
                )
            
            # Generate PDF
            pdf_result = self.pdf_service.generate_psychological_report(
                report_doc, template_name, user_id, send_email
            )
            
            if pdf_result["success"]:
                # Update report with PDF information
                pdf_update = {
                    "pdf_generation_status": "completed",
                    "pdf_file_path": pdf_result["pdf_document"].get("file_path"),
                    "pdf_generated_at": datetime.utcnow(),
                    "pdf_document_id": pdf_result["pdf_document"].get("id")
                }
                
                if self.db_service:
                    self.db_service.update_document(
                        "psychological_reports",
                        {"_id": report_id},
                        {"$set": pdf_update}
                    )
                
                logger.info(f"Generated PDF for report: {report_id}")
                
                return {
                    "success": True,
                    "pdf_document": pdf_result["pdf_document"],
                    "report_id": report_id
                }
            else:
                # Update failure status
                if self.db_service:
                    self.db_service.update_document(
                        "psychological_reports",
                        {"_id": report_id},
                        {
                            "$set": {
                                "pdf_generation_status": "failed",
                                "pdf_generation_error": pdf_result.get("error")
                            }
                        }
                    )
                
                return pdf_result
            
        except Exception as e:
            logger.error(f"Error generating report PDF: {e}")
            
            # Update failure status
            if self.db_service:
                try:
                    self.db_service.update_document(
                        "psychological_reports",
                        {"_id": report_id},
                        {
                            "$set": {
                                "pdf_generation_status": "failed",
                                "pdf_generation_error": str(e)
                            }
                        }
                    )
                except Exception:
                    pass
            
            return {
                "success": False,
                "error": str(e),
                "error_type": "unexpected"
            }
    
    def add_test_result(self, report_id: str, test_result_data: Dict[str, Any],
                       user_id: str = None) -> Dict[str, Any]:
        """Add test result to report"""
        try:
            # Get existing report
            report_doc = self.get_report(report_id, user_id)
            if not report_doc:
                return {
                    "success": False,
                    "error": "Report not found or access denied",
                    "error_type": "not_found"
                }
            
            # Check edit permissions
            if user_id and not self._check_report_edit_access(report_doc, user_id):
                return {
                    "success": False,
                    "error": "Permission denied",
                    "error_type": "permission"
                }
            
            # Create test result object
            test_result = TestResult(**test_result_data)
            test_result.administered_by = user_id
            test_result.administered_date = test_result.administered_date or datetime.utcnow()
            
            # Add to report
            if self.db_service:
                result = self.db_service.update_document(
                    "psychological_reports",
                    {"_id": report_id},
                    {
                        "$push": {"test_results": test_result.to_dict()},
                        "$set": {
                            "updated_at": datetime.utcnow(),
                            "last_modified_by": user_id
                        }
                    }
                )
                
                if result.modified_count == 0:
                    return {
                        "success": False,
                        "error": "Test result not added",
                        "error_type": "database"
                    }
            
            logger.info(f"Added test result to report: {report_id}")
            
            return {
                "success": True,
                "test_result": test_result.to_dict()
            }
            
        except Exception as e:
            logger.error(f"Error adding test result: {e}")
            return {
                "success": False,
                "error": str(e),
                "error_type": "unexpected"
            }
    
    def update_report_status(self, report_id: str, status: str,
                           user_id: str = None) -> Dict[str, Any]:
        """Update report status"""
        try:
            # Validate status
            try:
                ReportStatus(status)
            except ValueError:
                return {
                    "success": False,
                    "error": f"Invalid status: {status}",
                    "error_type": "validation"
                }
            
            # Update report
            update_data = {
                "status": status,
                "updated_at": datetime.utcnow(),
                "last_modified_by": user_id
            }
            
            # Add status-specific fields
            if status == ReportStatus.COMPLETED:
                update_data["completed_at"] = datetime.utcnow()
            elif status == ReportStatus.REVIEWED:
                update_data["reviewed_at"] = datetime.utcnow()
                update_data["reviewed_by"] = user_id
            
            return self.update_report(report_id, update_data, user_id)
            
        except Exception as e:
            logger.error(f"Error updating report status: {e}")
            return {
                "success": False,
                "error": str(e),
                "error_type": "unexpected"
            }
    
    def add_authorized_viewer(self, report_id: str, viewer_user_id: str,
                            user_id: str = None) -> Dict[str, Any]:
        """Add authorized viewer to report"""
        try:
            # Get existing report
            report_doc = self.get_report(report_id, user_id)
            if not report_doc:
                return {
                    "success": False,
                    "error": "Report not found or access denied",
                    "error_type": "not_found"
                }
            
            # Check permissions (only creator can add viewers)
            if user_id and report_doc.get("created_by") != user_id:
                return {
                    "success": False,
                    "error": "Permission denied",
                    "error_type": "permission"
                }
            
            # Add viewer
            if self.db_service:
                result = self.db_service.update_document(
                    "psychological_reports",
                    {"_id": report_id},
                    {
                        "$addToSet": {"authorized_viewers": viewer_user_id},
                        "$set": {
                            "updated_at": datetime.utcnow(),
                            "last_modified_by": user_id
                        }
                    }
                )
                
                if result.modified_count == 0:
                    return {
                        "success": False,
                        "error": "Viewer not added",
                        "error_type": "database"
                    }
            
            logger.info(f"Added authorized viewer {viewer_user_id} to report: {report_id}")
            
            return {"success": True}
            
        except Exception as e:
            logger.error(f"Error adding authorized viewer: {e}")
            return {
                "success": False,
                "error": str(e),
                "error_type": "unexpected"
            }
    
    def get_report_statistics(self, user_id: str = None) -> Dict[str, Any]:
        """Get report statistics"""
        if not self.db_service:
            return {}
        
        try:
            pipeline = []
            
            # Filter by user access if specified
            if user_id:
                pipeline.append({
                    "$match": {
                        "$or": [
                            {"created_by": user_id},
                            {"authorized_viewers": user_id},
                            {"professional_information.psychologist_id": user_id}
                        ]
                    }
                })
            
            # Group and calculate statistics
            pipeline.extend([
                {
                    "$group": {
                        "_id": None,
                        "total_reports": {"$sum": 1},
                        "by_status": {
                            "$push": "$status"
                        },
                        "by_type": {
                            "$push": "$report_type"
                        },
                        "with_pdf": {
                            "$sum": {
                                "$cond": [
                                    {"$eq": ["$pdf_generation_status", "completed"]},
                                    1, 0
                                ]
                            }
                        }
                    }
                }
            ])
            
            result = list(self.db_service.aggregate("psychological_reports", pipeline))
            
            if result:
                stats = result[0]
                
                # Process status statistics
                status_stats = {}
                for status in stats.get("by_status", []):
                    status_stats[status] = status_stats.get(status, 0) + 1
                
                # Process type statistics
                type_stats = {}
                for report_type in stats.get("by_type", []):
                    type_stats[report_type] = type_stats.get(report_type, 0) + 1
                
                return {
                    "total_reports": stats.get("total_reports", 0),
                    "reports_with_pdf": stats.get("with_pdf", 0),
                    "by_status": status_stats,
                    "by_type": type_stats
                }
            
            return {
                "total_reports": 0,
                "reports_with_pdf": 0,
                "by_status": {},
                "by_type": {}
            }
            
        except Exception as e:
            logger.error(f"Error getting report statistics: {e}")
            return {}
    
    def _validate_report_data(self, report: PsychologicalReport) -> Dict[str, Any]:
        """Validate report data"""
        try:
            errors = []
            
            # Validate client information
            if not report.client_information:
                errors.append("Client information is required")
            elif not report.client_information.full_name:
                errors.append("Client full name is required")
            
            # Validate professional information
            if not report.professional_information:
                errors.append("Professional information is required")
            elif not report.professional_information.get("psychologist_name"):
                errors.append("Psychologist name is required")
            
            # Validate session information
            if not report.session_information:
                errors.append("Session information is required")
            elif not report.session_information.get("session_date"):
                errors.append("Session date is required")
            
            # Validate test results if present
            for i, test_result in enumerate(report.test_results):
                if not test_result.test_name:
                    errors.append(f"Test result {i+1}: Test name is required")
                if not test_result.administered_date:
                    errors.append(f"Test result {i+1}: Administered date is required")
            
            if errors:
                return {
                    "valid": False,
                    "error": "; ".join(errors)
                }
            
            return {"valid": True}
            
        except Exception as e:
            return {"valid": False, "error": f"Validation error: {str(e)}"}
    
    def _check_report_access(self, report_doc: Dict[str, Any], user_id: str) -> bool:
        """Check if user has access to report"""
        # Creator has access
        if report_doc.get("created_by") == user_id:
            return True
        
        # Authorized viewers have access
        if user_id in report_doc.get("authorized_viewers", []):
            return True
        
        # Psychologist has access
        professional_info = report_doc.get("professional_information", {})
        if professional_info.get("psychologist_id") == user_id:
            return True
        
        return False
    
    def _check_report_edit_access(self, report_doc: Dict[str, Any], user_id: str) -> bool:
        """Check if user has edit access to report"""
        # Creator has edit access
        if report_doc.get("created_by") == user_id:
            return True
        
        # Psychologist has edit access
        professional_info = report_doc.get("professional_information", {})
        if professional_info.get("psychologist_id") == user_id:
            return True
        
        return False
    
    def cleanup_old_reports(self, days_old: int = 365) -> int:
        """Clean up old reports"""
        if not self.db_service:
            return 0
        
        try:
            cutoff_date = datetime.utcnow() - timedelta(days=days_old)
            
            # Find old reports (only drafts and cancelled)
            query = {
                "created_at": {"$lt": cutoff_date},
                "status": {"$in": [ReportStatus.DRAFT, ReportStatus.CANCELLED]}
            }
            
            old_reports = self.db_service.find("psychological_reports", query)
            
            deleted_count = 0
            for report in old_reports:
                result = self.delete_report(str(report["_id"]), report.get("created_by"))
                if result["success"]:
                    deleted_count += 1
            
            logger.info(f"Cleaned up {deleted_count} old reports")
            return deleted_count
            
        except Exception as e:
            logger.error(f"Error cleaning up old reports: {e}")
            return 0


# Global report service instance
report_service = ReportService()