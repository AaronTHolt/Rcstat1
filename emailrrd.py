# A prototype of sending a users' job infromation via email

import smtplib
from email.MIMEMultipart import MIMEMultipart
from email.MIMEText import MIMEText
from email.MIMEImage import MIMEImage

def send_an_email(toaddress):
    server = smtplib.SMTP('smtp.gmail.com', 587)
    server.ehlo()
    server.starttls()
    server.ehlo()
    server.login("testuser3216", "imadeapassword!!!")

    fromaddr = "testuser3216@gmail.com"
    toaddr = toaddress
    msgRoot = MIMEMultipart()
    msgRoot['From'] = fromaddr
    msgRoot['To'] = toaddr
    msgRoot['Subject'] = "Python email"
    msgRoot.preamble = 'This is a multi-part message in MIME format.'

    # Encapsulate the plain and HTML versions of the message body in an
    # 'alternative' part, so message agents can decide which they want to display.
    msgAlternative = MIMEMultipart('alternative')
    msgRoot.attach(msgAlternative)

    msgText = MIMEText('This is the alternative plain text message.')
    msgAlternative.attach(msgText)

    # We reference the image in the IMG SRC attribute by the ID we give it below
    msgText = MIMEText('<b>Some <i>HTML</i> text</b> and an image.<br><img src="cid:image1"><br>Nifty!', 'html')
    msgAlternative.attach(msgText)

    # This example assumes the image is in the current directory
    fp = open('flaskr/static/temp.png', 'rb')
    msgImage = MIMEImage(fp.read())
    fp.close()

    # Define the image's ID as referenced above
    msgImage.add_header('Content-ID', '<image1>')
    msgRoot.attach(msgImage)

    server.sendmail(fromaddr, toaddr, msgRoot.as_string())
    server.quit()

