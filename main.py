import streamlit as st
from streamlit_webrtc import webrtc_streamer, WebRtcMode, VideoProcessorBase
import av
import cv2
from pyzbar.pyzbar import decode
from streamlit_autorefresh import st_autorefresh


# ==========================================
# 1. ESCOPO GLOBAL: Processador de Vídeo Limpo
# ==========================================
class BarcodeProcessor(VideoProcessorBase):
    def __init__(self):
        self.resultado = None

    def recv(self, frame: av.VideoFrame) -> av.VideoFrame:
        img = frame.to_ndarray(format="bgr24")

        # Analisa o frame sem travas na thread de vídeo
        barcodes = decode(img)
        for barcode in barcodes:
            barcode_data = barcode.data.decode("utf-8")
            self.resultado = barcode_data

            # Desenha o feedback visual (retângulo verde e texto)
            (x, y, w, h) = barcode.rect
            cv2.rectangle(img, (x, y), (x + w, y + h), (0, 255, 0), 2)
            cv2.putText(img, barcode_data, (x, y - 10),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)

        return av.VideoFrame.from_ndarray(img, format="bgr24")


# ==========================================
# 2. CONFIGURAÇÃO DA INTERFACE
# ==========================================
st.title("Mobile Barcode Scanner")

if "ultimo_resultado" not in st.session_state:
    st.session_state["ultimo_resultado"] = None

# FLUXO A: Código detectado com sucesso
if st.session_state["ultimo_resultado"]:
    st.success(f"✅ Lido com sucesso: {st.session_state['ultimo_resultado']}")
    st.json({"status": "Processado", "conteudo": st.session_state["ultimo_resultado"]})

    if st.button("🔄 Escanear Próximo Código"):
        st.session_state["ultimo_resultado"] = None
        st.rerun()

# FLUXO B: Câmera Ativa para Escaneamento
else:
    # O componente WebRTC fica completamente estático aqui
    ctx = webrtc_streamer(
        key="barcode-scanner-autorefresh-v1",
        mode=WebRtcMode.SENDRECV,
        video_processor_factory=BarcodeProcessor,
        media_stream_constraints={
            "video": {"facingMode": "environment"},
            "audio": False
        },
        async_processing=True,
        rtc_configuration={
            "iceServers": [{"urls": ["stun:stun.l.google.com:19302"]}]
        }
    )

    if ctx.state.playing and ctx.video_processor:
        st.info("📷 Câmera ativa. Aproxime o código de barras...")

        # O SEGREDO: Configura o Streamlit para re-renderizar a página a cada 1000ms (1 segundo)
        # Isso substitui os loops pesados e os scripts de clique do JS que travavam o app.
        st_autorefresh(interval=1000, limit=1000, key="scanner_refresh")

        # Checa se o processador capturou o código
        detectado = getattr(ctx.video_processor, "resultado", None)

        if detectado:
            st.session_state["ultimo_resultado"] = detectado
            ctx.video_processor.resultado = None
            st.rerun()
    else:
        st.warning("Clique no botão 'Start' acima para ligar a câmera.")