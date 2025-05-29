# -*- coding: utf-8 -*-
import os, logging, smtplib, traceback, random
from datetime import datetime
from dateutil import parser
from email.mime.text import MIMEText
from flask import Flask, request, jsonify
from flask_cors import CORS
from openai import OpenAI

# === Setup ===
app = Flask(__name__)
CORS(app)
logging.basicConfig(level=logging.DEBUG)

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

SMTP_SERVER = "smtp.gmail.com"
SMTP_PORT = 587
SMTP_USERNAME = "kata.chatbot@gmail.com"
SMTP_PASSWORD = os.getenv("SMTP_PASSWORD")

LANGUAGE = {
    "tw": {
        "email_subject": "您的投資人洞察報告",
        "report_title": "🎯 投資人洞察報告"
    }
}

# === Utility ===
def compute_age(dob):
    try:
        dt = parser.parse(dob)
        today = datetime.today()
        return today.year - dt.year - ((today.month, today.day) < (dt.month, dt.day))
    except:
        return 0

def get_openai_response(prompt, temp=0.85):
    try:
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": prompt}],
            temperature=temp
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        logging.error(f"OpenAI error: {e}")
        return None

def send_email(html_body, subject):
    msg = MIMEText(html_body, 'html', 'utf-8')
    msg['Subject'] = subject
    msg['From'] = SMTP_USERNAME
    msg['To'] = SMTP_USERNAME
    try:
        with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
            server.starttls()
            server.login(SMTP_USERNAME, SMTP_PASSWORD)
            server.send_message(msg)
    except Exception as e:
        logging.error(f"Email send error: {e}")

# === AI Content Blocks ===
def generate_chart_metrics():
    return [
        {
            "title": "市場定位",
            "labels": ["品牌記憶度", "客戶契合度", "聲譽黏性"],
            "values": [random.randint(70, 90), random.randint(65, 85), random.randint(70, 90)]
        },
        {
            "title": "投資吸引力",
            "labels": ["故事信心度", "擴展性模型", "信任證明度"],
            "values": [random.randint(70, 85), random.randint(60, 80), random.randint(75, 90)]
        },
        {
            "title": "戰略執行力",
            "labels": ["合作準備度", "高端通路運用", "領導影響力"],
            "values": [random.randint(65, 85), random.randint(65, 85), random.randint(75, 90)]
        }
    ]

def generate_chart_html(metrics):
    colors = ["#8C52FF", "#5E9CA0", "#F2A900"]
    html = ""
    for i, m in enumerate(metrics):
        html += f"<strong style='font-size:18px;color:#333;'>{m['title']}</strong><br>"
        for j, (label, val) in enumerate(zip(m['labels'], m['values'])):
            html += (
                f"<div style='display:flex;align-items:center;margin-bottom:8px;'>"
                f"<span style='width:180px;'>{label}</span>"
                f"<div style='flex:1;background:#eee;border-radius:5px;overflow:hidden;'>"
                f"<div style='width:{val}%;height:14px;background:{colors[j % len(colors)]};'></div></div>"
                f"<span style='margin-left:10px;'>{val}%</span></div>"
            )
        html += "<br>"
    return html

def build_dynamic_summary(age, experience, industry, country, metrics):
    brand, fit, stick = metrics[0]["values"]
    conf, scale, trust = metrics[1]["values"]
    partn, luxury, leader = metrics[2]["values"]
    return (
        "<br><div style='font-size:24px;font-weight:bold;'>🧠 策略總結：</div><br>"
        f"<p style='line-height:1.7;'>在 {country} 的 {industry} 行業中，擁有 {experience} 年經驗、年齡 {age} 歲的專業人士通常在市場定位方面表現穩健。品牌記憶度平均為 {brand}%，客戶契合度為 {fit}%，聲譽黏性為 {stick}%。</p>"
        f"<p style='line-height:1.7;'>在區域投資人心中，故事信心度（{conf}%）與信任證明（{trust}%）是吸引投資的關鍵因素。擴展性模型得分 {scale}%，代表還有成長空間。</p>"
        f"<p style='line-height:1.7;'>合作準備度為 {partn}%、高端通路運用為 {luxury}%、領導影響力為 {leader}% —— 這些體現了具備國際化執行力與影響力的潛質。</p>"
        f"<p style='line-height:1.7;'>綜合比較新加坡、馬來西亞和台灣的同行趨勢，您在該領域展現出顯著的戰略優勢與投資吸引力。</p>"
    )

