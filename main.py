import streamlit as st
from streamlit_webrtc import webrtc_streamer, WebRtcMode, VideoProcessorBase
import av
import cv2
import zxingcpp


# ==========================================
# 1. ESCOPO GLOBAL: Processador com ZXing e Câmera Frontal
# ==========================================
class BarcodeProcessor(VideoProcessorBase):
    def __init__(self):
        self.codigo_detectado = None

    def recv(self, frame: av.VideoFrame) -> av.VideoFrame:
        img = frame.to_ndarray(format="bgr24")

        # O ZXing faz a leitura direto no frame de vídeo
        resultados = zxingcpp.read_barcodes(img)

        if resultados:
            for codigo in resultados:
                texto_lido = codigo.text.strip()
                if texto_lido:
                    self.codigo_detectado = texto_lido

                    # Desenha um feedback visual rápido na tela para o usuário saber que leu
                    cv2.putText(img, "CODIGO LIDO!", (50, 50),
                                cv2.FONT_HERSHEY_SIMPLEX, 1.0, (0, 255, 0), 3)
                    break  # Foca no primeiro encontrado

        return av.VideoFrame.from_ndarray(img, format="bgr24")


# ==========================================
# 2. INTERFACE E CONTROLE DE ESTADO
# ==========================================
st.set_page_config(page_title="Scanner de Código de Barras", layout="centered")
st.title("📷 Scanner de Código de Barras (Câmera Frontal)")

if "resultado_final" not in st.session_state:
    st.session_state["resultado_final"] = None

# TELA A: Sucesso (Código capturado)
if st.session_state["resultado_final"]:
    st.success("🎉 Código detectado com sucesso!")
    st.code(st.session_state["resultado_final"], language="text")

    if st.button("🔄 Escanear Próximo Código", use_container_width=True):
        st.session_state["resultado_final"] = None
        st.rerun()

# TELA B: Câmera Ativa em Tempo Real
else:
    st.write("Aproxime o código de barras da câmera frontal (selfie).")

    ctx = webrtc_streamer(
        key="barcode-scanner-frontal-v1",
        mode=WebRtcMode.SENDRECV,
        video_processor_factory=BarcodeProcessor,
        async_processing=True,
        media_stream_constraints={
            "video": {
                "facingMode": "user",  # <--- ALTERADO PARA FORÇAR A CÂMERA FRONTAL (SELFIE)
                "width": {"ideal": 1280},
                "height": {"ideal": 720}
            },
            "audio": False
        },
        rtc_configuration={
            "iceServers": [{"urls": ["stun:stun.l.google.com:19302"]}]
        }
    )

    # Monitora e exibe o botão de confirmação assim que o ZXing lê o código
    if ctx.state.playing and ctx.video_processor:
        dado_temporario = getattr(ctx.video_processor, "codigo_detectado", None)

        if dado_temporario:
            st.success("🎯 Código identificado no vídeo!")

            # Botão destacado para enviar o dado pro Streamlit sem quebrar o asyncio
            if st.button(f"📥 Confirmar Código: {dado_temporario}", type="primary", use_container_width=True):
                st.session_state["resultado_final"] = dado_temporario
                ctx.video_processor.codigo_detectado = None
                st.rerun()
        else:
            st.info("Aguardando leitura... Posicione o código em frente à câmera.")
    else:
        st.warning("Clique no botão **Start** acima para ligar a câmera frontal.")