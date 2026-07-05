import streamlit as st
from PIL import Image
import io
import time

st.set_page_config(page_title="포토부스", page_icon="📸", layout="centered")

# =========================================================
# 프레임 설정 (폴더 없이 같은 위치의 파일 사용)
# 각 프레임의 사진 넣는 칸(box) 좌표를 (left, top, right, bottom)으로 지정
# ※ 실제 프레임 이미지 크기에 맞춰 좌표값을 조정해야 합니다!
# =========================================================
FRAMES = {
    "하트 프레임": {
        "path": "frame1.png",
        "size": (712, 1080),  # 프레임 원본 크기
        "boxes": [
            (375, 88, 690, 455),    # 우상단 큰 칸
            (38, 250, 340, 640),    # 좌측 칸
            (375, 470, 690, 855),   # 우측 칸
            (38, 655, 340, 1040),   # 좌하단 칸
        ],
    },
    "필름 프레임": {
        "path": "frame2.png",
        "size": (736, 1533),
        "boxes": [
            (150, 90, 585, 400),
            (150, 435, 585, 745),
            (150, 785, 585, 1095),
            (150, 1130, 585, 1440),
        ],
    },
    "블랙 프레임": {
        "path": "frame3.png",
        "size": (736, 981),
        "boxes": [
            (240, 55, 515, 250),
            (240, 275, 515, 465),
            (240, 490, 515, 680),
            (240, 705, 515, 895),
        ],
    },
}

# =========================================================
# session_state 초기화
# =========================================================
if "step" not in st.session_state:
    st.session_state.step = "start"     # start -> capture -> result
if "frame_name" not in st.session_state:
    st.session_state.frame_name = None
if "photos" not in st.session_state:
    st.session_state.photos = []         # 촬영한 사진(PIL Image) 리스트
if "shot_index" not in st.session_state:
    st.session_state.shot_index = 0      # 몇 번째 촬영인지


def reset_all():
    """모든 상태를 초기화하고 시작화면으로"""
    st.session_state.step = "start"
    st.session_state.frame_name = None
    st.session_state.photos = []
    st.session_state.shot_index = 0


# =========================================================
# 이미지 크롭 함수 (칸 크기에 맞춰 중앙 기준으로 잘라줌)
# =========================================================
def crop_to_fit(img, target_w, target_h):
    """이미지를 target 비율에 맞게 중앙 크롭 후 리사이즈"""
    src_w, src_h = img.size
    target_ratio = target_w / target_h
    src_ratio = src_w / src_h

    if src_ratio > target_ratio:
        # 원본이 더 넓음 -> 좌우를 자름
        new_w = int(src_h * target_ratio)
        left = (src_w - new_w) // 2
        img = img.crop((left, 0, left + new_w, src_h))
    else:
        # 원본이 더 높음 -> 위아래를 자름
        new_h = int(src_w / target_ratio)
        top = (src_h - new_h) // 2
        img = img.crop((0, top, src_w, top + new_h))

    return img.resize((target_w, target_h))


def make_result(frame_name, photos):
    """프레임 위에 4장의 사진을 합성"""
    conf = FRAMES[frame_name]
    frame = Image.open(conf["path"]).convert("RGBA")
    frame = frame.resize(conf["size"])

    result = Image.new("RGBA", conf["size"], (255, 255, 255, 0))

    for i, box in enumerate(conf["boxes"]):
        if i < len(photos):
            left, top, right, bottom = box
            w, h = right - left, bottom - top
            photo = photos[i].convert("RGBA")
            photo = crop_to_fit(photo, w, h)
            result.paste(photo, (left, top))

    # 프레임을 사진 위에 덮기
    result = Image.alpha_composite(result, frame)
    return result.convert("RGB")


# =========================================================
# 1. 시작화면
# =========================================================
if st.session_state.step == "start":
    st.title("📸 포토부스")
    st.write("원하는 프레임을 골라 시작해보세요!")

    cols = st.columns(3)
    frame_names = list(FRAMES.keys())
    for col, name in zip(cols, frame_names):
        with col:
            try:
                st.image(FRAMES[name]["path"], caption=name, use_container_width=True)
            except Exception:
                st.write(f"[{name} 이미지]")

    selected = st.radio("프레임 선택", frame_names, horizontal=True)

    if st.button("🎬 시작하기", use_container_width=True):
        st.session_state.frame_name = selected
        st.session_state.step = "capture"
        st.session_state.photos = []
        st.session_state.shot_index = 0
        st.rerun()

# =========================================================
# 2. 촬영화면
# =========================================================
elif st.session_state.step == "capture":
    idx = st.session_state.shot_index
    st.title(f"📷 촬영 중... ({idx + 1} / 4)")
    st.write("아래 카메라 버튼을 눌러 촬영하세요!")

    # 카운트다운 (선택적으로 실행)
    if st.button("⏱️ 카운트다운 시작 (3-2-1)"):
        placeholder = st.empty()
        for n in [3, 2, 1]:
            placeholder.markdown(f"<h1 style='text-align:center;'>{n}</h1>",
                                 unsafe_allow_html=True)
            time.sleep(1)
        placeholder.markdown("<h1 style='text-align:center;'>📸 찰칵!</h1>",
                             unsafe_allow_html=True)
        time.sleep(0.5)
        placeholder.empty()

    # camera_input은 브라우저 카메라를 사용 (미리보기 자동 제공)
    photo = st.camera_input(f"{idx + 1}번째 사진 촬영")

    if photo is not None:
        img = Image.open(photo)
        # 거울처럼 좌우반전
        img = img.transpose(Image.FLIP_LEFT_RIGHT)

        if st.button("✅ 이 사진 사용하기", use_container_width=True):
            st.session_state.photos.append(img)
            st.session_state.shot_index += 1

            if st.session_state.shot_index >= 4:
                st.session_state.step = "result"
            st.rerun()

    st.progress(idx / 4)

    if st.button("🏠 처음으로"):
        reset_all()
        st.rerun()

# =========================================================
# 3. 결과화면
# =========================================================
elif st.session_state.step == "result":
    st.title("🎉 완성!")

    result_img = make_result(st.session_state.frame_name,
                             st.session_state.photos)
    st.image(result_img, caption="완성된 포토부스 사진", use_container_width=True)

    # PNG로 변환하여 다운로드
    buf = io.BytesIO()
    result_img.save(buf, format="PNG")
    buf.seek(0)

    col1, col2 = st.columns(2)
    with col1:
        st.download_button(
            "💾 저장하기 (PNG)",
            data=buf,
            file_name="photobooth.png",
            mime="image/png",
            use_container_width=True,
        )
    with col2:
        if st.button("🔄 다시하기", use_container_width=True):
            reset_all()
            st.rerun()
