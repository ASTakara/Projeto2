import streamlit as st
from streamlit_webrtc import webrtc_streamer, WebRtcMode, VideoProcessorBase
import av
import cv2
from pyzbar.pyzbar import decode
import streamlit.components.v1 as components


# ==========================================
# 1. ESCOPO GLOBAL: Processador de Vídeo Isolado
# ==========================================
class BarcodeProcessor(VideoProcessorBase):
    def __init__(self):
        # Usamos uma lista para garantir mutabilidade segura entre threads
        self.resultado_compartilhado = []

    def recv(self, frame: av.VideoFrame) -> av.VideoFrame:
        img = frame.to_ndarray(format="bgr24")

        # Faz a leitura do frame
        barcodes = decode(img)
        for barcode in barcodes:
            barcode_data = barcode.data.decode("utf-8")

            # Se ainda não detectamos nada neste ciclo, armazena
            if not self.resultado_compartilhado:
                self.resultado_compartilhado.append(barcode_data)

            # Desenha o feedback visual na tela do usuário
            (x, y, w, h) = barcode.rect
            cv2.rectangle(img, (x, y), (x + w, y + h), (0, 255, 0), 2)
            cv2.putText(img, barcode_data, (x, y - 10),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)

        return av.VideoFrame.from_ndarray(img, format="bgr24")


# ==========================================
# 2. CONFIGURAÇÃO DA INTERFACE
# ==========================================
st.title("Mobile Barcode Scanner Pro")

if "ultimo_resultado" not in st.session_state:
    st.session_state["ultimo_resultado"] = None

# FLUXO A: Código detectado com sucesso -> Processamento
if st.session_state["ultimo_resultado"]:
    st.success(f"✅ Lido com sucesso: {st.session_state['ultimo_resultado']}")
    st.json({"status": "Processado", "conteudo": st.session_state["ultimo_resultado"]})

    if st.button("🔄 Escanear Próximo Código"):
        st.session_state["ultimo_resultado"] = None
        st.rerun()

# FLUXO B: Câmera Ativa para Escaneamento
else:
    # Componente WebRTC montado de forma estática
    ctx = webrtc_streamer(
        key="scanner-barcode-v4-stable",
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

    # Monitoramento Passivo Sem Interrupções de Ciclo (Sem st.rerun forçado no Python)
    if ctx.state.playing and ctx.video_processor:
        st.info("📷 Câmera ativa. Posicione o código de barras na marcação verde.")

        # Verifica se a lista interna da thread de vídeo recebeu o código lido
        if ctx.video_processor.resultado_compartilhado:
            dado_detectado = ctx.video_processor.resultado_compartilhado[0]
            st.session_state["ultimo_resultado"] = dado_detectado

            # TRUQUE DE MESTRE: Injetamos um script JS para recarregar a interface
            # pelo lado do cliente. Isso evita estourar o loop assíncrono do backend.
            components.html(
                """
                <script>
                    window.parent.document.dispatchEvent(new Event('DOMContentLoaded'));
                    window.parent.location.reload();
                </script>
                """,
                height=0,
                width=0
            )
    else:
        st.warning("Clique no botão 'Start' acima para ligar a câmera do dispositivo.")