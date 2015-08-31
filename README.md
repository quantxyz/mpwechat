# mpwechat
python demo for weixin or wechat on https://mp.weixin.qq.com

one for get picture messages from wechat

# About MpWeChat

------

MpWeChat is a tool for get image messages(im:just for the lastest three days ) from https://mp.weixin.qq.com with yourself account：

> * auto manage everyone's image in themselves folder(named by remark_name or nick_name)
> * create the folder by the message date not the current date
> * store the lastest message id in text file everytime
> * self define the message begin time and the endl time you want to download
> * ...




## How to use it?

Only two things you need to do before use it.

### step one
```bash
pip install requests
```
### step two
copy the 'cacert.pem' file from your python runtime folder
---| why do this?
because the https, and it also needed for zip to exe or sh

---

## Structure
```text
-| WechatPublic(Main class)
-| Assist function
---| createdir() 
---| get_max_id() 
---| set_max_id() 
---| waitapp()
---| get_total_page()
---| get_day()
---| get_datetime()
---| format_time()
---| get_time()
---| get_filename()
```

## what's the next?
> * zip the .py to exe or sh with PyInstaller
> * change the max id rule
> * ...

author [@Jerry][http://www.cppfun.com]     
enjoy it~ 

