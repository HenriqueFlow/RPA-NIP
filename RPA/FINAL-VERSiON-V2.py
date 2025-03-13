import os
import re
import pyautogui
import time
import json
import shutil
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, StaleElementReferenceException, ElementClickInterceptedException
from webdriver_manager.chrome import ChromeDriverManager
from supabase import create_client, Client
from datetime import datetime, timedelta

# Configurações do Supabase
SUPABASE_URL = "https://uvgznbifmwocdpkbuumv.supabase.co"  # Substitua pelo seu URL do Supabase
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InV2Z3puYmlmbXdvY2Rwa2J1dW12Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3Mzc1NDgzMzksImV4cCI6MjA1MzEyNDMzOX0.aqwOrYMELMyXtIfph9Val_qq72Q80jQ3hIRCRaOgQbQ"  # Substitua pela sua API Key
TABLE_NAME = "nips_abertas"  # Nome correto da tabela
COLUMN_NAME = "demanda"  # Nome correto da coluna

# Configuração da URL da ANS e credenciais
URL_LOGIN = "https://www2.ans.gov.br/nip_operadora/?target=3396a8b22ba2f5ff5500f7672a11a803ea7189ab0141d68f5148553f4beab2c6"
USUARIO = "57862897889"
SENHA = "@Blue2025"

# Criar cliente do Supabase
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

# Configurações globais
TEMPO_ESPERA = 15  # segundos
SLEEP_TIME = 900  # 15 minutos em segundos

def salvar_log(mensagem):
    with open("log_Raspberry.txt", "a", encoding="utf-8") as arquivo_log:
        timestamp = time.strftime('%Y-%m-%d %H:%M:%S')
        arquivo_log.write(f"{timestamp} - {mensagem}\n")

def criar_diretorio_downloads(id_atual, pasta_base="C:\\Users\\Nome (Setor)\\Documents\\teste"):
    """Cria um diretório exclusivo para os arquivos do ID atual e retorna o caminho completo."""
    caminho_id = os.path.join(pasta_base, str(id_atual))
    if not os.path.exists(caminho_id):
        os.makedirs(caminho_id)
        salvar_log(f"[INFO] Diretório criado para ID {id_atual}: {caminho_id}")
    return caminho_id

def iniciar_navegador():
    options = webdriver.ChromeOptions()
    options.add_argument("--start-maximized")
    options.add_argument("--kiosk-printing")  # Ativa impressão automática
    options.add_experimental_option("prefs", {
        "printing.print_preview_sticky_settings.appState": json.dumps({
            "recentDestinations": [{"id": "Save as PDF", "origin": "local", "account": ""}],
            "selectedDestinationId": "Save as PDF",
            "version": 2
        }),
        "savefile.default_directory": "C:\\Users\\Nome (Setor)\\Downloads"
    })
    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=options)
    return driver

def configurar_downloads_para_id(driver, caminho_id):
    """Configura o navegador para salvar os downloads no diretório do ID."""
    prefs = {
        "download.default_directory": caminho_id,
        "download.prompt_for_download": False,
        "download.directory_upgrade": True,
        "safebrowsing.enabled": True
    }
    driver.execute_cdp_cmd("Page.setDownloadBehavior", {
        "behavior": "allow",
        "downloadPath": caminho_id
    })
    salvar_log(f"[INFO] Configuração de downloads ajustada para: {caminho_id}")

def realizar_login(driver, max_tentativas=3):
    for tentativa in range(max_tentativas):
        try:
            driver.get(URL_LOGIN)
            WebDriverWait(driver, TEMPO_ESPERA).until(
                EC.presence_of_element_located((By.ID, "input-mask"))
            ).send_keys(USUARIO)
            driver.find_element(By.ID, "mod-login-password").send_keys(SENHA)
            driver.find_element(By.ID, "botao").click()
            WebDriverWait(driver, TEMPO_ESPERA).until(EC.url_changes(URL_LOGIN))
            salvar_log("[INFO] Login realizado com sucesso.")
            return True  # Login bem-sucedido
        except Exception as e:
            salvar_log(f"[ERRO] Tentativa {tentativa + 1} de login falhou: {str(e)}")
            if tentativa < max_tentativas - 1:
                time.sleep(5)  # Aguarda antes de tentar novamente
            else:
                salvar_log("[ERRO] Todas as tentativas de login falharam.")
                return False

def testar_conexao_supabase():
    """Testa a conexão com o Supabase e verifica se a tabela está acessível."""
    try:
        salvar_log("[INFO] Testando conexão com o Supabase...")
        response = supabase.table("nips-abertas").select("*").limit(1).execute()

        if hasattr(response, "error") and response.error:
            salvar_log(f"[ERRO] Falha ao conectar ao Supabase: {response.error}")
            return False

        salvar_log("[SUCESSO] Conexão com Supabase estabelecida e tabela acessível.")
        return True
    except Exception as e:
        salvar_log(f"[ERRO] Exceção ao testar conexão com Supabase: {str(e)}")
        return False

def carregar_ids_processados():
    try:
        response = supabase.table(TABLE_NAME).select("demanda").execute()
        ids = {item["demanda"] for item in response.data if item["demanda"]} if response.data else set()  # Pegando a coluna correta
        salvar_log(f"[INFO] IDs carregados do banco de dados: {ids}")
        return ids
    except Exception as e:
        salvar_log(f"[ERRO] Falha ao carregar IDs do banco: {str(e)}")
        return set()
  
