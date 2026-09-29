import streamlit as st
import pandas as pd
import re
import json
import os
import unicodedata
from datetime import datetime
from zoneinfo import ZoneInfo


# ================================================================
# FUNÇÕES AUXILIARES
# ================================================================

def normalizar(texto):
    """
    Remove acentos, espaços extras e deixa em maiúsculas.
    Usado para comparar textos de forma robusta.
    """
    texto = str(texto).strip().upper()
    texto = unicodedata.normalize("NFKD", texto)
    texto = "".join(
        c for c in texto
        if not unicodedata.combining(c)
    )

    return texto


# ================================================================
# METAS POR EMPRESA
# ================================================================

METAS = {
    "MITSUBISHI": (["MITSUBISHI", "AKANE"], 30),
    "FORD": (["FORD"], 15),
    "SEMINOVOS": (["SEMINOVOS", "JRCA"], 35),
    "BYD": (["BYD"], 65),
    "DENZA": (["DENZA"], 11),
    "VIVA VOLKS": (["VIVA VOLKS", "VOLKSWAGEN", "VW"], 30),
    "BAJAJ": (["BAJAJ"], 30),
    "NIKAI": (["NIKAI"], 35),
    "TRIUMPH": (["TRIUMPH"], 14),
    "MG": (["MG"], 14),
}


def obter_meta(empresa):
    """
    Recebe o texto da coluna Empresa e devolve:
    (nome_padronizado, meta)
    ou
    (None, None)
    """

    if pd.isna(empresa) or not str(empresa).strip():
        return None, None

    texto = normalizar(empresa)
    tokens = set(texto.split())

    for chave, (palavras, meta) in METAS.items():

        for p in palavras:

            p_norm = normalizar(p)

            if " " in p_norm:

                if p_norm in texto:
                    return chave, meta

            else:

                if p_norm in tokens:
                    return chave, meta

    return None, None


# ================================================================
# CONFIGURAÇÃO DO STREAMLIT
# ================================================================

st.set_page_config(
    page_title="Ranking de Visita em Loja - Admin",
    page_icon="🔥",
    layout="wide"
)


# ================================================================
# ARQUIVO DE RESULTADO
# ================================================================

PASTA_DADOS = os.path.join(
    os.path.dirname(__file__),
    "dados"
)

ARQUIVO_RESULTADO = os.path.join(
    PASTA_DADOS,
    "ultimo_resultado.json"
)

FUSO = ZoneInfo("America/Maceio")

os.makedirs(
    PASTA_DADOS,
    exist_ok=True
)


# ================================================================
# TÍTULO
# ================================================================

st.title("🔥 Ranking de Aquecimento — Admin")

st.write(
    "Envie uma planilha para contar os aquecedores dos clientes "
    "com visita realizada. "
    "Cada **Evento** será contabilizado apenas uma vez."
)

st.info(
    "📌 Regra aplicada: **1 visita = 1 Evento**. "
    "Se o mesmo evento aparecer várias vezes na planilha, "
    "ele será contado somente uma vez."
)


# ================================================================
# UPLOAD
# ================================================================

arquivo = st.file_uploader(
    "📁 Selecione sua planilha Excel",
    type=["xlsx", "xls"]
)


# ================================================================
# PROCESSAMENTO
# ================================================================

