import socket

def show(body):
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
  show(body)

class URL:
  # 파이썬의 메서드에는 항상 self 매개변수가 있어야 함
  def __init__(self, url):
    self.scheme, url = url.split("://", 1)
    # assert self.scheme in ["http", "https", "file", "data", "view-source"]
    assert self.scheme == "http" # 실습은 http만 지원

    if '/' not in url:
      url  = url + '/'
    self.host, url = url.split("/", 1)
    self.path = "/" + url

  def request(self):
    # 서버 연결
    s = socket.socket(
      family=socket.AF_INET,
      type=socket.SOCK_STREAM,
      proto=socket.IPPROTO_TCP
    )
    s.connect((self.host, 80))

    # 서버에 요청 보내기
    request = "GET {} HTTP/1.0\r\n".format(self.path)
    request += "Host: {}\r\n".format(self.host)
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
  load(URL(sys.argv[1]))