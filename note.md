https://github.com/mbebenita/Broadway
https://github.com/131/h264-live-player
https://flask-socketio.readthedocs.io/en/latest/getting_started.html
https://docs.python.org/zh-cn/3/library/asyncio-dev.html#asyncio-multithreading
https://docs.python.org/zh-cn/3/library/asyncio.html#module-asyncio


```javascript
var player = new Player({<options>});
playerElement = document.getElementById(playerId)
playerElement.appendChild(player.canvas)
player.decode(<h264 data>);
```



```shell
ffmpeg -re -i test.mp4 -c:v libx264 -preset ultrafast -tune zerolatency -f h264 -g 30 tcp://127.0.0.1:8989

ffplay -flags low_delay -vf setpts=0 -f h264 tcp://127.0.0.1:8989
```

```powershell
##win 循环推流
@echo off
:loop
ffmpeg -re -i test.mp4 -c:v libx264 -preset ultrafast -tune zerolatency -f h264 tcp://127.0.0.1:8989
timeout /t 1 /nobreak >nul
goto loop
```

```shell
#!/bin/bash
while true
do
  ffmpeg -re -i test.mp4 -c:v libx264 -preset ultrafast -tune zerolatency -f h264 tcp://127.0.0.1:8989
  sleep 1
done
```

