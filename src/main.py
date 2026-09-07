import pandas as pd
import os
import glob

def obter_estados_disponiveis(ano):
    """Varre a pasta do ano especificado e identifica quais estados possuem arquivo de votos."""
    padrao_busca = f'data/{ano}/votacao_secao_{ano}_*.csv'
    arquivos = glob.glob(padrao_busca)
    
    estados = []
    for arquivo in arquivos:
        # Extrai a sigla da UF do nome do arquivo (Ex: 'votacao_secao_2022_RJ.csv' -> 'RJ')
        nome_arquivo = os.path.basename(arquivo)
        uf = nome_arquivo.replace(f'votacao_secao_{ano}_', '').replace('.csv', '')
        estados.append(uf.upper())
    
    return estados

def processar_estado(ano, uf, df_locais_nacional):
    """Processa o cruzamento de votos e endereços para um estado específico."""
    print(f"\n--- Iniciando processamento para: {uf} ({ano}) ---")
    arquivo_votos = f'data/{ano}/votacao_secao_{ano}_{uf}.csv'
    
    # 1. Filtra a base nacional de locais apenas para o estado atual
    print(f"[{uf}] Isolando endereços do estado...")
    df_locais_uf = df_locais_nacional[df_locais_nacional['SG_UF'] == uf]
    
    # 2. Carrega os votos do estado
    print(f"[{uf}] Lendo arquivo de votos...")
    col_votos = ['NM_MUNICIPIO', 'NR_ZONA', 'NR_SECAO', 'DS_CARGO', 'NR_VOTAVEL', 'NM_VOTAVEL', 'QT_VOTOS']
    df_votos = pd.read_csv(arquivo_votos, sep=';', encoding='latin1', usecols=col_votos)
    
    # 3. Cruzamento (Inner Join)
    print(f"[{uf}] Cruzando votos com coordenadas territoriais...")
    df_final = pd.merge(df_votos, df_locais_uf, on=['NM_MUNICIPIO', 'NR_ZONA', 'NR_SECAO'], how='inner')
    
    # 4. Agregação e redução de desperdício
    print(f"[{uf}] Consolidando totais por bairro e candidato...")
    df_agrupado = df_final.groupby(
        ['DS_CARGO', 'NR_VOTAVEL', 'NM_VOTAVEL', 'NM_MUNICIPIO', 'NM_BAIRRO', 'NR_LATITUDE', 'NR_LONGITUDE'],
        as_index=False
    )['QT_VOTOS'].sum()
    
    print(f"[{uf}] Concluído. {len(df_agrupado)} blocos gerados.")
    return df_agrupado

def orquestrar_pipeline(ano):
    """Função principal que gerencia o fluxo de trabalho."""
    estados = obter_estados_disponiveis(ano)
    
    if not estados:
        print(f"Nenhum arquivo de votos encontrado na pasta data/{ano}/.")
        return
        
    print(f"Estados identificados para {ano}: {estados}")
    
    # Carrega a base nacional UMA VEZ para não sobrecarregar a leitura do disco
    print(f"Carregando base nacional de locais de votação de {ano} na memória...")
    arquivo_locais = f'data/{ano}/eleitorado_local_votacao_{ano}.csv'
    col_locais = ['SG_UF', 'NM_MUNICIPIO', 'NR_ZONA', 'NR_SECAO', 'NM_BAIRRO', 'NR_LATITUDE', 'NR_LONGITUDE']
    df_locais_nacional = pd.read_csv(arquivo_locais, sep=';', encoding='latin1', usecols=col_locais)
    
    for uf in estados:
        # [FUTURO] Ponto de injeção da regra de Idempotência:
        # Aqui faremos a checagem no Supabase para pular o estado caso ele já tenha sido processado.
        
        df_estado = processar_estado(ano, uf, df_locais_nacional)
        
        # Gera o CSV de validação local
        nome_saida = f'resultado_{uf}_{ano}.csv'
        df_estado.to_csv(nome_saida, index=False, sep=';', encoding='latin1')
        print(f"[{uf}] Arquivo {nome_saida} salvo com sucesso.")

if __name__ == "__main__":
    orquestrar_pipeline(2022)