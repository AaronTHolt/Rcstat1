# A prototype of sending a users' job infromation via email

import os
import smtplib
import zipfile
import tempfile
import shutil
from email import encoders
from email.MIMEMultipart import MIMEMultipart
from email.MIMEText import MIMEText
from email.MIMEBase import MIMEBase
from email.MIMEImage import MIMEImage

def send_email(toaddr, jobid):

    print 'in email 1'

    server = smtplib.SMTP('10.128.0.190') ##rcmail.rc.colorado.edu
    # server = smtplib.SMTP('smtp.gmail.com', 587)
    server.ehlo('10.225.160.55') ##rcstat1

    print 'in email 2'
    # server.login("testuser3216", "imadeapassword!!!")


    fromaddr = 'NO REPLY <rcmail.rc.colorado.edu>'
    msgRoot = MIMEMultipart()
    msgRoot['From'] = fromaddr
    msgRoot['To'] = toaddr
    msgRoot['Subject'] = 'Graphs for job {j}'.format(j=jobid)
    # msgRoot.preamble = 'This is a multi-part message in MIME format.'

    print 'in email 3'

    # Encapsulate the plain and HTML versions of the message body in an
    # 'alternative' part, so message agents can decide which they want to display.
    msgAlternative = MIMEMultipart('alternative')
    msgRoot.attach(msgAlternative)

    # We reference the image in the IMG SRC attribute by the ID we give it below
    # msgText = MIMEText('<b>Some <i>HTML</i> text</b> and an image.<br><img src="cid:image1"><br>Nifty!', 'html')
    msgText = MIMEText('Graphs from job {j}'.format(j=jobid), 'html')
    msgAlternative.attach(msgText)

    print 'in email 4'

    the_file = 'web/static/job/{j}.zip'.format(j=jobid)

    try:
        shutil.make_archive('web/static/job/{j}'.format(j=jobid), 'zip', 
            'web/static/job/{j}'.format(j=jobid))

        msg = MIMEBase('application', 'zip')
        msg.set_payload(open(the_file, 'rb').read())
        encoders.encode_base64(msg)
        msg.add_header('Content-Disposition', 'attachment', 
                       filename=the_file + '.zip')
        msgRoot.attach(msg)
    except Exception, e:
        print 'Error: ', e

    print 'in email 5'
    ## For attaching individual graphs instead
    # image_paths = []
    # for root, dirs, files in os.walk('web/static/job/{j}'.format(j=jobid)):
    #     for filename in [os.path.join(root, name) for name in files]:
    #         if not 'agg' in filename:
    #             continue
    #         if not filename.endswith('.png'):
    #             continue
    #         image_paths.append(filename)

    # if len(image_paths) <= 0:
    #     server.quit()
    #     return 'NoImages'

    # for path in image_paths:
    #     fp = open(path, 'rb')
    #     img = MIMEImage(fp.read())
    #     fp.close()
    #     msgRoot.attach(img)

    try:
        server.sendmail(fromaddr, toaddr, msgRoot.as_string())
        server.quit()
        return True
    except smtplib.SMTPRecipientsRefused:
        server.quit()
        return False
    except Exception, e:
        print 'Another Error: ', e
        return False

    

