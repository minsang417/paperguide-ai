import os
import json
import hmac
import base64
import hashlib

from dotenv import load_dotenv

load_dotenv()

SECRET_KEY = os.getenv("FEEDBACK_SECRET_KEY")


def _sign(data: str) -> str:
    return hmac.new(
        SECRET_KEY.encode(),
        data.encode(),
        hashlib.sha256
    ).hexdigest()


def _create_token(payload: dict) -> str:
    json_payload = json.dumps(
        payload,
        separators=(",", ":")
    )

    encoded = base64.urlsafe_b64encode(
        json_payload.encode()
    ).decode()

    signature = _sign(encoded)

    return f"{encoded}.{signature}"


def _verify_token(token: str):
    try:
        encoded, signature = token.split(".")

        expected = _sign(encoded)

        if not hmac.compare_digest(
            signature,
            expected
        ):
            return None

        decoded = base64.urlsafe_b64decode(
            encoded.encode()
        ).decode()

        return json.loads(decoded)

    except Exception:
        return None


def create_feedback_token(
    user_id: str,
    paper_id: str
) -> str:
    payload = {
        "type": "feedback",
        "user_id": user_id,
        "paper_id": paper_id
    }

    return _create_token(payload)


def verify_feedback_token(token: str):
    payload = _verify_token(token)

    if not payload:
        return None

    if payload.get("type") != "feedback":
        return None

    return payload


def create_unsubscribe_token(user_id: str) -> str:
    payload = {
        "type": "unsubscribe",
        "user_id": user_id
    }

    return _create_token(payload)


def verify_unsubscribe_token(token: str):
    payload = _verify_token(token)

    if not payload:
        return None

    if payload.get("type") != "unsubscribe":
        return None

    return payload