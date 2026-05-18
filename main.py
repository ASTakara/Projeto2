import streamlit as st
import cv2
import numpy as np
from pyzbar.pyzbar import decode
import streamlit.components.v1 as components
import requests  # Biblioteca para chamadas de API

# --- CONFIGURAÇÃO DA PÁGINA ---
st.set_page_config(page_title="Coletor de Inventário", layout="centered")
st.title("📦 Sistema de Coleta de Inventário")


# =====================================================================
# FUNÇÕES DE INTEGRAÇÃO COM AS SUAS APIS (SUBSTITUA PELOS SEUS ENDEREÇOS)
# =====================================================================

def consultar_api_endereco(codigo_endereco):
    """Valida se o endereço existe no sistema"""
    # url_api = f"https://seu_sistema.com.br/api/localizacao/{codigo_endereco}"
    try:
        # --- SIMULAÇÃO (Substitua pela chamada real) ---
        if codigo_endereco.isalnum():
            return True, f"Setor Logístico - Rua 4 (Código: {codigo_endereco})"
        else:
            return False, "Endereço não localizado no sistema."
    except Exception:
        return False, "Erro de conexão com o servidor da API."


def consultar_api_produto(codigo_barras):
    """Consulta a API para verificar se o produto existe e trazer seu Título"""
    # url_api = f"https://seu_sistema.com.br/api/produto/{codigo_barras}"
    try:
        # --- SIMULAÇÃO (Substitua pela chamada real) ---
        # Simulando que se o código tiver tamanho padrão (ex: de 8 a 14 dígitos), ele existe
        if 8 <= len(codigo_barras) <= 14:
            titulo_produto = f"Produto Exemplo SKU-{codigo_barras[:4]}"
            return True, titulo_produto
        else:
            return False, "Produto não cadastrado no catálogo."
    except Exception:
        return False, "Erro ao conectar na API de produtos."


def gravar_dados_inventario(endereco, codigo_barras, quantidade):
    """Envia o payload final via POST para salvar no banco de dados"""
    # url_api = "https://seu_sistema.com.br/api/inventario/gravar"
    # payload = {
    #     "endereco": endereco,
    #     "codigo_barras": codigo_barras,
    #     "quantidade": quantidade
    # }
    try:
        # --- SIMULAÇÃO (Substitua pela chamada real) ---
        # response = requests.post(url_api, json=payload, timeout=5)
        # return response.status_code in [200, 201]

        return True  # Retorna True se gravou com sucesso
    except Exception:
        return False


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
            if texto: return texto

    # Tentativa 2: Deitado
    gray_rotated = cv2.rotate(gray, cv2.ROTATE_90_CLOCKWISE)
    codigos_rotacionados = decode(gray_rotated)
    if codigos_rotacionados:
        for obj in codigos_rotacionados:
            texto = obj.data.decode("utf-8").strip()
            if texto: return texto
    return None


# --- INICIALIZAÇÃO DO ESTADO (SESSION STATE) ---
if "prateleira_atual" not in st.session_state:
    st.session_state["prateleira_atual"] = ""
if "label_api_prateleira" not in st.session_state:
    st.session_state["label_api_prateleira"] = ""
if "produto_escanear" not in st.session_state:
    st.session_state["produto_escanear"] = True
if "produto_codigo" not in st.session_state:
    st.session_state["produto_codigo"] = None
if "produto_titulo" not in st.session_state:
    st.session_state["produto_titulo"] = ""  # Guarda o título retornado pela API do produto
if "produto_quantidade" not in st.session_state:
    st.session_state["produto_quantidade"] = 1
if "encerrado" not in st.session_state:
    st.session_state["encerrado"] = False

# =====================================================================
# FLUXO DE SAÍDA: SE O OPERADOR CLICOU EM ENCERRAR
# =====================================================================
if st.session_state["encerrado"]:
    st.warning("⚠️ O processo foi encerrado. Você já pode fechar esta aba do navegador.")
    components.html("""
        <script>
            window.close();
            setTimeout(function() {
                document.body.innerHTML = '<h2 style="color: gray; text-align: center; font-family: sans-serif; margin-top: 50px;">Sessão encerrada com segurança. Pode fechar o aplicativo.</h2>';
            }, 300);
        </script>
    """, height=100)
    st.stop()

# =====================================================================
# BLOCO 1: IDENTIFICAÇÃO E FECHAMENTO DA PRATELEIRA
# =====================================================================
st.write("---")
st.subheader("📍 Localização")

col_input, col_botao = st.columns([3, 1], vertical_alignment="bottom")

with col_input:
    st.text_input(
        "Endereço da Prateleira Ativa:",
        value=st.session_state["prateleira_atual"],
        disabled=True,
        placeholder="Aguardando leitura do código da prateleira...",
    )

