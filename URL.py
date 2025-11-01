import socket
import ssl
import base64

__all__ = ['URL', 'lex', 'load', 'showRawContent', 'decodeHtmlEntities', 'decodeLines']

connection_pool = {}

class URL:
  def __init__(self, url):    
    if url.startswith("view-source:"):
      self.scheme = "view-source"
      url = url[12:]
    elif url.startswith("data:"):
      self.scheme = "data"
      url = url[5:]
    else:
      self.scheme, url = url.split("://", 1)

    assert self.scheme in ["http", "https", "file", "data", "view-source"]
    match self.scheme:
      case "view-source": self.initWithViewSourceScheme(url)
      case "file": self.initWithFileScheme(url)
      case "http": self.initWithHttpScheme(url)
      case "https": self.initWithHttpScheme(url)
      case "data": self.initWithDataScheme(url)

  def initWithViewSourceScheme(self, url):
    self.inner_url = url
    self.inner_url_obj = URL(self.inner_url)
    self.host = None
    self.port = None
  
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
      case "view-source": return self.requestWithViewSourceScheme()
  
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

  def requestWithViewSourceScheme(self):
    result = self.inner_url_obj.request()

    if result is None:
      return ""

    return str(result)

  def requestWithHttpScheme(self, redirect_count=0):
    MAX_REDIRECTS = 10
    
    if redirect_count >= MAX_REDIRECTS:
      return f"Error: Too many redirects (maximum {MAX_REDIRECTS})"
    
    connection_key = (self.scheme, self.host, self.port)
    s = connection_pool.get(connection_key)

    if s is None:
      s = self.connectToSocket()

    request = f"GET {self.path} HTTP/1.1\r\n"
    request += f"Host: {self.host}\r\n"
    request += "Connection: keep-alive\r\n"
    request += "User-Agent: SimpleHTTPClient/1.0\r\n"
    request += "\r\n"
    
    try:
      s.send(request.encode("utf8"))
    except (BrokenPipeError, ConnectionResetError):
      s = self.connectToSocket()
      s.send(request.encode("utf8"))

    response = s.makefile("rb", newline=None)
    statusLine = decodeLines(response.readline())
    version, status, explanation = statusLine.split(" ", 2)

    responseHeaders = {}
    while True:
      line = decodeLines(response.readline())
      if line == "\r\n": break
      header, value = line.split(":", 1)
      responseHeaders[header.casefold()] = value.strip()

      assert "transfer-encoding" not in responseHeaders
      assert "content-encoding" not in responseHeaders

    if "content-length" in responseHeaders:
      content_length = int(responseHeaders["content-length"])
      body = decodeLines(response.read(content_length))
    else:
      body = decodeLines(response.read())
    
    connection_header = responseHeaders.get("connection", "").lower()
    if connection_header == "close":
      s.close()
      if connection_key in connection_pool:
        del connection_pool[connection_key]
    else:
      connection_pool[connection_key] = s

    status_code = int(status)
    if 300 <= status_code < 400 and "location" in responseHeaders:
      body = self.redirect(responseHeaders["location"], redirect_count)

    return body
  
  def connectToSocket(self):
    s = socket.socket(
      family=socket.AF_INET,
      type=socket.SOCK_STREAM,
      proto=socket.IPPROTO_TCP
    )
    s.connect((self.host, self.port))
    
    if self.scheme == "https":
      ctx = ssl.create_default_context()
      s = ctx.wrap_socket(s, server_hostname=self.host)
    return s
  
  def redirect(self, location, redirect_count=0):
    if location.startswith("/"):
      if self.port not in [80, 443]:
        redirect_url = f"{self.scheme}://{self.host}:{self.port}{location}"
      else:
        redirect_url = f"{self.scheme}://{self.host}{location}"
    elif location.startswith("http://") or location.startswith("https://"):
      redirect_url = location
    else:
      base_path = "/".join(self.path.split("/")[:-1])
      redirect_url = f"{self.scheme}://{self.host}{base_path}/{location}"
    
    redirect_url_obj = URL(redirect_url)
    return redirect_url_obj.requestWithHttpScheme(redirect_count + 1)


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

def decodeLines(lines):
  return lines.decode("utf8")

def showRawContent(body):
  print(body)

def lex(body):
  decoded_body = decodeHtmlEntities(body)
  
  text = ""
  in_tag = False
  for content in decoded_body:
    if content == "<":
      in_tag = True
    elif content == ">":
      in_tag = False
    elif not in_tag:
      text += content
  return text

def load(url):
  body = url.request()
  
  if url.scheme == "view-source":
    return showRawContent(body)
  else:
    return lex(body)

if __name__ == "__main__":
  import sys
  load(URL(sys.argv[1]))
