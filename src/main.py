import pandas as pd
import os
import glob
from dotenv import load_dotenv
from supabase import create_client, Client
import math
import time
import tracemalloc

# 1. Configuração do Supabase
load_dotenv()
SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_KEY = os.environ.get("SUPABASE_KEY")
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

def obter_anos_disponiveis():
    """Varre a pasta raiz de dados e identifica as subpastas correspondentes aos anos."""
    if not os.path.exists('data'):
        return []
    
    anos = []
    for item in os.listdir('data'):
        caminho_completo = os.path.join('data', item)
        # Verifica se é uma pasta e se o nome contém apenas números (ex: '2022')
        if os.path.isdir(caminho_completo) and item.isdigit():
            anos.append(int(item))
            
    return sorted(anos) # Retorna em ordem cronológica

def estado_ja_processado(ano, uf):
    """Consulta a tabela de logs no Supabase para garantir idempotência."""
    resposta = supabase.table('etl_logs').select('id').eq('ano_eleicao', ano).eq('uf', uf).execute()
    return len(resposta.data) > 0

def registrar_log(ano, uf):
    """Grava o registro de sucesso para evitar reprocessamento futuro."""
    supabase.table('etl_logs').insert({'ano_eleicao': ano, 'uf': uf}).execute()

def obter_estados_disponiveis(ano):
    """Varre a pasta local e lista as UFs disponíveis."""
    padrao_busca = f'data/{ano}/votacao_secao_{ano}_*.csv'
    arquivos = glob.glob(padrao_busca)
    
    estados = []
    for arquivo in arquivos:
        nome_arquivo = os.path.basename(arquivo)
        uf = nome_arquivo.replace(f'votacao_secao_{ano}_', '').replace('.csv', '')
        estados.append(uf.upper())
    return estados

def processar_estado(ano, uf, df_locais_nacional):
    """Cruza votos e locais, retornando o dataframe padronizado para o banco."""
    print(f"\n[{uf}] Iniciando transformação de dados...")
    arquivo_votos = f'data/{ano}/votacao_secao_{ano}_{uf}.csv'
    
    df_locais_uf = df_locais_nacional[df_locais_nacional['SG_UF'] == uf]
    
    col_votos = ['NM_MUNICIPIO', 'NR_ZONA', 'NR_SECAO', 'DS_CARGO', 'NR_VOTAVEL', 'NM_VOTAVEL', 'QT_VOTOS']
    df_votos = pd.read_csv(arquivo_votos, sep=';', encoding='latin1', usecols=col_votos)
    
    df_final = pd.merge(df_votos, df_locais_uf, on=['NM_MUNICIPIO', 'NR_ZONA', 'NR_SECAO'], how='inner')
    
    df_agrupado = df_final.groupby(
        ['DS_CARGO', 'NR_VOTAVEL', 'NM_VOTAVEL', 'NM_MUNICIPIO', 'NM_BAIRRO', 'NR_LATITUDE', 'NR_LONGITUDE'],
        as_index=False
    )['QT_VOTOS'].sum()
    
    # Prepara as colunas para bater exatamente com a estrutura do Supabase
    df_agrupado = df_agrupado.rename(columns={
        'DS_CARGO': 'cargo',
        'NR_VOTAVEL': 'numero_candidato',
        'NM_VOTAVEL': 'nome_candidato',
        'NM_MUNICIPIO': 'municipio',
        'NM_BAIRRO': 'bairro',
        'NR_LATITUDE': 'latitude',
        'NR_LONGITUDE': 'longitude',
        'QT_VOTOS': 'total_votos'
    })
    df_agrupado['ano_eleicao'] = ano
    df_agrupado['sigla_uf'] = uf
    
    # Converte NaN (Not a Number) do Pandas para None, compatível com inserção JSON/SQL
    df_agrupado = df_agrupado.where(pd.notnull(df_agrupado), None)
    
    return df_agrupado

def fazer_upload_em_lotes(df, tamanho_lote=2000):
    """Fatia o dataframe em pequenos lotes e envia para a nuvem."""
    registros = df.to_dict(orient='records')
    total_lotes = math.ceil(len(registros) / tamanho_lote)
    
    print(f"Iniciando upload para o Supabase: {len(registros)} registros em {total_lotes} lotes.")
    
    for i in range(0, len(registros), tamanho_lote):
        lote = registros[i:i + tamanho_lote]
        supabase.table('votos_consolidados').insert(lote).execute()
        
        # Feedback visual a cada 10 lotes para você acompanhar o progresso
        if (i // tamanho_lote) % 10 == 0:
            print(f" Progresso: Lote {i // tamanho_lote} de {total_lotes} enviado.")

def orquestrar_pipeline(ano):
    estados = obter_estados_disponiveis(ano)
    if not estados:
        print(f"Nenhum arquivo de votos encontrado para {ano}.")
        return
        
    print(f"Carregando base nacional de endereços de {ano}...")
    arquivo_locais = f'data/{ano}/eleitorado_local_votacao_{ano}.csv'
    col_locais = ['SG_UF', 'NM_MUNICIPIO', 'NR_ZONA', 'NR_SECAO', 'NM_BAIRRO', 'NR_LATITUDE', 'NR_LONGITUDE']
    df_locais_nacional = pd.read_csv(arquivo_locais, sep=';', encoding='latin1', usecols=col_locais)
    
    for uf in estados:
        # Trava de Idempotência
        if estado_ja_processado(ano, uf):
            print(f"[{uf}] IGNORADO: Estado já consta no log de processamento.")
            continue
            
        df_estado = processar_estado(ano, uf, df_locais_nacional)
        fazer_upload_em_lotes(df_estado, tamanho_lote=2000)
        registrar_log(ano, uf)
        
        print(f"[{uf}] Pipeline finalizado com sucesso!")

if __name__ == "__main__":
    print("Iniciando monitoramento de hardware (Profiling)...")
    tracemalloc.start()
    tempo_inicio = time.time()
    
    anos_para_processar = obter_anos_disponiveis()
    
    if not anos_para_processar:
        print("Nenhuma pasta de dados encontrada na raiz do projeto.")
    else:
        print(f"=== INICIANDO PIPELINE AUTOMATIZADO ===")
        print(f"Anos identificados para varredura: {anos_para_processar}")
        
        for ano in anos_para_processar:
            print(f"\n>>> Avaliando ciclo eleitoral de {ano} <<<")
            orquestrar_pipeline(ano)
            
        print("\n=== PIPELINE CONCLUÍDO COM SUCESSO ===")

    # Captura as métricas finais
    tempo_fim = time.time()
    memoria_atual, memoria_pico = tracemalloc.get_traced_memory()
    tracemalloc.stop()
    
    # Conversão e cálculo
    tempo_total = tempo_fim - tempo_inicio
    pico_mb = memoria_pico / (1024 * 1024)
    
    print(f"\n=== RELATÓRIO DE PERFORMANCE ===")
    print(f"Tempo total de execução: {tempo_total:.2f} segundos")
    print(f"Pico máximo de RAM alocada: {pico_mb:.2f} MB")
    print(f"================================")