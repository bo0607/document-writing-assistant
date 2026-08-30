# 应用形态与分发说明

## Windows 桌面版

项目根目录的 `desktop_app.py` 会在本机启动写作服务，并以独立窗口打开系统。打包脚本 `scripts/build_windows.ps1` 会生成单文件程序：

```text
release/windows/DocumentWritingAssistant.exe
```

桌面版的数据会保存在当前 Windows 用户的本地应用数据目录，不会写入打包程序内部，因此重新打开程序后仍可看到任务和模型配置。

## PWA 网页应用

浏览器端提供 `manifest.webmanifest`、应用图标和离线静态资源缓存。使用 HTTPS 部署到服务器后，Android Chrome 和桌面 Chrome 都可以通过浏览器菜单安装为应用。

## Android 手机端

`mobile/android` 是可用 Android Studio 打开的原生壳工程。手机首次打开时填写写作服务地址，页面由已有的前端工作台提供，写作任务仍由 Python 后端负责。

在同一可信 Wi-Fi 内，可以在电脑上运行 `scripts/start_mobile_service.ps1`，然后在手机中填写电脑的局域网地址，例如：

```text
http://192.168.1.15:8000
```

局域网服务没有账号登录机制，只应在自己信任的家庭、实验室或校园私有网络中临时使用。部署到互联网时，应使用 HTTPS、账号认证和反向代理。