def reiniciar_conexao_supabase():
    """Reinicia a conexão com o Supabase para evitar cache de sessões antigas."""
    global supabase
    salvar_log("[INFO] Reiniciando conexão com o Supabase para limpar cache...")
    supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

def aguardar_proxima_execucao():
    """Aguarda o tempo de sleep definido e reinicia a conexão com Supabase para evitar cache."""
    salvar_log(f"[INFO] Entrando em sleep de {SLEEP_TIME} segundos antes da próxima tentativa.")
    time.sleep(SLEEP_TIME)
    reiniciar_conexao_supabase()

def capturar_ids_html(driver):
    """Captura apenas os IDs numéricos da tabela HTML mantendo a ordem."""
    try:
        wait = WebDriverWait(driver, 15)
        celulas = wait.until(
            EC.presence_of_all_elements_located(
                (By.XPATH, "//tbody[contains(@id, 'tbDemandaAguardandoResposta_data')]//td[@role='gridcell' and text()[number()=number()]]")
            )
        )
        ids = [td.text.strip() for td in celulas if td.text.strip().isdigit()]

        salvar_log(f"[INFO] IDs capturados no HTML: {ids}")
        return ids

    except TimeoutException:
        salvar_log("[ERRO] Timeout ao capturar IDs do HTML.")
        return []

def salvar_dados_no_banco(dados_linha):
    """Salva corretamente os dados no Supabase, garantindo que a estrutura original funcione."""
    try:
        if not isinstance(dados_linha, dict):
            salvar_log(f"[ERRO] O formato dos dados está incorreto! Esperado um dicionário, recebido: {type(dados_linha)}")
            return False

        # Converte `datetime` para string antes de salvar
        if isinstance(dados_linha.get("data_notificacao"), datetime):
            dados_linha["data_notificacao"] = dados_linha["data_notificacao"].strftime("%Y-%m-%d %H:%M:%S")

        response = supabase.table(TABLE_NAME).insert(dados_linha).execute()

        if response.data:
            id_gerado = response.data[0].get('id')
            salvar_log(f"[INFO] Dados salvos com sucesso no banco. ID único gerado: {id_gerado}")
            return id_gerado
        else:
            salvar_log(f"[ERRO] Falha ao salvar os dados no banco. Resposta: {response}")
            return False

    except Exception as e:
        salvar_log(f"[ERRO] Exceção ao salvar dados no banco: {str(e)}")
        return False

def capturar_dados_linha(driver, id_atual):
    """ Captura todas as informações da linha correspondente ao ID atual e ajusta os tipos antes de salvar. """
    try:
        linha_xpath = f"//td[text()='{id_atual}']/parent::tr"
        linha_elemento = WebDriverWait(driver, TEMPO_ESPERA).until(
            EC.presence_of_element_located((By.XPATH, linha_xpath))
        )
        
        colunas = linha_elemento.find_elements(By.TAG_NAME, "td")
        salvar_log(f"[DEBUG] Total de colunas encontradas para ID {id_atual}: {len(colunas)}")

        if len(colunas) < 7:
            salvar_log(f"[ERRO] A linha do ID {id_atual} não contém todas as colunas esperadas. Captura pode estar incorreta.")
            return None

        # 🔹 Extração correta das colunas, garantindo o alinhamento correto
        data_notificacao = colunas[0].text.strip() if len(colunas) > 0 else None
        demanda = colunas[1].text.strip() if len(colunas) > 1 else None
        protocolo = colunas[2].text.strip() if len(colunas) > 2 else None
        beneficiario = colunas[3].text.strip() if len(colunas) > 3 else None
        prazo = colunas[4].text.strip() if len(colunas) > 4 else None
        respondido = colunas[5].text.strip() if len(colunas) > 5 else None
        natureza = colunas[6].text.strip() if len(colunas) > 6 else None

        # 🔹 Conversão de Data (String -> Datetime)
        try:
            data_notificacao = datetime.strptime(data_notificacao, "%d/%m/%Y %H:%M:%S")
        except ValueError:
            salvar_log(f"[ERRO] Data inválida encontrada para o ID {id_atual}: {data_notificacao}. Definindo como NULL.")
            data_notificacao = None  # Define como NULL se estiver incorreta

        # 🔹 Conversão de Prazo para Integer
        try:
            prazo = int(prazo.split()[0]) if "dias" in prazo else None
        except ValueError:
            salvar_log(f"[ERRO] Prazo inválido encontrado: {prazo}. Definindo como NULL.")
            prazo = None

        # 🔹 Ajuste do Campo Respondido (Máx. 10 caracteres)
        if respondido:
            respondido = respondido.replace("\n", " ")[:10]  # Remove quebras de linha e limita a 10 caracteres

        # 🔹 Monta o dicionário final
        dados = {
            "demanda": demanda,
            "data_notificacao": data_notificacao,  # Agora no formato datetime correto
            "protocolo": protocolo,
            "beneficiario": beneficiario,
            "cpf": None,  # CPF não está na tabela, definindo como NULL
            "descricao_demanda": None,  # Esse campo não existe na visualização direta
            "prazo": prazo,  # Agora convertido para inteiro corretamente
            "respondido": respondido,  # Agora sem '\n' e limitado a 10 caracteres
            "natureza": natureza
        }

        salvar_log(f"[INFO] Dados capturados corretamente para o ID {id_atual}: {dados}")
        return dados

    except Exception as e:
        salvar_log(f"[ERRO] Falha ao capturar os dados da linha para o ID {id_atual}: {str(e)}")
        return None
    
