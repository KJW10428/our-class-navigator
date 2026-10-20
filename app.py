import datetime
import os
import pandas as pd
import streamlit as st

# 1. 페이지 기본 설정
st.set_page_config(
    page_title="우리반 네비게이터",
    page_icon="🏫",
    layout="wide",
    initial_sidebar_state="expanded",
)

# 2. 커스텀 디자인 설정 (친구들 앱보다 훨씬 예쁜 카드 스타일 적용!)
st.markdown(
    """
    <style>
    /* 카드 상자 스타일 */
    .custom-card {
        background: linear-gradient(135deg, #ffffff 0%, #f0f4ff 100%);
        border: 2px solid #3b82f6;
        border-radius: 12px;
        padding: 18px;
        margin-bottom: 15px;
        box-shadow: 0 4px 6px rgba(0,0,0,0.05);
    }
    /* 알림 카드 스타일 */
    .notice-card {
        background-color: #fef3c7;
        border-left: 6px solid #f59e0b;
        padding: 15px;
        border-radius: 8px;
        margin-bottom: 12px;
    }
    /* 큰 메인 제목 */
    .main-title {
        color: #1e40af;
        font-weight: 800;
        margin-bottom: 10px;
    }
    </style>
""",
    unsafe_allow_html=True,
)

# 3. Gemini AI 설정 (에러 방지 안전 로직)
ai_client = None
try:
    from google import genai

    api_key = st.secrets.get("GEMINI_API_KEY") or os.environ.get(
        "GEMINI_API_KEY"
    )
    if api_key:
        ai_client = genai.Client(api_key=api_key)
except Exception:
    ai_client = None

# 4. 데이터 저장 공간 (공지사항)
if "announcements" not in st.session_state:
    st.session_state.announcements = [
        {
            "date": "2026-10-21",
            "period": "3교시",
            "subject": "과학",
            "original": "1반 교실",
            "changed": "제2과학실 (창의관 3층)",
            "note": "실험복 착용 필수",
        },
        {
            "date": "2026-10-22",
            "period": "5교시",
            "subject": "체육",
            "original": "운동장",
            "changed": "체육관 (강당)",
            "note": "우천으로 인한 장소 변경",
        },
    ]

# 5. 시간표 및 교실 정보 데이터
TIMETABLE = {
    "월요일": [
        ("1교시", "국어", "1반 교실"),
        ("2교시", "수학", "1반 교실"),
        ("3교시", "과학", "제1과학실 (본관 3층)"),
        ("4교시", "영어", "영어 전용실 (본관 2층)"),
        ("5교시", "사회", "1반 교실"),
        ("6교시", "체육", "운동장"),
        ("7교시", "동아리", "각 동아리실"),
    ],
    "화요일": [
        ("1교시", "수학", "1반 교실"),
        ("2교시", "국어", "1반 교실"),
        ("3교시", "음악", "음악실 (예술관 2층)"),
        ("4교시", "과학", "1반 교실"),
        ("5교시", "영어", "1반 교실"),
        ("6교시", "역사", "1반 교실"),
        ("7교시", "자율", "1반 교실"),
    ],
    "수요일": [
        ("1교시", "미술", "미술실 (예술관 1층)"),
        ("2교시", "미술", "미술실 (예술관 1층)"),
        ("3교시", "국어", "1반 교실"),
        ("4교시", "수학", "1반 교실"),
        ("5교시", "정보", "컴퓨터실 (창의관 2층)"),
        ("6교시", "정보", "컴퓨터실 (창의관 2층)"),
        ("7교시", "학급회의", "1반 교실"),
    ],
    "목요일": [
        ("1교시", "영어", "1반 교실"),
        ("2교시", "사회", "1반 교실"),
        ("3교시", "수학", "1반 교실"),
        ("4교시", "체육", "체육관"),
        ("5교시", "과학", "제2과학실 (창의관 3층)"),
        ("6교시", "국어", "1반 교실"),
        ("7교시", "한문", "1반 교실"),
    ],
    "금요일": [
        ("1교시", "역사", "1반 교실"),
        ("2교시", "영어", "1반 교실"),
        ("3교시", "수학", "1반 교실"),
        ("4교시", "국어", "1반 교실"),
        ("5교시", "기술가정", "가정실습실 (본관 4층)"),
        ("6교시", "기술가정", "가정실습실 (본관 4층)"),
        ("7교시", "진로", "1반 교실"),
    ],
}

