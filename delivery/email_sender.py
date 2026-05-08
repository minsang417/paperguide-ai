import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

from config import (
    SMTP_HOST,
    SMTP_PORT,
    SENDER_NAME,
    SENDER_EMAIL,
    SENDER_APP_PASSWORD,
    FEEDBACK_SERVER_URL
)

from backend.token_utils import (
    create_feedback_token
)


def build_paper_card(item, user_id):
    insight = item.get("insight", {})

    url = item.get("url", "#")

    token = create_feedback_token(
        user_id,
        item["paper_id"]
    )

    like_url = (
        f"{FEEDBACK_SERVER_URL}/feedback"
        f"?token={token}&rating=like"
    )

    dislike_url = (
        f"{FEEDBACK_SERVER_URL}/feedback"
        f"?token={token}&rating=dislike"
    )


    return f"""
    <div style="
        background:#ffffff;
        border:1px solid #e5e7eb;
        border-radius:16px;
        padding:20px;
        margin-bottom:20px;
        box-shadow:0 2px 8px rgba(0,0,0,0.05);
    ">
        <h2 style="
            margin:0 0 14px 0;
            font-size:20px;
            line-height:1.4;
            color:#111827;
        ">
            {item["title"]}
        </h2>

        <p style="font-size:16px; line-height:1.6;">
            <b>한 줄 요약:</b><br>
            {insight.get("one_sentence_summary", "")}
        </p>

        <p style="font-size:16px; line-height:1.6;">
            <b>쉬운 설명:</b><br>
            {insight.get("easy_explanation", "")}
        </p>

        <p style="font-size:16px; line-height:1.6;">
            <b>왜 중요한가:</b><br>
            {insight.get("why_it_matters", "")}
        </p>

        <p style="font-size:16px; line-height:1.6;">
            <b>더 생각해볼 질문:</b><br>
            {insight.get("question_to_explore", "")}
        </p>

        <div style="margin-top:18px;">
            <a href="{url}" style="
                background:#2563eb;
                color:white;
                text-decoration:none;
                padding:12px 18px;
                border-radius:10px;
                font-size:15px;
                font-weight:bold;
                display:inline-block;
                margin-right:8px;
            ">
                논문 보기
            </a>

            <a href="{like_url}" style="
                background:#16a34a;
                color:white;
                text-decoration:none;
                padding:12px 18px;
                border-radius:10px;
                font-size:15px;
                font-weight:bold;
                display:inline-block;
                margin-right:8px;
            ">
                좋아요
            </a>

            <a href="{dislike_url}" style="
                background:#dc2626;
                color:white;
                text-decoration:none;
                padding:12px 18px;
                border-radius:10px;
                font-size:15px;
                font-weight:bold;
                display:inline-block;
            ">
                별로예요
            </a>
        </div>
    </div>
    """

def build_section(title, items, user_id):
    cards = "".join(
        build_paper_card(item, user_id)
        for item in items
    )

    return f"""
    <div style="margin-top:40px;">
        <h1 style="
            font-size:26px;
            color:#111827;
            margin-bottom:20px;
        ">
            {title}
        </h1>
        {cards}
    </div>
    """

def build_html_email(recommendation_data):
    user_id = recommendation_data["user_id"]

    highly = build_section(
        "관심사와 높은 관련성이 있는 논문",
        recommendation_data["highly_relevant"],
        user_id
    )

    explore = build_section(
        "새롭게 탐색해볼 만한 논문",
        recommendation_data["explore_nearby_topics"],
        user_id
    )

    return f"""
    <html>
    <body style="
        margin:0;
        padding:0;
        background:#f3f4f6;
        font-family:Arial, sans-serif;
    ">
        <div style="
            max-width:800px;
            margin:0 auto;
            padding:30px;
        ">
            <div style="
                background:linear-gradient(135deg,#2563eb,#1d4ed8);
                color:white;
                padding:30px;
                border-radius:20px;
                margin-bottom:30px;
            ">
                <h1 style="
                    margin:0;
                    font-size:34px;
                ">
                    PaperGuide AI
                </h1>

                <p style="
                    margin-top:12px;
                    font-size:18px;
                    line-height:1.6;
                ">
                    이번 주 당신을 위한 맞춤 논문 추천
                </p>
            </div>

            {highly}
            {explore}

            <p style="
                color:#6b7280;
                font-size:13px;
                line-height:1.6;
                text-align:center;
                margin-top:40px;
            ">
                좋아요/별로예요 버튼을 누르면 다음 추천 품질 개선에 반영됩니다.
            </p>
        </div>
    </body>
    </html>
    """


def send_email(
    recipient_email: str,
    subject: str,
    html_body: str
):
    message = MIMEMultipart("alternative")

    message["From"] = (
        f"{SENDER_NAME} <{SENDER_EMAIL}>"
    )

    message["To"] = recipient_email
    message["Subject"] = subject

    message.attach(
        MIMEText(
            html_body,
            "html",
            "utf-8"
        )
    )

    with smtplib.SMTP(
        SMTP_HOST,
        SMTP_PORT
    ) as server:

        server.starttls()

        server.login(
            SENDER_EMAIL,
            SENDER_APP_PASSWORD
        )

        server.send_message(message)


def send_weekly_report_email(
    user: dict,
    recommendation_data: dict
):
    user_id = user["user_id"]
    recipient_email = user.get("email")

    if not recipient_email:
        print(
            f"[EMAIL SKIPPED] "
            f"{user_id}: no email"
        )
        return

    html_body = build_html_email(
        recommendation_data
    )

    subject = "PaperGuide AI 주간 논문 추천"

    send_email(
        recipient_email=recipient_email,
        subject=subject,
        html_body=html_body
    )

    print(
        f"[EMAIL SENT] "
        f"{user_id} -> {recipient_email}"
    )