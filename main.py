import streamlit as st
from streamlit_webrtc import webrtc_streamer, WebRtcMode
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
    # Função interna para processar os frames da câmera
    def video_frame_callback(frame):
        img = frame.to_ndarray(format="bgr24")

        # Analisa a imagem atrás de códigos de barras
        barcodes = decode(img)
        for barcode in barcodes:
            barcode_data = barcode.data.decode("utf-8")

            # ATENÇÃO: Salvamos no dicionário global de estado interno do componente
            # Isso é seguro e não trava o interpretador assíncrono
            ctx.video_processor.resultado_temporario = barcode_data

            # Desenha o retângulo verde na tela
            (x, y, w, h) = barcode.rect
            cv2.rectangle(img, (x, y), (x + w, y + h), (0, 255, 0), 2)
            cv2.putText(img, barcode_data, (x, y - 10),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)

        return av.VideoFrame.from_ndarray(img, format="bgr24")


    # Criamos uma classe boba de processador para carregar nossa variável de resultado
    class ProcessadorDeCodigo:
        def __init__(self):
            self.resultado_temporario = None


    # Inicializa o componente de streaming com chave única e fixa
    ctx = webrtc_streamer(
        key="barcode-scanner-final-stable",
        mode=WebRtcMode.SENDRECV,
        video_frame_callback=video_frame_callback,
        media_stream_constraints={
            "video": {"facingMode": "environment"},
            "audio": False
        },
        async_processing=True,
        # Injeta nossa classe de persistência dentro do WebRTC
        video_html_attrs={"video_processor": ProcessadorDeCodigo()},
        rtc_configuration={
            "iceServers": [{"urls": ["stun:stun.l.google.com:19302"]}]
        }
    )

    # 4. O segredo da estabilidade: Verificação passiva a cada re-render
    # Não há laços "while", o Streamlit apenas checa se a thread de vídeo mandou algo
    if ctx.state.playing and hasattr(ctx, "video_processor") and ctx.video_processor:
        # Verifica se a thread da câmera achou um código
        detectado = getattr(ctx.video_processor, "resultado_temporario", None)

        if detectado:
            # Salva no estado global do Streamlit
            st.session_state["ultimo_resultado"] = detectado
            # Limpa o temporizador para evitar loops
            ctx.video_processor.resultado_temporario = None
            st.rerun()
        else:
            st.info("📷 Scanner ativo. Aproxime o código de barras da câmera...")
    else:
        st.warning("Clique no botão 'Start' para iniciar a câmera.")