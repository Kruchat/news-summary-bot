import os
import smtplib
import requests
import xml.etree.ElementTree as ET
from datetime import datetime
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders

# --- [รับค่าจาก GitHub Secrets เพื่อความปลอดภัย] ---
EMAIL_SENDER = os.environ.get("EMAIL_SENDER")
EMAIL_PASSWORD = os.environ.get("EMAIL_PASSWORD")
EMAIL_RECEIVER = os.environ.get("EMAIL_RECEIVER")
SEARCH_QUERY = "ข่าวล่าสุด"
# ------------------------------------------------

def get_latest_news():
    print(f"[{datetime.now().strftime('%H:%M:%S')}] กำลังรวบรวมข่าวล่าสุด...")
    url = f"https://news.google.com/rss/search?q={SEARCH_QUERY}&hl=th&gl=TH&ceid=TH:th"
    
    try:
        response = requests.get(url)
        root = ET.fromstring(response.content)
        
        news_items = []
        for i, item in enumerate(root.findall('.//item')[:15]):
            title = item.find('title').text
            clean_title = title.rsplit(' - ', 1)[0] if ' - ' in title else title
            news_items.append(f"{i+1}. {clean_title}")
            
        summary = f"📢 สรุปข่าวสำคัญ (GitHub Actions): {SEARCH_QUERY}\n"
        summary += f"ประจำวันที่: {datetime.now().strftime('%d/%m/%Y')} เวลา {datetime.now().strftime('%H:%M')} น.\n"
        summary += "="*50 + "\n\n"
        summary += "\n".join(news_items)
        summary += "\n\n" + "="*50
        summary += "\n(ส่งโดย GitHub Actions อัตโนมัติ 24 ชม.)"
        
        filename = "news_summary.txt"
        with open(filename, "w", encoding="utf-8") as f:
            f.write(summary)
        return filename
    except Exception as e:
        print(f"เกิดข้อผิดพลาดในการดึงข่าว: {e}")
        return None

def send_email(filename):
    if not filename: return
    if not EMAIL_SENDER or not EMAIL_PASSWORD:
        print("Error: EMAIL_SENDER หรือ EMAIL_PASSWORD ไม่ได้ถูกตั้งค่าใน Environment Variables")
        return
    
    print(f"กำลังส่งสรุปข่าวไปยัง {EMAIL_RECEIVER}...")
    msg = MIMEMultipart()
    msg['From'] = EMAIL_SENDER
    msg['To'] = EMAIL_RECEIVER
    msg['Subject'] = f"📊 [Auto] สรุปข่าวเด่น: {datetime.now().strftime('%H:%M')}"

    body = f"สรุปข่าวล่าสุดส่งตรงจาก GitHub Actions ครับ (ไม่มีลิงก์รบกวน)"
    msg.attach(MIMEText(body, 'plain'))

    with open(filename, "rb") as attachment:
        part = MIMEBase('application', 'octet-stream')
        part.set_payload(attachment.read())
        encoders.encode_base64(part)
        part.add_header('Content-Disposition', f"attachment; filename= {filename}")
        msg.attach(part)

    try:
        server = smtplib.SMTP('smtp.gmail.com', 587)
        server.starttls()
        server.login(EMAIL_SENDER, EMAIL_PASSWORD)
        server.sendmail(EMAIL_SENDER, EMAIL_RECEIVER, msg.as_string())
        server.quit()
        print("✅ ส่งอีเมลสรุปข่าวเรียบร้อยแล้ว!")
    except Exception as e:
        print(f"❌ ส่งอีเมลไม่สำเร็จ: {e}")

if __name__ == "__main__":
    file_name = get_latest_news()
    send_email(file_name)
