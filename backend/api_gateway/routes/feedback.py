"""Beta feedback endpoints (Phase 7.6)."""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from backend.shared.auth import get_current_user
from backend.shared.database import get_db
from backend.shared.schemas import FeedbackSubmission
from backend.shared.logging import api_logger

router = APIRouter()


@router.post("/", status_code=201)
async def submit_feedback(
    feedback: FeedbackSubmission,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Submit beta feedback.

    Users can submit feedback about the application, report bugs,
    or suggest features during the beta period.
    """

    # Log feedback (in production, also save to database and/or send to Slack)
    api_logger.info(
        "Beta feedback received",
        user_id=current_user["user_id"],
        tenant_id=current_user["tenant_id"],
        email=current_user["email"],
        page=feedback.page,
        message=feedback.message,
        rating=feedback.rating
    )

    # TODO: In production, implement:
    # 1. Save to database (create FeedbackSubmission model)
    # 2. Send to Slack channel (#beta-feedback)
    # 3. Send confirmation email to user
    # 4. Trigger alert if rating <= 2

    # Example Slack webhook (uncomment in production):
    # import httpx
    # slack_webhook_url = settings.slack_feedback_webhook
    # slack_message = {
    #     "text": f"📝 Beta Feedback from {current_user['email']}",
    #     "blocks": [
    #         {
    #             "type": "section",
    #             "text": {"type": "mrkdwn", "text": f"*Feedback:* {feedback.message}"}
    #         },
    #         {
    #             "type": "section",
    #             "text": {"type": "mrkdwn", "text": f"*Page:* {feedback.page or 'N/A'}"}
    #         },
    #         {
    #             "type": "section",
    #             "text": {"type": "mrkdwn", "text": f"*Rating:* {'⭐' * (feedback.rating or 0)}"}
    #         }
    #     ]
    # }
    # async with httpx.AsyncClient() as client:
    #     await client.post(slack_webhook_url, json=slack_message)

    return {
        "status": "success",
        "message": "Thank you for your feedback! We review every submission."
    }


@router.get("/stats")
async def get_feedback_stats(
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get feedback statistics (admin only).

    Returns aggregated feedback metrics for beta analysis.
    """

    # Check if user is admin
    if current_user.get("subscription_tier") != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")

    # TODO: Implement feedback statistics
    # For now, return placeholder

    return {
        "total_feedback": 0,
        "average_rating": 0.0,
        "feedback_by_page": {},
        "recent_feedback": []
    }
