import streamlit as st
from streamlit_webrtc import webrtc_streamer, WebRtcMode, VideoProcessorBase
import av
import cv2
from pyzbar.pyzbar import decode
import time


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

            # ATENÇÃO: Guarda o resultado
            self.resultado_temporario = barcode_data

            # Feedback visual na tela da câmera
            (x, y, w, h) = barcode.rect
            cv2.rectangle(img, (x, y), (x + w, y + h), (0, 255, 0), 2)
            cv2.putText(img, barcode_data, (x, y - 10),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)

        return av.VideoFrame.from_ndarray(img, format="bgr24")


# ==========================================
# 2. INTERFACE E LÓGICA DO APP
# ==========================================
st.title("Mobile Barcode Scanner")

# Inicialização do Session State
if "ultimo_resultado" not in st.session_state:
    st.session_state["ultimo_resultado"] = None

# FLUXO A: Código detectado com sucesso -> Exibe resultado fora da câmera
if st.session_state["ultimo_resultado"]:
    st.success(f"✅ Lido com sucesso: {st.session_state['ultimo_resultado']}")

    # Aqui você pode colocar sua lógica de banco de dados, API, etc.
    st.json({"status": "Processado", "conteudo": st.session_state["ultimo_resultado"]})

    if st.button("🔄 Escanear Próximo Código"):
        st.session_state["ultimo_resultado"] = None
        st.rerun()

# FLUXO B: Scanner Ativo
else:
    ctx = webrtc_streamer(
        key="barcode-scanner-final-v3",
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

    # Criamos um container de texto dinâmico para feedback do usuário
    status_placeholder = st.empty()

    # Se a câmera estiver ligada, criamos uma escuta ultra-leve baseada em fragmento/loop controlado
    if ctx.state.playing and ctx.video_processor:
        status_placeholder.info("📷 Câmera ativa. Aproxime o código de barras...")

        # Fazemos pequenas verificações repetidas. Como não há processamento pesado aqui dentro
        # (o processamento é feito na thread do WebRTC), isso não vai travar o Python 3.14.
        for _ in range(30):  # Tenta checar por alguns segundos nesta renderização
            detectado = getattr(ctx.video_processor, "resultado_temporario", None)

            if detectado:
                # Se achou, salva no estado global do Streamlit e força o encerramento do fluxo b
                st.session_state["ultimo_resultado"] = detectado
                ctx.video_processor.resultado_temporario = None
                st.rerun()
                break

            time.sleep(0.1)  # Aguarda 100ms antes da próxima checagem passiva

        # Força o Streamlit a dar um "refresh" na página para continuar escutando a thread do vídeo
        st.rerun()
    else:
        status_placeholder.warning("Clique no botão 'Start' para iniciar a câmera.")