# 基于大模型的文档智能写作助手

这是一个面向文档与作文生成场景的智能写作助手。系统参考 OpenClaw 的任务运行、上下文管理、技能注册和模型适配思想，但将其缩减并改造为面向文档写作的轻量化任务内核。

## 已实现功能

- 写作要求输入：主题、文体、字数、风格、补充要求
- 一键生成：需求解析、内部组织要点、自然正文生成
- 正文编辑：在页面中直接修改并保存
- 摘要生成
- 文档导出：Word `.docx` 和文本 `.txt`
- 最近任务查看与载入
- 字数控制：正文生成后自动控制在目标字数约 ±10% 范围内
- 自动化测试：接口闭环测试和导出结构测试
- 应用形态：Windows 桌面程序、可安装 PWA 网页应用、Android 手机端工程

## 运行方式

在 VSCode 中打开 `D:\SRT`，选择运行和调试里的：

```text
启动文档写作助手后端
```

启动后访问：

```text
http://127.0.0.1:8000/
```

健康检查：

```text
http://127.0.0.1:8000/api/health
```

## Windows 桌面版

已生成可直接打开的 Windows 程序：

```text
D:\SRT\release\windows\DocumentWritingAssistant.exe
```

双击该文件即可使用，不需要再手动启动浏览器或输入网址。程序保存的任务和模型设置位于当前 Windows 用户的本地应用数据目录，重新打开后仍会保留。

需要重新生成安装包时，在 VSCode 终端运行：

```text
powershell -ExecutionPolicy Bypass -File scripts\build_windows.ps1
```

## 手机端与 PWA

网页端已经具备可安装网页应用（PWA）所需的图标、应用清单和离线静态资源缓存。部署到 HTTPS 服务器后，可在手机 Chrome 的浏览器菜单中选择“安装应用”。

同时，`mobile/android` 提供了 Android Studio 手机应用工程。打开手机应用后，填写写作服务地址即可使用同一套写作工作台。当前电脑没有可用于生成 APK 的 Android 开发环境，因此已经提供完整源码，待在 Android Studio 中打开后即可构建 APK。

手机与电脑处于同一可信 Wi-Fi 时，可以运行：

```text
powershell -ExecutionPolicy Bypass -File scripts\start_mobile_service.ps1
```

再在手机应用中填写电脑的局域网地址，例如 `http://192.168.1.15:8000`。这类局域网服务没有登录保护，只应在可信网络中临时使用。

## 测试方式

在 VSCode 终端中运行：

```text
python backend/tests/run_all.py
```

测试通过时会输出：

```text
All tests passed.
```

## 模型配置

未配置远程模型时，系统会使用本地演示生成逻辑，仍然可以完整演示。

启动系统后，点击页面右上角的“模型设置”，填写 OpenAI 兼容接口的地址、模型名称和 API Key，点击“保存并启用”后即可使用。点击“测试连接”可确认模型是否能正常调用；点击“使用本地模式”可随时切回演示生成逻辑。

API Key 只保存在本机的 `backend/data/model_config.json` 中，接口不会把它返回到浏览器页面；该文件也已被 Git 忽略，不会上传到 GitHub。

## 项目结构

```text
D:\SRT
  backend/
    app/
      core/
      skills/
      storage/
      exporter/
      main.py
    static/
      index.html
      styles.css
      app.js
    tests/
      http_smoke_test.py
      export_structure_test.py
      run_all.py
    server.py
  docs/
    01-requirements-positioning.md
    02-system-architecture.md
    03-writing-task-kernel-design.md
    04-backend-implementation.md
    05-frontend-workbench.md
    06-testing-and-output.md
    07-paper-summary-and-demo.md
```

## 关键文档

- 需求与差异化定位：`docs/01-requirements-positioning.md`
- 系统总体架构：`docs/02-system-architecture.md`
- 写作任务内核设计：`docs/03-writing-task-kernel-design.md`
- 后端实现说明：`docs/04-backend-implementation.md`
- 前端工作台说明：`docs/05-frontend-workbench.md`
- 测试与输出说明：`docs/06-testing-and-output.md`
- 论文说明与项目总结：`docs/07-paper-summary-and-demo.md`
- 应用形态与分发：`docs/09-app-distribution.md`

## 当前状态

项目已经完成可演示闭环：前端输入写作要求，后端生成提纲和正文，用户执行修订和摘要生成，最终导出 Word 或文本文件。
