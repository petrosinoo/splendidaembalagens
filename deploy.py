import ftplib, os, ssl, sys

HOST    = 'ftp.splendidaembalagens.com.br'
USER    = 'splendidaembalagens'
PASSWD  = os.environ['FTP_PASSWORD']
EXCLUDE = {'.git', '.github', 'node_modules', 'package-lock.json', 'deploy.py'}

ftp = None
for use_tls in (True, False):
    try:
        if use_tls:
            ctx = ssl.create_default_context()
            ctx.check_hostname = False
            ctx.verify_mode = ssl.CERT_NONE
            ftp = ftplib.FTP_TLS(context=ctx)
        else:
            ftp = ftplib.FTP()
        ftp.connect(HOST, 21, timeout=30)
        ftp.login(USER, PASSWD)
        if use_tls:
            ftp.prot_p()
        ftp.set_pasv(True)
        print(f'Connected via {"FTPS" if use_tls else "FTP"}')
        break
    except Exception as e:
        print(f'{"FTPS" if use_tls else "FTP"} failed: {e}')
        ftp = None

if ftp is None:
    print('ERROR: could not connect', file=sys.stderr)
    sys.exit(1)

try:
    ftp.cwd('www')
    print('Changed to www/')
except Exception as e:
    print(f'Could not CWD to www: {e}')

def ensure_dir(name):
    try:
        ftp.mkd(name)
    except ftplib.error_perm:
        pass

def upload_dir(local, remote_prefix):
    for item in sorted(os.listdir(local)):
        if item in EXCLUDE or item.startswith('.'):
            continue
        lpath = os.path.join(local, item)
        rpath = (remote_prefix + '/' + item).lstrip('/')
        if os.path.isdir(lpath):
            ensure_dir(rpath)
            try:
                ftp.cwd(item if not remote_prefix else rpath)
                upload_dir(lpath, '')
                ftp.cwd('..')
            except Exception as e:
                print(f'ERROR entering {rpath}: {e}', file=sys.stderr)
        else:
            print(f'  {rpath}')
            try:
                with open(lpath, 'rb') as f:
                    ftp.storbinary(f'STOR {item}', f)
            except Exception as e:
                print(f'ERROR uploading {rpath}: {e}', file=sys.stderr)
                sys.exit(1)

upload_dir('.', '')
ftp.quit()
print('Deploy complete!')
