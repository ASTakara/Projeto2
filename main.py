import streamlit as st
from streamlit_webrtc import webrtc_streamer, WebRtcMode, VideoProcessorBase
import av
import cv2
from pyzbar.pyzbar import decode


# ==========================================
# 1. ESCOPO GLOBAL: Processador de Alta Performance
# ==========================================
class BarcodeProcessor(VideoProcessorBase):
    def __init__(self):
        self.codigo_detectado = None

    def recv(self, frame: av.VideoFrame) -> av.VideoFrame:
        img = frame.to_ndarray(format="bgr24")

        # Converte para tons de cinza para melhorar a detecção do PyZbar em ambientes móveis
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

        # Executa o decode do código de barras
        barcodes = decode(gray)

        for barcode in barcodes:
            barcode_data = barcode.data.decode("utf-8")
            self.codigo_detectado = barcode_data

            # Desenha o retângulo verde e o texto na imagem do cliente
            (x, y, w, h) = barcode.rect
            cv2.rectangle(img, (x, y), (x + w, y + h), (0, 255, 0), 3)
            cv2.putText(img, "OK! Clique abaixo", (x, y - 10),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
            break  # Foca apenas no primeiro código encontrado

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
    st.success(f"🎉 Código detectado com sucesso!")
    st.info(f"**Conteúdo:** {st.session_state['resultado_final']}")

    if st.button("🔄 Escanear Próximo Código", use_container_width=True):
        st.session_state["resultado_final"] = None
        st.rerun()

# TELA B: Câmera Ativa
else:
    st.write("Aproxime o código de barras da câmera traseira do celular.")

    # Instancia o Streamer WebRTC de forma totalmente isolada
    ctx = webrtc_streamer(
        key="webrtc-barcode-final-v6",
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

    # Bloco reativo de monitoramento
    if ctx.state.playing and ctx.video_processor:
        # Puxa o dado diretamente do objeto em tempo de execução
        dado_temporario = getattr(ctx.video_processor, "codigo_detectado", None)

        if dado_temporario:
            st.success("🎯 Código na memória!")

            # Criamos o gatilho nativo para o usuário confirmar sem estourar o asyncio
            if st.button(f"📥 Processar Código: {dado_temporario}", type="primary", use_container_width=True):
                st.session_state["resultado_final"] = dado_temporario
                ctx.video_processor.codigo_detectado = None
                st.rerun()
        else:
            st.info("Aguardando detecção... Certifique-se de que o código está bem iluminado.")

            # Pequeno botão de apoio para forçar o Streamlit a ler o estado do frame atual
            if st.button("🔄 Sincronizar Câmera / Forçar Leitura", use_container_width=True):
                st.rerun()
    else:
        st.warning("Clique no botão **Start** acima para liberar o acesso à câmera.")