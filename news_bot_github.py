import os
import smtplib
import requests
import xml.etree.ElementTree as ET
from datetime import datetime
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders

# --- [ตั้งค่า] ---
EMAIL_SENDER = os.environ.get("EMAIL_SENDER")
EMAIL_PASSWORD = os.environ.get("EMAIL_PASSWORD")
EMAIL_RECEIVER = os.environ.get("EMAIL_RECEIVER")
SEARCH_QUERY = "ข่าวการศึกษา ข่าวเทคโนโลยี"
# ----------------

def get_latest_news():
    print("กำลังรวบรวมข่าวล่าสุด...")
    url = f"https://news.google.com/rss/search?q={SEARCH_QUERY}&hl=th&gl=TH&ceid=TH:th"
    
    try:
        response = requests.get(url)
        root = ET.fromstring(response.content)
        
        news_items = []
        html_items = ""
        
        for i, item in enumerate(root.findall('.//item')[:10]):
            title = item.find('title').text
            clean_title = title.rsplit(' - ', 1)[0] if ' - ' in title else title
            pub_date = item.find('pubDate').text
            
            news_items.append(f"{i+1}. {clean_title}")
            
            html_items += f"""
            <div class='news-item'>
                <div class='news-title'>{i+1}. {clean_title}</div>
                <div class='news-date'>{pub_date}</div>
            </div>
            """
            
        # 1. สร้างไฟล์ .txt สำหรับอีเมล
        summary_txt = f"สรุปข่าว: {SEARCH_QUERY}\n" + "\n".join(news_items)
        with open("news_summary.txt", "w", encoding="utf-8") as f:
            f.write(summary_txt)
            
        # 2. สร้างไฟล์ index.html (ต้องชื่อนี้เท่านั้นเพื่อให้ GitHub Actions หาเจอ)
        html_content = f"""
        <!DOCTYPE html>
        <html lang="th">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <style>
                body {{ font-family: 'Sarabun', sans-serif; background: transparent; margin: 0; padding: 10px; }}
                .container {{ background: white; border-radius: 10px; padding: 15px; box-shadow: 0 2px 5px rgba(0,0,0,0.1); }}
                .header {{ color: #2c3e50; border-bottom: 2px solid #3498db; padding-bottom: 10px; margin-bottom: 15px; font-size: 18px; font-weight: bold; }}
                .news-item {{ margin-bottom: 12px; padding-bottom: 8px; border-bottom: 1px solid #eee; }}
                .news-title {{ font-size: 15px; color: #333; line-height: 1.4; }}
                .news-date {{ font-size: 11px; color: #999; margin-top: 4px; }}
                .footer {{ font-size: 10px; color: #ccc; text-align: right; margin-top: 10px; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">📌 อัปเดตข่าวสารล่าสุด ({datetime.now().strftime('%H:%M')})</div>
                {html_items}
                <div class="footer">อัปเดตอัตโนมัติทุก 15 นาที</div>
            </div>
        </body>
        </html>
        """
        with open("index.html", "w", encoding="utf-8") as f:
            f.write(html_content)
            
        return "news_summary.txt"
    except Exception as e:
        print(f"เกิดข้อผิดพลาดในการดึงข่าว: {e}")
        return None

def send_email(filename):
    if not filename or not EMAIL_SENDER: return
    msg = MIMEMultipart()
    msg['From'] = EMAIL_SENDER
    msg['To'] = EMAIL_RECEIVER
    msg['Subject'] = f"📊 สรุปข่าวโรงเรียน: {datetime.now().strftime('%H:%M')}"
    msg.attach(MIMEText("สรุปข่าวล่าสุดตามไฟล์แนบครับ (ไม่มีลิงก์รบกวน)", 'plain'))
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
        print("✅ ส่งอีเมลสำเร็จ!")
    except Exception as e:
        print(f"❌ ส่งอีเมลไม่สำเร็จ: {e}")

if __name__ == "__main__":
    file_txt = get_latest_news()
    send_email(file_txt)
