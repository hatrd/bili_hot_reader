"""
Usage: 
1. python bili_hot_reader.py 
2. python bili_hot_reader.py 5 #热门前五条
3. python bili_hot_reader.py BV1ij41177b8 BV1ca4y1S71Y #带BV号，指定转译BV
需要个性化推荐，请填充cookies的SESSDATA。

环境主要是 requests 库和 openai 的 whisper. https://github.com/openai/whisper
本地跑不动大语言模型，不然得把输出喂进去，然后就可以实现AI逛b站发表感言，人类出去上班上学了。
"""

import requests
import re
import json
import whisper
import os
import sys

# cookies 添加 SESSDATA 才有个性化推荐
cookies = {
    'SESSDATA': '<YOUR COOKIE HERE>'
}

def get_audio(bvid, save_name):
    if os.path.exists(save_name):
        print(f"{save_name} 已经存在。")
        return
        
    
    url=f"https://www.bilibili.com/{bvid}"
    headers = {'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/106.0.0.0 Safari/537.36 Edg/106.0.1370.37',"Referer": "https://www.bilibili.com"}
    session = requests.session()
    response = session.get(url=url, headers=headers)
    # 提取视频对应的json数据
    play_info = re.findall('<script>window\.__playinfo__=(.*?)</script>', response.text)[0]
    json_data = json.loads(play_info)
    # 提取音频的url地址
    audio_url = json_data['data']['dash']['audio'][0]['backupUrl'][-1]
    # print('解析到的音频地址:', audio_url)

    # 提取视频画面的url地址
    # video_url = json_data['data']['dash']['video'][0]['backupUrl'][0]
    # print('解析到的视频地址:', video_url)

    audio_content = session.get(audio_url, headers=headers).content
    with open(save_name, 'wb') as f:
        f.write(audio_content)
        
    return

def audio_to_text(save_name):
    if not os.path.exists(save_name):
        print(f"文件 {save_name} 不存在，无法进行转换。")
        return
    txt_name = f"{save_name[:-4]}.txt"
    if os.path.exists(txt_name):
        print(f"{txt_name} 已经存在。")
        return
    model = whisper.load_model("medium")
    result = model.transcribe(save_name, initial_prompt='这是bilibili视频网站上的一段视频。') # prompt解决没有标点符号的问题。
    with open(txt_name, 'w') as f:
        f.write(result["text"])

def trans_bv(bvid):
    url = f"https://api.bilibili.com/x/web-interface/view?bvid={bvid}" #这个接口比较容易被ban
    response = requests.get(url)
    # 处理响应
    if response.status_code == 200:
        data = response.json()
        # 获取title和owner name
        title = data["data"]["title"]
        owner_name = data["data"]["owner"]["name"]
        save_name = f"{bvid}-{owner_name}-{title}.mp3"
        save_name = re.sub('[\/:*?"<>|]','-',save_name)#去掉非法字符
        get_audio(bvid, save_name)
        audio_to_text(save_name)
        print(f"{bvid}-{owner_name}-{title}已完成转译")
    else:
        # 如果请求不成功，输出错误信息
        print(response.text)
        return None, None

    
def hot_video(maxcnt=None):
    if maxcnt == None:
        user_input = input("读取几条热门数据？")
        try:
            # 尝试将输入的内容转为整数
            number = int(user_input)
            # 将整数转为字符串
            maxcnt = str(number)
            print("输入的数字为:", maxcnt)
        except ValueError:
            maxcnt = 1
            print("使用默认：", maxcnt)

    url = f"https://api.bilibili.com/x/web-interface/popular?ps={maxcnt}&pn=1"


    response = requests.get(url, cookies=cookies)
    if response.status_code == 200:
        data = response.json()
        
        if data["code"] == 0:
            videos = data["data"]["list"]

            for video in videos:
                short_link = video.get("short_link_v2", "")
                bvid = short_link[15:]
                title = video.get("title", "")
                pub_location = video.get("pub_location", "") #有些人发布不带 ip 信息
                owner_name = video["owner"].get("name", "")

                save_name = f"{bvid}-{owner_name}-{title}.mp3"
                save_name = re.sub('[\/:*?"<>|]','-',save_name)#去掉非法字符
                
                get_audio(bvid, save_name)
                audio_to_text(save_name)
                print(f"{bvid}-{owner_name}-{title}已完成转译")
        else:
            print(f"Error: {data['message']}")
    else:
        print(f"Error: {response.status_code}")
        

if __name__ == '__main__':
    arguments = sys.argv
    if len(arguments) == 1:
        hot_video()
    elif arguments[1].startswith("BV"):
        for arg in arguments[1:]:
            trans_bv(arg)    
    else:
        hot_video(int(arguments[1]))