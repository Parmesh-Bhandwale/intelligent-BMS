from app.services.ai_service import AIService
from app.services.book_service import update_book_summary
from app.core.job_store import jobs

ai_service = AIService()

async def process_book_summary(
    job_id: str,
    title: str,
    content: str,
):
    try:
        jobs[job_id]["status"] = "processing"

        summary = await ai_service.generate_book_summary(title, content)
        await update_book_summary(db=None, book_id=None, summary=summary)  # db and book_id are placeholders
        jobs[job_id] = {
            "status": "completed",
            "summary": summary
        }

    except Exception as e:
        jobs[job_id] = {
            "status": "failed",
            "error": str(e)
        }
