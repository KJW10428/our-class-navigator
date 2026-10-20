import datetime
import os
import pandas as pd
import streamlit as st

# 1. 페이지 기본 설정
st.set_page_config(
    page_title="우리 반 네비게이터",
    page_icon="🏫",
    layout="wide",
    initial_sidebar_state="expanded",
)

# 2. Gemini AI 설정 (API 키 없어도 에러 없이 작동하도록 예외 처리)
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

# 3. Session State (화면 이동 및 공지 데이터 관리)
if "current_page" not in st.session_state:
    st.session_state.current_page = "🏠 메인 홈 (앱 소개)"

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

# 4. 데이터베이스 (시간표 및 교실 정보)
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

# 5. 사이드바 메뉴 구성
st.sidebar.title("📌 메뉴 이동")
pages = [
    "🏠 메인 홈 (앱 소개)",
    "📅 1. 우리 반 기본 시간표",
    "📢 2. 이동 수업 및 교실 공지",
    "🗺️ 3. 학교 지도 및 길 안내",
    "🔍 4. 교실/특별실 상세 정보 & AI",
]

# 사이드바 선택박스
selected_page = st.sidebar.radio(
    "원하는 메뉴를 선택하세요:",
    options=pages,
    index=pages.index(st.session_state.current_page),
)

# 사이드바 선택 시 session_state 업데이트
if selected_page != st.session_state.current_page:
    st.session_state.current_page = selected_page
    st.rerun()

# 6. 메인 상단 헤더 및 상태 안내 바 (사진 2 스타일 반영)
st.title("🚌 우리 반 네비게이터")
st.caption(
    "오늘의 시간표를 제공하고 이동 수업 위치를 안내해 주는 학교 생활 보조 앱"
)

st.info(
    f"🔊 **안내 상태**: 정상 작동 중 | 📢 **현재 등록된 교실 변경 알림**: {len(st.session_state.announcements)}건"
)

st.markdown("---")

# ---------------------------------------------------------
# PAGE 1: 메인 홈 (사진 1 보고서 스케치 + 사진 2 스타일 조합)
# ---------------------------------------------------------
if st.session_state.current_page == "🏠 메인 홈 (앱 소개)":
    st.subheader("📋 앱 소개 및 가이드 안내")

    # 상단 질문 상자 (사진 1 스케치 문구 반영)
    with st.container(border=True):
        st.markdown(
            "### ❓ **어느 날 시간표가 갑자기 바뀌거나 특별실 위치가 바뀌어 당황하신 적이 있나요?**"
        )
        st.markdown(
            "### 👉 **이제 걱정할 필요 없습니다! '우리 반 네비게이터'가 있기 때문입니다!**"
        )

    st.write("")
    st.write("### 👇 아래 버튼을 눌러 원하는 기능으로 이동하세요")

    # 기능 1 카드 (사진 2 스타일 카드 + 큰 버튼)
    with st.container(border=True):
        st.markdown("#### 1️⃣ 우리 반 기본 시간표")
        st.write(
            "요일별, 교시별 정규 시간표와 기본 교실 위치를 안내합니다."
        )
        if st.button(
            "👉 [기능 1] 기본 시간표 보러가기",
            use_container_width=True,
            type="primary",
        ):
            st.session_state.current_page = "📅 1. 우리 반 기본 시간표"
            st.rerun()

    # 기능 2 카드
    with st.container(border=True):
        st.markdown("#### 2️⃣ 이동 수업 및 교실 공지")
        st.write(
            "시간표 변경이나 특별실 이동 수업 정보를 빠르게 확인하고 등록합니다."
        )
        if st.button(
            "👉 [기능 2] 이동 수업 및 교실 공지 보러가기",
            use_container_width=True,
            type="primary",
        ):
            st.session_state.current_page = "📢 2. 이동 수업 및 교실 공지"
            st.rerun()

    # 기능 3 카드
    with st.container(border=True):
        st.markdown("#### 3️⃣ 학교 지도 및 길 안내")
        st.write(
            "우리 반 교실에서 헤매지 않고 목적지 특별실까지 가는 길을 찾습니다."
        )
        if st.button(
            "👉 [기능 3] 학교 지도 및 길 안내 이용하기",
            use_container_width=True,
            type="primary",
        ):
            st.session_state.current_page = "🗺️ 3. 학교 지도 및 길 안내"
            st.rerun()

    # 기능 4 카드
    with st.container(border=True):
        st.markdown("#### 4️⃣ 교실/특별실 상세 정보 & AI")
        st.write(
            "특별실 주의사항 검색 및 AI 길잡이에게 궁금한 점을 질문합니다."
        )
        if st.button(
            "👉 [기능 4] 상세 정보 및 AI 질문하러 가기",
            use_container_width=True,
            type="primary",
        ):
            st.session_state.current_page = (
                "🔍 4. 교실/특별실 상세 정보 & AI"
            )
            st.rerun()

