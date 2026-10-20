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

# 2. Gemini AI 설정 (오류 방지 예외 처리)
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

# 3. Session State (공지사항 데이터 관리)
if "announcements" not in st.session_state:
    st.session_state.announcements = [
        {
            "date": "2026-10-21",
            "period": "3교시",
            "subject": "과학",
            "original": "1반 교실",
            "changed": "제2과학실 (창의관 3층)",
            "note": "실험복 착용 및 창의관 3층으로 이동",
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

# 4. 시간표 및 특별실 데이터
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
        "guide": "본관 중앙 계단을 통해 3층으로 올라간 뒤 오른쪽 두 번째 교실입니다.",
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

# 5. 사이드바 메뉴 (스크린샷 메뉴 구성 완벽 일치)
st.sidebar.title("📌 네비게이션")
menu = st.sidebar.radio(
    "메뉴를 선택하세요:",
    [
        "우리반 네비게이터",
        "교실 및 특별실 상세정보",
        "우리반 기본 시간표",
        "이동 수업 및 교실 공지",
        "학교 지도 및 길 안내",
    ],
)

# 6. 상단 타이틀
st.title("🏫 우리반 네비게이터")
st.info(
    f"🔊 **안내 상태**: 정상 작동 중 | 📢 **현재 등록된 변경 알림**: {len(st.session_state.announcements)}건"
)
st.markdown("---")

# =========================================================
# 1) 우리반 네비게이터 (메인 홈 화면)
# =========================================================
if menu == "우리반 네비게이터":
    st.subheader("📋 앱 소개 및 가이드 안내")

    with st.container(border=True):
        st.markdown(
            "### ❓ **어느 날 시간표가 갑자기 바뀌거나 특별실 위치가 바뀌어 당황하신 적이 있나요?**"
        )
        st.markdown(
            "### 👉 **이제 걱정할 필요 없습니다! '우리반 네비게이터'가 있기 때문입니다!**"
        )

    st.write("")
    st.write("### 📌 서비스 이용 가이드")
    st.success(
        "👈 **왼쪽 사이드바 메뉴**를 클릭하시면 원하시는 정보로 바로 이동합니다!"
    )

    col1, col2 = st.columns(2)
    with col1:
        with st.container(border=True):
            st.markdown("#### 📅 우리반 기본 시간표")
            st.write("요일별/교시별 정규 시간표와 기본 교실 위치 안내")
        with st.container(border=True):
            st.markdown("#### 📢 이동 수업 및 교실 공지")
            st.write("장소가 변경된 이동 수업 및 특별실 일정 확인 및 등록")

    with col2:
        with st.container(border=True):
            st.markdown("#### 🗺️ 학교 지도 및 길 안내")
            st.write("출발지부터 목적지 특별실까지의 최적 이동 경로 안내")
        with st.container(border=True):
            st.markdown("#### 🔍 교실 및 특별실 상세정보")
            st.write("특별실 주의사항 검색 사전 및 Gemini AI 길잡이 질문 기능")

# =========================================================
# 2) 교실 및 특별실 상세정보
# =========================================================
elif menu == "교실 및 특별실 상세정보":
    st.subheader("🔍 교실 및 특별실 상세정보 & AI")

    st.write("### 📌 특별실 상세 사전")
    selected_room = st.selectbox(
        "궁금한 특별실을 선택하세요:", list(ROOM_INFO.keys())
    )
    if selected_room:
        data = ROOM_INFO[selected_room]
        st.write(f"• **위치**: {data['location']}")
        st.write(f"• **상세 경로**: {data['guide']}")
        st.write(f"• **이용 수칙**: {data['note']}")

    st.markdown("---")
    st.write("### 🤖 AI 네비게이터에게 질문하기 (Gemini)")

    user_query = st.text_input(
        "질문을 입력하세요:",
        placeholder="예: 비 오는 날 체육관까지 우산 없이 가는 빠른 길이 있어?",
    )

    if st.button("AI에게 질문하기"):
        if user_query:
            if ai_client is not None:
                with st.spinner("AI가 답변을 생각 중입니다..."):
                    try:
                        prompt = f"당신은 학교 길 안내 도우미입니다. 학생의 질문에 친절히 답변하세요: {user_query}"
                        response = ai_client.models.generate_content(
                            model="gemini-2.5-flash-lite", contents=prompt
                        )
                        st.write("🤖 **AI 답변:**")
                        st.info(response.text)
                    except Exception as e:
                        st.error(f"오류가 발생했습니다: {e}")
            else:
                st.warning(
                    "🔑 GEMINI_API_KEY가 설정되지 않아 기본 응답으로 작동합니다."
                )
                st.info(
                    f"'{user_query}'에 대한 답변입니다.\n\n"
                    "왼쪽 메뉴의 **[학교 지도 및 길 안내]**에서 목적지를 선택하면 상세 안내를 확인하실 수 있습니다!"
                )
        else:
            st.warning("질문을 입력해 주세요.")

# =========================================================
# 3) 우리반 기본 시간표
# =========================================================
elif menu == "우리반 기본 시간표":
    st.subheader("📅 우리반 기본 시간표")

    weekdays = ["월요일", "화요일", "수요일", "목요일", "금요일"]
    today_num = datetime.datetime.now().weekday()
    default_day = weekdays[today_num] if today_num < 5 else "월요일"

    selected_day = st.selectbox(
        "요일을 선택하세요:",
        weekdays,
        index=weekdays.index(default_day),
    )

    data = TIMETABLE[selected_day]
    df = pd.DataFrame(data, columns=["교시", "과목", "기본 장소"])

    st.write(f"### 📖 {selected_day} 시간표")
    st.table(df)

# =========================================================
# 4) 이동 수업 및 교실 공지
# =========================================================
elif menu == "이동 수업 및 교실 공지":
    st.subheader("📢 이동 수업 및 교실 공지")

    with st.expander("➕ 새 이동 수업 공지 등록하기"):
        with st.form("add_notice_form", clear_on_submit=True):
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
                    st.success("공지가 성공적으로 등록되었습니다!")
                    st.rerun()
                else:
                    st.error("과목명과 변경 장소는 필수 입력 사항입니다.")

    st.write("### 🚨 등록된 장소 변경 공지")
    for item in reversed(st.session_state.announcements):
        st.warning(
            f"**[{item['date']}] {item['period']} - {item['subject']}**\n\n"
            f"📍 **위치 변경**: {item['original']} ➡️ **{item['changed']}**\n\n"
            f"📝 **비고**: {item['note']}"
        )

# =========================================================
# 5) 학교 지도 및 길 안내
# =========================================================
elif menu == "학교 지도 및 길 안내":
    st.subheader("🗺️ 학교 지도 및 길 안내")

    col1, col2 = st.columns(2)
    with col1:
        start_point = st.selectbox(
            "출발지 선택:", ["1반 교실 (본관 2층)", "운동장", "본관 입구"]
        )
    with col2:
        dest_point = st.selectbox("목적지 선택:", list(ROOM_INFO.keys()))

    if st.button("🚩 경로 안내 시작", type="primary"):
        info = ROOM_INFO[dest_point]
        st.success(f"🎯 **목적지**: {dest_point} ({info['location']})")
        st.write(f"🚶 **이동 경로**: {info['guide']}")
        st.info(f"💡 **주의 사항**: {info['note']}")
