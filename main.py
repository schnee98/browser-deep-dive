import socket
import ssl
import base64

class URL:
  def __init__(self, url):
    if url.startswith("data:"):
      self.scheme = "data"
      url = url[5:]
    else:
      self.scheme, url = url.split("://", 1)

    assert self.scheme in ["http", "https", "file", "data"]
    match self.scheme:
      case "file": self.initWithFileScheme(url)
      case "http": self.initWithHttpScheme(url)
      case "https": self.initWithHttpScheme(url)
      case "data": self.initWithDataScheme(url)
  
  def initWithFileScheme(self, url):
    self.host = None
    self.port = None
    self.path = url

  def initWithDataScheme(self, url):
    self.host = None
    self.port = None
    
    if "," in url:
      header, self.data = url.split(",", 1)
      
      if ";" in header and "base64" in header:
        self.mediatype = header.split(";")[0]
        self.is_base64 = True
      else:
        self.mediatype = header if header else "text/plain;charset=US-ASCII"
        self.is_base64 = False
    else:
      self.mediatype = "text/plain"
      self.is_base64 = False
      self.data = url

  def initWithHttpScheme(self, url):
    self.host, url = url.split("/", 1)
    self.path = "/" + url

    if ":" in self.host:
      self.host, port = self.host.split(":", 1)
      self.port = int(port)
    elif self.scheme == "http":
      self.port = 80
    elif self.scheme == "https":
      self.port = 443

    if "/" not in url:
      url = url + "/"

  def request(self):
    match self.scheme:
      case "file": return self.requestWithFileScheme()
      case "http": return self.requestWithHttpScheme()
      case "https": return self.requestWithHttpScheme()
      case "data": return self.requestWithDataScheme()
  
  def requestWithFileScheme(self):
    try:
      with open(self.path, 'r', encoding='utf8') as f:
        return f.read()
    except FileNotFoundError:
      return "File not found: " + self.path
    except Exception as e:
      return "Error reading file: " + str(e)

  def requestWithDataScheme(self):
    try:
      if self.is_base64:
        decoded_bytes = base64.b64decode(self.data)
        try:
          return decoded_bytes.decode('utf-8')
        except UnicodeDecodeError:
          return f"[Binary data: {len(decoded_bytes)} bytes, mediatype: {self.mediatype}]"
      else:
        import urllib.parse
        return urllib.parse.unquote(self.data)
    except Exception as e:
      return f"Error processing data URL: {str(e)}"

  def requestWithHttpScheme(self):
    s = socket.socket(
      family=socket.AF_INET,
      type=socket.SOCK_STREAM,
      proto=socket.IPPROTO_TCP
    )
    s.connect((self.host, self.port))

    if self.scheme == "https":
      ctx = ssl.create_default_context()
      s = ctx.wrap_socket(s, server_hostname=self.host)

    request = f"GET {self.path} HTTP/1.1\r\n"
    request += f"Host: {self.host}\r\n"
    request += "Connection: close\r\n"
    request += "User-Agent: SimpleHTTPClient/1.0\r\n"
    request += "\r\n"
    s.send(request.encode("utf8"))

    response = s.makefile("r", encoding="utf8", newline="\r\n")
    statusLine = response.readline()
    version, status, explanation = statusLine.split(" ", 2)

    responseHeaders = {}
    while True:
      line = response.readline()
      if line == "\r\n": break
      header, value = line.split(":", 1)
      responseHeaders[header.casefold()] = value.strip()

      assert "transfer-encoding" not in responseHeaders
      assert "content-encoding" not in responseHeaders

    body = response.read()
    s.close()

    return body

def decodeHtmlEntities(text):
  entities = {
    '&lt;': '<',
    '&gt;': '>',
    '&amp;': '&',
    '&quot;': '"',
    '&apos;': "'",
    '&nbsp;': ' '
  }
  
  result = text
  for entity, char in entities.items():
    result = result.replace(entity, char)
  
  return result

def show(body):
  decoded_body = decodeHtmlEntities(body)
  
  inTag = False
  for content in decoded_body:
    if content == "<":
      inTag = True
    elif content == ">":
      inTag = False
    elif not inTag:
      print(content, end="")

def load(url):
  body = url.request()
  show(body)

if __name__ == "__main__":
  import sys
  load(URL(sys.argv[1]))
