import time
import os
import requests
import json
from aido.config import *
# # from aido.recorder import Recorder
import random
import urllib.request
import base64
from aido.grabtext import *
import logging
# import subprocess
import string
from aido.delCmdCh import deal_control_char

logger = logging.getLogger(__name__)
logger.setLevel(level = logging.INFO)
handler = logging.FileHandler("aido.log")
handler.setLevel(logging.INFO)
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
handler.setFormatter(formatter)
logger.addHandler(handler)

MAXWORK = 100

# 获取百度API调用的认证，实时生成，因为有时间限制
def getToken():
    # token认证的url
    api_url = "https://openapi.baidu.com/oauth/2.0/token?" \
                     "grant_type=client_credentials&client_id=%s&client_secret=%s"
    token_url = api_url % (BaiDu_API_Key_GetVoi, BaiDu_Secret_Key_GetVoi)
    r_str = urllib.request.urlopen(token_url).read()
    token_data = json.loads(r_str)
    token_str = token_data['access_token']
    return token_str

class ChatBot(object):
    def __init__(self):
        self.name = "AIDO"
        self.voice_url = r'media/voice_ss.mp3'
        # # self.recorder = Recorder()

    def get_data(self,text):
        data = {
            "appid": "96e172cabcf3b21089395c484b65668e",
            "userid": "BluqL2PT",
            "spoken": text,
        }
        return data

    def get_response(self,text,voice_flag=False):
        prefix = "  "
        if not voice_flag:
            data = self.get_data(text)
        else:
            self.recording()
            text = self.voice2text()
            data = self.get_data(text)

        if (text == "todo"):
            output = os.popen("todo").read()
            output = deal_control_char(output)
            logger.info(output)
            if output != "":
                return prefix + "您的待办事项有以下这些哦：\n" + output
            else:
                return prefix + "您没有待办事项哦~"

        if(text == "setup"):
            os.popen("rm -rf ~/.toduh")
            return prefix + "已为您清除所有任务"

        if (grabdate(text)):
            command = getcommand(text)
            # return output
            try:
                output = os.popen(command).read()
            except:
                return prefix + "添加的事项输入有问题哦"

            output = os.popen("todo").read()
            output = deal_control_char(output)
            logger.info(output)
            return prefix + "帮您记录好啦\n" + output
        if (grabdel(text)):
            command = getdel(text)
            try:
                output = os.popen(command).read()
            except:
                return prefix + "┗|｀O′|┛ 嗷~~删除的信息不存在，请输入正确的删除信息(删除+数字/字母)"
            output = os.popen("todo").read()
            output = deal_control_char(output)
            logger.info(output)
            return prefix + "已删除~\n" + output

        data = self.get_data(text)
        url = 'https://api.ownthink.com/bot'  # API接口
        try:
            response = requests.post(url=url, data=data, headers=headers,timeout=10)
            response.encoding = 'utf-8'
            result = response.json()
            answer = result['data']['info']['text']
        except:
            answer = "LoL 小思有点忙..."
        logger.info("Q: {}".format(text)) # used for logging
        logger.info("A: {}".format(answer))
        return prefix + answer

    def text2voice(self,answer):
        # 获取access_token
        logger.info("text2voice")
        token = getToken()
        get_url = baidu_api_url2 % (urllib.parse.quote(answer), "test", token)
        voice_data = urllib.request.urlopen(get_url).read()
        voice_fp = open(self.voice_url, 'wb+')
        voice_fp.write(voice_data)
        voice_fp.close()
        logger.info("Done writing audio file!")
        return

    def recording(self):
        pass
        # self.recorder.recording(self.voice_url)

    def voice2text(self):
        # 获取access_token
        token = getToken()
        data = {}
        data['format'] = 'wav'
        data['rate'] = 16000
        data['channel'] = 1
        data['cuid'] = str(random.randrange(123456, 999999))
        data['token'] = token
        wav_fp = open(self.voice_url, 'rb')
        voice_data = wav_fp.read()
        data['len'] = len(voice_data)
        data['speech'] = base64.b64encode(voice_data).decode('utf-8')
        post_data = json.dumps(data)
        # 语音识别的api url
        upvoice_url = 'http://vop.baidu.com/server_api'
        r_data = urllib.request.urlopen(upvoice_url, data=bytes(post_data, encoding="utf-8"),timeout=10).read()
        logger.info(json.loads(r_data))
        err = json.loads(r_data)['err_no']
        if err == 0:
            return json.loads(r_data)['result'][0]
        else:
            return json.loads(r_data)['err_msg']
