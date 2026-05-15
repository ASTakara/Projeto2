import streamlit as st
import cv2
import numpy as np
import zxingcpp

# Configuração da Página
st.set_page_config(page_title="Scanner de Código de Barras", layout="centered")
st.title("📷 Scanner de Código de Barras")

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

# FLUXO B: Captura usando o App de Câmera Nativo do Celular (Sempre Traseira)
else:
    st.write("Clique no botão abaixo para abrir a câmera traseira do seu celular:")

    # st.file_uploader configurado para acionar diretamente a câmera traseira no mobile
    img_file = st.file_uploader(
        "Tire uma foto nítida do código de barras",
        type=["jpg", "jpeg", "png"],
        accept_all_files=False,
        key="camera_traseira_nativa"
    )

    if img_file is not None:
        # Converte a imagem enviada para o formato do OpenCV
        bytes_data = img_file.getvalue()
        cv_img = cv2.imdecode(np.frombuffer(bytes_data, np.uint8), cv2.IMREAD_COLOR)

        # Executa a leitura com o ZXing (Alta precisão)
        resultados = zxingcpp.read_barcodes(cv_img)

        if resultados:
            for codigo in resultados:
                texto_lido = codigo.text.strip()
                if texto_lido:
                    st.session_state["resultado_final"] = texto_lido
                    st.rerun()
            st.error(
                "❌ O scanner detectou a região do código, mas não conseguiu decodificar os números. Tente tirar a foto um pouco mais de longe ou melhore a iluminação.")
        else:
            st.error(
                "❌ Nenhum código de barras identificado. Certifique-se de que a foto está bem focada, sem reflexos brilhantes sobre as barras e tente novamente.")

    # Dica útil para o usuário na tela
    st.caption(
        "💡 Dica: Ao clicar no botão, escolha a opção 'Câmera' ou 'Tirar Foto'. O sistema usará os recursos automáticos de foco do seu aparelho.")