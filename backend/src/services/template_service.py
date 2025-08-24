"""Template service for managing HTML templates"""

import os
import logging
from typing import Dict, Any, List, Optional, Union
from datetime import datetime, timedelta
from pathlib import Path
import json
import uuid
from jinja2 import Environment, FileSystemLoader, Template as Jinja2Template

from ..core.template_processor import TemplateProcessor
from ..models.template_model import Template, TemplateVariable

logger = logging.getLogger(__name__)


class TemplateService:
    """Service for template management and operations"""
    
    def __init__(self):
        self.template_processor = None
        self.db_service = None
        self.storage_service = None
        self._initialized = False
        self.template_cache = {}
        self.cache_ttl = 3600  # 1 hour
    
    def initialize(self, db_service=None, storage_service=None, 
                   template_dirs: List[str] = None) -> bool:
        """Initialize template service"""
        try:
            # Initialize template processor with the first template directory
            template_dir = None
            if template_dirs and len(template_dirs) > 0:
                template_dir = template_dirs[0]
            
            self.template_processor = TemplateProcessor(template_dir)
            
            # Set service dependencies
            self.db_service = db_service
            self.storage_service = storage_service
            
            self._initialized = True
            logger.info("Template service initialized successfully")
            return True
            
        except Exception as e:
            logger.error(f"Failed to initialize template service: {e}")
            return False
    
    def health_check(self) -> Dict[str, Any]:
        """Perform template service health check"""
        try:
            health_info = {
                "status": "healthy",
                "template_processor": False,
                "database_available": False,
                "storage_available": False,
                "template_directories": [],
                "cached_templates": len(self.template_cache),
                "timestamp": datetime.utcnow().isoformat()
            }
            
            # Check template processor
            if self.template_processor:
                try:
                    # Test template rendering
                    test_template = "Hello {{ name }}!"
                    result = self.template_processor.render_string(test_template, {"name": "World"})
                    health_info["template_processor"] = result == "Hello World!"
                    health_info["template_directories"] = self.template_processor.get_template_directories()
                except Exception as e:
                    health_info["template_processor_error"] = str(e)
            
            # Check service dependencies
            if self.db_service:
                try:
                    db_health = self.db_service.health_check()
                    health_info["database_available"] = db_health.get("status") == "healthy"
                except Exception as e:
                    health_info["database_error"] = str(e)
            
            if self.storage_service:
                try:
                    storage_health = self.storage_service.health_check()
                    health_info["storage_available"] = storage_health.get("status") == "healthy"
                except Exception as e:
                    health_info["storage_error"] = str(e)
            
            return health_info
            
        except Exception as e:
            return {
                "status": "error",
                "message": f"Template service health check failed: {str(e)}",
                "timestamp": datetime.utcnow().isoformat()
            }
    
    def create_template(self, template_data: Dict[str, Any], 
                       user_id: str = None) -> Dict[str, Any]:
        """Create a new template"""
        try:
            # Create template object
            template = Template(**template_data)
            template.author_id = user_id
            template.created_at = datetime.utcnow()
            template.updated_at = datetime.utcnow()
            
            # Validate template content
            validation_result = self._validate_template_content(template.content)
            if not validation_result["valid"]:
                return {
                    "success": False,
                    "error": f"Template validation failed: {validation_result['error']}",
                    "error_type": "validation"
                }
            
            # Save template file if storage service is available
            if self.storage_service:
                try:
                    file_path = f"templates/{template.name}.html"
                    file_info = self.storage_service.save_file(
                        template.content.encode('utf-8'), 
                        f"{template.name}.html", 
                        "templates"
                    )
                    template.file_path = file_info.get("relative_path")
                except Exception as e:
                    logger.warning(f"Failed to save template file: {e}")
            
            # Save to database
            if self.db_service:
                try:
                    result = self.db_service.create_document(
                        "templates", template.to_dict()
                    )
                    template.id = str(result.inserted_id)
                except Exception as e:
                    logger.error(f"Failed to save template to database: {e}")
                    return {
                        "success": False,
                        "error": str(e),
                        "error_type": "database"
                    }
            
            # Clear cache
            self._clear_template_cache(template.name)
            
            logger.info(f"Created template: {template.name}")
            
            return {
                "success": True,
                "template": template.to_dict()
            }
            
        except Exception as e:
            logger.error(f"Error creating template: {e}")
            return {
                "success": False,
                "error": str(e),
                "error_type": "unexpected"
            }
    
    def get_template(self, template_id: str = None, 
                    template_name: str = None) -> Optional[Dict[str, Any]]:
        """Get template by ID or name"""
        if not self.db_service:
            return None
        
        try:
            query = {}
            if template_id:
                query["_id"] = template_id
            elif template_name:
                query["name"] = template_name
            else:
                return None
            
            template_doc = self.db_service.find_one("templates", query)
            return template_doc
            
        except Exception as e:
            logger.error(f"Error getting template: {e}")
            return None
    
    def list_templates(self, page: int = 1, limit: int = 50, 
                      filters: Dict[str, Any] = None, sort_by: str = "updated_at",
                      sort_order: str = "desc") -> Dict[str, Any]:
        """List templates with filtering and pagination"""
        try:
            # Calculate skip based on page
            skip = (page - 1) * limit
            
            # Build query from filters
            query = {"status": "active"}  # Default to active templates
            
            if filters:
                if "category" in filters:
                    query["category"] = filters["category"]
                if "search" in filters:
                    # Simple text search in name and description
                    query["$or"] = [
                        {"name": {"$regex": filters["search"], "$options": "i"}},
                        {"description": {"$regex": filters["search"], "$options": "i"}}
                    ]
            
            # Handle sort order
            sort_direction = -1 if sort_order == "desc" else 1
            sort_field = sort_by if sort_by else "updated_at"
            
            # Get total count for pagination
            total_count = 0
            if self.db_service:
                total_count = self.db_service.count_documents("templates", query)
            
            # Get templates
            templates = []
            if self.db_service:
                templates = self.db_service.find_many(
                    "templates", query, limit=limit, skip=skip,
                    sort=[(sort_field, sort_direction)]
                )
            
            # Calculate pagination info
            total_pages = (total_count + limit - 1) // limit
            has_next = page < total_pages
            has_prev = page > 1
            
            return {
                "success": True,
                "templates": templates,
                "pagination": {
                    "page": page,
                    "limit": limit,
                    "total": total_count,
                    "total_pages": total_pages,
                    "has_next": has_next,
                    "has_prev": has_prev
                }
            }
            
        except Exception as e:
            logger.error(f"Error listing templates: {str(e)}")
            return {
                "success": False,
                "error": f"Failed to list templates: {str(e)}",
                "templates": [],
                "pagination": {
                    "page": page,
                    "limit": limit,
                    "total": 0,
                    "total_pages": 0,
                    "has_next": False,
                    "has_prev": False
                }
            }
    
    def update_template(self, template_id: str, update_data: Dict[str, Any],
                       user_id: str = None) -> Dict[str, Any]:
        """Update template"""
        try:
            # Get existing template
            existing_template = self.get_template(template_id=template_id)
            if not existing_template:
                return {
                    "success": False,
                    "error": "Template not found",
                    "error_type": "not_found"
                }
            
            # Check user permission
            if user_id and existing_template.get("author_id") != user_id:
                return {
                    "success": False,
                    "error": "Permission denied",
                    "error_type": "permission"
                }
            
            # Validate content if being updated
            if "content" in update_data:
                validation_result = self._validate_template_content(update_data["content"])
                if not validation_result["valid"]:
                    return {
                        "success": False,
                        "error": f"Template validation failed: {validation_result['error']}",
                        "error_type": "validation"
                    }
            
            # Update version if content changed
            if "content" in update_data:
                current_version = existing_template.get("version", "1.0.0")
                # Simple version increment (you might want more sophisticated versioning)
                version_parts = current_version.split(".")
                version_parts[-1] = str(int(version_parts[-1]) + 1)
                update_data["version"] = ".".join(version_parts)
            
            # Set update timestamp
            update_data["updated_at"] = datetime.utcnow()
            
            # Update file if storage service is available and content changed
            if self.storage_service and "content" in update_data:
                try:
                    if existing_template.get("file_path"):
                        # Update existing file
                        self.storage_service.save_file(
                            update_data["content"].encode('utf-8'),
                            existing_template["file_path"]
                        )
                    else:
                        # Create new file
                        file_info = self.storage_service.save_file(
                            update_data["content"].encode('utf-8'),
                            f"{existing_template['name']}.html",
                            "templates"
                        )
                        update_data["file_path"] = file_info.get("relative_path")
                except Exception as e:
                    logger.warning(f"Failed to update template file: {e}")
            
            # Update in database
            if self.db_service:
                result = self.db_service.update_document(
                    "templates",
                    {"_id": template_id},
                    {"$set": update_data}
                )
                
                if result.modified_count == 0:
                    return {
                        "success": False,
                        "error": "Template not updated",
                        "error_type": "database"
                    }
            
            # Clear cache
            self._clear_template_cache(existing_template.get("name"))
            
            # Get updated template
            updated_template = self.get_template(template_id=template_id)
            
            logger.info(f"Updated template: {template_id}")
            
            return {
                "success": True,
                "template": updated_template
            }
            
        except Exception as e:
            logger.error(f"Error updating template: {e}")
            return {
                "success": False,
                "error": str(e),
                "error_type": "unexpected"
            }
    
    def delete_template(self, template_id: str, user_id: str = None) -> Dict[str, Any]:
        """Delete template"""
        try:
            # Get existing template
            existing_template = self.get_template(template_id=template_id)
            if not existing_template:
                return {
                    "success": False,
                    "error": "Template not found",
                    "error_type": "not_found"
                }
            
            # Check user permission
            if user_id and existing_template.get("author_id") != user_id:
                return {
                    "success": False,
                    "error": "Permission denied",
                    "error_type": "permission"
                }
            
            # Delete file if exists
            if self.storage_service and existing_template.get("file_path"):
                try:
                    self.storage_service.delete_file(existing_template["file_path"])
                except Exception as e:
                    logger.warning(f"Failed to delete template file: {e}")
            
            # Delete from database
            if self.db_service:
                result = self.db_service.delete_document(
                    "templates", {"_id": template_id}
                )
                
                if result.deleted_count == 0:
                    return {
                        "success": False,
                        "error": "Template not deleted",
                        "error_type": "database"
                    }
            
            # Clear cache
            self._clear_template_cache(existing_template.get("name"))
            
            logger.info(f"Deleted template: {template_id}")
            
            return {"success": True}
            
        except Exception as e:
            logger.error(f"Error deleting template: {e}")
            return {
                "success": False,
                "error": str(e),
                "error_type": "unexpected"
            }
    
    def render_template(self, template_name: str, variables: Dict[str, Any],
                       use_cache: bool = True) -> Dict[str, Any]:
        """Render template with variables"""
        try:
            # Check cache first
            if use_cache:
                cached_content = self._get_cached_template(template_name)
                if cached_content:
                    try:
                        rendered = self.template_processor.render_string(
                            cached_content, variables
                        )
                        return {
                            "success": True,
                            "rendered_content": rendered,
                            "from_cache": True
                        }
                    except Exception as e:
                        logger.warning(f"Failed to render cached template: {e}")
                        # Continue to load from database
            
            # Get template from database
            template_doc = self.get_template(template_name=template_name)
            if not template_doc:
                return {
                    "success": False,
                    "error": f"Template '{template_name}' not found",
                    "error_type": "not_found"
                }
            
            # Check if template is active
            if template_doc.get("status") != "active":
                return {
                    "success": False,
                    "error": f"Template '{template_name}' is not active",
                    "error_type": "inactive"
                }
            
            # Get template content
            content = template_doc.get("content")
            if not content:
                # Try to load from file
                if self.storage_service and template_doc.get("file_path"):
                    try:
                        file_content = self.storage_service.get_file(template_doc["file_path"])
                        if file_content:
                            content = file_content.decode('utf-8')
                    except Exception as e:
                        logger.warning(f"Failed to load template file: {e}")
                
                if not content:
                    return {
                        "success": False,
                        "error": f"Template '{template_name}' has no content",
                        "error_type": "no_content"
                    }
            
            # Validate variables against template requirements
            template_vars = template_doc.get("variables", [])
            validation_result = self._validate_template_variables(variables, template_vars)
            if not validation_result["valid"]:
                return {
                    "success": False,
                    "error": f"Variable validation failed: {validation_result['error']}",
                    "error_type": "variable_validation",
                    "missing_variables": validation_result.get("missing", []),
                    "invalid_variables": validation_result.get("invalid", [])
                }
            
            # Render template
            rendered = self.template_processor.render_string(content, variables)
            
            # Cache template content
            if use_cache:
                self._cache_template(template_name, content)
            
            # Update usage statistics
            if self.db_service:
                try:
                    self.db_service.update_document(
                        "templates",
                        {"_id": template_doc["_id"]},
                        {
                            "$inc": {"usage_count": 1},
                            "$set": {"last_used_at": datetime.utcnow()}
                        }
                    )
                except Exception as e:
                    logger.warning(f"Failed to update template usage statistics: {e}")
            
            return {
                "success": True,
                "rendered_content": rendered,
                "from_cache": False,
                "template_info": {
                    "id": str(template_doc["_id"]),
                    "name": template_doc["name"],
                    "version": template_doc.get("version"),
                    "category": template_doc.get("category")
                }
            }
            
        except Exception as e:
            logger.error(f"Error rendering template: {e}")
            return {
                "success": False,
                "error": str(e),
                "error_type": "unexpected"
            }
    
    def preview_template(self, template_name: str, 
                        sample_variables: Dict[str, Any] = None) -> Dict[str, Any]:
        """Preview template with sample data"""
        try:
            # Get template
            template_doc = self.get_template(template_name=template_name)
            if not template_doc:
                return {
                    "success": False,
                    "error": f"Template '{template_name}' not found",
                    "error_type": "not_found"
                }
            
            # Generate sample variables if not provided
            if not sample_variables:
                sample_variables = self._generate_sample_variables(
                    template_doc.get("variables", [])
                )
            
            # Render template
            result = self.render_template(template_name, sample_variables, use_cache=False)
            
            if result["success"]:
                result["sample_variables"] = sample_variables
                result["template_variables"] = template_doc.get("variables", [])
            
            return result
            
        except Exception as e:
            logger.error(f"Error previewing template: {e}")
            return {
                "success": False,
                "error": str(e),
                "error_type": "unexpected"
            }
    
    def get_template_variables(self, template_name: str) -> List[Dict[str, Any]]:
        """Get template variable definitions"""
        template_doc = self.get_template(template_name=template_name)
        if template_doc:
            return template_doc.get("variables", [])
        return []
    
    def validate_template_data(self, template_name: str, 
                              data: Dict[str, Any]) -> Dict[str, Any]:
        """Validate data against template requirements"""
        template_doc = self.get_template(template_name=template_name)
        if not template_doc:
            return {
                "valid": False,
                "error": f"Template '{template_name}' not found"
            }
        
        template_vars = template_doc.get("variables", [])
        return self._validate_template_variables(data, template_vars)
    
    def get_template_categories(self) -> List[str]:
        """Get list of template categories"""
        if not self.db_service:
            return []
        
        try:
            pipeline = [
                {"$match": {"status": "active"}},
                {"$group": {"_id": "$category"}},
                {"$sort": {"_id": 1}}
            ]
            
            result = list(self.db_service.aggregate("templates", pipeline))
            categories = [item["_id"] for item in result if item["_id"]]
            return categories
            
        except Exception as e:
            logger.error(f"Error getting template categories: {e}")
            return []
    
    def get_template_statistics(self, user_id: str = None) -> Dict[str, Any]:
        """Get template usage statistics"""
        if not self.db_service:
            return {}
        
        try:
            pipeline = []
            
            # Filter by user if specified
            if user_id:
                pipeline.append({"$match": {"author_id": user_id}})
            
            # Group and calculate statistics
            pipeline.extend([
                {
                    "$group": {
                        "_id": None,
                        "total_templates": {"$sum": 1},
                        "total_usage": {"$sum": "$usage_count"},
                        "by_category": {
                            "$push": {
                                "category": "$category",
                                "usage": "$usage_count"
                            }
                        },
                        "by_status": {
                            "$push": "$status"
                        }
                    }
                }
            ])
            
            result = list(self.db_service.aggregate("templates", pipeline))
            
            if result:
                stats = result[0]
                
                # Process category statistics
                category_stats = {}
                for item in stats.get("by_category", []):
                    category = item.get("category", "uncategorized")
                    if category not in category_stats:
                        category_stats[category] = {"count": 0, "total_usage": 0}
                    category_stats[category]["count"] += 1
                    category_stats[category]["total_usage"] += item.get("usage", 0)
                
                # Process status statistics
                status_stats = {}
                for status in stats.get("by_status", []):
                    status_stats[status] = status_stats.get(status, 0) + 1
                
                return {
                    "total_templates": stats.get("total_templates", 0),
                    "total_usage": stats.get("total_usage", 0),
                    "by_category": category_stats,
                    "by_status": status_stats
                }
            
            return {
                "total_templates": 0,
                "total_usage": 0,
                "by_category": {},
                "by_status": {}
            }
            
        except Exception as e:
            logger.error(f"Error getting template statistics: {e}")
            return {}
    
    def _validate_template_content(self, content: str) -> Dict[str, Any]:
        """Validate template content"""
        try:
            # Try to parse as Jinja2 template
            template = Jinja2Template(content)
            
            # Basic validation - check for common issues
            if not content.strip():
                return {"valid": False, "error": "Template content is empty"}
            
            # Check for balanced tags (basic check)
            open_tags = content.count('{%')
            close_tags = content.count('%}')
            if open_tags != close_tags:
                return {"valid": False, "error": "Unbalanced template tags"}
            
            open_vars = content.count('{{')
            close_vars = content.count('}}')
            if open_vars != close_vars:
                return {"valid": False, "error": "Unbalanced variable tags"}
            
            return {"valid": True}
            
        except Exception as e:
            return {"valid": False, "error": f"Template syntax error: {str(e)}"}
    
    def _validate_template_variables(self, data: Dict[str, Any], 
                                   template_vars: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Validate data against template variable requirements"""
        try:
            missing = []
            invalid = []
            
            for var_def in template_vars:
                var_name = var_def.get("name")
                var_type = var_def.get("type", "string")
                required = var_def.get("required", False)
                
                if required and var_name not in data:
                    missing.append(var_name)
                    continue
                
                if var_name in data:
                    value = data[var_name]
                    
                    # Type validation
                    if var_type == "string" and not isinstance(value, str):
                        invalid.append({"name": var_name, "error": "Expected string"})
                    elif var_type == "number" and not isinstance(value, (int, float)):
                        invalid.append({"name": var_name, "error": "Expected number"})
                    elif var_type == "boolean" and not isinstance(value, bool):
                        invalid.append({"name": var_name, "error": "Expected boolean"})
                    elif var_type == "array" and not isinstance(value, list):
                        invalid.append({"name": var_name, "error": "Expected array"})
                    elif var_type == "object" and not isinstance(value, dict):
                        invalid.append({"name": var_name, "error": "Expected object"})
            
            if missing or invalid:
                error_msg = []
                if missing:
                    error_msg.append(f"Missing required variables: {', '.join(missing)}")
                if invalid:
                    invalid_msgs = [f"{item['name']}: {item['error']}" for item in invalid]
                    error_msg.append(f"Invalid variables: {'; '.join(invalid_msgs)}")
                
                return {
                    "valid": False,
                    "error": "; ".join(error_msg),
                    "missing": missing,
                    "invalid": invalid
                }
            
            return {"valid": True}
            
        except Exception as e:
            return {"valid": False, "error": f"Validation error: {str(e)}"}
    
    def _generate_sample_variables(self, template_vars: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Generate sample data for template variables"""
        sample_data = {}
        
        for var_def in template_vars:
            var_name = var_def.get("name")
            var_type = var_def.get("type", "string")
            default_value = var_def.get("default_value")
            
            if default_value is not None:
                sample_data[var_name] = default_value
            elif var_type == "string":
                sample_data[var_name] = f"Sample {var_name}"
            elif var_type == "number":
                sample_data[var_name] = 42
            elif var_type == "boolean":
                sample_data[var_name] = True
            elif var_type == "array":
                sample_data[var_name] = ["Item 1", "Item 2", "Item 3"]
            elif var_type == "object":
                sample_data[var_name] = {"key": "value"}
            else:
                sample_data[var_name] = f"Sample {var_name}"
        
        return sample_data
    
    def _get_cached_template(self, template_name: str) -> Optional[str]:
        """Get template content from cache"""
        if template_name in self.template_cache:
            cache_entry = self.template_cache[template_name]
            if datetime.utcnow() - cache_entry["timestamp"] < timedelta(seconds=self.cache_ttl):
                return cache_entry["content"]
            else:
                # Remove expired cache entry
                del self.template_cache[template_name]
        return None
    
    def _cache_template(self, template_name: str, content: str):
        """Cache template content"""
        self.template_cache[template_name] = {
            "content": content,
            "timestamp": datetime.utcnow()
        }
    
    def _clear_template_cache(self, template_name: str = None):
        """Clear template cache"""
        if template_name:
            self.template_cache.pop(template_name, None)
        else:
            self.template_cache.clear()
    
    def cleanup_old_templates(self, days_old: int = 90) -> int:
        """Clean up old unused templates"""
        if not self.db_service:
            return 0
        
        try:
            cutoff_date = datetime.utcnow() - timedelta(days=days_old)
            
            # Find old unused templates
            query = {
                "$or": [
                    {"last_used_at": {"$lt": cutoff_date}},
                    {"last_used_at": {"$exists": False}, "created_at": {"$lt": cutoff_date}}
                ],
                "usage_count": {"$lte": 0}
            }
            
            old_templates = self.db_service.find("templates", query)
            
            deleted_count = 0
            for template in old_templates:
                result = self.delete_template(str(template["_id"]))
                if result["success"]:
                    deleted_count += 1
            
            logger.info(f"Cleaned up {deleted_count} old templates")
            return deleted_count
            
        except Exception as e:
            logger.error(f"Error cleaning up old templates: {e}")
            return 0


# Global template service instance
template_service = TemplateService()