with col_botao:
    botao_fechar_desabilitado = not bool(st.session_state["prateleira_atual"])

    if st.button("Fechar Prateleira", type="primary", disabled=botao_fechar_desabilitado, use_container_width=True):
        st.toast(f"🔒 Prateleira {st.session_state['prateleira_atual']} fechada com sucesso!")
        st.session_state["prateleira_atual"] = ""
        st.session_state["label_api_prateleira"] = ""
        st.session_state["produto_codigo"] = None
        st.session_state["produto_titulo"] = ""
        st.session_state["produto_quantidade"] = 1
        st.session_state["produto_escanear"] = True
        st.rerun()

if st.session_state["label_api_prateleira"]:
    st.caption(f"ℹ️ **Descrição do Local:** {st.session_state['label_api_prateleira']}")

# =====================================================================
# BLOCO 2: FLUXO DINÂMICO (CÂMERAS E PRODUTOS)
# =====================================================================

# PASSO A: Escanear Prateleira
if not st.session_state["prateleira_atual"]:
    st.info("👋 Para iniciar, aponte a câmera para o código da **Prateleira**.")
    img_prateleira = st.camera_input("Escanear Código da Prateleira", key="cam_prateleira")

    if img_prateleira is not None:
        codigo_prat = escanear_codigo(img_prateleira)
        if codigo_prat:
            sucesso, resultado_api = consultar_api_endereco(codigo_prat)
            if sucesso:
                st.session_state["prateleira_atual"] = codigo_prat
                st.session_state["label_api_prateleira"] = resultado_api
                st.rerun()
            else:
                st.error(f"❌ Erro na validação do endereço: {resultado_api}")
        else:
            st.error("❌ Código da prateleira não reconhecido. Tente novamente.")

# PASSO B: Prateleira ativa, libera os produtos
else:
    st.write("---")

    # Tela de Sucesso (Produto já validado e gravado com sucesso no Banco/API)
    if not st.session_state["produto_escanear"] and st.session_state["produto_codigo"]:
        st.success("🎉 Dados gravados com sucesso no sistema!")

        col_p1, col_p2 = st.columns(2)
        with col_p1:
            st.metric(label="Código do Produto", value=st.session_state["produto_codigo"])
            st.caption(f"🏷️ **Título:** {st.session_state['produto_titulo']}")  # Label do Título do Produto
        with col_p2:
            st.metric(label="Quantidade Gravada", value=f"{st.session_state['produto_quantidade']} un")

        if st.button("🔄 Escanear Próximo Produto", use_container_width=True):
            st.session_state["produto_codigo"] = None
            st.session_state["produto_titulo"] = ""
            st.session_state["produto_quantidade"] = 1
            st.session_state["produto_escanear"] = True
            st.rerun()

    # Tela de Captura e Validação do Produto
    else:
        st.subheader("📦 Coleta de Itens")

        quantidade_input = st.number_input(
            "1. Informe a quantidade do item:",
            min_value=1, value=1, step=1,
            key="campo_quantidade",
        )

        st.write("2. Tire a foto do código de barras do **produto**:")
        img_produto = st.camera_input("Escanear Código do Produto", key="cam_produto")

        if img_produto is not None:
            codigo_prod = escanear_codigo(img_produto)
            if codigo_prod:

                # 1ª Etapa: Verifica a existência do Produto na API
                sucesso_prod, resultado_prod = consultar_api_produto(codigo_prod)

                if sucesso_prod:
                    # 2ª Etapa: Se válido, chama a API de gravação enviando tudo
                    sucesso_gravacao = gravar_dados_inventario(
                        endereco=st.session_state["prateleira_atual"],
                        codigo_barras=codigo_prod,
                        quantidade=quantidade_input
                    )

                    if sucesso_gravacao:
                        # Salva tudo no state para exibir na tela de sucesso
                        st.session_state["produto_codigo"] = codigo_prod
                        st.session_state["produto_titulo"] = resultado_prod  # Passa o título encontrado
                        st.session_state["produto_quantidade"] = quantidade_input
                        st.session_state["produto_escanear"] = False
                        st.rerun()
                    else:
                        st.error("❌ O produto é válido, mas ocorreu um erro ao gravar os dados no servidor.")
                else:
                    # Produto não cadastrado
                    st.error(f"❌ Erro no Produto: {resultado_prod}")
            else:
                st.error("❌ Código do produto não reconhecido fisicamente. Verifique o enquadramento.")

# =====================================================================
# BLOCO 3: BOTÃO FIXO NO FIM DA TELA PARA ENCERRAR O NAVEGADOR
# =====================================================================
st.write("---")
st.write("")

if st.button("❌ Encerrar Processo e Sair", type="secondary", use_container_width=True):
    st.session_state["prateleira_atual"] = ""
    st.session_state["label_api_prateleira"] = ""
    st.session_state["produto_codigo"] = None
    st.session_state["produto_titulo"] = ""
    st.session_state["encerrado"] = True
    st.rerun()