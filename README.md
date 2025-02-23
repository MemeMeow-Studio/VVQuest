<div align="center">

<pre align="center">
██╗   ██╗██╗   ██╗ ██████╗ ██╗   ██╗███████╗███████╗████████╗
██║   ██║██║   ██║██╔═══██╗██║   ██║██╔════╝██╔════╝╚══██╔══╝
██║   ██║██║   ██║██║   ██║██║   ██║█████╗  ███████╗   ██║   
╚██╗ ██╔╝╚██╗ ██╔╝██║▄▄ ██║██║   ██║██╔══╝  ╚════██║   ██║   
 ╚████╔╝  ╚████╔╝ ╚██████╔╝╚██████╔╝███████╗███████║   ██║   
  ╚═══╝    ╚═══╝   ╚══▀▀═╝  ╚═════╝ ╚══════╝╚══════╝   ╚═╝   
</pre>

_✨ 通过自然语言检索表情包 ✨_

[在线体验](https://zvv.quest) · [反馈问题](https://github.com/DanielZhangyc/VVQuest/issues) · [参与贡献](https://github.com/DanielZhangyc/VVQuest/pulls)

[![License](https://img.shields.io/github/license/DanielZhangyc/VVQuest)](LICENSE)
[![Python Version](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org)
[![Online Demo](https://img.shields.io/website?url=https%3A%2F%2Fvv.xy0v0.top&up_message=online&down_message=offline&label=demo)](https://zvv.quest)

---

<p align="center">
    <a href="#-features">Features</a> •
    <a href="#-screenshots">Screenshots</a> •
    <a href="#-quick-start">Quick Start</a> •
    <a href="#-usage">Usage</a> •
    <a href="#-related-applications">Related Applications</a>
</p>

</div>

<a id="-features"></a>
## ✨ Features

> [!CAUTION]
> 本项目返回表情包结果由AI生成，与本人观点无关。

- **自然语言处理**: 采用嵌入模型，实现 Q&A 式的检索，能够对给出问题自动使用表情包回应。
- **高拓展性**: 可结合 VLM 高效为图片打上标签，制作资源包并在 [Issues](https://github.com/DanielZhangyc/VVQuest/issues) 中分享。
- **便捷使用**: 提供现成的web（无法导入资源包），API使用，以及iOS捷径使用，可不用部署到本地。
- 另外，**单纯使用检索功能**，若使用API无需任何花费💰

VVQuest 是一个基于自然语言的表情包检索工具。它能让你通过描述想要的场景，快速找到合适的表情包。不再需要记住具体的文件名或标签，就能轻松找到想要的表情！

<a id="-screenshots"></a>
## 📸 Screenshots

<table>
<tr>
<td width="50%">
<img src="screenshots/streamlit_vvquest.png" alt="主页面" width="100%"/>
<p align="center">主页面 - 表情包检索</p>
</td>
<td width="50%">
<img src="screenshots/webui.png" alt="Web界面" width="100%"/>
<p align="center">Web界面展示</p>
</td>
</tr>
<tr>
<td width="50%">
<img src="screenshots/streamlit_upload_images.png" alt="上传页面" width="100%"/>
<p align="center">上传页面 - 添加新表情包</p>
</td>
<td width="50%">
<img src="screenshots/streamlit_label_images.png" alt="标签页面" width="100%"/>
<p align="center">标签页面 - 为表情包添加描述</p>
</td>
</tr>
</table>

## ℹ️ Data Source

本项目张维为表情包来源于 [知乎](https://www.zhihu.com/question/656505859/answer/55843704436)

> [!CAUTION]
> 若有侵权，请联系删除

<a id="-quick-start"></a>
## 🚀 Quick Start

### 环境要求

- Python 3.11+
- 可选: Silicon Flow API Key (用于云端模型) / OpenAI API Key (用于 VLM 打标)

### 安装步骤

1. 克隆仓库
```bash
git clone https://github.com/DanielZhangyc/VVQuest.git
cd VVQuest
```

2. 安装依赖
```bash
pip install -r requirements.txt
```

3. 启动应用
```bash
python -m streamlit run app.py
```

> [!NOTE]
> 首次运行本地模型时会需要下载必要的模型文件，这可能需要一些时间。

<a id="-usage"></a>
## 📖 Usage

### Basic Usage

1. 访问 Web 界面 (默认为 `http://localhost:8501`)
2. 在搜索框中输入你想要的表情包场景描述
3. 点击搜索，系统会返回最匹配的表情包

### 图片管理

#### 上传新图片

1. 进入 `upload images` 页面
2. 在 `添加表情包` 下选择图片
3. 可选: 启用 `使用VLM自动生成文件名` 功能，这样省去人工打标的步骤

> [!CAUTION]
> 每次上传后需要重新生成缓存。

#### 图片打标

1. 进入 `label images` 页面
2. 选择图片文件夹
3. 点击 `使用VLM生成描述` 生成标签
4. 选择合适的描述并重命名文件或直接点击 `下一张` (会自动重命名)

### 导出资源包

1. 检查图片已经完全标记完成
2. 填写资源包相关信息
3. 点击 `导出资源包` 按钮
4. 等待生成完成后点击 `下载资源包`

> [!TIP]
> 你可以在 [Issues](https://github.com/DanielZhangyc/VVQuest/issues) 中分享你的资源包，或者查看其他用户分享的资源包。

### 导入资源包 (WIP)

<a id="-related-applications"></a>
## 📦 Related Applications

VVQuest 相关应用:
| 应用 | 作者   | GitHub | 链接 |
| --- | --- | --- | --- |
| VVQuest网页端 |  | [VVQuest](https://github.com/DanielZhangyc/VVQuest) | [链接](https://zvv.quest) |
| VVQuest iOS捷径 | [TomSmith163](https://github.com/TomSmith163) | [VVQuest](https://github.com/DanielZhangyc/VVQuest) | [链接](https://www.icloud.com/shortcuts/e6b0bd4c1b4c4b5195ff4e256fb009f8) |

> [!TIP]
> 如果你想添加你的应用，请提交 [PR](https://github.com/DanielZhangyc/VVQuest/pulls) 或 [Issue](https://github.com/DanielZhangyc/VVQuest/issues)

## 📄 License

本项目采用 [MIT](LICENSE) 开源协议。

## ⭐ Star History

[![Star History Chart](https://api.star-history.com/svg?repos=DanielZhangyc/VVQuest&type=Date)](https://star-history.com/#DanielZhangyc/VVQuest&Date)

---