def id_existe_no_banco(id_novo):
    """Verifica se o ID já existe na tabela Supabase antes de processá-lo."""
    try:
        salvar_log(f"[DEBUG] Verificando se o ID {id_novo} já existe no banco de dados...")

        response = supabase.table("nips_abertas").select("demanda").eq("demanda", id_novo).execute()

        if response.data:
            salvar_log(f"[INFO] ID {id_novo} já existe no banco. Pulando para o próximo.")
            return True  # ID já processado
        
        salvar_log(f"[DEBUG] ID {id_novo} não encontrado na base. Pode ser processado.")
        return False

    except Exception as e:
        salvar_log(f"[ERRO] Falha ao verificar ID {id_novo} no banco: {type(e).__name__} - {str(e)}")
        return False

def clicar_botao(driver, xpath):
    tentativas = 3
    for tentativa in range(tentativas):
        try:
            botao = WebDriverWait(driver, TEMPO_ESPERA).until(
                EC.element_to_be_clickable((By.XPATH, xpath))
            )
            driver.execute_script("arguments[0].scrollIntoView();", botao)  # Rolando até o botão
            time.sleep(1)
            botao.click()
            return True
        except TimeoutException:
            salvar_log(f"[ERRO] Tentativa {tentativa+1}: Timeout ao clicar no botão. Verifique o XPath.")
            return False
        except ElementClickInterceptedException:
            salvar_log(f"[ERRO] Tentativa {tentativa+1}: Outro elemento interceptou o clique. Tentando novamente...")
            driver.execute_script("window.scrollBy(0,100);")  # Rola um pouco para baixo
            time.sleep(1)
        except StaleElementReferenceException:
            salvar_log(f"[ERRO] Tentativa {tentativa+1}: Elemento recarregado. Tentando novamente...")
            time.sleep(2)
        except Exception as e:
            salvar_log(f"[ERRO] Tentativa {tentativa+1}: Erro inesperado ao clicar no botão: {str(e)}")
            return False
    return False

def clicar_botao_visualizar(driver, id_atual):
    """
    Função específica para rolar e clicar no botão Visualizar.
    Retorna True se conseguiu clicar, False caso contrário.
    """
    try:
        salvar_log(f"[INFO] Tentando encontrar e clicar no botão Visualizar para o ID {id_atual}")
        
        # Espera um tempo extra para garantir que o botão carregou
        time.sleep(2)
        
        # Rolar a página um pouco mais para garantir que o botão fique visível
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        time.sleep(2)

        visualizar_xpath = "//button[contains(@id, 'j_idt') and .//span[text()='Visualizar']]"

        botao_visualizar = WebDriverWait(driver, TEMPO_ESPERA).until(
            EC.element_to_be_clickable((By.XPATH, visualizar_xpath))
        )

        driver.execute_script("arguments[0].scrollIntoView();", botao_visualizar)
        time.sleep(1)
        botao_visualizar.click()

        salvar_log(f"[INFO] Botão Visualizar clicado com sucesso para o ID {id_atual}")
        return True
    except TimeoutException:
        salvar_log(f"[ERRO] Timeout ao clicar no botão Visualizar para o ID {id_atual}. Verifique se o botão está presente.")
        return False
    except StaleElementReferenceException:
        salvar_log(f"[ERRO] O botão Visualizar ficou indisponível repentinamente. Tentando novamente...")
        time.sleep(2)
        return clicar_botao_visualizar(driver, id_atual)  # Recursão para tentar clicar novamente
    except Exception as e:
        salvar_log(f"[ERRO] Erro inesperado ao clicar no botão Visualizar para o ID {id_atual}: {str(e)}")
        return False

def clicar_botao_salvar_pdf(driver):
    """Aguarda a janela de impressão e confirma o salvamento como PDF."""
    try:
        salvar_log("[INFO] Aguardando janela de impressão...")
        time.sleep(2)  # Pequena espera para garantir que a janela seja carregada
        
        # Enviar comando para confirmar o salvamento automático
        driver.execute_script("window.print();")
        salvar_log("[INFO] Documento salvo como PDF automaticamente.")
        return True
    except Exception as e:
        salvar_log(f"[ERRO] Falha ao salvar o documento PDF: {str(e)}")
        return False

def mover_arquivos_para_diretorio(caminho_downloads, caminho_destino):
    """
    Move todos os arquivos do diretório de downloads para o diretório de destino.
    :param caminho_downloads: Diretório de downloads onde os arquivos estão localizados.
    :param caminho_destino: Diretório de destino onde os arquivos devem ser movidos.
    """
    try:
        salvar_log(f"[INFO] Movendo arquivos de {caminho_downloads} para {caminho_destino}")

        # Listar todos os arquivos no diretório de downloads
        arquivos = os.listdir(caminho_downloads)

        if not arquivos:
            salvar_log("[INFO] Nenhum arquivo encontrado no diretório de downloads.")
            return

        # Mover cada arquivo para o diretório de destino
        for arquivo in arquivos:
            caminho_origem = os.path.join(caminho_downloads, arquivo)
            caminho_destino_arquivo = os.path.join(caminho_destino, arquivo)

            # Verificar se o arquivo existe antes de mover
            if os.path.exists(caminho_origem):
                shutil.move(caminho_origem, caminho_destino_arquivo)
                salvar_log(f"[INFO] Arquivo {arquivo} movido com sucesso para {caminho_destino}")
            else:
                salvar_log(f"[ERRO] Arquivo não encontrado: {caminho_origem}")

        salvar_log(f"[INFO] Todos os arquivos movidos com sucesso para {caminho_destino}")
    except Exception as e:
        salvar_log(f"[ERRO] Falha ao mover arquivos para {caminho_destino}: {str(e)}")

