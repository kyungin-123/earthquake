import streamlit as st
import pandas as pd
import folium
from streamlit_folium import st_folium

# 1. 데이터 불러오기
@st.cache_data 
def load_data():
    try:
        # 파일명을 'quake.csv'로 변경
        df = pd.read_csv('quake.csv')
        return df
    except:
        st.error("지진 데이터 파일(quake.csv)을 찾을 수 없습니다.")
        return None

def main():
    st.set_page_config(page_title="지진 위험도 분석 시스템", layout="wide")
    
    st.title("🌍 지진 위험도 예측 및 지도 시각화")
    st.write("특정 위치의 위도와 경도를 입력하면 주변 데이터를 분석하여 위험도를 알려주고 지도로 표시합니다.")

    df_new = load_data()
    
    if df_new is not None:
        
        # 데이터의 모든 열 이름을 강제로 소문자로 통일
        df_new.columns = df_new.columns.str.lower()
        
        # [안전 장치] 데이터에 'cluster' 열이 있는지 확인
        if 'cluster' not in df_new.columns:
            st.error("🚨 에러: 불러온 데이터에 'cluster'라는 열(항목)이 없습니다!")
            st.info(f"현재 quake.csv 파일에 있는 실제 열 이름들: {df_new.columns.tolist()}")
            st.warning("해결 방법: 군집화(K-Means 등)를 통해 'cluster' 데이터를 생성하는 과정이 파일에 포함되어 있는지 확인해 주세요.")
            st.stop() # 에러 방지를 위해 여기서 코드 실행을 멈춥니다.

        # 위험도 및 색상 정의
        risk_dict = {0: '높음', 1: '낮음', 2: '중간'}
        colors = {0: 'red', 1: 'blue', 2: 'green'}

        # 좌측 사이드바: 입력값 받기
        st.sidebar.header("📍 위치 입력")
        lat = st.sidebar.number_input("위도(Latitude) 입력:", value=37.5665, format="%.4f")
        lon = st.sidebar.number_input("경도(Longitude) 입력:", value=126.9780, format="%.4f")
        
        # ⭐ 버튼 클릭 여부를 기억하는 메모장(session_state) 생성
        if 'btn_clicked' not in st.session_state:
            st.session_state.btn_clicked = False

        # 버튼을 누르면 메모장에 True(눌림)라고 기록
        if st.sidebar.button("데이터 분석 및 지도 표시"):
            st.session_state.btn_clicked = True
        
        # 버튼이 눌렸던 기록이 있다면 아래 분석 및 지도 그리기 실행
        if st.session_state.btn_clicked:
            # A. 반경 5도 이내 데이터 필터링
            near_df = df_new[
                (df_new['위도'] >= lat - 5) & (df_new['위도'] <= lat + 5) & 
                (df_new['경도'] >= lon - 5) & (df_new['경도'] <= lon + 5)
            ]

            st.subheader("📊 분석 결과")
            
            # 필터링된 데이터가 존재하는지 확인 (빈 데이터 에러 방지)
            if not near_df.empty:
                # 위험도 연산 로직
                cluster_ratio = near_df['cluster'].value_counts(normalize=True) 
                main_cluster = cluster_ratio.idxmax()
                risk_level = risk_dict[main_cluster]

                # 텍스트 결과 출력
                col1, col2 = st.columns(2)
                with col1:
                    st.metric(label="예상 위험도", value=risk_level)
                with col2:
                    st.write(f"반경 5도 내 관측된 지진 횟수: **{len(near_df)}**회")
                
                # B. 지도 시각화 로직
                st.subheader("🗺️ 지진 분포 지도")
                st.write("🔴: 높음 | 🟢: 중간 | 🔵: 낮음 | ⭐: 입력 위치")
                
                # 지도 생성 (입력한 위치를 중심으로 설정)
                m = folium.Map(location=[lat, lon], zoom_start=5)
                
                # 샘플링 데이터 표시 (화면 멈춤을 방지하기 위해 최대 500개 샘플링)
                sample_count = min(len(df_new), 500)
                df_sample = df_new.sample(sample_count, random_state=42)

                for i in range(len(df_sample)):
                    row = df_sample.iloc[i]
                    cluster_val = row['cluster']
                    
                    folium.CircleMarker(
                        location=[row['위도'], row['경도']],
                        radius=3,
                        color=colors.get(cluster_val, 'gray'),
                        fill=True,
                        fill_color=colors.get(cluster_val, 'gray'),
                        fill_opacity=0.6
                    ).add_to(m)

                # 입력한 위치에 별모양 마커 표시
                folium.Marker(
                    location=[lat, lon],
                    popup="입력 위치",
                    icon=folium.Icon(color='black', icon='star')
                ).add_to(m)

                # 스트림릿에 지도 표시
                st_folium(m, width=1000, height=500)
                
            else:
                st.warning("입력하신 위치 반경 5도 이내에 분석할 수 있는 지진 데이터가 없습니다. 다른 좌표를 입력해 보세요.")

if __name__ == "__main__":
    main()