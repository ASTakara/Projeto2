import streamlit as st
import cv2
import numpy as np

# Configuração da Página
st.set_page_config(page_title="Scanner de Código de Barras", layout="centered")
st.title("📷 Scanner de Código de Barras")

# Inicializa o estado para guardar o resultado
if "resultado_final" not in st.session_state:
    st.session_state["resultado_final"] = None

# FLUXO A: Código processado com sucesso
if st.session_state["resultado_final"]:
    st.success("🎉 Código capturado com sucesso!")
    st.info(f"**Conteúdo do Código:** {st.session_state['resultado_final']}")

    if st.button("🔄 Escanear Próximo Código", use_container_width=True):
        st.session_state["resultado_final"] = None
        st.rerun()

# FLUXO B: Captura de Foto/Frame Estável
else:
    st.write("Tire uma foto nítida e aproximada do código de barras:")

    # Componente oficial e nativo do Streamlit para câmeras
    img_file = st.camera_input("Alinhe o código de barras")

    if img_file is not None:
        # Converte a imagem capturada para o formato do OpenCV
        bytes_data = img_file.getvalue()
        cv_img = cv2.imdecode(np.frombuffer(bytes_data, np.uint8), cv2.IMREAD_COLOR)

        # Converte para escala de cinza para otimizar
        gray = cv2.cvtColor(cv_img, cv2.COLOR_BGR2GRAY)

        # Inicializa o detector nativo do OpenCV
        detector = cv2.barcode.BarcodeDetector()

        # Desempacotando os 3 valores retornados pelo OpenCV
        retval, decoded_info, points = detector.detectAndDecode(gray)

        # --- BLINDAGEM ANTI-NUMPY DEFINITIVA ---
        # 1. Avalia o retval sem gerar ambiguidade
        sucesso_leitura = False
        if decoded_info is not None:
            if isinstance(retval, np.ndarray):
                sucesso_leitura = bool(retval.any())
            else:
                sucesso_leitura = bool(retval)

        # 2. Se o OpenCV diz que leu algo, limpamos os dados convertendo para strings nativas
        if sucesso_leitura:
            strings_limpas = []
            try:
                # Transforma qualquer tipo de array/tupla em uma lista iterável do Python
                for item in decoded_info:
                    # Se o item interno for outro array do NumPy, extrai o primeiro elemento dele
                    if isinstance(item, np.ndarray):
                        if item.size > 0:
                            strings_limpas.append(str(item.flat[0]).strip())
                    else:
                        strings_limpas.append(str(item).strip())
            except Exception:
                strings_limpas = []

            # 3. Valida se encontramos alguma string que não seja vazia
            codigo_encontrado = None
            for texto in strings_limpas:
                if texto and texto != "":
                    codigo_encontrado = texto
                    break

            if codigo_encontrado:
                st.session_state["resultado_final"] = codigo_encontrado
                st.rerun()
            else:
                st.error(
                    "❌ O scanner processou a imagem, mas não conseguiu extrair um texto válido. Tente aproximar mais e focar no código.")
        else:
            # Se falhar a detecção básica
            st.error(
                "❌ Código de barras não identificado. Certifique-se de que a foto não ficou tremida ou cortada e tente novamente.")