def aplicar_filtro_data(driver):
    """Aplica o filtro de data na interface com um período fixo entre 01/12/2024 e 31/12/2024."""
    try:
        salvar_log("[INFO] Aplicando filtro de datas.")
        wait = WebDriverWait(driver, TEMPO_ESPERA)

        hoje = datetime.now().strftime("%d/%m/%Y")
        ontem = (datetime.now() - timedelta(days=1)).strftime("%d/%m/%Y")

        # Aguardar até que os campos de data e o botão de busca estejam visíveis
        salvar_log("[INFO] Aguardando campos de data e botão de busca...")
        campo_data_inicial = wait.until(EC.visibility_of_element_located((By.ID, "formContent:dtInicio_input")))
        campo_data_final = wait.until(EC.visibility_of_element_located((By.ID, "formContent:dtFim_input")))
        botao_buscar = wait.until(EC.element_to_be_clickable((By.ID, "formContent:j_idt82")))

        # Limpar e preencher os campos de data com as datas fixas
        salvar_log("[INFO] Preenchendo campos de data...")
        campo_data_inicial.clear()
        campo_data_inicial.send_keys(ontem)
        campo_data_final.clear()
        campo_data_final.send_keys(hoje)

        # Clicar no botão de busca
        salvar_log("[INFO] Clicando no botão de busca...")
        botao_buscar.click()

        # Aguardar até que a tabela de resultados esteja visível
        salvar_log("[INFO] Aguardando tabela de resultados...")
        wait.until(EC.presence_of_element_located((By.ID, "formContent:j_idt85:tbDemandaAguardandoResposta_data")))
        salvar_log("Filtro de data aplicado com sucesso.")
        return True

    except StaleElementReferenceException:
        salvar_log("[ERRO] Elemento não está mais presente na página. Tentando novamente após recarregar a página.")
        driver.refresh()
        time.sleep(5)  # Aguardar um pouco antes de tentar novamente
        return aplicar_filtro_data(driver)

    except TimeoutException:
        salvar_log("[ERRO] Timeout ao aguardar elementos da página. Tentando novamente após recarregar a página.")
        driver.refresh()
        time.sleep(5)  # Aguardar um pouco antes de tentar novamente
        return aplicar_filtro_data(driver)

    except Exception as e:
        salvar_log(f"[ERRO] Falha ao aplicar filtro de data: {str(e)}")
        return False

def navegar_paginacao(driver):
    """Navega para a próxima página se disponível, senão retorna False para indicar que não há mais páginas."""
    try:
        botao_proxima = WebDriverWait(driver, 5).until(
            EC.presence_of_element_located((By.XPATH, "//span[contains(@class, 'ui-paginator-next') and not(contains(@class, 'ui-state-disabled'))]"))
        )
        botao_proxima.click()
        salvar_log("[INFO] Avançando para a próxima página de resultados...")
        time.sleep(3)  # Tempo para carregar a próxima página
        return True
    except TimeoutException:
        salvar_log("[INFO] Nenhuma próxima página disponível.")
        return False

