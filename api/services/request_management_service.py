"""
Request Management Service for Pre-Authorization Workflow.

Handles complete request lifecycle including storage, status tracking,
patient history integration, and workflow management.
"""

import json
import uuid
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple
from loguru import logger

from api.models import (
    PreAuthRequest, PatientHistory, RequestStatus, RequestPriority,
    DecisionOutcome, RequestInboxFilter, DecisionSubmission
)
from api.services.patient_lookup_service import get_patient_lookup_service


class RequestManagementService:
    """Service for managing pre-authorization requests and patient history."""
    
    def __init__(self, storage_path: str = "data/requests"):
        """Initialize request management service.
        
        Args:
            storage_path: Base directory for request storage
        """
        self.storage_path = Path(storage_path)
        self.storage_path.mkdir(parents=True, exist_ok=True)
        
        # Storage subdirectories
        self.requests_dir = self.storage_path / "requests"
        self.patient_history_dir = self.storage_path / "patient_history" 
        self.index_dir = self.storage_path / "indexes"
        
        for dir_path in [self.requests_dir, self.patient_history_dir, self.index_dir]:
            dir_path.mkdir(exist_ok=True)
            
        self.patient_service = get_patient_lookup_service()
        
        # Initialize indexes
        self._initialize_indexes()
    
    def _initialize_indexes(self):
        """Initialize or load existing indexes for fast queries."""
        try:
            # Status index
            self.status_index_file = self.index_dir / "status_index.json"
            if self.status_index_file.exists():
                with open(self.status_index_file, 'r') as f:
                    self.status_index = json.load(f)
            else:
                self.status_index = {status.value: [] for status in RequestStatus}
            
            # Patient index
            self.patient_index_file = self.index_dir / "patient_index.json"
            if self.patient_index_file.exists():
                with open(self.patient_index_file, 'r') as f:
                    self.patient_index = json.load(f)
            else:
                self.patient_index = {}
                
            # Assignee index
            self.assignee_index_file = self.index_dir / "assignee_index.json"
            if self.assignee_index_file.exists():
                with open(self.assignee_index_file, 'r') as f:
                    self.assignee_index = json.load(f)
            else:
                self.assignee_index = {}
                
        except Exception as e:
            logger.warning(f"Failed to load indexes, starting fresh: {e}")
            self.status_index = {status.value: [] for status in RequestStatus}
            self.patient_index = {}
            self.assignee_index = {}
    
    def _save_indexes(self):
        """Save indexes to disk."""
        try:
            with open(self.status_index_file, 'w') as f:
                json.dump(self.status_index, f)
            with open(self.patient_index_file, 'w') as f:
                json.dump(self.patient_index, f)
            with open(self.assignee_index_file, 'w') as f:
                json.dump(self.assignee_index, f)
        except Exception as e:
            logger.error(f"Failed to save indexes: {e}")
    
    def create_request_from_pipeline(
        self,
        xml_filename: str,
        xml_format: str,
        xml_content: str,
        pipeline_result: Dict[str, Any],
        submitted_by: Optional[str] = None
    ) -> PreAuthRequest:
        """Create a new request from pipeline processing results.
        
        Args:
            xml_filename: Original XML filename
            xml_format: XML format (eclaim/shafafiya)
            xml_content: Original XML content
            pipeline_result: Complete pipeline processing results
            submitted_by: Provider/user who submitted the request
            
        Returns:
            Created PreAuthRequest object
        """
        try:
            # Generate unique request ID
            request_id = f"REQ-{datetime.now().strftime('%Y%m%d')}-{str(uuid.uuid4())[:8].upper()}"
            
            # Extract patient ID from pipeline results
            intake_data = pipeline_result.get("intake", {})
            patient_id = intake_data.get("patient_id", "Unknown")
            
            # Determine priority based on urgency indicators
            priority = self._calculate_priority(pipeline_result)
            
            # Create request object
            request = PreAuthRequest(
                request_id=request_id,
                patient_id=patient_id,
                xml_filename=xml_filename,
                xml_format=xml_format,
                xml_content=xml_content,
                submitted_by=submitted_by,
                priority=priority,
                status=RequestStatus.PENDING,
                
                # Store pipeline results
                intake_data=pipeline_result.get("intake"),
                clinical_summary=pipeline_result.get("clinical_summary"),
                evidence_data=pipeline_result.get("evidence"),
                checklist_data=pipeline_result.get("checklist"),
                decision_data=pipeline_result.get("decision"),
                dossier_data=pipeline_result.get("dossier"),
                
                # Performance metrics
                processing_time_seconds=pipeline_result.get("timings", {}).get("total_ms", 0) / 1000,
                cost_usd=pipeline_result.get("cost", {}).get("total_cost_usd", 0.0),
                audit_trail=pipeline_result.get("audit_trail")
            )
            
            # Save request
            self._save_request(request)
            
            # Update patient history
            self._update_patient_history(patient_id, request)
            
            # Update indexes
            self._update_indexes(request)
            
            logger.info(f"Created request {request_id} for patient {patient_id}")
            return request
            
        except Exception as e:
            logger.error(f"Failed to create request from pipeline: {e}")
            raise
    
    def _calculate_priority(self, pipeline_result: Dict[str, Any]) -> RequestPriority:
        """Calculate request priority based on pipeline results.
        
        Args:
            pipeline_result: Pipeline processing results
            
        Returns:
            Calculated priority level
        """
        try:
            # Check for urgent indicators
            clinical_summary = pipeline_result.get("clinical_summary", {})
            intake = pipeline_result.get("intake", {})
            
            # High priority indicators
            urgent_keywords = ["emergency", "urgent", "acute", "critical", "life-threatening"]
            high_cost_threshold = 50000.0  # AED
            
            # Check clinical urgency
            summary_text = str(clinical_summary.get("clinical_narrative", "")).lower()
            if any(keyword in summary_text for keyword in urgent_keywords):
                return RequestPriority.URGENT
            
            # Check procedure cost
            procedures = intake.get("procedures", [])
            total_cost = sum(proc.get("amount", 0) for proc in procedures)
            if total_cost > high_cost_threshold:
                return RequestPriority.HIGH
                
            # Check age-based priority (elderly patients)
            patient_age = intake.get("patient_age")
            if patient_age and patient_age >= 75:
                return RequestPriority.HIGH
                
            # Check multiple procedures
            if len(procedures) > 3:
                return RequestPriority.HIGH
                
            return RequestPriority.MEDIUM
            
        except Exception as e:
            logger.warning(f"Priority calculation failed, using medium: {e}")
            return RequestPriority.MEDIUM
    
    def _save_request(self, request: PreAuthRequest):
        """Save request to disk storage."""
        try:
            request_file = self.requests_dir / f"{request.request_id}.json"
            with open(request_file, 'w', encoding='utf-8') as f:
                json.dump(request.model_dump(), f, indent=2, default=str)
        except Exception as e:
            logger.error(f"Failed to save request {request.request_id}: {e}")
            raise
    
    def _load_request(self, request_id: str) -> Optional[PreAuthRequest]:
        """Load request from disk storage."""
        try:
            request_file = self.requests_dir / f"{request_id}.json"
            if not request_file.exists():
                return None
                
            with open(request_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                return PreAuthRequest(**data)
        except Exception as e:
            logger.error(f"Failed to load request {request_id}: {e}")
            return None
    
    def _update_indexes(self, request: PreAuthRequest):
        """Update indexes with new request."""
        try:
            # Status index
            if request.request_id not in self.status_index[request.status.value]:
                self.status_index[request.status.value].append(request.request_id)
            
            # Patient index
            if request.patient_id not in self.patient_index:
                self.patient_index[request.patient_id] = []
            if request.request_id not in self.patient_index[request.patient_id]:
                self.patient_index[request.patient_id].append(request.request_id)
            
            # Assignee index
            if request.assigned_to:
                if request.assigned_to not in self.assignee_index:
                    self.assignee_index[request.assigned_to] = []
                if request.request_id not in self.assignee_index[request.assigned_to]:
                    self.assignee_index[request.assigned_to].append(request.request_id)
            
            self._save_indexes()
            
        except Exception as e:
            logger.error(f"Failed to update indexes: {e}")
    
    def _update_patient_history(self, patient_id: str, request: PreAuthRequest):
        """Update patient history with new request."""
        try:
            history_file = self.patient_history_dir / f"{patient_id}_history.json"
            
            # Load existing history or create new
            if history_file.exists():
                with open(history_file, 'r', encoding='utf-8') as f:
                    history_data = json.load(f)
                    history = PatientHistory(**history_data)
            else:
                # Get patient profile
                patient_profile = self.patient_service.get_patient_profile(patient_id)
                
                history = PatientHistory(
                    patient_id=patient_id,
                    total_requests=0,
                    first_request_date=request.created_at,
                    last_request_date=request.created_at,
                    patient_profile=patient_profile
                )
            
            # Update history with new request
            history.total_requests += 1
            history.last_request_date = request.created_at
            
            # Update counts based on status
            if request.status == RequestStatus.PENDING:
                history.pending_count += 1
            
            # Extract clinical data
            if request.intake_data:
                # Add conditions
                diagnoses = request.intake_data.get("diagnoses", [])
                for diagnosis in diagnoses:
                    condition = diagnosis.get("description", "")
                    if condition and condition not in history.conditions:
                        history.conditions.append(condition)
                
                # Add procedures
                procedures = request.intake_data.get("procedures", [])
                for procedure in procedures:
                    proc_name = procedure.get("description", "")
                    if proc_name and proc_name not in history.procedures:
                        history.procedures.append(proc_name)
                
                # Add medications
                medications = request.intake_data.get("medications", [])
                for medication in medications:
                    med_name = medication.get("name", "")
                    if med_name and med_name not in history.medications:
                        history.medications.append(med_name)
            
            # Add to recent requests (keep last 10)
            request_summary = {
                "request_id": request.request_id,
                "created_at": request.created_at.isoformat(),
                "status": request.status.value,
                "priority": request.priority.value,
                "xml_filename": request.xml_filename,
                "decision": request.final_decision.value if request.final_decision else None
            }
            
            history.recent_requests.insert(0, request_summary)
            history.recent_requests = history.recent_requests[:10]  # Keep only last 10
            
            # Check for high-cost request
            if request.cost_usd and request.cost_usd > 100:  # USD threshold
                history.high_cost_requests += 1
            
            # Check for emergency request
            if request.priority == RequestPriority.URGENT:
                history.emergency_requests += 1
            
            # Save updated history
            with open(history_file, 'w', encoding='utf-8') as f:
                json.dump(history.model_dump(), f, indent=2, default=str)
                
        except Exception as e:
            logger.error(f"Failed to update patient history for {patient_id}: {e}")
    
    def get_request_inbox(
        self,
        filters: RequestInboxFilter
    ) -> Tuple[List[PreAuthRequest], int, Dict[str, Any]]:
        """Get filtered list of requests for inbox display.
        
        Args:
            filters: Request filters and pagination
            
        Returns:
            Tuple of (requests, total_count, summary_stats)
        """
        try:
            # Get all request IDs that match filters
            matching_request_ids = self._filter_request_ids(filters)
            
            # Load matching requests
            requests = []
            for request_id in matching_request_ids:
                request = self._load_request(request_id)
                if request:
                    requests.append(request)
            
            # Sort by priority and creation date
            requests.sort(key=lambda r: (
                r.priority == RequestPriority.URGENT,
                r.priority == RequestPriority.HIGH,
                r.created_at
            ), reverse=True)
            
            total_count = len(requests)
            
            # Apply pagination
            start_idx = filters.offset
            end_idx = start_idx + filters.limit
            paginated_requests = requests[start_idx:end_idx]
            
            # Calculate summary statistics
            summary_stats = self._calculate_inbox_summary(requests)
            
            return paginated_requests, total_count, summary_stats
            
        except Exception as e:
            logger.error(f"Failed to get request inbox: {e}")
            return [], 0, {}
    
    def _filter_request_ids(self, filters: RequestInboxFilter) -> List[str]:
        """Filter request IDs based on criteria."""
        try:
            # Start with all request IDs
            all_request_ids = set()
            for status_requests in self.status_index.values():
                all_request_ids.update(status_requests)
            
            matching_ids = all_request_ids.copy()
            
            # Filter by status
            if filters.status:
                status_ids = set()
                for status in filters.status:
                    status_ids.update(self.status_index.get(status.value, []))
                matching_ids &= status_ids
            
            # Filter by patient
            if filters.patient_id:
                patient_ids = set(self.patient_index.get(filters.patient_id, []))
                matching_ids &= patient_ids
            
            # Filter by assignee
            if filters.assigned_to:
                assignee_ids = set(self.assignee_index.get(filters.assigned_to, []))
                matching_ids &= assignee_ids
            
            # Date filtering requires loading requests (expensive for large datasets)
            if filters.date_from or filters.date_to:
                date_filtered_ids = []
                for request_id in matching_ids:
                    request = self._load_request(request_id)
                    if request:
                        if filters.date_from and request.created_at < filters.date_from:
                            continue
                        if filters.date_to and request.created_at > filters.date_to:
                            continue
                        date_filtered_ids.append(request_id)
                matching_ids = set(date_filtered_ids)
            
            return list(matching_ids)
            
        except Exception as e:
            logger.error(f"Failed to filter request IDs: {e}")
            return []
    
    def _calculate_inbox_summary(self, requests: List[PreAuthRequest]) -> Dict[str, Any]:
        """Calculate summary statistics for inbox."""
        try:
            if not requests:
                return {}
            
            # Status counts
            status_counts = {}
            for status in RequestStatus:
                status_counts[status.value] = len([r for r in requests if r.status == status])
            
            # Priority counts
            priority_counts = {}
            for priority in RequestPriority:
                priority_counts[priority.value] = len([r for r in requests if r.priority == priority])
            
            # Time-based metrics
            now = datetime.utcnow()
            avg_age_hours = sum(
                (now - r.created_at).total_seconds() / 3600 for r in requests
            ) / len(requests)
            
            # Cost metrics
            total_cost = sum(r.cost_usd or 0 for r in requests)
            avg_cost = total_cost / len(requests)
            
            return {
                "total_requests": len(requests),
                "status_breakdown": status_counts,
                "priority_breakdown": priority_counts,
                "average_age_hours": round(avg_age_hours, 2),
                "total_cost_usd": round(total_cost, 2),
                "average_cost_usd": round(avg_cost, 2),
                "unassigned_count": len([r for r in requests if not r.assigned_to]),
                "overdue_count": len([
                    r for r in requests 
                    if r.status == RequestStatus.UNDER_REVIEW 
                    and (now - r.created_at).days > 3
                ])
            }
            
        except Exception as e:
            logger.error(f"Failed to calculate inbox summary: {e}")
            return {}
    
    def get_request_details(self, request_id: str) -> Optional[PreAuthRequest]:
        """Get complete request details by ID.
        
        Args:
            request_id: Request identifier
            
        Returns:
            Complete PreAuthRequest object or None if not found
        """
        return self._load_request(request_id)
    
    def assign_request(
        self,
        request_id: str,
        assigned_to: str,
        priority: Optional[RequestPriority] = None,
        notes: Optional[str] = None
    ) -> bool:
        """Assign request to medical director.
        
        Args:
            request_id: Request identifier
            assigned_to: Medical director identifier
            priority: Optional priority update
            notes: Assignment notes
            
        Returns:
            True if assignment successful, False otherwise
        """
        try:
            request = self._load_request(request_id)
            if not request:
                return False
            
            # Update assignment
            old_assignee = request.assigned_to
            request.assigned_to = assigned_to
            request.updated_at = datetime.utcnow()
            
            if priority:
                request.priority = priority
            
            # Update status to under review if pending
            if request.status == RequestStatus.PENDING:
                request.status = RequestStatus.UNDER_REVIEW
            
            # Save updated request
            self._save_request(request)
            
            # Update indexes
            if old_assignee and old_assignee in self.assignee_index:
                if request_id in self.assignee_index[old_assignee]:
                    self.assignee_index[old_assignee].remove(request_id)
            
            self._update_indexes(request)
            
            logger.info(f"Assigned request {request_id} to {assigned_to}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to assign request {request_id}: {e}")
            return False
    
    def submit_decision(
        self,
        request_id: str,
        decision: DecisionSubmission,
        decided_by: str
    ) -> bool:
        """Submit final decision for request.
        
        Args:
            request_id: Request identifier
            decision: Decision details
            decided_by: Medical director making decision
            
        Returns:
            True if decision submitted successfully, False otherwise
        """
        try:
            request = self._load_request(request_id)
            if not request:
                return False
            
            # Update decision fields
            request.final_decision = decision.decision
            request.decision_rationale = decision.rationale
            request.decision_conditions = decision.conditions
            request.decided_by = decided_by
            request.decided_at = datetime.utcnow()
            request.updated_at = datetime.utcnow()
            request.status = RequestStatus.DECIDED
            
            # Save updated request
            self._save_request(request)
            
            # Update patient history decision counts
            self._update_patient_decision_history(request.patient_id, decision.decision)
            
            # Update indexes
            self._update_indexes(request)
            
            logger.info(f"Decision submitted for request {request_id}: {decision.decision.value}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to submit decision for {request_id}: {e}")
            return False
    
    def _update_patient_decision_history(self, patient_id: str, decision: DecisionOutcome):
        """Update patient history with decision outcome."""
        try:
            history_file = self.patient_history_dir / f"{patient_id}_history.json"
            if not history_file.exists():
                return
            
            with open(history_file, 'r', encoding='utf-8') as f:
                history_data = json.load(f)
                history = PatientHistory(**history_data)
            
            # Update decision counts
            if decision == DecisionOutcome.APPROVED:
                history.approved_count += 1
            elif decision == DecisionOutcome.DENIED:
                history.denied_count += 1
            
            # Decrease pending count
            if history.pending_count > 0:
                history.pending_count -= 1
            
            # Save updated history
            with open(history_file, 'w', encoding='utf-8') as f:
                json.dump(history.model_dump(), f, indent=2, default=str)
                
        except Exception as e:
            logger.error(f"Failed to update patient decision history: {e}")
    
    def get_patient_history(self, patient_id: str) -> Optional[PatientHistory]:
        """Get complete patient history.
        
        Args:
            patient_id: Patient identifier
            
        Returns:
            PatientHistory object or None if not found
        """
        try:
            history_file = self.patient_history_dir / f"{patient_id}_history.json"
            if not history_file.exists():
                return None
            
            with open(history_file, 'r', encoding='utf-8') as f:
                history_data = json.load(f)
                return PatientHistory(**history_data)
                
        except Exception as e:
            logger.error(f"Failed to get patient history for {patient_id}: {e}")
            return None
    
    def get_patient_timeline(self, patient_id: str) -> List[Dict[str, Any]]:
        """Get chronological timeline of patient events.
        
        Args:
            patient_id: Patient identifier
            
        Returns:
            List of timeline events sorted by date
        """
        try:
            timeline = []
            
            # Get all request IDs for patient
            request_ids = self.patient_index.get(patient_id, [])
            
            # Load all requests and extract timeline events
            for request_id in request_ids:
                request = self._load_request(request_id)
                if not request:
                    continue
                
                # Request submitted event
                timeline.append({
                    "date": request.created_at,
                    "type": "request_submitted",
                    "title": f"Request {request.request_id} Submitted",
                    "description": f"Pre-authorization request for {request.xml_filename}",
                    "request_id": request.request_id,
                    "priority": request.priority.value,
                    "status": request.status.value
                })
                
                # Assignment event
                if request.assigned_to:
                    timeline.append({
                        "date": request.updated_at,
                        "type": "request_assigned",
                        "title": f"Request Assigned",
                        "description": f"Assigned to {request.assigned_to}",
                        "request_id": request.request_id,
                        "assigned_to": request.assigned_to
                    })
                
                # Decision event
                if request.decided_at:
                    timeline.append({
                        "date": request.decided_at,
                        "type": "decision_made",
                        "title": f"Decision: {request.final_decision.value.title()}",
                        "description": request.decision_rationale or "Decision made",
                        "request_id": request.request_id,
                        "decision": request.final_decision.value,
                        "decided_by": request.decided_by
                    })
                
                # Communication event
                if request.communicated_at:
                    timeline.append({
                        "date": request.communicated_at,
                        "type": "decision_communicated",
                        "title": "Decision Communicated",
                        "description": f"Decision communicated via {request.communication_method}",
                        "request_id": request.request_id
                    })
            
            # Sort timeline by date (newest first)
            timeline.sort(key=lambda x: x["date"], reverse=True)
            
            return timeline
            
        except Exception as e:
            logger.error(f"Failed to get patient timeline for {patient_id}: {e}")
            return []
    
    def mark_communicated(
        self,
        request_id: str,
        communication_method: str = "api"
    ) -> bool:
        """Mark request decision as communicated.
        
        Args:
            request_id: Request identifier
            communication_method: How decision was communicated
            
        Returns:
            True if successful, False otherwise
        """
        try:
            request = self._load_request(request_id)
            if not request:
                return False
            
            request.status = RequestStatus.COMMUNICATED
            request.communicated_at = datetime.utcnow()
            request.communication_method = communication_method
            request.updated_at = datetime.utcnow()
            
            self._save_request(request)
            self._update_indexes(request)
            
            logger.info(f"Marked request {request_id} as communicated")
            return True
            
        except Exception as e:
            logger.error(f"Failed to mark request {request_id} as communicated: {e}")
            return False
    
    def get_dashboard_metrics(self) -> Dict[str, Any]:
        """Get comprehensive dashboard metrics.
        
        Returns:
            Dictionary containing various metrics and statistics
        """
        try:
            # Load all requests for metrics calculation
            all_requests = []
            for status_requests in self.status_index.values():
                for request_id in status_requests:
                    request = self._load_request(request_id)
                    if request:
                        all_requests.append(request)
            
            if not all_requests:
                return {
                    "total_requests": 0,
                    "status_distribution": {},
                    "priority_distribution": {},
                    "recent_activity": [],
                    "performance_metrics": {}
                }
            
            # Calculate various metrics
            now = datetime.utcnow()
            
            # Status distribution
            status_dist = {}
            for status in RequestStatus:
                status_dist[status.value] = len([r for r in all_requests if r.status == status])
            
            # Priority distribution
            priority_dist = {}
            for priority in RequestPriority:
                priority_dist[priority.value] = len([r for r in all_requests if r.priority == priority])
            
            # Recent activity (last 7 days)
            week_ago = now - timedelta(days=7)
            recent_requests = [r for r in all_requests if r.created_at >= week_ago]
            
            # Performance metrics
            avg_processing_time = sum(r.processing_time_seconds or 0 for r in all_requests) / len(all_requests)
            total_cost = sum(r.cost_usd or 0 for r in all_requests)
            
            # Decision metrics
            decided_requests = [r for r in all_requests if r.final_decision]
            approval_rate = 0
            if decided_requests:
                approved = len([r for r in decided_requests if r.final_decision == DecisionOutcome.APPROVED])
                approval_rate = (approved / len(decided_requests)) * 100
            
            return {
                "total_requests": len(all_requests),
                "status_distribution": status_dist,
                "priority_distribution": priority_dist,
                "recent_activity_count": len(recent_requests),
                "performance_metrics": {
                    "average_processing_time_seconds": round(avg_processing_time, 2),
                    "total_cost_usd": round(total_cost, 2),
                    "approval_rate_percent": round(approval_rate, 1),
                    "total_decided": len(decided_requests),
                    "pending_requests": len([r for r in all_requests if r.status == RequestStatus.PENDING])
                },
                "recent_activity": [
                    {
                        "request_id": r.request_id,
                        "patient_id": r.patient_id,
                        "created_at": r.created_at.isoformat(),
                        "status": r.status.value,
                        "priority": r.priority.value
                    }
                    for r in sorted(recent_requests, key=lambda x: x.created_at, reverse=True)[:10]
                ]
            }
            
        except Exception as e:
            logger.error(f"Failed to get dashboard metrics: {e}")
            return {}


# Global service instance
_request_service = None

def get_request_management_service() -> RequestManagementService:
    """Get global request management service instance."""
    global _request_service
    if _request_service is None:
        _request_service = RequestManagementService()
    return _request_service