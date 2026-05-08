import os
from datetime import datetime

from fastapi import FastAPI
from fastapi.responses import HTMLResponse

from backend.token_utils import (
    verify_feedback_token
)

from utils.file_io import (
    load_json,
    save_json
)

FEEDBACK_LOG_PATH = (
    "data/feedback_log.json"
)

app = FastAPI()


def append_feedback(
    user_id: str,
    paper_id: str,
    rating: str
):
    feedback = load_json(
        FEEDBACK_LOG_PATH
    )

    if not isinstance(feedback, list):
        feedback = []

    feedback.append({
        "user_id": user_id,
        "paper_id": paper_id,
        "rating": rating,
        "timestamp": datetime.now().isoformat()
    })

    save_json(
        FEEDBACK_LOG_PATH,
        feedback
    )


@app.get("/feedback")
def feedback(
    token: str,
    rating: str
):
    if rating not in [
        "like",
        "dislike"
    ]:
        return HTMLResponse(
            "<h1>잘못된 요청입니다.</h1>",
            status_code=400
        )

    payload = verify_feedback_token(
        token
    )

    if not payload:
        return HTMLResponse(
            "<h1>유효하지 않은 토큰입니다.</h1>",
            status_code=400
        )

    append_feedback(
        payload["user_id"],
        payload["paper_id"],
        rating
    )

    return HTMLResponse("""
    <html>
        <body style="
            font-family: Arial;
            text-align: center;
            padding-top: 80px;
            background: #f3f4f6;
        ">
            <div style="
                max-width: 600px;
                margin: auto;
                background: white;
                padding: 40px;
                border-radius: 20px;
                box-shadow: 0 4px 16px rgba(0,0,0,0.08);
            ">
                <h1 style="color:#2563eb;">
                    피드백 반영 완료
                </h1>

                <p style="
                    font-size:18px;
                    line-height:1.6;
                ">
                    PaperGuide AI가
                    다음 추천을 더 잘 준비할게요.
                </p>
            </div>
        </body>
    </html>
    """)