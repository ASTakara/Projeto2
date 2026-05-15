import streamlit as st
import cv2
import numpy as np
import zxingcpp
import streamlit.components.v1 as components

# Configuração da Página
st.set_page_config(page_title="Scanner de Código de Barras", layout="centered")
st.title("📷 Scanner de Código de Barras de Alta Precisão")

# Inicializa o estado para guardar o resultado
if "resultado_final" not in st.session_state:
    st.session_state["resultado_final"] = None

# FLUXO A: Código processado com sucesso
if st.session_state["resultado_final"]:
    st.success("🎉 Código capturado com sucesso!")
    st.code(st.session_state["resultado_final"], language="text")

    if st.button("🔄 Escanear Próximo Código", use_container_width=True):
        st.session_state["resultado_final"] = None
        st.rerun()

# FLUXO B: Captura de Foto/Frame Estável (COM FORÇAMENTO DE CÂMERA TRASEIRA)
else:
    st.write("Tire uma foto nítida e aproximada do código de barras:")

    # TRUQUE DE MESTRE: Script injetado para forçar o navegador a priorizar a câmera traseira ("environment")
    components.html(
        """
        <script>
            // Sobrescreve a API de mídia do navegador antes do componente carregar
            if (navigator.mediaDevices && navigator.mediaDevices.getUserMedia) {
                const origGetUserMedia = navigator.mediaDevices.getUserMedia.bind(navigator.mediaDevices);
                navigator.mediaDevices.getUserMedia = function(constraints) {
                    if (constraints && constraints.video) {
                        // Força o modo de ambiente (câmera traseira) nas requisições de vídeo
                        constraints.video.facingMode = { ideal: "environment" };
                    }
                    return origGetUserMedia(constraints);
                };
            }
        </script>
        """,
        height=0,
        width=0
    )

    # Componente oficial de câmera
    img_file = st.camera_input("Centralize o código de barras na tela")

    if img_file is not None:
        bytes_data = img_file.getvalue()
        cv_img = cv2.imdecode(np.frombuffer(bytes_data, np.uint8), cv2.IMREAD_COLOR)

        # Executa o ZXing
        resultados = zxingcpp.read_barcodes(cv_img)

        if resultados:
            for codigo in resultados:
                texto_lido = codigo.text.strip()
                if texto_lido:
                    st.session_state["resultado_final"] = texto_lido
                    st.rerun()
            st.error(
                "❌ O scanner detectou a região do código, mas não conseguiu decodificar os números. Tente focar melhor.")
        else:
            st.error(
                "❌ Nenhum código de barras identificado. Certifique-se de que a foto está bem focada, sem sombras fortes sobre as barras e tente novamente.")