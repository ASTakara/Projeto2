import streamlit as st
import cv2
import numpy as np

# Configuração da Página
st.set_page_config(page_title="Scanner de Código de Barras", layout="centered")
st.title("📷 Scanner de Código de Barras (Modo Foto)")

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

# FLUXO B: Captura de Foto Estável
else:
    st.write("Tire uma foto nítida e aproximada do código de barras usando o botão abaixo:")

    # Componente oficial do Streamlit (usa a câmera frontal/padrão do dispositivo)
    img_file = st.camera_input("Alinhe o código de barras na tela")

    if img_file is not None:
        # Converte a imagem capturada para o formato do OpenCV
        bytes_data = img_file.getvalue()
        cv_img = cv2.imdecode(np.frombuffer(bytes_data, np.uint8), cv2.IMREAD_COLOR)

        # Converte para escala de cinza para otimizar a leitura
        gray = cv2.cvtColor(cv_img, cv2.COLOR_BGR2GRAY)

        # Inicializa o detector nativo do OpenCV
        detector = cv2.barcode.BarcodeDetector()

        # Desempacota os 3 valores da API moderna do OpenCV
        retval, decoded_info, points = detector.detectAndDecode(gray)

        # --- BLINDAGEM ANTI-NUMPY ---
        sucesso_leitura = False
        if decoded_info is not None:
            if isinstance(retval, np.ndarray):
                sucesso_leitura = bool(retval.any())
            else:
                sucesso_leitura = bool(retval)

        if sucesso_leitura:
            # Garante que os dados virem uma lista comum do Python (saindo do NumPy)
            lista_resultados = list(decoded_info) if isinstance(decoded_info, np.ndarray) else decoded_info

            if len(lista_resultados) > 0 and lista_resultados[0]:
                primeiro_resultado = str(lista_resultados[0]).strip()

                if primeiro_resultado != "":
                    st.session_state["resultado_final"] = primeiro_resultado
                    st.rerun()
                else:
                    st.error("❌ A foto foi tirada, mas o conteúdo extraído veio vazio. Tente focar melhor.")
            else:
                st.error("❌ Não foi possível decodificar as barras desta foto. Tente aproximar mais.")
        else:
            # Se o OpenCV não encontrar nenhuma estrutura de código de barras
            st.error(
                "❌ Código de barras não identificado na foto. Centralize bem o código, evite tremer e tente novamente.")