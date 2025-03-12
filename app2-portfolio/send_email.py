import smtplib, ssl


def send_email(message):
    host = "smtp.gmail.com"
    port = 465
    username = "narayana0497@gmail.com"
    password = "vrdvjqdhdqxrgmoy"
    receiver = "narayana0497@gmail.com"
    context = ssl.create_default_context()
    message = message
    with smtplib.SMTP_SSL(host, port, context=context) as server:
        server.login(username, password)
        server.sendmail(username, receiver, message)



