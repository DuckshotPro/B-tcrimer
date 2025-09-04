
import os
import re
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail

SENDGRID_API_KEY = os.getenv("SENDGRID_API_KEY")
# This should be an email address you have verified with SendGrid
FROM_EMAIL = os.getenv("SENDGRID_FROM_EMAIL", "noreply@b-tcrimer.com") 


def get_email_template(template_path, email_key="Email 1"):
    """Parses a markdown email template to extract a specific email's subject and body."""
    try:
        with open(template_path, 'r') as f:
            content = f.read()
        
        # Find the specific email section (e.g., ### Email 1: ...)
        match = re.search(f"### {re.escape(email_key)}:.*?\n(.*?)\n\n(.*?)(?=\n### |\Z)", content, re.DOTALL | re.IGNORECASE)
        if not match:
            return None, None

        # Extract subject from a line like "Subject: Welcome! Your API key is ready."
        subject_line = match.group(1).strip()
        subject = subject_line.split("Subject:", 1)[-1].strip()

        # The rest is the body
        body = match.group(2).strip()
        return subject, body
    except FileNotFoundError:
        print(f"ERROR: Email template not found at {template_path}")
        return None, None

def send_welcome_email(to_email: str, username: str):
    """Sends the hobbyist welcome email."""
    if not SENDGRID_API_KEY or not FROM_EMAIL:
        print("\n--- ERROR ---")
        print("SendGrid API key or From Email are not configured.")
        print("Please set SENDGRID_API_KEY and SENDGRID_FROM_EMAIL environment variables.")
        print("--------------------\n")
        return False

    template_path = "/data/data/com.termux/files/home/b-tcrimer/marketing/emails/sequence_hobbyist.md"
    subject_template, body_template = get_email_template(template_path, email_key="Email 1")

    if not subject_template or not body_template:
        print("Could not load welcome email template.")
        return False

    # For now, we don't have a real API key to send, so we'll use a placeholder
    # In a real scenario, you would pass the generated API key here.
    body = body_template.replace("{{firstName}}", username).replace("{{apiKey}}", "YOUR_API_KEY_HERE")
    # A simple regex to convert markdown links to HTML
    body_html = re.sub(r'\[(.*?)\]\((.*?)\)', r'<a href="\2">\1</a>', body).replace('\n', '<br>')

    message = Mail(
        from_email=FROM_EMAIL,
        to_emails=to_email,
        subject=subject_template,
        html_content=body_html
    )

    try:
        sg = SendGridAPIClient(SENDGRID_API_KEY)
        response = sg.send(message)
        print(f"Welcome email sent to {to_email} (Status: {response.status_code})")
        return True
    except Exception as e:
        print(f"Error sending email via SendGrid: {e}")
        return False
