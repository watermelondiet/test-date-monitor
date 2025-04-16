import requests
from bs4 import BeautifulSoup
import re
import os
import json
import time
from datetime import datetime

# Configuration
TOPIC_NAME = "NIC-Esthetics-Alerts-Fife"
SEEN_FILE = "seen_test_entries.json"
URL = "https://www.isoqualitytesting.com/waavail.aspx"

def send_push_notification(test_info):
    url = f"https://ntfy.sh/NIC-Esthetics-Alerts-Fife"
    headers = {
        "Title": "New Test Date Found!",
        "Priority": "high"
    }
    message = f"🚨 A new NIC Esthetics test has been posted:\n\n{test_info}"
    response = requests.post(url, data=message.encode("utf-8"), headers=headers)
    if response.status_code == 200:
        print("✅ Notification sent.")
    else:
        print(f"❌ Failed to send notification: {response.status_code}")

def load_seen_entries():
    if os.path.exists(SEEN_FILE):
        with open(SEEN_FILE, "r", encoding="utf-8") as f:
            return set(json.load(f))
    return set()

def save_seen_entries(seen_entries):
    with open(SEEN_FILE, "w", encoding="utf-8") as f:
        json.dump(list(seen_entries), f)

def extract_hidden_fields(soup):
    data = {}
    for tag in soup.find_all("input", type="hidden"):
        if tag.has_attr("name"):
            data[tag["name"]] = tag.get("value", "")
    return data

def check_for_new_test_dates():
    seen_entries = load_seen_entries()
    new_found = False

    session = requests.Session()
    headers_get = {"User-Agent": "Mozilla/5.0"}
    res = session.get(URL, headers=headers_get)
    soup = BeautifulSoup(res.text, "html.parser")

    data = extract_hidden_fields(soup)

    data.update({
        "RadScriptManager1": "rcbPracticalPanel|rcbPractical",
        "__EVENTTARGET": "rcbPractical",
        "__EVENTARGUMENT": '{"Command":"Select","Index":0}',
        "__ASYNCPOST": "true",
        "rcbPractical": "IQT/DL Roope Administrations - Washington - Fife Test Facility",
        "rcbPractical_ClientState": '{"logEntries":[],"value":"1342","text":"IQT/DL Roope Administrations - Washington - Fife Test Facility","enabled":true,"checkedIndices":[],"checkedItemsTextOverflows":false}',
        "RadAJAXControlID": "RadAjaxManager1"
    })

    headers_post = {
        "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
        "User-Agent": "Mozilla/5.0",
        "X-MicrosoftAjax": "Delta=true",
        "Origin": URL,
        "Referer": URL
    }

    res_post = session.post(URL, headers=headers_post, data=data)

    start = res_post.text.find("<table")
    end = res_post.text.rfind("</table>") + len("</table>")

    if start != -1 and end != -1:
        table_html = res_post.text[start:end]
        soup_table = BeautifulSoup(table_html, "html.parser")

        for row in soup_table.find_all("tr"):
            row_text = row.text.strip()
            if re.search(r"NIC.*Esthetics", row_text, re.IGNORECASE):
                if row_text not in seen_entries:
                    send_push_notification(row_text)
                    seen_entries.add(row_text)
                    new_found = True

        if not new_found:
            print("ℹ️ No new matching entries found.")
        save_seen_entries(seen_entries)
    else:
        print("❌ No table found in the response.")

def wait_until_next_half_hour():
    while True:
        now = datetime.now()
        if now.minute in [0, 30] and now.second == 0:
            break
        time.sleep(1)

# Main loop
while True:
    wait_until_next_half_hour()
    print(f"🕒 Running at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    check_for_new_test_dates()
    time.sleep(61)  # Avoid duplicate triggers within the same minute
