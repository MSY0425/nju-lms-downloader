import requests
import os
import json
import urllib.parse
import re
from urllib.parse import unquote

CONFIG_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "config.json")

if not os.path.exists(CONFIG_FILE):
    print("未找到 config.json，请先创建配置文件。")
    print("参考 config.example.json 填写你的 Cookie 和课程 ID。")
    exit(1)

with open(CONFIG_FILE, encoding="utf-8") as f:
    config = json.load(f)

COOKIES_STR = config.get("cookies", "")
COURSE_ID = str(config.get("course_id", ""))
SAVE_DIR = config.get("save_dir", os.path.dirname(os.path.abspath(__file__)))

if not COOKIES_STR or not COURSE_ID:
    print("config.json 中缺少 cookies 或 course_id，请检查配置。")
    exit(1)
BASE = "https://lms.nju.edu.cn"

session = requests.Session()
session.headers.update({
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Referer": f"{BASE}/course/{COURSE_ID}/courseware",
    "Accept": "application/json, */*",
})
for item in COOKIES_STR.split(";"):
    item = item.strip()
    if "=" in item:
        k, v = item.split("=", 1)
        session.cookies.set(k.strip(), v.strip(), domain="lms.nju.edu.cn")


def get_download_url(upload_id):
    r = session.get(f"{BASE}/api/uploads/{upload_id}/url", timeout=15)
    if r.status_code == 200:
        return r.json().get("url", "")
    return ""


def get_upload_name(upload_id):
    r = session.get(f"{BASE}/api/uploads/{upload_id}", timeout=15)
    if r.status_code == 200:
        return r.json().get("name", f"file_{upload_id}")
    return f"file_{upload_id}"


def download_file(url, filename):
    filepath = os.path.join(SAVE_DIR, filename)
    if os.path.exists(filepath):
        print(f"  已存在，跳过: {filename}")
        return True
    try:
        r = session.get(url, stream=True, timeout=60)
        if r.status_code == 200:
            with open(filepath, "wb") as f:
                for chunk in r.iter_content(chunk_size=65536):
                    f.write(chunk)
            size_kb = os.path.getsize(filepath) // 1024
            print(f"  已下载 ({size_kb} KB): {filename}")
            return True
        else:
            print(f"  下载失败 [{r.status_code}]: {filename}")
    except Exception as e:
        print(f"  下载出错: {e}")
    return False


print("=" * 55)
print("南京大学 LMS 课件下载器")
print("=" * 55)

# 获取全部课件（分页）
CONDITIONS = urllib.parse.quote('{"category":null,"class_ids":[],"itemsSortBy":{"predicate":"chapter","reverse":false},"ignore_activity_types":["lesson"]}')

all_activities = []
page, total_pages = 1, 1
while page <= total_pages:
    url = f"{BASE}/api/course/{COURSE_ID}/coursewares?conditions={CONDITIONS}&page={page}&page_size=50"
    r = session.get(url, timeout=15)
    if r.status_code != 200:
        print(f"获取课件列表失败 [{r.status_code}]")
        break
    data = r.json()
    activities = data.get("activities", [])
    all_activities.extend(activities)
    total = data.get("total", len(activities))
    total_pages = max(total_pages, (total + 49) // 50)
    print(f"第 {page}/{total_pages} 页，累计 {len(all_activities)} 个活动")
    page += 1

print(f"\n共 {len(all_activities)} 个活动，开始下载...\n")

success, skip, fail = 0, 0, 0
for act in all_activities:
    title = act.get("title", act.get("name", f"activity_{act.get('id')}"))
    refs = act.get("cc_license_references", [])

    if not refs:
        # 尝试从活动详情获取
        act_detail = session.get(f"{BASE}/api/activities/{act['id']}", timeout=10)
        if act_detail.status_code == 200:
            refs = act_detail.json().get("cc_license_references", [])

    if not refs:
        print(f"  [跳过] {title}（无附件）")
        skip += 1
        continue

    for ref in refs:
        upload_id = ref.get("upload_id")
        if not upload_id:
            continue

        # 获取文件名
        filename = get_upload_name(upload_id)
        # 清理文件名非法字符
        filename = re.sub(r'[\\/:*?"<>|]', '_', filename)

        # 获取带签名的下载链接
        dl_url = get_download_url(upload_id)
        if not dl_url:
            print(f"  [失败] 无法获取下载链接: {title}")
            fail += 1
            continue

        print(f"  [{title}] -> {filename}")
        if download_file(dl_url, filename):
            success += 1
        else:
            fail += 1

print("\n" + "=" * 55)
print(f"完成！成功: {success}  跳过: {skip}  失败: {fail}")
print(f"文件保存在: {SAVE_DIR}")
