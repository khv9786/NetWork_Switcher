# NetSwitcher

네트워크 프로필을 클릭 한 번으로 전환하는 윈도우 전용 도구입니다.

---

## 주요 기능

- 여러 개의 네트워크 프로필(IP, 서브넷, 게이트웨이, DNS) 저장 및 전환
- 관리자 권한 자동 요청 (netsh 명령 실행에 필요)
- 다크 모드 UI, 시안 글로우 버튼

---

## 시작하기

### 1. 실행 파일 사용 (권장)

`dist/net_switcher.exe` 를 `config.json` 과 **같은 폴더**에 놓고 실행합니다.

```
📁 폴더
 ├── net_switcher.exe
 └── config.json
```

### 2. 소스 직접 실행

Python 3.10 이상 필요 (tkinter 기본 포함)

```bash
python net_switcher.py
```

---

## config.json 설정

`config.example.json` 을 복사해 `config.json` 으로 이름을 바꾼 뒤 값을 수정합니다.

```json
{
  "adapter": "이더넷",
  "profiles": [
    {
      "name": "내부망",
      "ip": "192.168.1.100",
      "subnet": "255.255.255.0",
      "gateway": "192.168.1.1",
      "dns": "8.8.8.8",
      "dns2": ""
    },
    {
      "name": "행망",
      "ip": "10.0.0.50",
      "subnet": "255.255.0.0",
      "gateway": "10.0.0.1",
      "dns": "168.126.63.1",
      "dns2": "168.126.63.2"
    }
  ]
}
```

| 필드 | 설명 |
|------|------|
| `adapter` | 네트워크 어댑터 이름 (장치 관리자 또는 `ncpa.cpl` 에서 확인) |
| `name` | 프로필 표시 이름 |
| `ip` | 고정 IP 주소 |
| `subnet` | 서브넷 마스크 |
| `gateway` | 기본 게이트웨이 |
| `dns` | 기본 DNS 서버 |
| `dns2` | 보조 DNS 서버 (없으면 `""` 로 비워두세요) |

> **어댑터 이름 확인 방법**  
> `Win + R` → `ncpa.cpl` 실행 → 사용 중인 어댑터 이름 확인

---

## 사용 방법

1. `net_switcher.exe` 실행 → 관리자 권한 승인
2. 프로필 카드에서 원하는 네트워크의 **활성화** 버튼 클릭
3. 확인 창에서 **예** 선택 → 자동 적용

---

## exe 직접 빌드

```bash
pip install pyinstaller
python -m PyInstaller net_switcher.spec --clean
```

빌드 결과물은 `dist/net_switcher.exe` 에 생성됩니다.

---

## 주의사항

- Windows 전용입니다 (netsh 명령 사용)
- 관리자 권한 없이는 IP 변경이 불가합니다
- 어댑터 이름이 `config.json` 과 정확히 일치해야 합니다
