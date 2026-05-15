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

    # Componente oficial do Streamlit (Câmera frontal por padrão)
    img_file = st.camera_input("Alinhe o código de barras na tela")

    if img_file is not None:
        # Converte a imagem capturada para o formato do OpenCV
        bytes_data = img_file.getvalue()
        cv_img = cv2.imdecode(np.frombuffer(bytes_data, np.uint8), cv2.IMREAD_COLOR)

        # Converte para escala de cinza para otimizar a leitura
        gray = cv2.cvtColor(cv_img, cv2.COLOR_BGR2GRAY)

        # Inicializa o detector nativo do OpenCV
        detector = cv2.barcode.BarcodeDetector()

        # Executa a detecção
        retval, decoded_info, points = detector.detectAndDecode(gray)

        # --- BLINDAGEM TOTAL ANTI-NUMPY ---
        # Verificamos a existência do decoded_info usando referências que não disparam o erro
        tem_conteudo = False
        try:
            if isinstance(decoded_info, np.ndarray):
                tem_conteudo = decoded_info.size > 0 and any(decoded_info.flat)
            elif decoded_info is not None:
                tem_conteudo = len(decoded_info) > 0
        except Exception:
            tem_conteudo = False

        if tem_conteudo:
            # Força tudo para uma lista pura de strings do Python, matando o NumPy aqui
            lista_limpa = []
            for item in decoded_info:
                if isinstance(item, np.ndarray):
                    if item.size > 0:
                        lista_limpa.append(str(item.flat[0]).strip())
                else:
                    lista_limpa.append(str(item).strip())

            # Valida o primeiro resultado encontrado
            if len(lista_limpa) > 0 and lista_limpa[0] != "":
                st.session_state["resultado_final"] = lista_limpa[0]
                st.rerun()
            else:
                st.error("❌ A foto foi tirada, mas o conteúdo decodificado veio em branco. Tente focar melhor.")
        else:
            # Se o OpenCV não encontrar nenhuma estrutura de código de barras
            st.error(
                "❌ Código de barras não identificado na foto. Centralize bem o código, evite tremer e tente novamente.")