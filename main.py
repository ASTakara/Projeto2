import streamlit as st
from streamlit_webrtc import webrtc_streamer, WebRtcMode, VideoProcessorBase
import av
import cv2
from pyzbar.pyzbar import decode


# ==========================================
# 1. ESCOPO GLOBAL: Definição estável do Processador
# ==========================================
class BarcodeProcessor(VideoProcessorBase):
    def __init__(self):
        self.resultado_temporario = None

    def recv(self, frame: av.VideoFrame) -> av.VideoFrame:
        img = frame.to_ndarray(format="bgr24")

        # Analisa o frame atrás de códigos de barras
        barcodes = decode(img)
        for barcode in barcodes:
            barcode_data = barcode.data.decode("utf-8")

            # Guarda o resultado no próprio objeto da instância (no backend)
            self.resultado_temporario = barcode_data

            # Feedback visual (Retângulo verde e texto)
            (x, y, w, h) = barcode.rect
            cv2.rectangle(img, (x, y), (x + w, y + h), (0, 255, 0), 2)
            cv2.putText(img, barcode_data, (x, y - 10),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)

        return av.VideoFrame.from_ndarray(img, format="bgr24")


# ==========================================
# 2. INTERFACE E LÓGICA DO APP
# ==========================================
st.title("Mobile Barcode Scanner")

# Inicialização limpa do Session State
if "ultimo_resultado" not in st.session_state:
    st.session_state["ultimo_resultado"] = None

# FLUXO A: Código detectado com sucesso -> Pausa e exibe resultado
if st.session_state["ultimo_resultado"]:
    st.success(f"✅ Lido com sucesso: {st.session_state['ultimo_resultado']}")

    if st.button("🔄 Escanear Próximo Código"):
        st.session_state["ultimo_resultado"] = None
        st.rerun()

# FLUXO B: Scanner Ativo
else:
    # Inicializa o componente usando a factory global (100% imune a erros de JSON)
    ctx = webrtc_streamer(
        key="barcode-scanner-factory-stable",
        mode=WebRtcMode.SENDRECV,
        video_processor_factory=BarcodeProcessor,
        media_stream_constraints={
            "video": {"facingMode": "environment"},  # Força a câmera traseira no celular
            "audio": False
        },
        async_processing=True,
        rtc_configuration={
            "iceServers": [{"urls": ["stun:stun.l.google.com:19302"]}]  # Servidor STUN público do Google
        }
    )

    # Verificação passiva (Executada a cada ciclo de renderização do Streamlit)
    if ctx.state.playing and ctx.video_processor:
        # Captura o dado assim que a thread paralela do WebRTC preencher a variável
        detectado = getattr(ctx.video_processor, "resultado_temporario", None)

        if detectado:
            # Salva no estado global do app
            st.session_state["ultimo_resultado"] = detectado
            # Reseta a variável do processador para evitar re-triggers acidentais
            ctx.video_processor.resultado_temporario = None
            # Recarrega o app para mudar instantaneamente para o FLUXO A
            st.rerun()
        else:
            st.info("📷 Scanner ativo. Aproxime o código de barras da câmera...")
    else:
        st.warning("Clique no botão 'Start' para iniciar a câmera.")