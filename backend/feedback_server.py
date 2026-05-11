import os
from datetime import datetime, timezone
from uuid import uuid4

from dotenv import load_dotenv
from fastapi import FastAPI, Form
from fastapi.responses import HTMLResponse
from supabase import create_client

from backend.token_utils import (
    verify_feedback_token,
    verify_unsubscribe_token
)

from users.data_store import (
    email_exists,
    create_user,
    deactivate_user
)

from backend.token_utils import (
    verify_feedback_token
)

from users.data_store import (
    email_exists,
    create_user
)

from keywords.ai_interest_mapper import (
    map_interest_to_canonical_keywords
)

from backend.token_utils import (
    verify_feedback_token,
    verify_unsubscribe_token
)

from users.data_store import (
    email_exists,
    create_user,
    deactivate_user,
    update_delivery_frequency
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


REPRESENTATIVE_KEYWORDS = [
    "cancer",
    "immunotherapy",
    "genetics",
    "aging",
    "neuroscience",
    "protein",
    "cell",
    "inflammation",
    "machine_learning",
    "physics",
    "mathematics"
]

DEFAULT_WEIGHT = 0.1
SELECTED_WEIGHT = 1.0

def build_initial_keyword_weights(
    selected_keywords,
    custom_interests: str
):
    keyword_weights = {
        keyword: DEFAULT_WEIGHT
        for keyword in REPRESENTATIVE_KEYWORDS
    }

    mapping_results = []

    for keyword in selected_keywords:
        if keyword in REPRESENTATIVE_KEYWORDS:
            keyword_weights[keyword] = SELECTED_WEIGHT

            mapping_results.append({
                "input": keyword,
                "matched": keyword,
                "source": "checkbox",
                "reason": "대표 관심사로 선택됨"
            })

    custom_terms = [
        term.strip()
        for term in custom_interests.split(",")
        if term.strip()
    ]

    for term in custom_terms:
        matches = map_interest_to_canonical_keywords(
            term,
            max_matches=3
        )

        if not matches:
            mapping_results.append({
                "input": term,
                "matched": None,
                "source": "custom",
                "reason": "명확히 연결되는 canonical keyword를 찾지 못함"
            })
            continue

        for match in matches:
            canonical_name = match["canonical_name"]

            keyword_weights[canonical_name] = SELECTED_WEIGHT

            mapping_results.append({
                "input": term,
                "matched": canonical_name,
                "source": "custom",
                "reason": match.get("reason", "")
            })

    return keyword_weights, mapping_results

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


@app.get("/signup")
def signup_page():
    checkbox_html = ""

    for keyword in REPRESENTATIVE_KEYWORDS:
        label = keyword.replace("_", " ").title()

        checkbox_html += f"""
        <label style="display:block; margin:10px 0;">
            <input type="checkbox" name="selected_keywords" value="{keyword}">
            {label}
        </label>
        """

    return HTMLResponse(f"""
    <html>
        <body style="
            font-family: Arial;
            background: #f3f4f6;
            padding: 40px;
        ">
            <div style="
                max-width: 700px;
                margin: auto;
                background: white;
                padding: 40px;
                border-radius: 20px;
                box-shadow: 0 4px 16px rgba(0,0,0,0.08);
            ">
                <h1 style="color:#2563eb;">
                    PaperGuide AI 가입 / 설정 변경
                </h1>

                <p style="line-height:1.6;">
                    관심 분야를 선택하면 매주 또는 매일 관련 논문을 쉽게 설명해서 보내드립니다.
                    이미 가입한 이메일을 입력하면 추천 메일 주기만 변경됩니다.
                </p>

                <form method="post" action="/signup">
                    <label>이름</label><br>
                    <input name="name" required style="
                        width:100%;
                        padding:12px;
                        margin:8px 0 20px;
                    "><br>

                    <label>이메일</label><br>
                    <input name="email" type="email" required style="
                        width:100%;
                        padding:12px;
                        margin:8px 0 20px;
                    "><br>

                    <h3>관심 분야 선택</h3>
                    {checkbox_html}

                    <h3>기타 관심사</h3>
                    <p style="font-size:14px; color:#555;">
                        쉼표로 구분해서 입력하세요. 예: CRISPR, Alzheimer's disease, deep learning
                    </p>

                    <input name="custom_interests" style="
                        width:100%;
                        padding:12px;
                        margin:8px 0 24px;
                    ">

                    <h3>추천 메일 주기</h3>

                    <label style="display:block; margin:10px 0;">
                        <input type="radio" name="delivery_frequency" value="weekly" checked>
                        주 1회 추천 받기
                    </label>

                    <label style="display:block; margin:10px 0 24px;">
                        <input type="radio" name="delivery_frequency" value="daily">
                        매일 추천 받기
                    </label>

                    <button type="submit" style="
                        background:#2563eb;
                        color:white;
                        border:none;
                        padding:14px 22px;
                        border-radius:10px;
                        font-size:16px;
                        cursor:pointer;
                    ">
                        가입 또는 설정 변경
                    </button>
                </form>
            </div>
        </body>
    </html>
    """)

@app.post("/signup")
def signup_submit(
    name: str = Form(...),
    email: str = Form(...),
    selected_keywords: list[str] = Form(default=[]),
    custom_interests: str = Form(default=""),
    delivery_frequency: str = Form(default="weekly")
):
    print("SIGNUP POST RECEIVED", flush=True)
    print("name:", repr(name), flush=True)
    print("email:", repr(email), flush=True)
    print("selected_keywords:", selected_keywords, flush=True)
    print("custom_interests:", repr(custom_interests), flush=True)
    print("delivery_frequency:", repr(delivery_frequency), flush=True)

    email = email.strip().lower()
    name = name.strip()

    if delivery_frequency not in [
        "weekly",
        "daily"
    ]:
        delivery_frequency = "weekly"

    if email_exists(email):
        update_delivery_frequency(
            email=email,
            frequency=delivery_frequency
        )

        frequency_label = (
            "매일"
            if delivery_frequency == "daily"
            else "주 1회"
        )

        return HTMLResponse(f"""
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
                        추천 주기 변경 완료
                    </h1>

                    <p style="
                        font-size:18px;
                        line-height:1.6;
                    ">
                        앞으로 추천 메일은
                        <b>{frequency_label}</b>
                        발송됩니다.
                    </p>
                </div>
            </body>
        </html>
        """)

    user_id = f"user_{uuid4().hex[:12]}"

    keyword_weights, mapping_results = build_initial_keyword_weights(
        selected_keywords,
        custom_interests
    )

    create_user(
        user_id=user_id,
        name=name,
        email=email,
        keyword_weights=keyword_weights,
        delivery_frequency=delivery_frequency
    )

    print("USER CREATED:", user_id, flush=True)

    mapping_html = ""

    for result in mapping_results:
        input_text = result.get("input", "")
        matched = result.get("matched")
        reason = result.get("reason", "")

        if matched:
            mapping_html += f"""
            <li style="margin-bottom:12px;">
                <b>{input_text}</b>
                → <span style="color:#2563eb;">{matched}</span>
                <br>
                <span style="font-size:13px; color:#666;">
                    {reason}
                </span>
            </li>
            """
        else:
            mapping_html += f"""
            <li style="margin-bottom:12px;">
                <b>{input_text}</b>
                → <span style="color:#dc2626;">매칭 실패</span>
                <br>
                <span style="font-size:13px; color:#666;">
                    {reason}
                </span>
            </li>
            """

    if not mapping_html:
        mapping_html = """
        <li style="margin-bottom:12px;">
            선택되거나 매핑된 관심사가 없습니다.
        </li>
        """

    frequency_label = (
        "매일"
        if delivery_frequency == "daily"
        else "주 1회"
    )

    return HTMLResponse(f"""
    <html>
        <body style="
            font-family: Arial;
            text-align: center;
            padding-top: 80px;
            background: #f3f4f6;
        ">
            <div style="
                max-width: 700px;
                margin: auto;
                background: white;
                padding: 40px;
                border-radius: 20px;
                box-shadow: 0 4px 16px rgba(0,0,0,0.08);
                text-align: left;
            ">
                <h1 style="color:#2563eb; text-align:center;">
                    가입 완료
                </h1>

                <p style="
                    font-size:18px;
                    line-height:1.6;
                    text-align:center;
                ">
                    다음 추천 메일 발송 때부터 PaperGuide AI가 관심 분야에 맞는 논문을 보내드립니다.
                </p>

                <p style="
                    font-size:16px;
                    line-height:1.6;
                    text-align:center;
                ">
                    추천 메일 주기:
                    <b>{frequency_label}</b>
                </p>

                <h3>반영된 관심사</h3>

                <ul style="line-height:1.8;">
                    {mapping_html}
                </ul>
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

@app.get("/unsubscribe")
def unsubscribe(token: str):
    payload = verify_unsubscribe_token(token)

    if not payload:
        return HTMLResponse(
            "<h1>유효하지 않은 구독 해지 링크입니다.</h1>",
            status_code=400
        )

    user_id = payload.get("user_id")

    if not user_id:
        return HTMLResponse(
            "<h1>잘못된 구독 해지 요청입니다.</h1>",
            status_code=400
        )

    deactivate_user(user_id)

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
                    구독 해지 완료
                </h1>

                <p style="
                    font-size:18px;
                    line-height:1.6;
                ">
                    앞으로 PaperGuide AI 추천 메일이 발송되지 않습니다.
                </p>
            </div>
        </body>
    </html>
    """)