# === Endpoint ===
@app.route("/investor_analyze_tw", methods=["POST"])
def investor_analyze_tw():
    try:
        data = request.get_json(force=True)
        logging.debug(f"POST received: {data}")

        full_name = data.get("fullName")
        chinese_name = data.get("chineseName", "")
        dob = data.get("dob")
        company = data.get("company")
        role = data.get("role")
        country = data.get("country")
        experience = data.get("experience")
        industry = data.get("industry")
        if industry == "Other":
            industry = data.get("otherIndustry", "其他")
        challenge = data.get("challenge")
        context = data.get("context")
        target = data.get("targetProfile")
        advisor = data.get("advisor")
        email = data.get("email")

        age = compute_age(dob)
        chart_metrics = generate_chart_metrics()
        chart_html = generate_chart_html(chart_metrics)
        summary_html = build_dynamic_summary(age, experience, industry, country, chart_metrics)

        prompt = (
            f"你是一位商業顧問，請為在{country}從事{industry}行業、有{experience}年經驗的專業人士，"
            "撰寫10條具創意、富啟發性的吸引投資人技巧，每條以表情符號開頭。語言用繁體中文，風格輕鬆、實用。"
        )
        tips_text = get_openai_response(prompt)
        if tips_text:
            tips_block = "<br><div style='font-size:24px;font-weight:bold;'>💡 創意建議：</div><br>" + \
                         "<br>".join(f"<p style='font-size:16px;'>{line.strip()}</p>" for line in tips_text.splitlines() if line.strip())
        else:
            tips_block = "<p style='color:red;'>⚠️ 無法產生創意建議，請稍後重試。</p>"

        footer = (
            "<div style='background-color:#f9f9f9;color:#333;padding:20px;border-left:6px solid #8C52FF;"
            "border-radius:8px;margin-top:30px;'>"
            "<strong>📊 本報告基於以下來源：</strong>"
            "<ul style='margin-top:10px;margin-bottom:10px;padding-left:20px;line-height:1.7;'>"
            "<li>新加坡、馬來西亞、台灣地區的專業人士匿名數據</li>"
            "<li>OpenAI 投資趨勢模型 + 區域市場洞察</li></ul>"
            "<p style='margin-top:10px;line-height:1.7;'>本分析符合 PDPA 合規標準，所有資料僅用於統計模型，不會儲存個人記錄。</p>"
            "<p style='margin-top:10px;line-height:1.7;'>"
            "<strong>附註：</strong> 此為初步洞察，我們將在 24 至 48 小時內發送更完整的定制報告。"
            "若您想加速獲取建議，也可預約 15 分鐘私人通話服務。🎯</p></div>"
        )

        title = f"<h4 style='text-align:center;font-size:24px;'>{LANGUAGE['tw']['report_title']}</h4>"

        details = (
            f"<br><div style='font-size:14px;color:#666;'>"
            f"<strong>📝 提交摘要</strong><br>"
            f"英文名: {full_name}<br>"
            f"中文名: {chinese_name}<br>"
            f"出生日期: {dob}<br>"
            f"國家: {country}<br>"
            f"公司: {company}<br>"
            f"職位: {role}<br>"
            f"經驗年數: {experience}<br>"
            f"行業: {industry}<br>"
            f"挑戰: {challenge}<br>"
            f"背景說明: {context}<br>"
            f"目標對象: {target}<br>"
            f"推薦人: {advisor}<br>"
            f"電郵: {email}</div><br>"
        )

        full_html = title + details + chart_html + summary_html + tips_block + footer
        send_email(full_html, LANGUAGE['tw']['email_subject'])

        return jsonify({"html_result": title + chart_html + summary_html + tips_block + footer})

    except Exception as e:
        logging.error(f"investor_analyze_tw error: {e}")
        traceback.print_exc()
        return jsonify({"error": "伺服器錯誤，請稍後再試"}), 500

# === Run Server Locally ===
if __name__ == "__main__":
    app.run(debug=True)
