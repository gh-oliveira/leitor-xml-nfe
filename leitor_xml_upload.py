import streamlit as st
import pandas as pd
import xmltodict
import io

def infos_xml(arquivo_xml):
    dic_arquivo = xmltodict.parse(arquivo_xml)
    dados_nf = dic_arquivo["nfeProc"]["NFe"]["infNFe"]
    dados_item = dados_nf["det"]

    # Normaliza sempre para lista
    if not isinstance(dados_item, list):
        dados_item = [dados_item]

    conteudo_itens = []
    for item in dados_item:
        numero_nf = dados_nf["ide"]["nNF"]
        natureza_op = dados_nf["ide"]["natOp"].upper()
        nome_fornecedor = dados_nf["emit"]["xNome"].upper()
        uf_fornecedor = dados_nf["emit"]["enderEmit"]["UF"]
        nome_destinatario = dados_nf["dest"]["xNome"].upper()
        cnpj_destinatario = dados_nf["dest"]["CNPJ"]
        uf_destinatario = dados_nf["dest"]["enderDest"]["UF"]
        vlr_nf = dados_nf["total"]["ICMSTot"]["vNF"]
        vlr_st_nf = dados_nf["total"]["ICMSTot"]["vST"]
        vlr_ipi = dados_nf["total"]["ICMSTot"]["vIPI"]
        vlr_frete = dados_nf["total"]["ICMSTot"]["vFrete"]
        vlr_icms_destino_nf = (dados_nf["total"]["ICMSTot"].get("vICMSUFDest", 0))
        vlr_fcp_nf = (dados_nf["total"]["ICMSTot"].get("vFCPUFDest", 0))
        chave_acesso = dados_nf["Id"][3:]

        numero_item = item["@nItem"] if "@nItem" in item else item.get("nItem", "")
        descricao_item = item["prod"]["xProd"].upper()
        ncm_item = item["prod"]["NCM"]
        cfop_item = item["prod"]["CFOP"]
        vlr_total_item = item["prod"]["vProd"]
        
        pis = list(item["imposto"].get("PIS", {}).values())[0] if "PIS" in item["imposto"] else {}
        cst_pis = pis.get("CST", "")
        cofins = list(item["imposto"].get("COFINS", {}).values())[0] if "COFINS" in item["imposto"] else {}
        cst_cofins = cofins.get("CST", "")

        icms = list(item["imposto"]["ICMS"].values())[0]
        origem_cst = icms.get("orig", "")
        cst_item = origem_cst + icms.get("CST", icms.get("CSOSN", ""))
        bc_icms_item = (icms.get("vBC", 0))
        alq_icms_item = icms.get("pICMS", 0)
        vlr_icms_item = (icms.get("vICMS", 0))
        vlr_st_item = (icms.get("vICMSST", 0))

        bc_icms_destino_item = (item["imposto"].get("ICMSUFDest", {}).get("vBCUFDest", 0))
        alq_icms_destino_item = item["imposto"].get("ICMSUFDest", {}).get("pICMSUFDest", 0)
        vlr_icms_destino_item = (item["imposto"].get("ICMSUFDest", {}).get("vICMSUFDest", 0))
        bc_fcp_item = (item["imposto"].get("ICMSUFDest", {}).get("vBCFCPUFDest", 0))
        alq_fcp_item = item["imposto"].get("ICMSUFDest", {}).get("pFCPUFDest", 0)
        vlr_fcp_item = (item["imposto"].get("ICMSUFDest", {}).get("vFCPUFDest", 0))
        inf_comp = dados_nf.get("infAdic", {}).get("infCpl", "")

        conteudo_itens.append({
            "Número NF": numero_nf,
            "Natureza da Operação": natureza_op,
            "Fornecedor": nome_fornecedor,
            "UF Fornecedor": uf_fornecedor,
            "Destinatário": nome_destinatario,
            "CNPJ Destinatário": cnpj_destinatario,
            "UF Destinatário": uf_destinatario,
            "Valor Total NFe": vlr_nf,
            "Valor Total ST": vlr_st_nf,
            "Valor Total IPI": vlr_ipi,
            "Valor Total Frete": vlr_frete,
            "Valor Total ICMS Destino": vlr_icms_destino_nf,
            "Valor Total FCP": vlr_fcp_nf,
            "Item": numero_item,
            "Descrição": descricao_item,
            "NCM": ncm_item,
            "CST": cst_item,
            "CFOP": cfop_item,
            "Valor Total Item": vlr_total_item,
            "CST PIS": cst_pis,
            "CST COFINS": cst_cofins,
            "BC ICMS Item": bc_icms_item,            
            "Alíquota ICMS Item": alq_icms_item,
            "Valor ICMS Item": vlr_icms_item,
            "BC ICMS Destino Item": bc_icms_destino_item,
            "Alíquota ICMS Destino Item": alq_icms_destino_item,
            "Valor ICMS Destino Item": vlr_icms_destino_item,
            "BC FCP Destino Item": bc_fcp_item,
            "Alíquota FCP Item": alq_fcp_item,
            "Valor FCP Item": vlr_fcp_item,
            "Valor ST Item": vlr_st_item,
            "Chave de Acesso": chave_acesso,
            "Info Complementar": inf_comp
        })

    return pd.DataFrame(conteudo_itens)

# Streamlit App
st.title("📑 Leitor de XML NFe")
st.write("Faça upload de **um ou mais arquivos XML** da Nota Fiscal para gerar um Excel consolidado.")

uploaded_files = st.file_uploader(
    "Selecione arquivos XML",
    type="xml",
    accept_multiple_files=True
)

if uploaded_files:
    try:
        conteudo_total = []
        for file in uploaded_files:
            tabela = infos_xml(file)
            conteudo_total.append(tabela)

        # Juntar tudo em um único DataFrame
        resultado_final = pd.concat(conteudo_total, ignore_index=True)

        st.success(f"{len(uploaded_files)} arquivos processados com sucesso! ✅")
        st.dataframe(resultado_final)

        # Gerar Excel em memória
        output = io.BytesIO()
        resultado_final.to_excel(output, index=False)
        output.seek(0)

        st.download_button(
            label="📥 Baixar Relatório",
            data=output,
            file_name="dados_xml_NFe.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )

    except Exception as e:

        st.error(f"Erro ao processar os arquivos: {e}")

