# 中国土地市场网云服务器中转运行手册

## 1. 云服务器开放端口

在云服务器 PowerShell 里运行：

```powershell
New-NetFirewallRule -DisplayName "LandChina Proxy 8787" -Direction Inbound -Action Allow -Protocol TCP -LocalPort 8787
```

同时在云服务器控制台的安全组/防火墙里放行 TCP `8787`。

## 2. 启动云服务器中转

把 `02_Process/landchina_proxy_server.ps1` 上传到云服务器，例如放到桌面。

在云服务器 PowerShell 里运行：

```powershell
Set-ExecutionPolicy -Scope Process Bypass -Force
cd $env:USERPROFILE\Desktop
.\landchina_proxy_server.ps1 -Port 8787 -Token "换成一串较长的随机密钥"
```

窗口保持打开。看到 `LandChina relay listening on http://+:8787/landchina/` 表示已启动。

## 3. 本地平台通过云服务器启动

在本机项目目录运行：

```powershell
.\scripts\start_demo_server_with_landchina_proxy.ps1 `
  -PythonExe "C:\Users\Lenovo\AppData\Local\Programs\Python\Python311\python.exe" `
  -ProxyUrl "http://117.72.179.235:8787/landchina/" `
  -ProxyToken "和云服务器一致的密钥"
```

然后打开：

```text
http://127.0.0.1:8000
```

## 4. 判断是否正常

在平台里点击“检查访问状态”，再试一次比较实例库抓取。

如果云服务器 PowerShell 出现 `OK /tGdxm/result/list` 和 `OK /tGdxm/result/detail`，说明请求已通过云服务器中转。

如果本地提示中转失败，优先检查：

- 云服务器 PowerShell 窗口是否还开着；
- 云服务器安全组是否放行 TCP `8787`；
- Windows 防火墙是否放行 TCP `8787`；
- 本地 `ProxyToken` 是否与云服务器 `-Token` 一致。
