# Capstone Victim System (DVWA Attack Script)

이 프로젝트는 캡스톤 디자인을 위한 희생양(Victim) 시스템으로, 취약점 실습 웹 애플리케이션인 DVWA(Damn Vulnerable Web App)와 통합 자동화 공격 스크립트(`attack.py`)로 구성되어 있습니다. 발생하는 로그는 Filebeat를 통해 수집되어 외부 ELK 스택(설정된 인프라)으로 전송됩니다.

## 🚀 시작하기 전 필수 사항 (Prerequisites)

- **Docker & Docker Compose**: DVWA 및 Filebeat 환경 배포를 위해 필요합니다.
- **Python 3.11 이상 & `uv`**: 파이썬 패키지 및 가상환경 구성을 빠르게 처리하기 위해 `uv`를 사용합니다.
- **외부 Docker 네트워크 (`elk-stack`)**: Filebeat(이 프로젝트)와 로깅 시스템 모니터링 컨테이너(외부 ELK 등) 간의 통신을 위해 `elk-stack`이라는 외부 네트워크가 필요합니다. 
  - *Tip: 만약 별도의 ELK 구성 없이 단독으로 DVWA의 가동 여부만 임시로 테스트해보고 싶다면, Docker Compose가 정상 실행되도록 로컬에 먼저 네트워크를 만들어주어야 합니다.*
    ```sh
    docker network create elk-stack
    ```

---

## 🛠️ 설치 및 서버 가동 가이드

### 1. 패키지 의존성 설치
`uv`를 사용하여 프로젝트 가상환경을 생성하고 필요한 패키지(`requests`, `beautifulsoup4`)를 설치합니다.

```sh
uv sync
```

### 2. 컨테이너 실행 (DVWA 서버 & Filebeat 에이전트)
Docker Compose를 사용하여 웹 서버와 로그 수집 에이전트를 백그라운드 환경에서 가동합니다.

```sh
docker-compose up -d
```

### 3. DVWA 접속 테스트
컨테이너가 정상적으로 준비되었는지 브라우저를 열고 `http://localhost` 에 접속하여 확인합니다.
- **초기 연결 계정**: Username `admin` / Password `password`
- *참고: 이어지는 DVWA 공격 스크립트(`attack.py -s`)가 실행될 때 내부 요청으로 자동 로그인 및 난이도를 'Low'로 맞춰주도록 구현되어 있습니다.*

---

## ⚔️ 공격 시나리오 스크립트 확인 및 실행

내장된 `attack.py`는 DVWA 웹 취약점 시나리오를 제공합니다.

### 사용법
`uv` 가상환경 내에서 아래와 같은 명령어로 실행할 수 있습니다.

```sh
uv run attack.py -s [DVWA_시나리오번호]
```
*(예: 첫 번째 시나리오 실행 시)*
```sh
uv run attack.py -s 1
```

### DVWA 지원 공격 시나리오
1. **무차별 대입 공격 (Brute Force)**: 관리자 비밀번호를 유추하기 위한 패스워드 사전 대입 공격
2. **명령어 삽입 (Command Injection)**: OS 명령어를 인젝션하여 서버 내부 정보(`/etc/passwd` 등) 열람
3. **SQL 인젝션 (Error Based)**: 에러 기반 SQL 구문 삽입을 통한 데이터베이스 유출 시도
4. **파일 업로드 (File Upload)**: PHP 웹 쉘 등 악성 파일을 업로드하고 시스템 원격 제어 목적의 실행
5. **반사형 XSS (Reflected XSS)**: 파라미터 값에 임의의 자바스크립트를 삽입하여 브라우저에서 스크립트 실행
6. **SQL Injection 침투 → 크리덴셜 탈취 → 시스템 침투**
7. **Command Injection 침투 → 권한 상승 시도**
8. **File Upload 침투 → 내부 정찰 및 횡적 이동**
9. **Brute Force 침투 → 백도어 설치 및 지속성 확보**
10. **Stored XSS 침투 → 세션 하이재킹 → 데이터 유출**

## 🛑 종료 및 정리

실습을 마치거나 재초기화할 목적으로 모든 컨테이너 환경을 종료하려면 아래 명령어를 사용합니다.

```sh
docker-compose down
```
(선택) 사용된 볼륨 데이터(Apache 로그 파일 등)까지 완전히 초기화하여 재설치하려면 아래의 `-v` 옵션을 붙여주세요.
```sh
docker-compose down -v
```
