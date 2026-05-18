import streamlit as st
import cv2
import numpy as np
from pyzbar.pyzbar import decode

# --- CONFIGURAÇÃO DA PÁGINA ---
st.set_page_config(page_title="Coletor de Inventário", layout="centered")
st.title("📦 Sistema de Coleta de Inventário")


# --- FUNÇÃO AUXILIAR DE LEITURA (OPENCV + PYZBAR) ---
def escanear_codigo(img_file):
    """Recebe a imagem da câmera e tenta decodificar em duas posições (em pé e deitado)"""
    if img_file is None:
        return None

    # Converte o arquivo enviado para o formato do OpenCV
    bytes_data = img_file.getvalue()
    cv_img = cv2.imdecode(np.frombuffer(bytes_data, np.uint8), cv2.IMREAD_COLOR)
    gray = cv2.cvtColor(cv_img, cv2.COLOR_BGR2GRAY)

    # Tentativa 1: Posição original (em pé)
    codigos = decode(gray)
    if codigos:
        for obj in codigos:
            texto = obj.data.decode("utf-8").strip()
            if texto:
                return texto

    # Tentativa 2: Rotacionado 90° (deitado)
    gray_rotated = cv2.rotate(gray, cv2.ROTATE_90_CLOCKWISE)
    codigos_rotacionados = decode(gray_rotated)
    if codigos_rotacionados:
        for obj in codigos_rotacionados:
            texto = obj.data.decode("utf-8").strip()
            if texto:
                return texto

    return None


# --- INICIALIZAÇÃO DO ESTADO (SESSION STATE) ---
if "prateleira_atual" not in st.session_state:
    st.session_state["prateleira_atual"] = ""
if "produto_escanear" not in st.session_state:
    # Controla se estamos na tela de sucesso do produto
    st.session_state["produto_escanear"] = True
if "produto_codigo" not in st.session_state:
    st.session_state["produto_codigo"] = None
if "produto_quantidade" not in st.session_state:
    st.session_state["produto_quantidade"] = 1


# =====================================================================
# BLOCO 1: IDENTIFICAÇÃO E FECHAMENTO DA PRATELEIRA
# =====================================================================
st.write("---")
st.subheader("📍 Localização")

# Cria duas colunas: campo de texto largo e o botão de fechar ao lado
col_input, col_botao = st.columns([3, 1], vertical_alignment="bottom")

with col_input:
    st.text_input(
        "Endereço da Prateleira Ativa:",
        value=st.session_state["prateleira_atual"],
        disabled=True,
        placeholder="Aguardando leitura do código da prateleira...",
    )

with col_botao:
    # O botão só fica ativo se houver uma prateleira bipada
    botao_fechar_desabilitado = not bool(st.session_state["prateleira_atual"])

    if st.button(
        "Fechar Prateleira",
        type="primary",
        disabled=botao_fechar_desabilitado,
        use_container_width=True,
    ):
        # --- AÇÃO DE FECHAMENTO ---
        # Aqui no futuro você pode salvar no banco que a prateleira X foi encerrada
        st.toast(
            f"🔒 Prateleira {st.session_state['prateleira_atual']} fechada com sucesso!"
        )

        # Reseta todo o estado para começar uma nova prateleira do zero
        st.session_state["prateleira_atual"] = ""
        st.session_state["produto_codigo"] = None
        st.session_state["produto_quantidade"] = 1
        st.session_state["produto_escanear"] = True
        st.rerun()


# =====================================================================
# BLOCO 2: FLUXO DINÂMICO (CÂMERAS E PRODUTOS)
# =====================================================================

# PASSO A: Se não tem prateleira bipada, abre a câmera da prateleira
if not st.session_state["prateleira_atual"]:
    st.info("👋 Para iniciar, aponte a câmera para o código da **Prateleira**.")
    img_prateleira = st.camera_input(
        "Escanear Código da Prateleira", key="cam_prateleira"
    )

    if img_prateleira is not None:
        codigo_prat = escanear_codigo(img_prateleira)
        if codigo_prat:
            st.session_state["prateleira_atual"] = codigo_prat
            st.rerun()
        else:
            st.error("❌ Código da prateleira não reconhecido. Tente novamente.")

# PASSO B: Se já tem prateleira, libera o fluxo de bipar produtos nela
else:
    st.write("---")

    # Tela de Sucesso do Produto Bipado
    if (
        not st.session_state["produto_escanear"]
        and st.session_state["produto_codigo"]
    ):
        st.success("🎉 Produto adicionado à prateleira!")

        col_p1, col_p2 = st.columns(2)
        with col_p1:
            st.metric(
                label="Código do Produto", value=st.session_state["produto_codigo"]
            )
        with col_p2:
            st.metric(
                label="Quantidade",
                value=f"{st.session_state['produto_quantidade']} un",
            )

        if st.button("🔄 Escanear Próximo Produto", use_container_width=True):
            # Reseta as variáveis do produto, mas mantém a prateleira intacta
            st.session_state["produto_codigo"] = None
            st.session_state["produto_quantidade"] = 1
            st.session_state["produto_escanear"] = True
            st.rerun()

    # Tela de Captura do Produto (Quantidade + Câmera)
    else:
        st.subheader("📦 Coleta de Itens")

        # Campo numérico para a quantidade
        quantidade_input = st.number_input(
            "1. Informe a quantidade do item:",
            min_value=1,
            value=1,
            step=1,
            key="campo_quantidade",
        )

        st.write("2. Tire a foto do código de barras do **produto**:")
        img_produto = st.camera_input(
            "Escanear Código do Produto", key="cam_produto"
        )

        if img_produto is not None:
            codigo_prod = escanear_codigo(img_produto)
            if codigo_prod:
                # Salva os dados do produto no estado
                st.session_state["produto_codigo"] = codigo_prod
                st.session_state["produto_quantidade"] = quantidade_input
                # Muda para a tela de sucesso do produto
                st.session_state["produto_escanear"] = False
                st.rerun()
            else:
                st.error(
                    "❌ Código do produto não reconhecido. Verifique a iluminação e tente novamente."
                )