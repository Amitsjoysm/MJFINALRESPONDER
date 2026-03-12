"""
Error Monitoring Routes
API endpoints to view and manage system errors
"""
from fastapi import APIRouter, Depends, HTTPException
from typing import List, Optional
from datetime import datetime

from routes.auth_routes import get_current_user_from_token, get_db
from models.user import User

router = APIRouter(prefix="/api/errors", tags=["Error Monitoring"])

@router.get("/recent")
async def get_recent_errors(
    limit: int = 50,
    severity: Optional[str] = None,
    user: User = Depends(get_current_user_from_token),
    db = Depends(get_db)
):
    """Get recent errors for monitoring"""
    try:
        query = {}
        
        # Non-admin users only see their own errors
        if user.role != 'super_admin':
            query['user_id'] = user.id
        
        if severity:
            query['severity'] = severity
        
        errors = await db.error_logs.find(query).sort(
            "created_at", -1
        ).limit(limit).to_list(limit)
        
        return errors
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/stats")
async def get_error_stats(
    user: User = Depends(get_current_user_from_token),
    db = Depends(get_db)
):
    """Get error statistics"""
    try:
        query = {}
        if user.role != 'super_admin':
            query['user_id'] = user.id
        
        # Count by severity
        total = await db.error_logs.count_documents(query)
        critical = await db.error_logs.count_documents({**query, "severity": "critical"})
        errors = await db.error_logs.count_documents({**query, "severity": "error"})
        warnings = await db.error_logs.count_documents({**query, "severity": "warning"})
        
        # Unresolved
        unresolved = await db.error_logs.count_documents({**query, "resolved": False})
        
        # Recent (last 24 hours)
        from datetime import timedelta
        yesterday = (datetime.now(datetime.timezone.utc) - timedelta(days=1)).isoformat()
        recent = await db.error_logs.count_documents({
            **query,
            "created_at": {"$gte": yesterday}
        })
        
        return {
            "total": total,
            "by_severity": {
                "critical": critical,
                "error": errors,
                "warning": warnings
            },
            "unresolved": unresolved,
            "last_24h": recent
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.patch("/{error_id}/resolve")
async def resolve_error(
    error_id: str,
    user: User = Depends(get_current_user_from_token),
    db = Depends(get_db)
):
    """Mark an error as resolved"""
    try:
        result = await db.error_logs.update_one(
            {"id": error_id},
            {"$set": {
                "resolved": True,
                "resolved_at": datetime.now(datetime.timezone.utc).isoformat(),
                "resolved_by": user.id
            }}
        )
        
        if result.modified_count == 0:
            raise HTTPException(status_code=404, detail="Error not found")
        
        return {"message": "Error marked as resolved"}
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
