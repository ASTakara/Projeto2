import streamlit as st
import streamlit.components.v1 as components

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

# FLUXO B: Scanner em tempo real via JavaScript (Client-Side)
else:
    st.write("Aproxime o código de barras da câmera traseira:")

    # Código HTML/JavaScript que injeta o scanner nativo no navegador do cliente
    codigo_html = """
    <div id="reader" style="width: 100%; max-width: 500px; margin: 0 auto; border-radius: 8px; overflow: hidden;"></div>

    <!-- Inclui a biblioteca oficial Html5-QRCode via CDN de forma segura -->
    <script src="https://unpkg.com/html5-qrcode" type="text/javascript"></script>

    <script>
        function onScanSuccess(decodedText, decodedResult) {
            // Atualiza os parâmetros da URL do Streamlit com o código lido
            const url = new URL(window.parent.location.href);
            url.searchParams.set('barcode', decodedText);
            window.parent.location.href = url.toString();
        }
        

        function onScanFailure(error) {
            // Ignora falhas de frames individuais onde o código não foi focado
        }

        // Configura o scanner priorizando a câmera traseira ('environment')
        let html5QrcodeScanner = new Html5QrcodeScanner(
            "reader", 
            { 
                fps: 15, 
                qrbox: { width: 300, height: 150 },
                videoConstraints: { facingMode: "environment" } // FORÇA CÂMERA TRASEIRA
            },
            /* verbose= */ false
        );

        html5QrcodeScanner.render(onScanSuccess, onScanFailure);
    </script>
    """

    # Renderiza o scanner na tela do Streamlit e captura o retorno do JavaScript
    # Ajustamos a altura para que o quadrado do vídeo apareça confortavelmente
    resultado_js = components.html(codigo_html, height=420)

    # Nota importante: Para enviar dados do JS para o Python de forma síncrona
    # no Streamlit de forma simples, capturamos o valor retornado na interface.
    # Como usamos o postMessage interno, podemos monitorar as mudanças de query params
    # ou usar um truque simples: o componente HTML injeta o valor na URL ou no estado.

    # Para capturar o resultado do componente HTML customizado de forma nativa e simples:
    # Caso o componente HTML envie dados, o Streamlit armazena no retorno da função:
    if resultado_js:
        # Se o retorno direto do componente receber o dado do postMessage
        st.session_state["resultado_final"] = str(resultado_js).strip()
        st.rerun()

    # Como o Streamlit puro às vezes precisa de uma ponte para o postMessage,
    # aqui está a alternativa usando query_params para garantir recepção instantânea:
    query_params = st.query_params
    if "barcode" in query_params:
        st.session_state["resultado_final"] = query_params["barcode"]
        # Limpa o parâmetro da URL para não entrar em loop
        st.query_params.clear()
        st.rerun()