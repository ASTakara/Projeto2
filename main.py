import streamlit as st
from streamlit_webrtc import webrtc_streamer, WebRtcMode, VideoProcessorBase
import av
import cv2
from pyzbar.pyzbar import decode


# ==========================================
# 1. ESCOPO GLOBAL: Processador de Vídeo
# ==========================================
class BarcodeProcessor(VideoProcessorBase):
    def __init__(self):
        self.resultado_temporario = None

    def recv(self, frame: av.VideoFrame) -> av.VideoFrame:
        img = frame.to_ndarray(format="bgr24")

        barcodes = decode(img)
        for barcode in barcodes:
            barcode_data = barcode.data.decode("utf-8")
            self.resultado_temporario = barcode_data

            # Feedback visual na câmera
            (x, y, w, h) = barcode.rect
            cv2.rectangle(img, (x, y), (x + w, y + h), (0, 255, 0), 2)
            cv2.putText(img, barcode_data, (x, y - 10),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)

        return av.VideoFrame.from_ndarray(img, format="bgr24")


# ==========================================
# 2. INTERFACE PRINCIPAL
# ==========================================
st.title("Mobile Barcode Scanner Pro")

if "ultimo_resultado" not in st.session_state:
    st.session_state["ultimo_resultado"] = None

# FLUXO A: Sucesso (Fora da câmera)
if st.session_state["ultimo_resultado"]:
    st.success(f"✅ Lido com sucesso: {st.session_state['ultimo_resultado']}")
    st.json({"status": "Processado", "conteudo": st.session_state["ultimo_resultado"]})

    if st.button("🔄 Escanear Próximo Código"):
        st.session_state["ultimo_resultado"] = None
        st.rerun()

# FLUXO B: Scanner Ativo
else:
    # Componente WebRTC estático (não sofre rerun por conta do fragmento abaixo)
    ctx = webrtc_streamer(
        key="barcode-scanner-fragment-v1",
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


    # 3. O SEGREDO: Fragmento isolado para checagem assíncrona
    # Esse decorator faz com que APENAS esta função rode repetidamente, protegendo o WebRTC
    @st.fragment(run_every="0.5s")  # Verifica a cada 500 milissegundos de forma leve
    def verificar_leitura(webrtc_context):
        if webrtc_context.state.playing and webrtc_context.video_processor:
            st.info("📷 Scanner ativo e monitorado. Aproxime o código...")

            detectado = getattr(webrtc_context.video_processor, "resultado_temporario", None)

            if detectado:
                st.session_state["ultimo_resultado"] = detectado
                webrtc_context.video_processor.resultado_temporario = None
                # Como alteramos o session_state global, o rerun vai atualizar a página inteira para o FLUXO A
                st.rerun()
        else:
            st.warning("Clique no botão 'Start' acima para iniciar a câmera.")


    # Executa o monitor de fragmento passando o contexto do WebRTC
    verificar_leitura(ctx)