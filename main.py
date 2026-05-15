import streamlit as st
from streamlit_webrtc import webrtc_streamer, WebRtcMode, VideoProcessorBase
import av
import cv2
from pyzbar.pyzbar import decode


# ==========================================
# 1. ESCOPO GLOBAL: Processador Estável
# ==========================================
class BarcodeProcessor(VideoProcessorBase):
    def __init__(self):
        self.resultado = None

    def recv(self, frame: av.VideoFrame) -> av.VideoFrame:
        img = frame.to_ndarray(format="bgr24")

        # Só processa se ainda não capturou nada
        if self.resultado is None:
            barcodes = decode(img)
            for barcode in barcodes:
                barcode_data = barcode.data.decode("utf-8")
                self.resultado = barcode_data

                # Feedback visual na tela da câmera
                (x, y, w, h) = barcode.rect
                cv2.rectangle(img, (x, y), (x + w, y + h), (0, 255, 0), 2)
                cv2.putText(img, barcode_data, (x, y - 10),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)

        return av.VideoFrame.from_ndarray(img, format="bgr24")


# ==========================================
# 2. CONFIGURAÇÃO DA INTERFACE PRINCIPAL
# ==========================================
st.title("Mobile Barcode Scanner")

if "ultimo_resultado" not in st.session_state:
    st.session_state["ultimo_resultado"] = None

# FLUXO A: Código capturado com sucesso
if st.session_state["ultimo_resultado"]:
    st.success(f"✅ Código Lido: {st.session_state['ultimo_resultado']}")
    st.json({"status": "Processado", "conteudo": st.session_state["ultimo_resultado"]})

    if st.button("🔄 Escanear Próximo Código"):
        st.session_state["ultimo_resultado"] = None
        st.rerun()

# FLUXO B: Janela do Scanner Ativo
else:
    # Cria o componente WebRTC estático
    ctx = webrtc_streamer(
        key="barcode-scanner-async-safe-v5",
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

    # Monitoramento seguro e não obstrutivo
    if ctx.state.playing and ctx.video_processor:
        st.info("📷 Câmera ativa. Aproxime o código de barras...")

        # Pega o dado se ele existir no buffer do processador
        detectado = getattr(ctx.video_processor, "resultado", None)

        if detectado:
            st.warning(f"🔍 Código identificado: {detectado}")

            # Criamos um botão explícito de envio.
            # Ao clicar nele, o Streamlit assume o controle do fluxo síncrono de forma segura.
            if st.button("📥 Confirmar e Processar Código"):
                st.session_state["ultimo_resultado"] = detectado
                ctx.video_processor.resultado = None
                st.rerun()
    else:
        st.warning("Clique no botão 'Start' acima para ligar a câmera do dispositivo.")