import streamlit as st
import pandas as pd
from PIL import Image
import io
import base64
from openai import OpenAI

# 1. 초기 설정
st.set_page_config(page_title="나이키 재고 관리", layout="wide")
st.title("👟 나이키 매장 통합 관리 시스템 (고속 모드)")

# OpenAI 클라이언트 (사장님 API 키가 환경변수에 등록되어 있어야 합니다)
client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])

# 2. 사진 업로드 (여러 장 허용)
uploaded_files = st.file_uploader(
    "사진들을 한꺼번에 선택하세요 (100장도 가능!)", 
    type=["jpg", "png", "jpeg"], 
    accept_multiple_files=True
)

if uploaded_files:
    st.success(f"✅ 총 {len(uploaded_files)}장의 사진이 선택되었습니다.")
    
    if st.button("🚀 전체 분석 시작"):
        all_results = []
        progress_bar = st.progress(0)
        
        for i, uploaded_file in enumerate(uploaded_files):
            # [핵심] 사진 압축: 용량을 1/10 이하로 줄입니다.
            img = Image.open(uploaded_file)
            img.thumbnail((800, 800)) # AI가 글자를 읽기에 충분한 크기
            
            buffer = io.BytesIO()
            img.save(buffer, format="JPEG", quality=70) # 화질 최적화
            encoded_image = base64.b64encode(buffer.getvalue()).decode('utf-8')
            
            # [분석] GPT-4o-mini에게 전달
            try:
                response = client.chat.completions.create(
                    model="gpt-4o-mini",
                    messages=[
                        {
                            "role": "user",
                            "content": [
                                {"type": "text", "text": "이 사진 속 신발의 품번(sku), 사이즈, 가격을 찾아 JSON 형식으로 대답해줘."},
                                {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{encoded_image}"}}
                            ],
                        }
                    ],
                    response_format={"type": "json_object"}
                )
                
                # 결과 저장
                import json
                res = json.loads(response.choices[0].message.content)
                all_results.append(res)
                st.write(f"📸 {i+1}번 사진 완료: {res.get('sku', '미인식')}")
                
            except Exception as e:
                st.error(f"❌ {i+1}번 사진 분석 중 오류 발생")
            
            # 진행바 업데이트
            progress_bar.progress((i + 1) / len(uploaded_files))

        # 3. 결과 표시 및 엑셀 다운로드
        if all_results:
            df = pd.DataFrame(all_results)
            st.subheader("📊 전체 분석 결과")
            st.dataframe(df)
            
            csv = df.to_csv(index=False).encode('utf-8-sig')
            st.download_button("📥 전체 결과 엑셀 다운로드", csv, "nike_inventory.csv", "text/csv")
