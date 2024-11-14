from celery import shared_task
from django.core.mail import EmailMessage
from django.template.loader import render_to_string
from django.contrib.auth.tokens import default_token_generator
from django.utils.encoding import force_bytes
from django.utils.http import urlsafe_base64_encode
from django.conf import settings
from django.contrib.auth import get_user_model

User = get_user_model()

@shared_task
def send_verification_email_task(user_id, mail_subject, email_template, ngrok_url):
    user = User.objects.get(id=user_id)
    
    from_email = settings.DEFAULT_FROM_EMAIL
    message = render_to_string(
        email_template,
        {
            "user": user,
            "domain": ngrok_url,  # Use ngrok URL passed to the task
            "uid": urlsafe_base64_encode(force_bytes(user.pk)),
            "token": default_token_generator.make_token(user),
        },
    )
    to_mail = user.email
    mail = EmailMessage(mail_subject, message, from_email, to=[to_mail])
    mail.send()
