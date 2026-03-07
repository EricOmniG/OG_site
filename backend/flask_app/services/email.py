# ============================================================
#  flask_app/services/email.py
#  Email service — Microsoft Graph API (primary) or SMTP (fallback)
#
#  Usage:
#    from flask_app.services.email import send_email
#    send_email(
#        to="user@example.com",
#        subject="Welcome to Omnigenius",
#        html="<p>Your account is ready.</p>",
#    )
# ============================================================

import smtplib
import logging
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from typing import Optional

import requests
from flask import current_app

logger = logging.getLogger(__name__)


# ── Microsoft Graph API ───────────────────────────────────────

def _get_graph_token() -> Optional[str]:
    """
    Fetch an OAuth2 access token from Azure AD using client credentials flow.
    Tokens are valid for ~1 hour — in production, cache this in Redis.

    TODO: add Redis caching:
        token = redis.get("ms_graph_token")
        if token: return token
        ... fetch ... redis.setex("ms_graph_token", expires_in - 60, token)
    """
    tenant_id     = current_app.config["MS_TENANT_ID"]
    client_id     = current_app.config["MS_CLIENT_ID"]
    client_secret = current_app.config["MS_CLIENT_SECRET"]

    if not all([tenant_id, client_id, client_secret]):
        logger.warning("Microsoft Graph credentials not configured")
        return None

    url = f"https://login.microsoftonline.com/{tenant_id}/oauth2/v2.0/token"
    resp = requests.post(url, data={
        "grant_type":    "client_credentials",
        "client_id":     client_id,
        "client_secret": client_secret,
        "scope":         "https://graph.microsoft.com/.default",
    }, timeout=10)

    if resp.status_code != 200:
        logger.error("Failed to get Graph token: %s %s", resp.status_code, resp.text)
        return None

    return resp.json().get("access_token")


def _send_via_graph(to: str, subject: str, html: str, text: Optional[str] = None) -> bool:
    """
    Send an email using Microsoft Graph API.
    Requires Mail.Send application permission on the Azure app registration.
    """
    token  = _get_graph_token()
    sender = current_app.config["MS_SENDER_EMAIL"]

    if not token or not sender:
        return False

    body = {
        "message": {
            "subject": subject,
            "body": {
                "contentType": "HTML",
                "content": html,
            },
            "toRecipients": [
                {"emailAddress": {"address": to}}
            ],
        },
        "saveToSentItems": False,
    }

    url  = f"https://graph.microsoft.com/v1.0/users/{sender}/sendMail"
    resp = requests.post(
        url,
        json=body,
        headers={
            "Authorization": f"Bearer {token}",
            "Content-Type":  "application/json",
        },
        timeout=15,
    )

    if resp.status_code == 202:
        logger.info("Email sent via Graph to %s", to)
        return True
    else:
        logger.error("Graph sendMail failed: %s %s", resp.status_code, resp.text)
        return False


# ── SMTP Fallback ─────────────────────────────────────────────

def _send_via_smtp(to: str, subject: str, html: str, text: Optional[str] = None) -> bool:
    """
    Send email via Outlook SMTP (smtp.office365.com:587).
    Falls back to plain text if html rendering is unavailable.
    """
    cfg = current_app.config

    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"]    = f"{cfg['SMTP_FROM_NAME']} <{cfg['SMTP_FROM_EMAIL']}>"
    msg["To"]      = to

    if text:
        msg.attach(MIMEText(text, "plain"))
    msg.attach(MIMEText(html, "html"))

    try:
        with smtplib.SMTP(cfg["SMTP_HOST"], cfg["SMTP_PORT"], timeout=15) as server:
            if cfg.get("SMTP_USE_TLS", True):
                server.starttls()
            server.login(cfg["SMTP_USERNAME"], cfg["SMTP_PASSWORD"])
            server.sendmail(cfg["SMTP_FROM_EMAIL"], [to], msg.as_string())
        logger.info("Email sent via SMTP to %s", to)
        return True
    except smtplib.SMTPException as e:
        logger.error("SMTP send failed: %s", e)
        return False


# ── Public interface ──────────────────────────────────────────

def send_email(
    to: str,
    subject: str,
    html: str,
    text: Optional[str] = None,
) -> bool:
    """
    Send a transactional email.
    Uses EMAIL_BACKEND config to choose Graph API or SMTP.
    Falls back to SMTP if Graph fails.
    """
    backend = current_app.config.get("EMAIL_BACKEND", "graph")

    if backend == "graph":
        success = _send_via_graph(to, subject, html, text)
        if not success:
            logger.warning("Graph failed — falling back to SMTP")
            return _send_via_smtp(to, subject, html, text)
        return success

    return _send_via_smtp(to, subject, html, text)


# ── Email templates ───────────────────────────────────────────

def send_waitlist_confirmation(to: str, name: Optional[str] = None) -> bool:
    first = name.split()[0] if name else "there"
    return send_email(
        to=to,
        subject="You're on the Omnigenius waitlist",
        html=f"""
        <p>Hey {first},</p>
        <p>You're on the list. We're working through invites as fast as we can — you'll hear from us when your spot is ready.</p>
        <p>In the meantime, you can follow along on the <a href="https://omnigenius.co/blog">blog</a>.</p>
        <p>— Eric at Omnigenius</p>
        """,
    )


def send_invite_email(to: str, invite_url: str, name: Optional[str] = None) -> bool:
    first = name.split()[0] if name else "there"
    return send_email(
        to=to,
        subject="Your Omnigenius invite is ready",
        html=f"""
        <p>Hey {first},</p>
        <p>Your spot is ready. Click below to create your account — this link expires in 48 hours.</p>
        <p><a href="{invite_url}" style="background:#0ee8d4;color:#050810;padding:10px 20px;border-radius:8px;text-decoration:none;font-weight:bold;">Create your account</a></p>
        <p>— Eric at Omnigenius</p>
        """,
    )


def send_payment_failed_email(to: str, plan: str, retry_url: str) -> bool:
    return send_email(
        to=to,
        subject="Payment failed — action needed",
        html=f"""
        <p>Hi,</p>
        <p>We weren't able to process your payment for the Omnigenius {plan.title()} plan. Your account will remain active for a few days while we retry.</p>
        <p>To update your payment method: <a href="{retry_url}">click here</a></p>
        <p>If you have questions, reply to this email or contact support@omnigenius.net.</p>
        <p>— Omnigenius</p>
        """,
    )


def send_export_ready_email(to: str, download_url: str) -> bool:
    return send_email(
        to=to,
        subject="Your data export is ready",
        html=f"""
        <p>Hi,</p>
        <p>Your Omnigenius data export is ready. The link below will expire in 24 hours.</p>
        <p><a href="{download_url}">Download your data</a></p>
        <p>— Omnigenius</p>
        """,
    )
