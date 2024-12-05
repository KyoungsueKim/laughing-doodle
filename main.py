import os
import time
import datetime
import subprocess
from pydrive.auth import GoogleAuth
from pydrive.drive import GoogleDrive

# 설정 변수
BACKUP_INTERVAL = 3600  # 백업 주기(초 단위)
DIRECTORY_TO_BACKUP = '/path/to/directory'  # 백업할 디렉토리 경로
BACKUP_DESTINATION = '/path/to/backup_destination'  # 로컬 백업 저장 경로
BACKUP_FOLDER_ID = 'your_google_drive_folder_id'  # 구글 드라이브 폴더 ID


def create_snapshot():
    timestamp = datetime.datetime.now().strftime('%Y%m%d%H%M%S')
    backup_folder = os.path.join(BACKUP_DESTINATION, f'backup_{timestamp}')
    latest_backup = get_latest_backup()

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

    subprocess.run(rsync_command)
    return backup_folder


def get_latest_backup():
    backups = [d for d in os.listdir(BACKUP_DESTINATION) if d.startswith('backup_')]
    backups.sort()
    if backups:
        return os.path.join(BACKUP_DESTINATION, backups[-1])
    else:
        return None


def compress_backup(folder_path):
    zip_filename = folder_path + '.zip'
    zip_command = ['zip', '-r', zip_filename, folder_path]
    subprocess.run(zip_command)
    return zip_filename


def upload_to_drive(filename):
    # 구글 드라이브 인증
    gauth = GoogleAuth()
    gauth.LoadCredentialsFile("credentials.json")
    if gauth.credentials is None:
        # 처음 인증 시
        gauth.LocalWebserverAuth()
    elif gauth.access_token_expired:
        # 토큰 만료 시 갱신
        gauth.Refresh()
    else:
        # 기존 자격 증명 사용
        gauth.Authorize()
    gauth.SaveCredentialsFile("credentials.json")

    drive = GoogleDrive(gauth)
    # 파일 업로드
    file1 = drive.CreateFile({'title': os.path.basename(filename), 'parents': [{'id': BACKUP_FOLDER_ID}]})
    file1.SetContentFile(filename)
    file1.Upload()
    print(f'{filename} 파일을 구글 드라이브에 업로드했습니다.')


def main():
    while True:
        backup_folder = create_snapshot()
        zip_file = compress_backup(backup_folder)
        upload_to_drive(zip_file)
        os.remove(zip_file)  # 로컬 압축 파일 삭제
        time.sleep(BACKUP_INTERVAL)


if __name__ == '__main__':
    main()
