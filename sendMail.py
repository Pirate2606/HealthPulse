from flask_mail import Mail, Message
from models import app
from config import SendMail

app.config.from_object(SendMail)
mail = Mail(app)


def send_mail(name, email, phone_num, message):
    msg = Message('Feedback')
    address = 'maytrix.cafe@gmail.com'
    msg.recipients.append(str(address))
    msg.body = "Name : " + name + "\nEmail : " + email + "\nPhone Num. : " + phone_num + "\nMessage : " + message
    mail.send(msg)
