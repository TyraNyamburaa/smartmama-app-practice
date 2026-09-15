import os
import resend

resend.api_key = os.getenv("RESEND_API_KEY")

FROM_EMAIL = os.getenv("MAIL_FROM", "Smartmama")

def send_invite_email(to_email: str, first_name: str, invite_url: str, role: str) -> None:
    resend.Emails.send({
        "from": FROM_EMAIL,
        "to": [to_email],
        "subject": f"You've been invited to SmartMama as {role}",
        "html": f"""
            <p>Hi {first_name},</p>
            <p>You've been invited to join SmartMama as a {role}.</p>
            <p><a href="{invite_url}">Click here to set your password and get started</a></p>
            <p>This link expires in 48 hours.</p>
        """,
    })