def fluxo_processamento_id(driver, id_atual):
    tentativas = 3
    for tentativa in range(tentativas):
        try:
            salvar_log(f"[INFO] Iniciando processamento do ID {id_atual}")

            # Criar diretório para salvar arquivos
            caminho_id = criar_diretorio_downloads(id_atual)
            configurar_downloads_para_id(driver, caminho_id)

            # Capturar dados da linha
            dados_linha = capturar_dados_linha(driver, id_atual)
            if not dados_linha:
                salvar_log(f"[ERRO] Não foi possível capturar os dados da linha para o ID {id_atual}. Pulando para o próximo.")
                return False

            # Clicar no botão "Detalhes"
            detalhes_xpath = f"//tr[td[contains(text(), '{id_atual}')]]//button[contains(@id, 'j_idt') and .//span[text()='Detalhes']]"
            if clicar_botao(driver, detalhes_xpath):
                salvar_log(f"[INFO] Botão Detalhes clicado para o ID {id_atual}")
                time.sleep(2)
            else:
                salvar_log(f"[ERRO] Botão Detalhes não encontrado para o ID {id_atual}")
                return False

            # Clicar no botão "Visualizar"
            visualizar_xpath = "//button[contains(@id, 'j_idt') and .//span[text()='Visualizar']]"
            if clicar_botao(driver, visualizar_xpath):
                salvar_log(f"[INFO] Botão Visualizar clicado para o ID {id_atual}")
                time.sleep(2)
            else:
                salvar_log(f"[ERRO] Botão Visualizar não encontrado para o ID {id_atual}")
                return False

            # Clicar no botão "Imprimir" (sem aguardar janela de salvamento)
            imprimir_xpath = "//button[contains(@id, 'j_idt') and .//span[text()='Imprimir']]"
            if clicar_botao(driver, imprimir_xpath):
                salvar_log(f"[INFO] Botão Imprimir clicado para o ID {id_atual}")
                time.sleep(5)  # Aguardar tempo necessário para o PDF ser gerado e baixado
            else:
                salvar_log(f"[ERRO] Botão Imprimir não encontrado para o ID {id_atual}")
                return False

            # Mover o arquivo PDF para o diretório correto
            nome_arquivo = "www2.ans.gov.br_nip_operadora_pages_detalharDemanda.xhtml.pdf"
            caminho_downloads = "C:\\Users\\Nome (Setor)\\Downloads"
            caminho_destino = caminho_id  # Diretório do ID atual

            if mover_arquivos_para_diretorio(nome_arquivo, caminho_downloads, caminho_destino):
                salvar_log(f"[INFO] PDF movido com sucesso para {caminho_destino}")
            else:
                salvar_log(f"[ERRO] Falha ao mover o PDF para {caminho_destino}")

            # Clicar no botão "Fechar"
            fechar_xpath = "//button[contains(@id, 'j_idt') and .//span[text()='Fechar']]"
            if clicar_botao(driver, fechar_xpath):
                salvar_log(f"[INFO] Botão Fechar clicado para o ID {id_atual}")
                time.sleep(2)
            else:
                salvar_log(f"[ERRO] Botão Fechar não encontrado para o ID {id_atual}")

            # Iniciar download de arquivos adicionais
            salvar_log(f"[INFO] Iniciando download de arquivos para o ID {id_atual}")
            baixar_arquivos(driver, id_atual, caminho_id)

            # Mover todos os arquivos PDF para o diretório correto
            salvar_log(f"[INFO] Movendo arquivos PDF para o diretório {caminho_id}")
            mover_arquivos_pdf_para_diretorio(caminho_downloads, caminho_id)

            # Salvar no banco
            salvar_log(f"[DEBUG] Tentando salvar os seguintes dados no banco: {dados_linha}")
            if salvar_dados_no_banco(dados_linha):
                salvar_log(f"[INFO] ID {id_atual} salvo no banco de dados após processamento.")
            else:
                salvar_log(f"[ERRO] Falha ao salvar o ID {id_atual} no banco.")

            # Retornar à página inicial
            if not retornar_pagina_inicial(driver):
                salvar_log(f"[ERRO] Falha ao retornar à página inicial após o ID {id_atual}. Recarregando...")
                driver.refresh()
                time.sleep(5)

            salvar_log(f"[SUCESSO] Fluxo concluído para o ID {id_atual}")
            return True

        except Exception as e:
            salvar_log(f"[ERRO] Falha ao processar ID {id_atual}: {type(e).__name__} - {str(e)}")
            if tentativa < tentativas - 1:
                salvar_log(f"[INFO] Tentando novamente ({tentativa + 1}/{tentativas})...")
                time.sleep(5)  # Aguardar antes de tentar novamente
            else:
                salvar_log(f"[ERRO] Todas as tentativas falharam para o ID {id_atual}.")
                return False

def capturar_total_registros(driver):
    """ Captura o número total de registros da página para determinar o momento de ativar o sleep time. """
    try:
        elemento_paginacao = driver.find_element(By.CLASS_NAME, "ui-paginator-current")
        texto_paginacao = elemento_paginacao.text  # Exemplo: "Registros: 1 a 10 de 14"

        # Extrai os números do texto
        numeros = list(map(int, re.findall(r'\d+', texto_paginacao)))

        if len(numeros) == 3:
            inicio, fim, total = numeros
            salvar_log(f"[INFO] Página atual exibe registros de {inicio} a {fim} de um total de {total}")
            return inicio, fim, total
        else:
            salvar_log("[ERRO] Formato inesperado na paginação. Não foi possível extrair os valores.")
            return None, None, None

    except Exception as e:
        salvar_log(f"[ERRO] Falha ao capturar total de registros: {str(e)}")
        return None, None, None

def configurar_downloads_para_id(driver, caminho_id):
    """ Configura o navegador para sempre exibir a janela de salvamento ao baixar arquivos. """
    salvar_log(f"[INFO] Configurando downloads para a pasta: {caminho_id}")

    prefs = {
        "savefile.default_directory": caminho_id,  # Define diretório padrão
        "download.prompt_for_download": True,  # Ativa a janela de salvamento
        "download.directory_upgrade": True,
        "safebrowsing.enabled": True
    }

    options = webdriver.ChromeOptions()
    options.add_experimental_option("prefs", prefs)

    driver.execute_cdp_cmd("Page.setDownloadBehavior", {
        "behavior": "default"  # Agora exibe a janela de salvamento
    })

    salvar_log(f"[INFO] Configuração ajustada para exibir janela de salvamento.")

def iniciar_download(driver, id_atual, caminho_id):
    """Inicia o download do PDF imprimindo a página e garantindo que o arquivo seja salvo corretamente."""
    try:
        salvar_log(f"[INFO] Clicando no botão Imprimir para ID {id_atual}...")

        imprimir_xpath = "//button[contains(@id, 'j_idt') and .//span[text()='Imprimir']]"
        if clicar_botao(driver, imprimir_xpath):
            salvar_log("[INFO] Botão Imprimir clicado. Aguardando a janela de salvamento...")
            time.sleep(10)  # Aguardar mais tempo para que a janela e o documento carreguem completamente
        else:
            salvar_log("[ERRO] Botão Imprimir não encontrado.")
            return False

        # 🔹 **Aguardar a janela de impressão estar carregada**
        salvar_log("[INFO] Aguardando a janela de impressão renderizar o PDF...")
        time.sleep(5)  # Aguarda o carregamento do conteúdo

        # 🔹 **Garantir que o campo do nome do arquivo está ativo**
        salvar_log("[INFO] Garantindo que o campo do nome do arquivo está ativo...")
        pyautogui.click(500, 400)  # Clique no campo de nome do arquivo
        time.sleep(1)

        # 🔹 **Definir o caminho e manter o nome original do arquivo**
        caminho_arquivo = os.path.join(caminho_id)
        salvar_log(f"[INFO] Caminho digitado na janela: {caminho_arquivo}")

        pyautogui.write(caminho_arquivo, interval=0.1)  # Digita devagar para evitar erros
        time.sleep(1)
        pyautogui.press("enter")  # Pressiona Enter para salvar

        salvar_log(f"[INFO] PDF salvo com sucesso: {caminho_arquivo}")
        return True

    except Exception as e:
        salvar_log(f"[ERRO] Falha ao salvar o PDF: {str(e)}")
        return False