# ---------------------------------------------------------
# PAGE 2: 우리 반 기본 시간표
# ---------------------------------------------------------
elif st.session_state.current_page == "📅 1. 우리 반 기본 시간표":
    st.subheader("📅 우리 반 기본 시간표")

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

    if st.button("🔙 메인 홈으로 돌아가기"):
        st.session_state.current_page = "🏠 메인 홈 (앱 소개)"
        st.rerun()

# ---------------------------------------------------------
# PAGE 3: 이동 수업 및 교실 공지
# ---------------------------------------------------------
elif st.session_state.current_page == "📢 2. 이동 수업 및 교실 공지":
    st.subheader("📢 이동 수업 및 장소 변경 공지")

    with st.expander("➕ 새 변경 공지 등록하기"):
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
                    "비고", placeholder="예: 실험복 착용"
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
                    st.error("과목명과 변경 장소는 필수 입력값입니다.")

    st.write("### 🚨 등록된 변동 사항 목록")
    for item in reversed(st.session_state.announcements):
        st.warning(
            f"**[{item['date']}] {item['period']} - {item['subject']}**\n\n"
            f"📍 **위치**: {item['original']} ➡️ **{item['changed']}**\n\n"
            f"📝 **비고**: {item['note']}"
        )

    if st.button("🔙 메인 홈으로 돌아가기"):
        st.session_state.current_page = "🏠 메인 홈 (앱 소개)"
        st.rerun()

# ---------------------------------------------------------
# PAGE 4: 학교 지도 및 길 안내
# ---------------------------------------------------------
elif st.session_state.current_page == "🗺️ 3. 학교 지도 및 길 안내":
    st.subheader("🗺️ 학교 지도 및 빠른 길 안내")

    col1, col2 = st.columns(2)
    with col1:
        start_point = st.selectbox(
            "출발지:", ["1반 교실 (본관 2층)", "운동장", "본관 입구"]
        )
    with col2:
        dest_point = st.selectbox("도착지 (목적지):", list(ROOM_INFO.keys()))

    if st.button("🚩 경로 확인하기", type="primary"):
        info = ROOM_INFO[dest_point]
        st.success(f"🎯 **목적지**: {dest_point} ({info['location']})")
        st.write(f"🚶 **이동 경로**: {info['guide']}")
        st.info(f"💡 **주의 사항**: {info['note']}")

    if st.button("🔙 메인 홈으로 돌아가기"):
        st.session_state.current_page = "🏠 메인 홈 (앱 소개)"
        st.rerun()

# ---------------------------------------------------------
# PAGE 5: 교실/특별실 상세 정보 & AI
# ---------------------------------------------------------
elif st.session_state.current_page == "🔍 4. 교실/특별실 상세 정보 & AI":
    st.subheader("🔍 교실/특별실 상세 정보 & AI 길잡이")

    st.write("### 📌 특별실 사전")
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
                with st.spinner("AI가 답변을 생성 중입니다..."):
                    try:
                        prompt = f"당신은 학교 길 안내 도우미입니다. 질문에 대해 친절하게 답변해 주세요: {user_query}"
                        response = ai_client.models.generate_content(
                            model="gemini-2.5-flash-lite", contents=prompt
                        )
                        st.write("🤖 **AI 답변:**")
                        st.info(response.text)
                    except Exception as e:
                        st.error(f"오류가 발생했습니다: {e}")
            else:
                st.warning(
                    "🔑 GEMINI_API_KEY가 설정되지 않아 기본 응답으로 대체됩니다."
                )
                st.info(
                    f"'{user_query}'에 대한 답변입니다.\n\n"
                    "상단의 **[🗺️ 학교 지도 및 길 안내]** 메뉴에서 목적지를 선택하면 상세 이동 경로를 바로 확인하실 수 있습니다!"
                )
        else:
            st.warning("질문을 입력해 주세요.")

    if st.button("🔙 메인 홈으로 돌아가기"):
        st.session_state.current_page = "🏠 메인 홈 (앱 소개)"
        st.rerun()
