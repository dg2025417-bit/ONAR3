import streamlit as st
from PIL import Image
import io
import time

st.set_page_config(page_title="포토부스", page_icon="📸", layout="centered")

# =========================================================
# 프레임 설정
# =========================================================
FRAMES = {
    "하트 프레임": {
        "path": "frame1.png",
        "size": (712, 1080),
        "boxes": [
            (375, 88, 690, 455),
            (38, 250, 340, 640),
            (375, 470, 690, 855),
            (38, 655, 340, 1040),
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
    st.session_state.step = "start"
if "frame_name" not in st.session_state:
    st.session_state.frame_name = None
if "photos" not in st.session_state:
    st.session_state.photos = []
if "shot_index" not in st.session_state:
    st.session_state.shot_index = 0


def reset_all():
    st.session_state.step = "start"
    st.session_state.frame_name = None
    st.session_state.photos = []
    st.session_state.shot_index = 0


# =========================================================
# 이미지 크롭 함수
# =========================================================
def crop_to_fit(img, target_w, target_h):
    src_w, src_h = img.size
    target_ratio = target_w / target_h
    src_ratio = src_w / src_h

    if src_ratio > target_ratio:
        new_w = int(src_h * target_ratio)
        left = (src_w - new_w) // 2
        img = img.crop((left, 0, left + new_w, src_h))
    else:
        new_h = int(src_w / target_ratio)
        top = (src_h - new_h) // 2
        img = img.crop((0, top, src_w, top + new_h))

    return img.resize((target_w, target_h))


def make_result(frame_name, photos):
    conf = FRAMES[frame_name]

    try:
        frame = Image.open(conf["path"]).convert("RGBA")
    except FileNotFoundError:
        st.error(f"⚠️ '{conf['path']}' 파일을 찾을 수 없어요! "
                 f"GitHub 저장소에 이미지를 올렸는지, 이름이 정확한지 확인하세요.")
        st.stop()

    frame = frame.resize(conf["size"])
    result = Image.new("RGBA", conf["size"], (255, 255, 255, 0))

    for i, box in enumerate(conf["boxes"]):
        if i < len(photos):
            left, top, right, bottom = box
            w, h = right - left, bottom - top
            photo = photos[i].convert("RGBA")
            photo = crop_to_fit(photo, w, h)
            result.paste(photo, (left, top))

    result = Image.alpha_composite(result, frame)
    return result.convert("RGB")


# =========================================================
# 1. 시작화면
# =========================================================
if st.session_state.step == "start":
    st.title("📸 포토부스")
    st.write("원하는 프레임을 골라 시작해보세요!")

    frame_names = list(FRAMES.keys())
    cols = st.columns(len(frame_names))

    for col, name in zip(cols, frame_names):
        with col:
            path = FRAMES[name]["path"]
            try:
                st.image(path, caption=name, use_container_width=True)
            except FileNotFoundError:
                st.warning(f"⚠️ {path} 없음")
                st.write(f"[{name}]")

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

    photo = st.camera_input(f"{idx + 1}번째 사진 촬영")

    if photo is not None:
        # ★★★ 핵심 수정 ★★★
        # 임시 데이터를 확실히 메모리로 복사해서 사라지지 않게 함
        img = Image.open(photo).convert("RGB")   # RGB로 즉시 읽기
        img = img.transpose(Image.FLIP_LEFT_RIGHT)  # 거울 반전
        img = img.copy()   # 완전한 복사본 만들기

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

    # 안전 확인: 사진이 4장 모두 있는지 체크
    if len(st.session_state.photos) < 4:
        st.warning(f"사진이 {len(st.session_state.photos)}장만 있어요. 다시 촬영해주세요.")
        if st.button("🔄 다시하기"):
            reset_all()
            st.rerun()
        st.stop()

    result_img = make_result(st.session_state.frame_name,
                             st.session_state.photos)
    st.image(result_img, caption="완성된 포토부스 사진", use_container_width=True)

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
