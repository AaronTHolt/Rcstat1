# A prototype of sending a users' job infromation via email

import os
import smtplib
from email.MIMEMultipart import MIMEMultipart
from email.MIMEText import MIMEText
from email.MIMEImage import MIMEImage
# from flaskr import get_images

def send_email(toaddress, jobid):
    # print "IN SEND EMAIL"
    server = smtplib.SMTP('10.128.0.190') ##rcmail.rc.colorado.edu
    # server = smtplib.SMTP('smtp.gmail.com', 587)
    server.ehlo('10.225.160.55') ##rcstat1
    # server.starttls()
    # server.ehlo('10.225.160.55')

    # server.login("testuser3216", "imadeapassword!!!")

    fromaddr = "NO REPLY"
    # toaddr = "holtat@colorado.edu"
    toaddr = toaddress
    msgRoot = MIMEMultipart()
    msgRoot['From'] = fromaddr
    msgRoot['To'] = toaddr
    msgRoot['Subject'] = "Graphs for job {j}".format(j=jobid)
    msgRoot.preamble = 'This is a multi-part message in MIME format.'

    # Encapsulate the plain and HTML versions of the message body in an
    # 'alternative' part, so message agents can decide which they want to display.
    msgAlternative = MIMEMultipart('alternative')
    msgRoot.attach(msgAlternative)

    # We reference the image in the IMG SRC attribute by the ID we give it below
    # msgText = MIMEText('<b>Some <i>HTML</i> text</b> and an image.<br><img src="cid:image1"><br>Nifty!', 'html')
    msgText = MIMEText('Aggregate graphs from job {j}'.format(j=jobid), 'html')
    msgAlternative.attach(msgText)

    image_paths = []
    for root, dirs, files in os.walk('web/static/'):
        for filename in [os.path.join(root, name) for name in files]:
            if not '/'+str(jobid)+'/' in filename:
                continue
            if not 'all' in filename:
                continue
            if not filename.endswith('.png'):
                continue
            image_paths.append(filename)

    for path in image_paths:
        fp = open(path, 'rb')
        img = MIMEImage(fp.read())
        fp.close()
        msgRoot.attach(img)
    try:
        server.sendmail(fromaddr, toaddr, msgRoot.as_string())
        server.quit()
        return True
    except smtplib.SMTPRecipientsRefused:
        server.quit()
        return False

    

