# 라즈베리파이 스냅샷 백업 및 구글 드라이브 업로드 서비스

이 프로젝트는 라즈베리파이의 특정 디렉토리를 스냅샷 방식으로 주기적으로 백업하고, 해당 백업을 구글 드라이브에 자동으로 업로드하는 파이썬 스크립트를 제공합니다. 스냅샷 방식은 이전 백업과의 변경 사항만을 저장하여 저장 공간을 효율적으로 사용합니다. 이 스크립트는 서비스로 실행되어 부팅 시 자동으로 시작됩니다.

## 주요 기능

- 지정된 디렉토리의 스냅샷 방식 주기적 백업
- 백업본을 압축하여 구글 드라이브의 지정된 폴더에 자동 업로드
- 시스템 부팅 시 자동 실행되는 서비스 방식

## 필요 사항

- 라즈베리파이 및 Python 3 설치
- `rsync`, `zip` 명령어 사용 가능 (`sudo apt-get install rsync zip`로 설치)
- 구글 계정 및 구글 드라이브 접근 권한
- 인터넷 연결

## 설치 및 설정 방법

### 1. 프로젝트 클론 또는 다운로드

터미널에서 다음 명령어를 실행합니다:

```bash
git clone https://github.com/yourusername/raspberry-pi-backup.git
cd raspberry-pi-backup
```

### 2. 필요한 파이썬 패키지 설치

```bash
pip install PyDrive
```

### 3. 구글 드라이브 API 자격 증명 설정

#### a. 구글 드라이브 API 활성화

- [Google Developers Console](https://console.developers.google.com/)에 접속합니다.
- 새로운 프로젝트를 생성하거나 기존 프로젝트를 선택합니다.
- **APIs & Services > Dashboard**로 이동합니다.
- **Enable APIs and Services**를 클릭합니다.
- **Google Drive API**를 검색하여 활성화합니다.

#### b. OAuth 2.0 클라이언트 ID 생성

- **APIs & Services > Credentials**로 이동합니다.
- **Create Credentials > OAuth client ID**를 클릭합니다.
- 애플리케이션 유형으로 **Desktop app**을 선택합니다.
- 생성된 `client_secret.json` 파일을 프로젝트 디렉토리에 저장합니다.

#### c. PyDrive 설정 파일 생성

프로젝트 디렉토리에 `settings.yaml` 파일을 생성하고 다음 내용을 추가합니다:

```yaml
client_config_file: client_secret.json
save_credentials: True
save_credentials_file: credentials.json
oauth_scope:
  - https://www.googleapis.com/auth/drive
```

### 4. 스크립트 수정

`backup.py` 파일을 열어 다음 변수를 설정합니다:

```python
BACKUP_INTERVAL = 3600  # 백업 주기(초 단위)
DIRECTORY_TO_BACKUP = '/path/to/directory'  # 백업할 디렉토리 경로
BACKUP_DESTINATION = '/path/to/backup_destination'  # 로컬 백업 저장 경로
BACKUP_FOLDER_ID = 'your_google_drive_folder_id'  # 구글 드라이브 폴더 ID
```

- `DIRECTORY_TO_BACKUP`: 백업할 원본 디렉토리의 절대 경로
- `BACKUP_DESTINATION`: 백업본을 저장할 로컬 디렉토리의 절대 경로. 이 디렉토리는 존재해야 합니다.
- `BACKUP_FOLDER_ID`: 구글 드라이브에서 백업 파일을 저장할 폴더의 ID

**구글 드라이브 폴더 ID 찾기:**

- 구글 드라이브에서 원하는 폴더로 이동합니다.
- URL에서 `folders/` 다음에 오는 문자열이 폴더 ID입니다.
  예: `https://drive.google.com/drive/u/0/folders/ABC123`에서 폴더 ID는 `ABC123`입니다.

### 5. 초기 실행 및 인증

스크립트를 처음 실행하여 구글 계정 인증을 완료합니다:

```bash
python backup.py
```

- 브라우저 창이 열리면 구글 계정으로 로그인하고 앱 권한을 승인합니다.
- 인증이 완료되면 스크립트가 백업을 시작합니다.
- 테스트가 완료되면 `Ctrl+C`를 눌러 스크립트를 종료합니다.

### 6. 스크립트를 서비스로 설정

시스템 부팅 시 스크립트가 자동으로 실행되도록 서비스 파일을 생성합니다.

서비스 파일 생성:

```bash
sudo nano /etc/systemd/system/backup.service
```

다음 내용을 추가합니다:

```ini
[Unit]
Description=Raspberry Pi Backup Service
After=network.target

[Service]
ExecStart=/usr/bin/python3 /path/to/backup.py
WorkingDirectory=/path/to/
StandardOutput=inherit
StandardError=inherit
Restart=always
User=pi

[Install]
WantedBy=multi-user.target
```

- `/path/to/`를 실제 프로젝트 디렉토리 경로로 변경합니다.
- `User=pi`에서 `pi`는 스크립트를 실행할 사용자 이름입니다.

### 7. 서비스 활성화 및 시작

시스템 데몬을 리로드합니다:

```bash
sudo systemctl daemon-reload
```

서비스를 부팅 시 자동 시작되도록 활성화합니다:

```bash
sudo systemctl enable backup.service
```

서비스를 즉시 시작합니다:

```bash
sudo systemctl start backup.service
```

### 8. 서비스 상태 확인

서비스가 정상적으로 실행되는지 확인합니다:

```bash
sudo systemctl status backup.service
```

활성(running) 상태여야 합니다.

## 작동 원리

- **스냅샷 백업**: `rsync`의 `--link-dest` 옵션을 사용하여 변경된 파일만 복사하고, 변경되지 않은 파일은 하드 링크로 처리합니다. 이를 통해 매번 전체 파일을 복사하지 않고도 각 백업 폴더가 전체 백업본처럼 작동합니다.
- **백업 압축 및 업로드**: 생성된 백업 폴더를 `zip`으로 압축하여 구글 드라이브에 업로드합니다.
- **로컬 백업 관리**: 필요에 따라 오래된 백업 폴더를 삭제하여 로컬 저장 공간을 관리할 수 있습니다.

## 문제 해결

- **인증 오류 발생 시**: `client_secret.json` 및 `credentials.json` 파일이 프로젝트 디렉토리에 있고, 스크립트에서 접근 가능해야 합니다.
- **권한 문제 발생 시**: 서비스 파일에서 지정한 사용자(`User=pi`)가 해당 디렉토리 및 파일에 대한 적절한 권한을 가지고 있는지 확인합니다.
- **로그 확인**: 서비스 로그는 다음 명령어로 확인할 수 있습니다:

  ```bash
  journalctl -u backup.service
  ```

## 주의 사항

- **백업 저장 공간 관리**: 스냅샷 방식은 효율적이지만 백업이 누적되면 저장 공간을 많이 차지할 수 있습니다. 필요에 따라 오래된 백업을 삭제하는 스크립트를 추가로 작성하는 것이 좋습니다.
- **보안**: 구글 드라이브에 업로드되는 백업 파일이 민감한 정보를 포함할 경우, 업로드 전에 암호화하는 것을 고려하세요.

## 라이선스

이 프로젝트는 MIT 라이선스에 따라 배포됩니다.
