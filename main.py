import streamlit as st
from streamlit_webrtc import webrtc_streamer, WebRtcMode, VideoProcessorBase
import av
import cv2


# ==========================================
# 1. ESCOPO GLOBAL: Processador Utilizando OpenCV Nativo
# ==========================================
class BarcodeProcessor(VideoProcessorBase):
    def __init__(self):
        self.codigo_detectado = None
        # Inicializa o detector nativo do OpenCV (Não quebra o asyncio)
        self.detector = cv2.barcode.BarcodeDetector()

    def recv(self, frame: av.VideoFrame) -> av.VideoFrame:
        img = frame.to_ndarray(format="bgr24")

        # Converte para tons de cinza (otimiza a leitura nativa)
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

        # Executa a detecção nativa do OpenCV
        retval, decoded_info, decoded_type, points = self.detector.detectAndDecode(gray)

        if retval:
            for i, info in enumerate(decoded_info):
                if info:  # Se a string contiver dados lidos
                    self.codigo_detectado = info

                    # Desenha o feedback visual se houver pontos de marcação
                    if points is not None and len(points) > 0:
                        pts = points[i].astype(int)
                        for j in range(len(pts)):
                            pt1 = tuple(pts[j])
                            pt2 = tuple(pts[(j + 1) % len(pts)])
                            cv2.line(img, pt1, pt2, (0, 255, 0), 3)
                    break

        return av.VideoFrame.from_ndarray(img, format="bgr24")


# ==========================================
# 2. INTERFACE E CONTROLE DE ESTADO
# ==========================================
st.set_page_config(page_title="Scanner de Código de Barras", layout="centered")
st.title("📷 Scanner de Código de Barras")

if "resultado_final" not in st.session_state:
    st.session_state["resultado_final"] = None

# TELA A: Sucesso (Código capturado)
if st.session_state["resultado_final"]:
    st.success("🎉 Código detectado com sucesso!")
    st.info(f"**Conteúdo:** {st.session_state['resultado_final']}")

    if st.button("🔄 Escanear Próximo Código", use_container_width=True):
        st.session_state["resultado_final"] = None
        st.rerun()

# TELA B: Câmera Ativa
else:
    st.write("Aproxime o código de barras da câmera.")

    ctx = webrtc_streamer(
        key="barcode-scanner-native-opencv-v1",
        mode=WebRtcMode.SENDRECV,
        video_processor_factory=BarcodeProcessor,
        async_processing=True,
        media_stream_constraints={
            "video": {
                "facingMode": "environment",
                "width": {"ideal": 1280},
                "height": {"ideal": 720}
            },
            "audio": False
        },
        rtc_configuration={
            "iceServers": [{"urls": ["stun:stun.l.google.com:19302"]}]
        }
    )

    if ctx.state.playing and ctx.video_processor:
        dado_temporario = getattr(ctx.video_processor, "codigo_detectado", None)

        if dado_temporario:
            st.success("🎯 Leitura Efetuada!")

            # Botão nativo para o usuário avançar de fase sem quebrar o ecossistema do app
            if st.button(f"📥 Processar Código: {dado_temporario}", type="primary", use_container_width=True):
                st.session_state["resultado_final"] = dado_temporario
                ctx.video_processor.codigo_detectado = None
                st.rerun()
        else:
            st.info("Aguardando detecção... Certifique-se de alinhar o código de barras.")
    else:
        st.warning("Clique no botão **Start** acima para liberar o acesso à câmera.")