if arquivo is not None:

    # ------------------------------------------------------------
    # DESCOBRIR CABEÇALHO
    # ------------------------------------------------------------

    bruto = pd.read_excel(
        arquivo,
        header=None,
        nrows=15
    )

    linha_cabecalho = None

    for i, linha in bruto.iterrows():

        valores = [
            str(v).strip().lower()
            for v in linha.tolist()
        ]

        encontrou_visita = any(
            "visita agendada" in v
            for v in valores
        )

        encontrou_aquecimento = any(
            v == "aquecimento"
            for v in valores
        )

        if encontrou_visita and encontrou_aquecimento:

            linha_cabecalho = i

            break


    if linha_cabecalho is None:

        linha_cabecalho = 0


    # ------------------------------------------------------------
    # LER PLANILHA
    # ------------------------------------------------------------

    arquivo.seek(0)

    df = pd.read_excel(
        arquivo,
        header=linha_cabecalho
    )


    # ------------------------------------------------------------
    # LIMPAR NOMES DAS COLUNAS
    # ------------------------------------------------------------

    df.columns = [
        re.sub(
            r"\s+",
            " ",
            str(col)
        ).strip()

        for col in df.columns
    ]


    st.success(
        "Planilha carregada com sucesso! ✅"
    )


    # ============================================================
    # IDENTIFICAR COLUNAS
    # ============================================================

    coluna_evento = None
    coluna_agendada = None
    coluna_realizada = None
    coluna_aquecimento = None
    coluna_tipo_evento = None
    coluna_empresa = None


    for coluna in df.columns:

        nome = normalizar(coluna)


        # EVENTO
        if nome == "EVENTO":

            coluna_evento = coluna


        # VISITA AGENDADA
        if nome == "VISITA AGENDADA":

            coluna_agendada = coluna


        # VISITA REALIZADA
        if nome == "VISITA REALIZADA":

            coluna_realizada = coluna


        # AQUECIMENTO
        if nome == "AQUECIMENTO":

            coluna_aquecimento = coluna


        # TIPO EVENTO
        if (
            "TIPO EVENTO" in nome
            or
            "TIPO DE EVENTO" in nome
        ):

            coluna_tipo_evento = coluna


        # EMPRESA
        if nome == "EMPRESA":

            coluna_empresa = coluna


    # ============================================================
    # VALIDAÇÕES
    # ============================================================

    if coluna_evento is None:

        st.error(
            "❌ Não encontrei a coluna **Evento** na planilha."
        )

        st.write(
            "Colunas encontradas:"
        )

        st.write(
            df.columns.tolist()
        )

        st.stop()


    if coluna_aquecimento is None:

        st.error(
            "❌ Não encontrei a coluna **Aquecimento** na planilha."
        )

        st.write(
            "Colunas encontradas:"
        )

        st.write(
            df.columns.tolist()
        )

        st.stop()


    if coluna_agendada is None:

        st.warning(
            "⚠️ Não encontrei a coluna "
            "'Visita Agendada'."
        )


    if coluna_realizada is None:

        st.warning(
            "⚠️ Não encontrei a coluna "
            "'Visita Realizada'."
        )


    if coluna_tipo_evento is None:

        st.warning(
            "⚠️ Não encontrei a coluna "
            "'Tipo Evento'. "
            "O filtro de PROSPECÇÃO FEIRÃO "
            "não será aplicado."
        )


    if coluna_empresa is None:

        st.warning(
            "⚠️ Não encontrei a coluna "
            "'Empresa'. "
            "O controle de metas não será aplicado."
        )


    # ============================================================
    # BASE ORIGINAL
    # ============================================================

    df_original = df.copy()


    # ============================================================
    # FILTRAR VISITAS
    # ============================================================

    df_filtrado = df.copy()


    # ------------------------------------------------------------
    # VISITA AGENDADA
    # ------------------------------------------------------------

    if coluna_agendada is not None:

        df_filtrado = df_filtrado[
            df_filtrado[coluna_agendada]
            .astype(str)
            .str.strip()
            .str.upper()
            == "SIM"
        ].copy()


    # ------------------------------------------------------------
    # VISITA REALIZADA
    #
    # Essa é a base utilizada para o ranking de visitas.
    # ------------------------------------------------------------

    if coluna_realizada is not None:

        df_filtrado = df_filtrado[
            df_filtrado[coluna_realizada]
            .astype(str)
            .str.strip()
            .str.upper()
            == "SIM"
        ].copy()


    # ============================================================
    # EXCLUIR PROSPECÇÃO FEIRÃO
    # ============================================================

    if coluna_tipo_evento is not None:

        df_filtrado = df_filtrado[
            df_filtrado[coluna_tipo_evento]
            .apply(normalizar)
            != "PROSPECCAO FEIRAO"
        ].copy()


    # ============================================================
    # REMOVER EVENTOS VAZIOS
    # ============================================================

    df_filtrado = df_filtrado[
        df_filtrado[coluna_evento].notna()
    ].copy()


    df_filtrado = df_filtrado[
        df_filtrado[coluna_evento]
        .astype(str)
        .str.strip()
        != ""
    ].copy()


    # ============================================================
    # CONTAGEM ANTES DA DEDUPLICAÇÃO
    # ============================================================

    total_registros_antes = len(
        df_filtrado
    )


    total_eventos_antes = (
        df_filtrado[coluna_evento]
        .nunique()
    )


    # ============================================================
    # REGRA PRINCIPAL
    #
    # UMA VISITA POR EVENTO
    #
    # Se:
    #
    # Evento 123
    # Evento 123
    #
    # Resultado:
    #
    # Evento 123 = 1 visita
    #
    # ============================================================

    df_filtrado = df_filtrado.drop_duplicates(
        subset=[coluna_evento],
        keep="first"
    ).copy()


    # ============================================================
    # CONTAGEM APÓS DEDUPLICAÇÃO
    # ============================================================

    total_registros_depois = len(
        df_filtrado
    )


    total_eventos_depois = (
        df_filtrado[coluna_evento]
        .nunique()
    )


    duplicados_removidos = (
        total_registros_antes
        - total_registros_depois
    )


    # ============================================================
    # AQUECIMENTO
    # ============================================================

    df_filtrado = df_filtrado.dropna(
        subset=[coluna_aquecimento]
    ).copy()


    df_filtrado[coluna_aquecimento] = (
        df_filtrado[coluna_aquecimento]
        .astype(str)
        .str.strip()
    )


    # Remover aquecimentos vazios
    df_filtrado = df_filtrado[
        df_filtrado[coluna_aquecimento]
        .str.strip()
        != ""
    ].copy()


    # ============================================================
    # RANKING
    # ============================================================

    ranking = (
        df_filtrado[coluna_aquecimento]
        .value_counts()
        .reset_index()
    )


    ranking.columns = [
        "Aquecedor",
        "Quantidade"
    ]


    ranking.index = ranking.index + 1

    ranking.index.name = "Posição"


    # ============================================================
    # EMPRESA E METAS
    # ============================================================

    if coluna_empresa is not None:

        empresa_por_aquecedor = (
            df_filtrado
            .groupby(
                coluna_aquecimento
            )[coluna_empresa]
            .agg(
                lambda s:
                s.mode().iat[0]
                if not s.mode().empty
                else None
            )
        )


        ranking["Empresa"] = (
            ranking["Aquecedor"]
            .map(empresa_por_aquecedor)
        )


        metas_info = (
            ranking["Empresa"]
            .apply(obter_meta)
        )


        ranking["Meta"] = (
            metas_info
            .apply(
                lambda x: x[1]
            )
        )


        ranking["Atingiu Meta"] = (
            ranking.apply(
                lambda r:
                bool(
                    pd.notna(r["Meta"])
                    and
                    r["Quantidade"]
                    >= r["Meta"]
                ),
                axis=1
            )
        )


        # --------------------------------------------------------
        # EMPRESAS NÃO RECONHECIDAS
        # --------------------------------------------------------

        nao_reconhecidos = (
            ranking.loc[
                ranking["Meta"].isna(),
                "Empresa"
            ]
            .dropna()
            .unique()
        )


        if len(nao_reconhecidos) > 0:

            st.warning(
                "⚠️ Não reconheci a meta destas empresas "
                "(ajuste o dicionário METAS): "
                +
                ", ".join(
                    map(
                        str,
                        nao_reconhecidos
                    )
                )
            )


    # ============================================================
    # MÉTRICAS
    # ============================================================

    st.markdown("---")

    col1, col2, col3, col4 = st.columns(4)


    with col1:

        st.metric(
            "📅 Visitas Únicas",
            total_eventos_depois
        )


    with col2:

        st.metric(
            "🔥 Total de Aquecedores",
            len(ranking)
        )


    with col3:

        st.metric(
            "🔁 Duplicidades Removidas",
            duplicados_removidos
        )


    with col4:

        st.metric(
            "📄 Registros Analisados",
            total_registros_antes
        )


    # ============================================================
    # INFORMAÇÃO SOBRE A DEDUPLICAÇÃO
    # ============================================================

    if duplicados_removidos > 0:

        st.success(
            f"✅ Regra aplicada com sucesso: "
            f"{duplicados_removidos} registro(s) duplicado(s) "
            f"foram removidos. "
            f"Cada Evento passou a contar apenas uma vez."
        )

    else:

        st.info(
            "ℹ️ Nenhum Evento duplicado foi encontrado "
            "após os filtros aplicados."
        )


    # ============================================================
    # RANKING
    # ============================================================

    st.subheader(
        "🏆 Ranking dos Aquecedores"
    )


    if "Atingiu Meta" in ranking.columns:

        def destacar_meta(row):

            estilos = [
                ""
            ] * len(row)


            if row.get(
                "Atingiu Meta"
            ):

                idx = row.index.get_loc(
                    "Aquecedor"
                )

                estilos[idx] = (
                    "color: #16a34a; "
                    "font-weight: 800;"
                )


            return estilos


        st.dataframe(
            ranking.style.apply(
                destacar_meta,
                axis=1
            ),
            width="stretch"
        )

    else:

        st.dataframe(
            ranking,
            width="stretch"
        )


    # ============================================================
    # GRÁFICO
    # ============================================================

    st.subheader(
        "📊 Visitas por Aquecedor"
    )


    if not ranking.empty:

        st.bar_chart(
            ranking.set_index(
                "Aquecedor"
            )["Quantidade"]
        )


    # ============================================================
    # DETALHAMENTO DOS EVENTOS
    # ============================================================

    st.subheader(
        "📋 Eventos considerados"
    )


    colunas_detalhes = [
        coluna_evento,
        coluna_aquecimento
    ]


    if coluna_empresa is not None:
        colunas_detalhes.append(
            coluna_empresa
        )


    if coluna_realizada is not None:
        colunas_detalhes.append(
            coluna_realizada
        )


    if coluna_agendada is not None:
        colunas_detalhes.append(
            coluna_agendada
        )


    if "Cliente" in df_filtrado.columns:
        colunas_detalhes.append(
            "Cliente"
        )


    if "Vendedor" in df_filtrado.columns:
        colunas_detalhes.append(
            "Vendedor"
        )


    colunas_detalhes = list(
        dict.fromkeys(
            colunas_detalhes
        )
    )


    colunas_detalhes = [
        coluna
        for coluna in colunas_detalhes
        if coluna in df_filtrado.columns
    ]


    st.dataframe(
        df_filtrado[
            colunas_detalhes
        ],
        width="stretch",
        hide_index=True
    )


    # ============================================================
    # SALVAR RESULTADO
    # ============================================================

    agora = datetime.now(
        FUSO
    )


    resultado = {

        "atualizado_em":
            agora.strftime(
                "%d/%m/%Y %H:%M:%S"
            ),

        "total_visitas_agendadas":
            int(
                total_eventos_depois
            ),

        "total_visitas_unicas":
            int(
                total_eventos_depois
            ),

        "total_aquecedores":
            int(
                len(ranking)
            ),

        "registros_antes_deduplicacao":
            int(
                total_registros_antes
            ),

        "duplicados_removidos":
            int(
                duplicados_removidos
            ),

        "ranking":
            ranking
            .reset_index()
            .to_dict(
                orient="records"
            )
    }


    # ============================================================
    # PUBLICAR JSON
    # ============================================================

    with open(
        ARQUIVO_RESULTADO,
        "w",
        encoding="utf-8"
    ) as f:

        json.dump(
            resultado,
            f,
            ensure_ascii=False,
            indent=2
        )


    # ============================================================
    # STATUS
    # ============================================================

    st.info(
        f"📤 Painel público atualizado em "
        f"**{resultado['atualizado_em']}**. "
        f"Os novos números já estão disponíveis."
    )