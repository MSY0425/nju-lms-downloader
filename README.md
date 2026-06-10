# NJU LMS 课件批量下载工具

适用于南京大学 TronClass 学习管理平台（lms.nju.edu.cn），可批量下载指定课程的所有课件附件（PPT、PDF 等）。

## 功能

- 自动获取课程全部课件列表（支持分页）
- 通过签名 URL 下载附件文件
- 自动跳过已下载的文件
- 支持自定义保存目录

## 环境要求

- Python 3.7+
- requests 库

```bash
pip install requests
```

## 使用方法

### 第一步：获取 Cookie

1. 在浏览器中登录 [lms.nju.edu.cn](https://lms.nju.edu.cn)，进入目标课程页面
2. 按 `F12` 打开开发者工具 → **Network（网络）** 标签
3. 刷新页面，点击任意一条发往 `lms.nju.edu.cn` 的请求
4. 在 **Request Headers** 中找到 `Cookie:` 一行，复制其完整内容

### 第二步：创建配置文件

复制 `config.example.json` 为 `config.json`，填写你的信息：

```json
{
  "cookies": "session=你的session值; _ga=...",
  "course_id": 7228,
  "save_dir": "C:/Users/你的用户名/Desktop/下载目录"
}
```

| 字段 | 说明 |
|------|------|
| `cookies` | 从浏览器复制的完整 Cookie 字符串 |
| `course_id` | 课程 ID，从课程页面 URL 中获取，如 `lms.nju.edu.cn/course/7228/...` 中的 `7228` |
| `save_dir` | 文件保存路径，留空则保存到脚本所在目录 |

### 第三步：运行脚本

```bash
python download_ppt.py
```

## 注意事项

- Cookie 具有时效性，若下载失败请重新获取
- 本工具仅供个人学习使用，请遵守学校相关规定
- `config.json` 已加入 `.gitignore`，不会被提交到版本库，请勿手动上传

## 原理说明

1. 调用 `/api/course/{id}/coursewares` 获取课件活动列表
2. 从每个活动的 `cc_license_references` 字段中提取 `upload_id`
3. 调用 `/api/uploads/{upload_id}/url` 获取带签名的临时下载链接
4. 下载文件到本地

## License

MIT
