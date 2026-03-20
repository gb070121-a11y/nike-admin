import streamlit as st
import cv2
import numpy as np
import base64
import json
import pandas as pd
from openai import OpenAI
from datetime import datetime

# 1. AI 열쇠 설정 (사장님의 키를 여기에 넣으세요)
client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])

st.set_page_config(page_title="나이키 통합 관리", layout="centered")
st.title("👟 나이키 매장 통합 관리 시스템")

# 2. 매장 선택 기능
with st.sidebar:
    st.header("📍 매장 설정")
    target_store = st.selectbox("조사할 매장", ["김해 나이키", "정관 신세계 나이키", "기타"])
    if target_store == "기타":
        target_store = st.text_input("매장명 입력")

# 3. 사진 분석 함수
def is_blackout(image_bytes):
    nparr = np.frombuffer(image_bytes, np.uint8)
    img = cv2.imdecode(nparr, cv2.IMREAD_GRAYSCALE)
    return np.mean(img) < 15 # 암전 감지

def extract_data(image_bytes):
    base64_img = base64.b64encode(image_bytes).decode('utf-8')
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": [
            {"type": "text", "text": "나이키 신발 정보(sku, price, discount, final_price)를 JSON으로 추출해줘. sku에 I와 1을 정확히 구분해."},
            {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{base64_img}"}}
        ]}],
        response_format={"type": "json_object"}
    )
    return json.loads(response.choices[0].message.content)

# 4. 실행 화면
uploaded_files = st.file_uploader("사진들을 순서대로 선택하세요", type=["jpg", "png", "jpeg"], accept_multiple_files=True)

if st.button("🚀 분석 시작"):
    if uploaded_files:
        all_data = []
        rack_num = 1
        now_date = datetime.now().strftime("%Y-%m-%d %H:%M")
        
        for file in uploaded_files:
            img_bytes = file.read()
            if is_blackout(img_bytes):
                rack_num += 1
                st.info(f"⬛ {rack_num}번 랙 시작")
                continue
            
            res = extract_data(img_bytes)
            res.update({'매장명': target_store, '조사일시': now_date, '랙번호': f"{rack_num}번 랙"})
            all_data.append(res)
            st.write(f"✅ {res['sku']} 완료")

        if all_data:
            df = pd.DataFrame(all_data)
            st.subheader("📊 분석 결과")
            st.dataframe(df)
            csv = df.to_csv(index=False).encode('utf-8-sig')
            st.download_button("💾 엑셀 다운로드", csv, f"{target_store}_{now_date}.csv")
