import random
import requests
from wcferry import Wcf, WxMsg

def get_kout_text(self,msg:WxMsg):
    a = random.randint(2, 5)
    url = f"https://api.lolimi.cn/API/kout/k.php?msg={a}&amp;type=text"
    response = requests.get(url)

    self.sendTextMsg(response.text, msg.roomid)