ROOM_INFO = {
    "제1과학실": {
        "location": "본관 3층 중앙",
        "guide": "본관 중앙 계단을 이용해 3층으로 올라간 후 오른쪽 두 번째 교실입니다.",
        "note": "실습 도구 주의, 음료 반입 금지",
    },
    "제2과학실": {
        "location": "창의관 3층",
        "guide": "본관 2층 구름다리로 창의관 이동 후 3층으로 올라가세요.",
        "note": "실험복 착용 필수",
    },
    "음악실": {
        "location": "예술관 2층",
        "guide": "예술관 1층 입구 우측 계단을 이용해 2층으로 올라오세요.",
        "note": "실내화 착용, 악기 조심히 다루기",
    },
    "미술실": {
        "location": "예술관 1층",
        "guide": "예술관 1층 중앙 통로 우측입니다.",
        "note": "앞치마 지참",
    },
    "컴퓨터실": {
        "location": "창의관 2층",
        "guide": "창의관 엘리베이터 옆 201호입니다.",
        "note": "음식물 반입 절대 금지",
    },
    "체육관 (강당)": {
        "location": "체육관 1층",
        "guide": "운동장을 지나 우측 건물 입구로 들어오세요.",
        "note": "체육화 착용 필수",
    },
}

# 6. 사이드바 메뉴 (스크린샷 항목과 정확히 100% 일치하도록 작성)
st.sidebar.image(
    "https://img.icons8.com/color/96/school.png", use_container_width=False
)
st.sidebar.title("📌 바로가기")

menu = st.sidebar.radio(
    "원하는 페이지를 선택하세요:",
    [
        "우리반 네비게이터",
        "교실 및 특별실 상세정보",
        "우리반 기본 시간표",
        "이동 수업 및 교실 공지",
        "학교 지도 및 길 안내",
    ],
)

# 7. 메인 헤더
st.markdown(
    "<h1 class='main-title'>🏫 우리반 네비게이터</h1>", unsafe_allow_html=True
)
st.info(
    f"🔔 **알림**: 등록된 교실 변경 사항이 **{len(st.session_state.announcements)}건** 있습니다. 이동 수업 전 확인하세요!"
)
st.markdown("---")

# =========================================================
# PAGE 1: 우리반 네비게이터 (메인 홈)
# =========================================================
if menu == "우리반 네비게이터":
    st.subheader("📋 앱 소개 및 가이드 안내")

    st.markdown(
        """
    <div class="custom-card">
        <h3 style="margin-top:0;">❓ 어느 날 시간표가 갑자기 바뀌거나 특별실 위치가 바뀌어 당황하신 적이 있나요?</h3>
        <h4 style="color:#2563eb; margin-bottom:0;">👉 이제 걱정할 필요 없습니다! '우리반 네비게이터'가 정확하게 안내해 드립니다!</h4>
    </div>
    """,
        unsafe_allow_html=True,
    )

    st.write("### 🎨 주요 기능 안내")

    col1, col2 = st.columns(2)
    with col1:
        st.markdown(
            """
        <div class="custom-card">
            <h4>📅 1. 우리반 기본 시간표</h4>
            <p>요일별 정규 수업과 기본 교실 위치를 한눈에 확인하세요.</p>
        </div>
        """,
            unsafe_allow_html=True,
        )

        st.markdown(
            """
        <div class="custom-card">
            <h4>📢 2. 이동 수업 및 교실 공지</h4>
            <p>갑자기 바뀐 이동 수업 장소를 빠르게 확인하고 새로 등록합니다.</p>
        </div>
        """,
            unsafe_allow_html=True,
        )

    with col2:
        st.markdown(
            """
        <div class="custom-card">
            <h4>🗺️ 3. 학교 지도 및 길 안내</h4>
            <p>내가 가야 하는 특별실까지 헤매지 않는 최적 경로를 안내합니다.</p>
        </div>
        """,
            unsafe_allow_html=True,
        )

        st.markdown(
            """
        <div class="custom-card">
            <h4>🔍 4. 교실 및 특별실 상세정보</h4>
            <p>특별실 이용 수칙 및 Gemini AI 기반 길안내 답변 기능 제공!</p>
        </div>
        """,
            unsafe_allow_html=True,
        )

    st.success("👈 왼쪽 **사이드바 메뉴**를 클릭하시면 원하는 화면으로 바로 이동합니다!")

# =========================================================
# PAGE 2: 교실 및 특별실 상세정보
# =========================================================
elif menu == "교실 및 특별실 상세정보":
    st.subheader("🔍 교실 및 특별실 상세정보 사전")

    selected_room = st.selectbox(
        "궁금한 특별실을 선택하세요:", list(ROOM_INFO.keys())
    )
    if selected_room:
        data = ROOM_INFO[selected_room]
        st.markdown(
            f"""
        <div class="custom-card">
            <h3 style="margin-top:0;">📍 {selected_room}</h3>
            <p><b>• 위치:</b> {data['location']}</p>
            <p><b>• 찾아가는 길:</b> {data['guide']}</p>
            <p><b>• 이용 수칙:</b> <span style="color:#dc2626;">{data['note']}</span></p>
        </div>
        """,
            unsafe_allow_html=True,
        )

    st.markdown("---")
    st.subheader("🤖 AI 네비게이터에게 질문하기 (Gemini)")

    user_query = st.text_input(
        "학교 길 찾기나 이동 수업에 대해 질문해보세요:",
        placeholder="예: 제2과학실 갈 때 실습복 어디서 갈아입어?",
    )

    if st.button("✨ AI에게 질문하기", type="primary"):
        if user_query:
            if ai_client is not None:
                with st.spinner("AI 답변 생성 중..."):
                    try:
                        prompt = f"당신은 친절한 학교 길안내 도우미입니다. 질문에 답변해 주세요: {user_query}"
                        response = ai_client.models.generate_content(
                            model="gemini-2.5-flash-lite", contents=prompt
                        )
                        st.write("🤖 **AI 답변:**")
                        st.info(response.text)
                    except Exception as e:
                        st.error(f"오류가 발생했습니다: {e}")
            else:
                st.warning(
                    "🔑 API 키가 설정되지 않아 기본 안내 모드로 작동합니다."
                )
                st.info(
                    f"'{user_query}'에 대한 안내입니다.\n\n"
                    "상단 선택 상자에서 교실을 선택하면 정확한 위치 및 이용 수칙을 확인하실 수 있습니다!"
                )
        else:
            st.warning("질문을 입력해 주세요.")

