import os
import time
import datetime
import subprocess
import logging
from pydrive.auth import GoogleAuth
from pydrive.drive import GoogleDrive

# 설정 변수
BACKUP_INTERVAL = 3600  # 백업 주기(초 단위)
DIRECTORY_TO_BACKUP = './Documents'  # 백업할 디렉토리 경로
BACKUP_DESTINATION = './backup'  # 로컬 백업 저장 경로
BACKUP_FOLDER_ID = '1_jNQOLgUUrBsWM5YfZ_Ujte4rhg3tDjm'  # 구글 드라이브 폴더 ID

# 로깅 설정
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s [%(levelname)s] %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)


def create_snapshot():
    timestamp = datetime.datetime.now().strftime('%Y%m%d%H%M%S')
    backup_folder = os.path.join(BACKUP_DESTINATION, f'backup_{timestamp}')
    latest_backup = get_latest_backup()

    logging.debug(f'Creating snapshot: {backup_folder}')
    logging.debug(f'Latest backup: {latest_backup if latest_backup else "None"}')

    if latest_backup:
        # 변경된 파일만 복사하고, 나머지는 하드 링크로 처리
        rsync_command = [
            'rsync', '-a', '--link-dest={}'.format(latest_backup),
            DIRECTORY_TO_BACKUP + '/', backup_folder
        ]
    else:
        # 최초 백업인 경우 전체 복사
        rsync_command = [
            'rsync', '-a',
            DIRECTORY_TO_BACKUP + '/', backup_folder
        ]

    logging.debug(f'Executing command: {" ".join(rsync_command)}')
    subprocess.run(rsync_command, check=True)
    logging.info(f'Snapshot created at {backup_folder}')
    return backup_folder


def get_latest_backup():
    backups = [d for d in os.listdir(BACKUP_DESTINATION) if d.startswith('backup_')]
    backups.sort()
    return os.path.join(BACKUP_DESTINATION, backups[-1]) if backups else None


def compress_backup(folder_path):
    zip_filename = folder_path + '.zip'
    zip_command = ['zip', '-r', zip_filename, folder_path]
    logging.debug(f'Compressing {folder_path} into {zip_filename}')
    logging.debug(f'Executing command: {" ".join(zip_command)}')
    subprocess.run(zip_command, check=True)
    logging.info(f'Backup compressed to {zip_filename}')
    return zip_filename


def upload_to_drive(filename):
    logging.debug('Authenticating with Google Drive...')
    gauth = GoogleAuth()
    gauth.LoadCredentialsFile("credentials.json")
    if gauth.credentials is None:
        gauth.LocalWebserverAuth()
    elif gauth.access_token_expired:
        gauth.Refresh()
    else:
        gauth.Authorize()
    gauth.SaveCredentialsFile("credentials.json")

    drive = GoogleDrive(gauth)
    file_title = os.path.basename(filename)
    logging.debug(f'Uploading {filename} to Google Drive folder {BACKUP_FOLDER_ID}')
    file1 = drive.CreateFile({'title': file_title, 'parents': [{'id': BACKUP_FOLDER_ID}]})
    file1.SetContentFile(filename)
    file1.Upload()
    logging.info(f'{filename} uploaded to Google Drive.')


def main():
    logging.info('Starting backup service...')
    while True:
        try:
            backup_folder = create_snapshot()
            zip_file = compress_backup(backup_folder)
            upload_to_drive(zip_file)
            os.remove(zip_file)  # 로컬 압축 파일 삭제
            logging.debug(f'Removed local zip file: {zip_file}')
            logging.info('Backup cycle complete. Waiting for next backup interval.')
            time.sleep(BACKUP_INTERVAL)
        except Exception as e:
            logging.error(f'An error occurred: {e}')
            time.sleep(BACKUP_INTERVAL)  # 오류 발생 시에도 다음 주기까지 대기 후 재시도


if __name__ == '__main__':
    main()