def aguardar_download(pasta_downloads, timeout=30):
    """Aguarda até que um novo arquivo seja baixado na pasta de downloads."""
    salvar_log("[INFO] Aguardando conclusão do download...")

    tempo_inicial = time.time()
    arquivos_antes = set(os.listdir(pasta_downloads))

    while time.time() - tempo_inicial < timeout:
        arquivos_atual = set(os.listdir(pasta_downloads))
        novos_arquivos = arquivos_atual - arquivos_antes

        if novos_arquivos:
            salvar_log(f"[INFO] Download concluído: {novos_arquivos}")
            return True  # Download concluído com sucesso

        time.sleep(2)  # Aguarda um pouco antes de verificar novamente

    salvar_log("[ERRO] Timeout ao aguardar o download.")
    return False  # Download falhou

def baixar_arquivos(driver, id_nip, caminho_download):
    """
    Função para baixar todos os arquivos disponíveis para um determinado ID.
    :param driver: Instância do WebDriver.
    :param id_nip: ID do processo que está sendo processado.
    :param caminho_download: Diretório onde os arquivos devem ser salvos.
    """
    try:
        salvar_log(f"[INFO] Iniciando download de arquivos para o ID {id_nip}")

        # Criar diretório para armazenar os downloads se não existir
        if not os.path.exists(caminho_download):
            os.makedirs(caminho_download)
            salvar_log(f"[INFO] Diretório criado para ID {id_nip}: {caminho_download}")
        else:
            salvar_log(f"[INFO] Diretório já existe para ID {id_nip}: {caminho_download}")

        # Ajustar configurações do navegador para o diretório de download
        driver.execute_script(f"window.navigator.msSaveOrOpenBlob = function(blob, name) {{}};")
        driver.execute_script(f"window.navigator.msSaveBlob = function(blob, name) {{}};")
        driver.execute_script(f"window.navigator.webkitSaveAs = function(blob, name) {{}};")
        driver.execute_script(f"window.navigator.saveAs = function(blob, name) {{}};")

        salvar_log(f"[INFO] Configuração de downloads ajustada para a pasta: {caminho_download}")

        # Rolar a página para garantir que os botões de download fiquem visíveis
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        time.sleep(2)  # Aguardar um pouco para garantir que a página foi rolada

        # Esperar até que os botões de download estejam visíveis
        try:
            botoes_download = WebDriverWait(driver, 10).until(
                EC.presence_of_all_elements_located((By.XPATH, "//button[.//span[text()='Download']]"))
            )
        except TimeoutException:
            salvar_log("[ERRO] Tempo esgotado ao esperar pelos botões de download.")
            return

        if not botoes_download:
            salvar_log("[INFO] Nenhum botão de download encontrado.")
            return

        salvar_log(f"[INFO] Encontrados {len(botoes_download)} arquivos para download.")

        for i, botao in enumerate(botoes_download, start=1):
            try:
                salvar_log(f"[INFO] Clicando no botão de download {i}/{len(botoes_download)}...")
                driver.execute_script("arguments[0].click();", botao)
                time.sleep(3)  # Pequeno delay para iniciar o download
            except Exception as e:
                salvar_log(f"[ERRO] Falha ao clicar no botão de download {i}: {e}")

        salvar_log(f"[INFO] Todos os downloads finalizados para o ID {id_nip}")
    except Exception as e:
        salvar_log(f"[ERRO] Erro inesperado ao baixar arquivos para ID {id_nip}: {e}")

def mover_arquivos_pdf_para_diretorio(caminho_downloads, caminho_destino):
    """
    Move todos os arquivos PDF do diretório de downloads para o diretório de destino.
    :param caminho_downloads: Diretório de downloads onde os arquivos PDF estão localizados.
    :param caminho_destino: Diretório de destino onde os arquivos PDF devem ser movidos.
    """
    try:
        salvar_log(f"[INFO] Movendo arquivos PDF de {caminho_downloads} para {caminho_destino}")

        # Listar todos os arquivos PDF no diretório de downloads
        arquivos_pdf = [f for f in os.listdir(caminho_downloads) if f.endswith('.pdf')]

        if not arquivos_pdf:
            salvar_log("[INFO] Nenhum arquivo PDF encontrado no diretório de downloads.")
            return

        # Mover cada arquivo PDF para o diretório de destino
        for arquivo in arquivos_pdf:
            caminho_origem = os.path.join(caminho_downloads, arquivo)
            caminho_destino_arquivo = os.path.join(caminho_destino, arquivo)
            shutil.move(caminho_origem, caminho_destino_arquivo)
            salvar_log(f"[INFO] Arquivo {arquivo} movido com sucesso para {caminho_destino}")

        salvar_log(f"[INFO] Todos os arquivos PDF movidos com sucesso para {caminho_destino}")
    except Exception as e:
        salvar_log(f"[ERRO] Falha ao mover arquivos PDF para {caminho_destino}: {e}")

