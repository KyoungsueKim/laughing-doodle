import os
import time
import datetime
import subprocess
import logging
from pydrive.auth import GoogleAuth
from pydrive.drive import GoogleDrive

# 설정 변수
BACKUP_INTERVAL = 60  # 백업 주기(초 단위)
DIRECTORY_TO_BACKUP = os.path.expanduser('~/Documents')  # 백업할 디렉토리 경로
BACKUP_DESTINATION = os.path.expanduser('~/backup')  # 로컬 백업 저장 경로
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


def clear_drive_folder(drive, folder_id):
    # 폴더 내 파일 리스트 조회
    file_list = drive.ListFile({'q': f"'{folder_id}' in parents and trashed=false"}).GetList()
    for file in file_list:
        file.Delete()
    logging.info("Old backups on Google Drive have been deleted.")


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

    # 이전 백업본 삭제
    clear_drive_folder(drive, BACKUP_FOLDER_ID)

    file_title = os.path.basename(filename)
    logging.debug(f'Uploading {filename} to Google Drive folder {BACKUP_FOLDER_ID}')
    file1 = drive.CreateFile({'title': file_title, 'parents': [{'id': BACKUP_FOLDER_ID}]})
    file1.SetContentFile(filename)
    file1.Upload()
    logging.info(f'{filename} uploaded to Google Drive.')


def check_changes(latest_backup):
    if not latest_backup:
        # 최초 백업은 변경사항 체크 없이 무조건 진행
        return True
    # --dry-run 옵션을 사용하여 실제 복사 없이 변경사항을 확인
    # --out-format을 사용하여 변경 파일 리스트를 출력
    check_command = [
        'rsync', '-a', '--dry-run', '--out-format=%n',
        '--link-dest={}'.format(latest_backup),
        DIRECTORY_TO_BACKUP + '/', 'dummy_target'  # 여기서 dummy_target은 실제로 쓰이지 않을 경로입니다.
    ]
    
    result = subprocess.run(check_command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    changed_files = result.stdout.strip()
    
    # changed_files에 값이 있으면 변경사항이 있는 것이고, 없으면 없는 것
    return bool(changed_files)


def main():
    logging.info('Starting backup service...')
    while True:
        latest_backup = get_latest_backup()
        # 변경사항 확인
        if check_changes(latest_backup):
            logging.info("Changes detected. Creating new snapshot.")
            backup_folder = create_snapshot()  # 기존 create_snapshot 로직
            zip_file = compress_backup(backup_folder)
            upload_to_drive(zip_file)
            os.remove(zip_file)  # 로컬 압축 파일 삭제
            logging.info('Backup cycle complete. Waiting for next backup interval.')
        else:
            logging.info("No changes detected. Skipping backup this cycle.")
        
        time.sleep(BACKUP_INTERVAL)


if __name__ == '__main__':
    main()
