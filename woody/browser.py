import socket
import ssl

def decode_html_entities(text):
# HTML 엔티티를 실제 문자로 변환
  entities = {
    '&lt;': '<',
    '&gt;': '>',
  }
  
  for entity, char in entities.items():
    text = text.replace(entity, char)
  return text

def show(body):
  # HTML 엔티티를 먼저 디코딩
  body = decode_html_entities(body)
  
  in_tag = False
  for c in body:
    if c == "<":
      in_tag = True
    elif c == ">":
      in_tag = False
    elif not in_tag:
      print(c, end="")
      
def load(url):
  body = url.request()
  if url.scheme == "view-source":
    # view-source: HTML 소스 코드를 그대로 출력 (렌더링하지 않음)
    print(body)
  else:
    # 일반적인 렌더링 (HTML 태그 제거)
    show(body)

class URL:
  # 파이썬의 메서드에는 항상 self 매개변수가 있어야 함
  def __init__(self, url):
    if url.startswith("data:"):
      # data: URL 파싱 (예: data:text/html,hello world!)
      self.scheme = "data"
      url = url[5:]  # "data:" 제거
      if "," in url:
        self.mime_type, self.data = url.split(",", 1)
        if not self.mime_type:
          self.mime_type = "text/plain"
      else:
        self.mime_type = "text/plain"
        self.data = url
      self.host = None
      self.path = None
      self.port = None
    elif url.startswith("view-source:"):
      # view-source: URL 파싱 (예: view-source:http://example.org/)
      self.scheme = "view-source"
      self.target_url = url[12:]  # "view-source:" 제거
      # 내부적으로 실제 URL 객체 생성
      self.inner_url = URL(self.target_url)
      self.host = self.inner_url.host
      self.path = self.inner_url.path
      self.port = self.inner_url.port
    else:
      # HTTP/HTTPS/FILE URL 파싱
      self.scheme, url = url.split("://", 1)
      assert self.scheme in ["http", "https", "file"]

      if '/' not in url:
        url  = url + '/'
      self.host, url = url.split("/", 1)
      self.path = "/" + url

      if self.scheme == "https":
        self.port = 443
      elif self.scheme == "http":
        self.port = 80
      elif self.scheme == "file":
        self.port = None
      # 사용자 지정 포트 번호 처리
      if ":" in self.host:
        self.host, port = self.host.split(":", 1)
        self.port = int(port)

  def request(self):
    if self.scheme == "data":
      # data: URL에서 직접 데이터 반환
      return self.data
    
    if self.scheme == "view-source":
      # view-source: 실제 URL의 소스 코드 반환 (렌더링하지 않음)
      return self.inner_url.request()
    
    if self.scheme == "file":
      # 로컬 파일 읽기
      try:
        with open(self.path, "r", encoding="utf8") as f:
          return f.read()
      except FileNotFoundError:
        return "File not found: " + self.path
      except Exception as e:
        return "Error reading file: " + str(e)
    
    # HTTP/HTTPS 요청 처리
    # 서버 연결
    s = socket.socket(
      family=socket.AF_INET,
      type=socket.SOCK_STREAM,
      proto=socket.IPPROTO_TCP
    )
    s.connect((self.host, self.port))

    if self.scheme == "https":
      ctx = ssl.create_default_context()
      s = ctx.wrap_socket(s, server_hostname=self.host)

    # 서버에 요청 보내기
    request = "GET {} HTTP/1.1\r\n".format(self.path)
    request += "Host: {}\r\n".format(self.host)
    request += "Connection: close\r\n"
    request += "User-Agent: Woody-Browser/1.0\r\n"
    request += "\r\n"
    s.send(request.encode("utf8"))

    # 데이터가 도착할 떄마다 수집하는 루프
    response = s.makefile("r", encoding="utf8", newline="\r\n")  # socket.read 대신 파이썬에서는 소켓상태를 확인하는 루프 헬퍼 함수(makefile)를 사용
    statusLine = response.readline()
    version, status, explanation = statusLine.split(" ", 2)

    # 헤더 처리(헤더는 대소문자 구분하지 않기 때문에 소문자로 통일)
    response_headers = {}
    while True:
      line = response.readline()
      if line == "\r\n": break
      header, value = line.split(":", 1)
      response_headers[header.casefold()] = value.strip()

    # 처리하지 못하는 헤더는 무시
    assert "transfer-encoding" not in response_headers
    assert "content-encoding" not in response_headers

    if "content-length" in response_headers:
      content_length = int(response_headers["content-length"])
      body = response.read(content_length)

    return body


# http://example.org/index.html
if __name__ == "__main__":
  import sys
  if len(sys.argv) > 1:
    load(URL(sys.argv[1]))
  else:
    # URL이 없으면 기본 로컬 파일 로드
    load(URL("file:///Users/heominjeong/project/Woody/browser-deep-dive/index.html"))