def fluxo_processamento_id(driver, id_atual):
    tentativas = 3
    for tentativa in range(tentativas):
        try:
            salvar_log(f"[INFO] Iniciando processamento do ID {id_atual}")

            # Criar diretório para salvar arquivos
            caminho_id = criar_diretorio_downloads(id_atual)
            configurar_downloads_para_id(driver, caminho_id)

            # Capturar dados da linha
            dados_linha = capturar_dados_linha(driver, id_atual)
            if not dados_linha:
                salvar_log(f"[ERRO] Não foi possível capturar os dados da linha para o ID {id_atual}. Pulando para o próximo.")
                return False

            # Clicar no botão "Detalhes"
            detalhes_xpath = f"//tr[td[contains(text(), '{id_atual}')]]//button[contains(@id, 'j_idt') and .//span[text()='Detalhes']]"
            if clicar_botao(driver, detalhes_xpath):
                salvar_log(f"[INFO] Botão Detalhes clicado para o ID {id_atual}")
                time.sleep(2)
            else:
                salvar_log(f"[ERRO] Botão Detalhes não encontrado para o ID {id_atual}")
                return False

            # Clicar no botão "Visualizar"
            visualizar_xpath = "//button[contains(@id, 'j_idt') and .//span[text()='Visualizar']]"
            if clicar_botao(driver, visualizar_xpath):
                salvar_log(f"[INFO] Botão Visualizar clicado para o ID {id_atual}")
                time.sleep(2)
            else:
                salvar_log(f"[ERRO] Botão Visualizar não encontrado para o ID {id_atual}")
                return False

            # Clicar no botão "Imprimir" (sem aguardar janela de salvamento)
            imprimir_xpath = "//button[contains(@id, 'j_idt') and .//span[text()='Imprimir']]"
            if clicar_botao(driver, imprimir_xpath):
                salvar_log(f"[INFO] Botão Imprimir clicado para o ID {id_atual}")
                time.sleep(5)  # Aguardar tempo necessário para o PDF ser gerado e baixado
            else:
                salvar_log(f"[ERRO] Botão Imprimir não encontrado para o ID {id_atual}")
                return False

            # Mover o arquivo PDF para o diretório correto
            nome_arquivo = "www2.ans.gov.br_nip_operadora_pages_detalharDemanda.xhtml.pdf"
            caminho_downloads = "C:\\Users\\Nome (Setor)\\Downloads"
            caminho_destino = caminho_id  # Diretório do ID atual

            if mover_arquivos_para_diretorio(caminho_downloads, caminho_destino):
                salvar_log(f"[INFO] PDF movido com sucesso para {caminho_destino}")
            else:
                salvar_log(f"[ERRO] Falha ao mover o PDF para {caminho_destino}")

            # Clicar no botão "Fechar"
            fechar_xpath = "//button[contains(@id, 'j_idt') and .//span[text()='Fechar']]"
            if clicar_botao(driver, fechar_xpath):
                salvar_log(f"[INFO] Botão Fechar clicado para o ID {id_atual}")
                time.sleep(2)
            else:
                salvar_log(f"[ERRO] Botão Fechar não encontrado para o ID {id_atual}")

            # Iniciar download de arquivos adicionais
            salvar_log(f"[INFO] Iniciando download de arquivos para o ID {id_atual}")
            baixar_arquivos(driver, id_atual, caminho_id)

            # Mover todos os arquivos para o diretório correto
            mover_arquivos_para_diretorio(caminho_downloads, caminho_destino)

            # Salvar no banco
            salvar_log(f"[DEBUG] Tentando salvar os seguintes dados no banco: {dados_linha}")
            if salvar_dados_no_banco(dados_linha):
                salvar_log(f"[INFO] ID {id_atual} salvo no banco de dados após processamento.")
            else:
                salvar_log(f"[ERRO] Falha ao salvar o ID {id_atual} no banco.")

            # Retornar à página inicial
            if not retornar_pagina_inicial(driver):
                salvar_log(f"[ERRO] Falha ao retornar à página inicial após o ID {id_atual}. Recarregando...")
                driver.refresh()
                time.sleep(5)

            salvar_log(f"[SUCESSO] Fluxo concluído para o ID {id_atual}")
            return True

        except StaleElementReferenceException:
            salvar_log(f"[ERRO] Elemento não está mais presente na página. Tentando novamente ({tentativa + 1}/{tentativas})...")
            driver.refresh()
            time.sleep(5)  # Aguardar um pouco antes de tentar novamente

        except Exception as e:
            salvar_log(f"[ERRO] Falha ao processar ID {id_atual}: {type(e).__name__} - {str(e)}")
            if tentativa < tentativas - 1:
                salvar_log(f"[INFO] Tentando novamente ({tentativa + 1}/{tentativas})...")
                time.sleep(5)  # Aguardar antes de tentar novamente
            else:
                salvar_log(f"[ERRO] Todas as tentativas falharam para o ID {id_atual}.")
                return False

def retornar_pagina_inicial(driver, max_tentativas=3):
    for tentativa in range(max_tentativas):
        try:
            salvar_log("[INFO] Tentando retornar à página inicial...")

            botao_voltar_xpath = "//button[contains(@id, 'j_idt') and .//span[text()='Voltar']]"
            if clicar_botao(driver, botao_voltar_xpath):
                salvar_log("[INFO] Botão Voltar clicado com sucesso.")
                time.sleep(3)
                return True

            salvar_log(f"[ERRO] Tentativa {tentativa + 1}: Botão Voltar não encontrado. Tentando novamente...")

        except Exception as e:
            salvar_log(f"[ERRO] Tentativa {tentativa + 1}: Exceção ao tentar retornar à página inicial: {str(e)}")

        if tentativa < max_tentativas - 1:
            time.sleep(5)
            driver.refresh()  # Se falhar, recarrega a página e tenta de novo

    salvar_log("[ERRO] Todas as tentativas falharam ao retornar à página inicial.")
    return False

