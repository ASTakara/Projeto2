import streamlit as st
import cv2
import numpy as np
from pyzbar.pyzbar import decode
import streamlit.components.v1 as components

# --- CONFIGURAÇÃO DA PÁGINA ---
st.set_page_config(page_title="Inovacao - Coletor", layout="centered")
st.title("📦 Coletor")


# --- FUNÇÃO AUXILIAR DE LEITURA (OPENCV + PYZBAR) ---
def escanear_codigo(img_file):
    if img_file is None:
        return None

    bytes_data = img_file.getvalue()
    cv_img = cv2.imdecode(np.frombuffer(bytes_data, np.uint8), cv2.IMREAD_COLOR)
    gray = cv2.cvtColor(cv_img, cv2.COLOR_BGR2GRAY)

    # Tentativa 1: Em pé
    codigos = decode(gray)
    if codigos:
        for obj in codigos:
            texto = obj.data.decode("utf-8").strip()
            if texto:
                return texto

    # Tentativa 2: Deitado
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
    st.session_state["produto_escanear"] = True
if "produto_codigo" not in st.session_state:
    st.session_state["produto_codigo"] = None
if "produto_quantidade" not in st.session_state:
    st.session_state["produto_quantidade"] = 1
if "encerrado" not in st.session_state:
    st.session_state["encerrado"] = False

# =====================================================================
# FLUXO DE SAÍDA: SE O OPERADOR CLICOU EM ENCERRAR
# =====================================================================
if st.session_state["encerrado"]:
    st.warning("⚠️ O processo foi encerrado. Você já pode fechar esta aba do navegador.")

    # Injeta JavaScript para tentar fechar a aba do navegador automaticamente
    components.html("""
        <script>
            window.close();
            // Caso o navegador bloqueie o window.close(), avisa o usuário de forma limpa:
            setTimeout(function() {
                document.body.innerHTML = '<h2 style="color: gray; text-align: center; font-family: sans-serif; margin-top: 50px;">Sessão encerrada com segurança. Pode fechar o aplicativo.</h2>';
            }, 300);
        </script>
    """, height=100)
    st.stop()  # Interrompe a execução do script do Streamlit aqui

# =====================================================================
# BLOCO 1: IDENTIFICAÇÃO E FECHAMENTO DA PRATELEIRA
# =====================================================================
st.write("---")
st.subheader("📍 Endereço")

col_input, col_botao = st.columns([3, 1], vertical_alignment="bottom")

with col_input:
    st.text_input(
        "Endereço Ativo:",
        value=st.session_state["prateleira_atual"],
        disabled=True,
        placeholder="Aguardando leitura do Emdereço...",
    )

with col_botao:
    botao_fechar_desabilitado = not bool(st.session_state["prateleira_atual"])

    if st.button(
            "Fechar Emdereço",
            type="primary",
            disabled=botao_fechar_desabilitado,
            use_container_width=True,
    ):
        st.toast(f"🔒 Endereço {st.session_state['prateleira_atual']} fechada com sucesso!")
        st.session_state["prateleira_atual"] = ""
        st.session_state["produto_codigo"] = None
        st.session_state["produto_quantidade"] = 1
        st.session_state["produto_escanear"] = True
        st.rerun()

# =====================================================================
# BLOCO 2: FLUXO DINÂMICO (CÂMERAS E PRODUTOS)
# =====================================================================

if not st.session_state["prateleira_atual"]:
    st.info("👋 Para iniciar, aponte a câmera para a etiqueta do **Endereço**.")
    img_prateleira = st.camera_input("Escanear Etiqueta de Endereço", key="cam_prateleira")

    if img_prateleira is not None:
        codigo_prat = escanear_codigo(img_prateleira)
        if codigo_prat:
            st.session_state["prateleira_atual"] = codigo_prat
            st.rerun()
        else:
            st.error("❌ Código do Endereço não reconhecido. Tente novamente.")

else:
    st.write("---")

    # Tela de Sucesso do Produto Bipado
    if not st.session_state["produto_escanear"] and st.session_state["produto_codigo"]:
        st.success("🎉 Produto adicionado à prateleira!")

        col_p1, col_p2 = st.columns(2)
        with col_p1:
            st.metric(label="Código do Produto", value=st.session_state["produto_codigo"])
        with col_p2:
            st.metric(label="Quantidade", value=f"{st.session_state['produto_quantidade']} un")

        if st.button("🔄 Escanear Próximo Produto", use_container_width=True):
            st.session_state["produto_codigo"] = None
            st.session_state["produto_quantidade"] = 1
            st.session_state["produto_escanear"] = True
            st.rerun()

    # Tela de Captura do Produto
    else:
        st.subheader("📦 Coleta de Produtos")

        quantidade_input = st.number_input(
            "1. Informe a Quantidade do Produto:",
            min_value=1, value=1, step=1,
            key="campo_quantidade",
        )

        st.write("2. Tire a foto do código de barras do **produto**:")
        img_produto = st.camera_input("Escanear Código do Produto", key="cam_produto")

        if img_produto is not None:
            codigo_prod = escanear_codigo(img_produto)
            if codigo_prod:
                st.session_state["produto_codigo"] = codigo_prod
                st.session_state["produto_quantidade"] = quantidade_input
                st.session_state["produto_escanear"] = False
                st.rerun()
            else:
                st.error("❌ Código do produto não reconhecido. Verifique a iluminação e tente novamente.")

# =====================================================================
# BLOCO 3: BOTÃO FIXO NO FIM DA TELA PARA ENCERRAR O NAVEGADOR
# =====================================================================
st.write("---")
st.write("")  # Espaçamento visual

if st.button("❌ Encerrar Processo e Sair", type="secondary", use_container_width=True):
    # Limpa os dados salvos no state por segurança
    st.session_state["prateleira_atual"] = ""
    st.session_state["produto_codigo"] = None

    # Ativa a flag de encerramento para disparar o JavaScript no próximo ciclo
    st.session_state["encerrado"] = True
    st.rerun()