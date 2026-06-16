# jobs/email_utils.py
import smtplib
import ssl
import threading
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import os
from datetime import datetime

class GlobalGigsMailer:
    """Self-hosted email sender - NO EXTERNAL PROVIDERS"""
    
    def __init__(self):
        self.smtp_host = os.environ.get('SMTP_HOST', 'localhost')
        self.smtp_port = int(os.environ.get('SMTP_PORT', 25))
        self.smtp_user = os.environ.get('SMTP_USER', '')
        self.smtp_password = os.environ.get('SMTP_PASSWORD', '')
        self.from_email = os.environ.get('FROM_EMAIL', 'GlobalGigs <noreply@globalgigs.com>')
        self.admin_email = os.environ.get('ADMIN_EMAIL', 'kellysimiyu122@gmail.com')
    
    def send_confirmation(self, to_email, applicant_name, job_title, company_name):
        """Send job application confirmation email to applicant"""
        subject = f"Application Received: {job_title} at {company_name}"
        body = f"""
Dear {applicant_name},

Thank you for applying to the position of {job_title} at {company_name}.

Your application has been received and will be reviewed by the hiring team.

Application Details:
- Position: {job_title}
- Company: {company_name}
- Location: {company_name}
- Date Submitted: {self._get_current_date()}

If you have any questions, please contact us at support@globalgigs.com.

Best regards,
GlobalGigs Team
"""
        return self.send_email(to_email, subject, body)
    
    def send_employer_notification(self, application):
        """Send notification to employer/admin about new application"""
        subject = f"New Application: {application.job.title} at {application.job.company_name}"
        body = f"""
New Application Received!

Job: {application.job.title}
Company: {application.job.company_name}
Location: {application.job.location}

Applicant Details:
- Name: {application.full_name}
- Email: {application.email}
- Phone: {application.phone or 'Not provided'}
- Portfolio: {application.portfolio_url or 'Not provided'}

Cover Letter:
{application.cover_letter}

View all applications: https://globalgigs-0096.onrender.com/admin/jobs/jobapplication/
"""
        return self.send_email(self.admin_email, subject, body)
    
    def send_email(self, to_email, subject, body, html_body=None):
        """Send email using Python's smtplib"""
        def send_thread():
            try:
                msg = MIMEMultipart('alternative')
                msg['From'] = self.from_email
                msg['To'] = to_email
                msg['Subject'] = subject
                
                msg.attach(MIMEText(body, 'plain'))
                
                if html_body:
                    msg.attach(MIMEText(html_body, 'html'))
                
                # Send email
                if self.smtp_user and self.smtp_password:
                    server = smtplib.SMTP(self.smtp_host, self.smtp_port)
                    server.starttls(context=ssl.create_default_context())
                    server.login(self.smtp_user, self.smtp_password)
                    server.send_message(msg)
                    server.quit()
                else:
                    # Try local mail server without auth
                    server = smtplib.SMTP(self.smtp_host, self.smtp_port)
                    server.send_message(msg)
                    server.quit()
                
                print(f"✅ Email sent to {to_email}")
                return True
            except Exception as e:
                print(f"❌ Email error: {str(e)}")
                return False
        
        # Send in background to not block the request
        thread = threading.Thread(target=send_thread)
        thread.daemon = True
        thread.start()
        return True
    
    def _get_current_date(self):
        return datetime.now().strftime('%B %d, %Y')

# Global instance
mailer = GlobalGigsMailer()