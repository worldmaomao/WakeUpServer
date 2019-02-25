# WakeUpServer
可以唤醒局域网设备的restful服务
# 依赖
* flask
* pyjwt

# 配置文件
```
[
  {
    "username": "admin",
    "password": "123456",
    "devices": [
      {
        "device_name": "qnap_nas",
        "broadcast_ip": "192.168.188.255",
        "mac": "8C-EC-XX-XX-XX-XX"
      },
	  {
        "device_name": "ubuntu_server",
        "broadcast_ip": "192.168.188.255",
        "mac": "8C-EC-XX-XX-XX-XX"
      }
    ]
  }
]
```

# jwt secret
该secret用于jwt加解密，建议改掉
位于server.py的jwt_secret全局变量

# 接口
## /user/login
登陆接口
请求参数：
post body json
{
  "username": "admin",
  "password": "123456"
}

返回：
{
  code:10000,
  message: "ok",
  data:{
    token: "jwt_token123123123123123"
  }
}

## /devices
获取所有设备名称
在request header里带上jwt_token, header名称为token
返回：
{
  code: 30000,
  message: "ok",
  data:["qnap_nas", "ubunut_server"]
}

## /devices/<device_name>/wakeup
唤醒
在url里带上device_name,同时在request header里带上jwt_token, header名称为token
返回：
{
  code: 20000,
  message: "ok",
  data: null
}

# 其他
* 和frp配合，可实现内网设备唤醒
* 在R7000路由器上，实现唤醒该路由器下的设备









