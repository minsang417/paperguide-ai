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
    create_feedback_token,
    create_unsubscribe_token
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
        border:1px solid #e5e7eb;
        border-radius:16px;
        padding:22px;
        margin:24px 0;
        background:#ffffff;
    ">
        <h2 style="margin-top:0; color:#111827;">
            {item["title"]}
        </h2>

        <p>
            <b>한 줄 요약:</b><br>
            {insight.get("one_sentence_summary", "")}
        </p>

        <p>
            <b>쉬운 설명:</b><br>
            {insight.get("easy_explanation", "")}
        </p>

        <p>
            <b>왜 중요한가:</b><br>
            {insight.get("why_it_matters", "")}
        </p>

        <p>
            <b>더 생각해볼 질문:</b><br>
            {insight.get("question_to_explore", "")}
        </p>

        <p style="margin-top:20px;">
            <a href="{url}" style="
                display:inline-block;
                padding:10px 14px;
                background:#2563eb;
                color:white;
                text-decoration:none;
                border-radius:8px;
                margin-right:8px;
            ">
                논문 보기
            </a>

            <a href="{like_url}" style="
                display:inline-block;
                padding:10px 14px;
                background:#16a34a;
                color:white;
                text-decoration:none;
                border-radius:8px;
                margin-right:8px;
            ">
                좋아요
            </a>

            <a href="{dislike_url}" style="
                display:inline-block;
                padding:10px 14px;
                background:#dc2626;
                color:white;
                text-decoration:none;
                border-radius:8px;
            ">
                별로예요
            </a>
        </p>
    </div>
    """


def build_section(title, items, user_id):
    cards = "".join(
        build_paper_card(item, user_id)
        for item in items
    )

    return f"""
    <section style="margin-top:36px;">
        <h1 style="color:#111827;">
            {title}
        </h1>
        {cards}
    </section>
    """


def build_html_email(
    recommendation_data,
    user
):
    user_id = recommendation_data["user_id"]

    unsubscribe_token = create_unsubscribe_token(
        user_id
    )

    unsubscribe_url = (
        f"{FEEDBACK_SERVER_URL}/unsubscribe"
        f"?token={unsubscribe_token}"
    )

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

    user_name = user.get("name", "")

    greeting = (
        f"{user_name}님을 위한 맞춤 논문 추천"
        if user_name
        else "이번 주 당신을 위한 맞춤 논문 추천"
    )

    return f"""
    <html>
        <body style="
            font-family: Arial, sans-serif;
            background:#f3f4f6;
            padding:32px;
            color:#111827;
        ">
            <div style="
                max-width:760px;
                margin:auto;
                background:#ffffff;
                border-radius:20px;
                padding:36px;
                box-shadow:0 4px 16px rgba(0,0,0,0.08);
            ">
                <h1 style="color:#2563eb; margin-top:0;">
                    PaperGuide AI
                </h1>

                <p style="font-size:18px; line-height:1.6;">
                    {greeting}
                </p>

                {highly}

                {explore}

                <p style="
                    margin-top:32px;
                    font-size:14px;
                    color:#4b5563;
                    line-height:1.6;
                ">
                    좋아요/별로예요 버튼을 누르면 다음 추천 품질 개선에 반영됩니다.
                </p>

                <hr style="
                    margin:36px 0 20px;
                    border:none;
                    border-top:1px solid #e5e7eb;
                ">

                <p style="
                    font-size:12px;
                    color:#6b7280;
                    text-align:center;
                    line-height:1.6;
                ">
                    더 이상 추천 메일을 받고 싶지 않다면
                    <a href="{unsubscribe_url}" style="color:#6b7280;">
                        구독 해지
                    </a>
                    를 눌러주세요.
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
        recommendation_data,
        user
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