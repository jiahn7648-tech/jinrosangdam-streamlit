import streamlit as st
import os
from google import genai
from google.genai import errors

# ==============================================================================
# 0. 코딩 비서 역할을 위한 시스템 지침 설정 (디버깅 기능 강화!)
# ==============================================================================
SYSTEM_INSTRUCTION = (
    "당신은 구글 코랩(Colab) 환경에 최적화된 전문 코딩 비서입니다. "
    "사용자는 파이썬 초보자부터 숙련자까지 다양합니다. "
    "사용자의 질문에 대해 명확하고 간결하며 실행 가능한 파이썬 코드를 제공해야 합니다. "
    "사용자가 파이썬 코드를 제시하면, 해당 코드의 오류(SyntaxError, NameError, TypeError 등)를 진단하고, 오류가 난 이유와 함께 정확하고 친절한 해결책을 제시하여 코드를 고쳐주세요. 디버깅이 주요 업무 중 하나입니다. " # <--- 디버깅 지침 강화
    "코드 설명은 주석과 함께 제공하며, 모든 코드는 구글 코랩 환경에서 바로 실행 가능하도록 작성해야 합니다. "
    "사용자가 요청하지 않는 한, 불필요한 서론이나 결론 없이 핵심적인 코드와 설명을 제공하세요."
)

# 1. API 키 설정 및 클라이언트 초기화
# Streamlit Cloud에 배포할 때는 'GEMINI_API_KEY'라는 이름의 환경 변수(Secrets)를 사용합니다.
api_key = os.getenv("GEMINI_API_KEY")

if not api_key:
    # 로컬 환경에서 키가 없거나 Streamlit Cloud Secrets에 키가 없는 경우 오류 메시지 표시
    st.error("❌ 오류: 'GEMINI_API_KEY' 환경 변수 또는 Streamlit Secret이 설정되지 않았습니다.")
    st.error("👉 사이드바의 '실행 방법' 섹션을 참고하여 API 키를 설정해주세요.")
    st.stop()

# Gemini 클라이언트 초기화
try:
    client = genai.Client(api_key=api_key)
except Exception as e:
    st.error(f"⚠️ Gemini 클라이언트 초기화 실패: {e}")
    st.stop()

# 사용할 모델 설정
MODEL_NAME = "gemini-2.5-flash"

# Streamlit UI 설정 (제목 변경)
st.set_page_config(page_title="코랩 코딩 비서 챗봇", layout="centered")
st.title("💻 구글 코랩 코딩 비서: 제미나이")
st.caption("파이썬 코드 작성, 설명, **오류 수정**을 도와주는 전문 AI 비서입니다.")
st.divider()

# 2. 채팅 기록 초기화
if "messages" not in st.session_state:
    # 환영 메시지 변경
    st.session_state.messages = [
        {"role": "assistant", "content": "안녕하세요! 저는 코랩 환경에 최적화된 코딩 비서 제미나이입니다. 어떤 파이썬 코드가 필요하거나, **오류가 난 코드를 보여주시면 바로 고쳐드릴게요!**"}
    ]

# 3. 채팅 기록 표시
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# 4. 사용자 입력 처리
if prompt := st.chat_input("파이썬 코드를 요청하거나 오류를 물어보세요..."):
    # 4-1. 사용자 메시지 기록 및 화면 표시
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    # 4-2. Gemini API 호출을 위한 대화 기록 준비
    history = []
    for message in st.session_state.messages:
        role_map = {"user": "user", "assistant": "model"}
        if message["role"] in role_map:
            history.append(
                {"role": role_map[message["role"]], "parts": [{"text": message["content"]}]}
            )

    # 4-3. 챗봇 응답 스트리밍
    with st.chat_message("assistant"):
        message_placeholder = st.empty()
        full_response = ""
        
        try:
            # generate_content_stream 호출 시 config에 시스템 지침을 추가!
            response_stream = client.models.generate_content_stream(
                model=MODEL_NAME,
                contents=history,
                config={"system_instruction": SYSTEM_INSTRUCTION}  # <--- 시스템 지침 사용
            )

            for chunk in response_stream:
                if chunk.text:
                    full_response += chunk.text
                    message_placeholder.markdown(full_response + "▌") 
            
            message_placeholder.markdown(full_response)
            
        except errors.APIError as e:
            error_message = f"API 호출 중 오류가 발생했습니다: {e}"
            st.error(error_message)
            full_response = error_message
        except Exception as e:
            error_message = f"예상치 못한 오류가 발생했습니다: {e}"
            st.error(error_message)
            full_response = error_message

    # 4-4. 최종 응답을 채팅 기록에 저장
    st.session_state.messages.append({"role": "assistant", "content": full_response})

# 5. 실행 및 배포 방법 안내 (사이드바)
st.sidebar.header("실행 및 배포 방법")
st.sidebar.markdown(
    """
### 1. 라이브러리 설치
```bash
pip install streamlit google-genai
```

### 2. API 키 설정 (중요!)
Streamlit Cloud의 'Secrets' 설정에 **`GEMINI_API_KEY`**와 여러분의 API 키를 입력해주세요.

### 3. 앱 실행
```bash
streamlit run app.py
```
"""
)
