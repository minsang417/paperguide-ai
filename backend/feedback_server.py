import os
from datetime import datetime, timezone

from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.responses import HTMLResponse
from supabase import create_client

from backend.token_utils import (
    verify_feedback_token
)


load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_SERVICE_ROLE_KEY = os.getenv(
    "SUPABASE_SERVICE_ROLE_KEY"
)

supabase = create_client(
    SUPABASE_URL,
    SUPABASE_SERVICE_ROLE_KEY
)

app = FastAPI()


def append_feedback(
    user_id: str,
    paper_id: str,
    rating: str
):
    try:
        supabase.table("feedback_logs").upsert(
            {
                "user_id": user_id,
                "paper_id": paper_id,
                "rating": rating,
                "processed": False,
                "created_at": datetime.now(
                    timezone.utc
                ).isoformat(),
            },
            on_conflict="user_id,paper_id",
        ).execute()

        print(
            f"feedback saved: "
            f"user={user_id}, "
            f"paper={paper_id}, "
            f"rating={rating}",
            flush=True
        )

    except Exception as e:
        print(
            f"feedback save failed: {repr(e)}",
            flush=True
        )
        raise


@app.get("/")
def home():
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
                    PaperGuide AI Feedback Server
                </h1>
                <p style="font-size:18px;">
                    서버가 정상적으로 실행 중입니다.
                </p>
            </div>
        </body>
    </html>
    """)


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
                    이전에 남긴 피드백이 있다면
                    최신 선택으로 업데이트되었습니다.
                </p>
            </div>
        </body>
    </html>
    """)