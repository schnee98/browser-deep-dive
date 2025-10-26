## 1. 서버의 연결

1. url이 주어지면 브라우저는 웹페이지를 다운로드
2. 브라우저는 운영체제에게 호스트 이름에 해당하는 서버와 연결을 요청함
3. 운영체제는 DNS(DomainNameSystem)서버와 통신하여 example.org와 같은 호스트 이름을 93.184.216.34와 같은 IP주소로 변환함
4. 운영체제는 라우팅 테이블을 이용해 해당 IP주소와 통신하기에 가장 적합한 장치를 결정함
5. 운영체제는 장치 드라이벌르 사용하여 신호를 보냄
6. 라우터는 신호를 감지하고 유저의 메세지를 전달하기 위한 최적의 다음 라우터에 전송함
7. 일련의 라우터를 거니 뒤에 목적지 도착
8. 메세지가 서버에 도착하면 해당 서버와의 연결 성공

## 2. 정보 요청하기

연결 후 브라우저는 `index.html`처럼 호스트 이름 뒤에 오는 URL의 경로에 해당하는 정보를 요청함

## 3. 서버의 응답

[HTTP 버전] [응답 코드] [응답 설명]
HTTP/1.0 200 OK

## 4. 파이썬을 통한 텔넷

1. URL 파싱하여 호스트 이름과 경로를 추출
2. 소켓을 생성
3. 요청을 보내기
4. 응답을 수신

## 5. HTTP 스킴 지원 구현

### 구현된 기능

- **URL 클래스**: HTTP URL을 파싱하여 호스트, 경로, 스킴을 분리
- **HTTP 요청**: 소켓을 사용하여 HTTP/1.0 GET 요청 전송
- **응답 처리**: HTTP 응답 헤더와 본문을 파싱
- **HTML 렌더링**: HTML 태그를 제거하고 텍스트만 출력

### 주요 컴포넌트

#### URL 클래스

```python
class URL:
    def __init__(self, url):  # URL 파싱
    def request(self):        # HTTP 요청 전송
```

#### 핵심 함수

- `load(url)`: URL을 로드하고 렌더링
- `show(body)`: HTML 본문에서 태그 제거 후 텍스트 출력

### 사용법

```bash
python3 browser.py http://example.org/
```

### 지원 기능

- ✅ HTTP 스킴 지원
- ✅ HTTPS 스킴 지원 (SSL/TLS 암호화)
- ✅ 기본적인 HTML 태그 제거
- ✅ Content-Length 헤더 처리
- ✅ 사용자 지정 포트 번호 지원
- ❌ Transfer-Encoding (미지원)
- ❌ Content-Encoding (미지원)

## 6. HTTPS 스킴 지원 추가

### 새로 추가된 기능

- **SSL/TLS 암호화**: `ssl` 모듈을 사용한 HTTPS 연결 지원
- **포트 자동 감지**: HTTP(80), HTTPS(443) 포트 자동 설정
- **사용자 지정 포트**: URL에 포트 번호가 포함된 경우 자동 처리

### 기술적 구현

```python
# SSL/TLS 연결 처리
if self.scheme == "https":
    ctx = ssl.create_default_context()
    s = ctx.wrap_socket(s, server_hostname=self.host)

# 포트 자동 감지
if self.scheme == "https":
    self.port = 443
elif self.scheme == "http":
    self.port = 80
```

### 테스트 예제

```bash
# HTTP 사이트 테스트
python3 browser.py http://example.org/

# HTTPS 사이트 테스트
python3 browser.py https://example.org/

# 사용자 지정 포트 테스트
python3 browser.py http://localhost:8000/
```

## 7. HTTP/1.1 프로토콜 지원 및 표준 헤더 추가

### 새로 추가된 기능

- **HTTP/1.1 프로토콜**: HTTP/1.0에서 HTTP/1.1로 업그레이드
- **표준 HTTP 헤더**: Host, Connection, User-Agent 헤더 추가
- **브라우저 식별**: "Woody-Browser/1.0" User-Agent로 브라우저 식별

### 기술적 구현

```python
# HTTP/1.1 요청 헤더 구성
request = "GET {} HTTP/1.1\r\n".format(self.path)
request += "Host: {}\r\n".format(self.host)
request += "Connection: close\r\n"
request += "User-Agent: Woody-Browser/1.0\r\n"
```

### HTTP 헤더 설명

- **Host 헤더**: 가상 호스팅 지원, 서버가 요청 대상 도메인 식별
- **Connection: close**: 요청 후 연결 즉시 종료 (keep-alive 비활성화)

  Connection 일반 헤더는 현재의 전송이 완료된 후 네트워크 접속을 유지할지 말지를 제어합니다. 만약 전송된 값이 keep-alive면, 연결은 지속되고 끊기지 않으며, 동일한 서버에 대한 후속 요청을 수행할 수 있습니다.

  경고 : Connection 와 Keep-Alive 같은 연결-지정(Connection-specific) 헤더 필드들은 HTTP/2.에서 금지되었습니다.
  크롬과 Firefox는 HTTP/2 응답에서 그들을 무시하지만, Safari는 HTTP/2 규격 요건에 따라 해당 필드가 포함된 응답은 처리하지 않습니다.

- **User-Agent**: 서버가 클라이언트 브라우저를 식별할 수 있도록 함

### 요청 예시

```http
GET / HTTP/1.1
Host: example.org
Connection: close
User-Agent: Woody-Browser/1.0

```