# =========================================================
# PAGE 3: 우리반 기본 시간표
# =========================================================
elif menu == "우리반 기본 시간표":
    st.subheader("📅 우리반 기본 시간표")

    weekdays = ["월요일", "화요일", "수요일", "목요일", "금요일"]
    today_num = datetime.datetime.now().weekday()
    default_day = weekdays[today_num] if today_num < 5 else "월요일"

    selected_day = st.selectbox(
        "요일 선택:", weekdays, index=weekdays.index(default_day)
    )

    data = TIMETABLE[selected_day]
    df = pd.DataFrame(data, columns=["교시", "과목", "기본 장소"])

    st.write(f"### 📖 {selected_day} 시간표")
    st.dataframe(df, use_container_width=True)

# =========================================================
# PAGE 4: 이동 수업 및 교실 공지
# =========================================================
elif menu == "이동 수업 및 교실 공지":
    st.subheader("📢 이동 수업 및 교실 공지")

    with st.expander("➕ 새 이동 수업 공지 등록하기"):
        with st.form("add_form", clear_on_submit=True):
            col1, col2 = st.columns(2)
            with col1:
                input_date = st.date_input(
                    "날짜", value=datetime.date.today()
                )
                input_period = st.selectbox(
                    "교시",
                    [
                        "1교시",
                        "2교시",
                        "3교시",
                        "4교시",
                        "5교시",
                        "6교시",
                        "7교시",
                    ],
                )
                input_subject = st.text_input(
                    "과목명", placeholder="예: 과학"
                )
            with col2:
                input_orig = st.text_input(
                    "기존 장소", placeholder="예: 1반 교실"
                )
                input_changed = st.text_input(
                    "변경 장소", placeholder="예: 제2과학실"
                )
                input_note = st.text_input(
                    "비고", placeholder="예: 실험복 지참"
                )

            submit_btn = st.form_submit_button("공지 등록")

            if submit_btn:
                if input_subject and input_changed:
                    st.session_state.announcements.append(
                        {
                            "date": str(input_date),
                            "period": input_period,
                            "subject": input_subject,
                            "original": input_orig or "기존 교실",
                            "changed": input_changed,
                            "note": input_note or "-",
                        }
                    )
                    st.success("새로운 변경 공지가 등록되었습니다!")
                    st.rerun()
                else:
                    st.error("과목명과 변경 장소는 필수 입력값입니다.")

    st.write("### 🚨 변경된 위치 공지 목록")
    for item in reversed(st.session_state.announcements):
        st.markdown(
            f"""
        <div class="notice-card">
            <h4 style="margin-top:0;">[{item['date']}] {item['period']} - {item['subject']}</h4>
            <p>📍 <b>장소:</b> {item['original']} ➡️ <b style="color:#dc2626;">{item['changed']}</b></p>
            <p>📝 <b>비고:</b> {item['note']}</p>
        </div>
        """,
            unsafe_allow_html=True,
        )

# =========================================================
# PAGE 5: 학교 지도 및 길 안내
# =========================================================
elif menu == "학교 지도 및 길 안내":
    st.subheader("🗺️ 학교 지도 및 길 안내")

    col1, col2 = st.columns(2)
    with col1:
        start_point = st.selectbox(
            "출발지:", ["1반 교실 (본관 2층)", "운동장", "본관 입구"]
        )
    with col2:
        dest_point = st.selectbox("도착지 (목적지):", list(ROOM_INFO.keys()))

    if st.button("🚩 경로 안내 시작", type="primary"):
        info = ROOM_INFO[dest_point]
        st.markdown(
            f"""
        <div class="custom-card">
            <h3>🎯 목적지: {dest_point} ({info['location']})</h3>
            <p style="font-size: 1.05rem;">🚶 <b>이동 경로:</b> {info['guide']}</p>
            <p style="color: #b45309;">💡 <b>주의 사항:</b> {info['note']}</p>
        </div>
        """,
            unsafe_allow_html=True,
        )
