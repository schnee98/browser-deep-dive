import tkinter
from URL import *

WIDTH, HEIGHT = 800, 600
HSTEP, VSTEP = 13, 18
SCROLL_STEP = 100

class Browser:
  def __init__(self):
    self.window = tkinter.Tk()
    self.canvas = tkinter.Canvas(self.window, width=WIDTH, height=HEIGHT)
    self.canvas.pack(fill=tkinter.BOTH, expand=True)
    self.scroll = 0
    self.width = WIDTH
    self.height = HEIGHT
    self.window.bind("<Down>", self.scroll_down)
    self.window.bind("<Up>", self.scroll_up)
    self.window.bind("<MouseWheel>", self.wheel)
    self.window.bind("<Configure>", self.on_resize)
  
  def load(self, url):
    body = URL(url).request()
    text = lex(body)
    self.text = text
    self.display_list = layout(text, self.width)
    self.draw()
  
  def draw(self):
    self.canvas.delete("all")
    for x, y, c, in self.display_list:
      if y > self.scroll + self.height: continue
      if y + VSTEP < self.scroll: continue

      self.canvas.create_text(x, y - self.scroll, text=c)

  def wheel(self, event):
    self.scroll += event.delta / 3
    self.draw()

  def scroll_down(self, event):
    self.scroll += VSTEP
    self.draw()

  def scroll_up(self, event):
    self.scroll -= VSTEP
    self.draw()

  def on_resize(self, event):
    self.width = event.width
    self.height = event.height
    if hasattr(self, 'text'):
      self.display_list = layout(self.text, self.width)
      self.draw()


def layout(text, width=WIDTH):
  display_list = []
  cursor_x, cursor_y = HSTEP, VSTEP
  for content in text:
    if content == "\n":
      cursor_y += VSTEP
      cursor_x = HSTEP
      continue

    display_list.append((cursor_x, cursor_y, content))
    cursor_x += HSTEP
    if cursor_x >= width - HSTEP:
      cursor_y += VSTEP
      cursor_x = HSTEP

  return display_list

if __name__ == "__main__":
  import sys
  Browser().load("http://browser.engineering/examples/xiyouji.html")
  tkinter.mainloop()