def verificar_pagina_inicial(driver):
    """ Confirma se a página inicial foi carregada após voltar. """
    try:
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.XPATH, "//table[contains(@id, 'tbDemandaAguardandoResposta_data')]"))
        )
        return True
    except TimeoutException:
        return False

def verificar_sessao_expirada(driver):
    """Verifica se a sessão ainda está ativa ou se a página de login foi carregada."""
    try:
        WebDriverWait(driver, 5).until(
            EC.presence_of_element_located((By.ID, "input-mask"))  # Campo de login
        )
        return True  # Sessão expirada
    except TimeoutException:
        return False  # Sessão ainda está ativa

def capturar_total_registros(driver):

    """ Captura o número total de registros e os registros exibidos na página atual. """
    try:
        elemento_paginacao = driver.find_element(By.CLASS_NAME, "ui-paginator-current")
        texto_paginacao = elemento_paginacao.text  # Exemplo: "Registros: 1 a 10 de 123"

        # 🔹 Extrai os números do texto usando regex
        numeros = list(map(int, re.findall(r'\d+', texto_paginacao)))

        if len(numeros) == 3:
            inicio, fim, total = numeros
            salvar_log(f"[INFO] Página atual exibe registros de {inicio} a {fim} de um total de {total}")
            return inicio, fim, total
        else:
            salvar_log("[ERRO] Formato inesperado na paginação. Não foi possível extrair os valores.")
            return None, None, None

    except Exception as e:
        salvar_log(f"[ERRO] Falha ao capturar total de registros: {str(e)}")
        return None, None, None

def executar_fluxo_principal(driver):
    """
    Executa o fluxo principal e finaliza a execução desta rodada quando:
      - Todos os registros foram processados;
      - Não há próxima página;
      - Ou os IDs já foram processados.
    """
    while True:
        if not aplicar_filtro_data(driver):
            salvar_log("[ERRO] Falha ao aplicar o filtro de datas. Recarregando a página...")
            driver.refresh()
            time.sleep(5)
            continue

        ids_processados = carregar_ids_processados()
        todos_ids_processados = True

        while True:  # Loop para percorrer todas as páginas disponíveis
            time.sleep(2)
            ids_pagina = capturar_ids_html(driver)

            if not ids_pagina:
                salvar_log("[INFO] Nenhum ID encontrado na página.")
                break  # Finaliza o loop de paginação

            # Filtra apenas IDs nas posições pares que ainda não foram processados
            ids_a_processar = [
                id_html for index, id_html in enumerate(ids_pagina)
                if index % 2 == 0 and id_html not in ids_processados
            ]

            if not ids_a_processar:
                salvar_log("[INFO] Todos os IDs desta página já foram processados.")
                todos_ids_processados = True
            else:
                todos_ids_processados = False
                for id_atual in ids_a_processar:
                    if id_existe_no_banco(id_atual):
                        salvar_log(f"[INFO] ID {id_atual} já existe no banco. Pulando...")
                        continue
                    salvar_log(f"[INFO] Iniciando processamento do ID {id_atual}")
                    if fluxo_processamento_id(driver, id_atual):
                        salvar_log(f"[INFO] ID {id_atual} processado com sucesso.")
                    else:
                        salvar_log(f"[ERRO] Falha ao processar o ID {id_atual}. Continuando...")

            # Captura a paginação para decidir se há mais registros
            inicio, fim, total = capturar_total_registros(driver)
            if inicio and fim and total:
                if fim >= total:
                    salvar_log("[INFO] Todos os registros já foram processados nesta rodada.")
                    return  # Encerra a execução deste fluxo

            # Tenta navegar para a próxima página; se não houver, encerra
            if not navegar_paginacao(driver):
                salvar_log("[INFO] Nenhuma próxima página disponível nesta rodada.")
                return  # Encerra a execução deste fluxo

        if todos_ids_processados:
            salvar_log("[INFO] Todos os IDs já foram processados nesta rodada.")
            return  # Encerra a execução deste fluxo

def main():
    """
    Função principal que gerencia o ciclo de execução do RPA.
    Ao final de cada rodada (sleep time), o navegador é fechado e o processo é reiniciado.
    """
    while True:
        salvar_log("[INFO] Iniciando nova rodada do RPA.")
        driver = iniciar_navegador()
        if driver:
            if not realizar_login(driver):
                salvar_log("[ERRO] Falha no login. Encerrando esta rodada.")
                driver.quit()
                # Se necessário, você pode sair ou tentar novamente.
                time.sleep(SLEEP_TIME)
                continue

            time.sleep(3)  # Aguarda alguns segundos após o login
            executar_fluxo_principal(driver)
        else:
            salvar_log("[ERRO] Falha ao iniciar o navegador.")

        # Fecha o navegador e entra em sleep time
        try:
            driver.quit()
        except Exception:
            pass

        salvar_log(f"[INFO] Rodada concluída. Entrando em sleep time de {SLEEP_TIME} segundos.")
        time.sleep(SLEEP_TIME)
        # Após o sleep, o loop reinicia e o processo é refeito

if __name__ == "__main__":
    main()
