import streamlit as st
from streamlit_webrtc import webrtc_streamer, WebRtcMode, VideoProcessorBase
import av
import cv2
from pyzbar.pyzbar import decode

st.title("Mobile Barcode Scanner")

# 1. Gerenciamento estático de estados
if "ultimo_resultado" not in st.session_state:
    st.session_state["ultimo_resultado"] = None

# 2. Tela de Sucesso (Se um código já foi detectado)
if st.session_state["ultimo_resultado"]:
    st.success(f"✅ Lido com sucesso: {st.session_state['ultimo_resultado']}")

    if st.button("🔄 Escanear Próximo Código"):
        st.session_state["ultimo_resultado"] = None
        st.rerun()

# 3. Tela do Scanner Ativo
else:
    # Criamos o processador herdando da classe base oficial do streamlit-webrtc
    class BarcodeProcessor(VideoProcessorBase):
        def __init__(self):
            self.resultado_temporario = None

        def recv(self, frame: av.VideoFrame) -> av.VideoFrame:
            img = frame.to_ndarray(format="bgr24")

            # Analisa o frame atrás de códigos de barras
            barcodes = decode(img)
            for barcode in barcodes:
                barcode_data = barcode.data.decode("utf-8")

                # Guarda o resultado no próprio objeto do processador
                self.resultado_temporario = barcode_data

                # Desenha o feedback visual na tela
                (x, y, w, h) = barcode.rect
                cv2.rectangle(img, (x, y), (x + w, y + h), (0, 255, 0), 2)
                cv2.putText(img, barcode_data, (x, y - 10),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)

            return av.VideoFrame.from_ndarray(img, format="bgr24")


    # Inicializa o componente usando a factory nativa (Seguro contra erros de JSON)
    ctx = webrtc_streamer(
        key="barcode-scanner-factory-stable",
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

    # 4. Verificação passiva a cada ciclo do Streamlit (Sem travar com laços while)
    if ctx.state.playing and ctx.video_processor:
        # Acessa o processador instanciado pelo componente
        detectado = getattr(ctx.video_processor, "resultado_temporario", None)

        if detectado:
            # Salva no estado global e atualiza a tela para exibir a mensagem de sucesso
            st.session_state["ultimo_resultado"] = detectado
            ctx.video_processor.resultado_temporario = None
            st.rerun()
        else:
            st.info("📷 Scanner ativo. Aproxime o código de barras da câmera...")
    else:
        st.warning("Clique no botão 'Start' para iniciar a câmera.")