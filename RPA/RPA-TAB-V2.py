from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.service import Service
import time
import shutil

# Configuração dos caminhos para Chromium e ChromeDriver no Raspberry Pi
CHROMIUM_BINARY = "/usr/bin/chromium-browser"
CHROMEDRIVER_BINARY = "/usr/bin/chromedriver"

# Verifica se o Chromium e o ChromeDriver estão instalados
if not shutil.which(CHROMIUM_BINARY):
    raise FileNotFoundError(f"Erro: Chromium não encontrado em {CHROMIUM_BINARY}. Instale com: sudo apt install chromium-browser")
if not shutil.which(CHROMEDRIVER_BINARY):
    raise FileNotFoundError(f"Erro: ChromeDriver não encontrado em {CHROMEDRIVER_BINARY}. Instale com: sudo apt install chromium-chromedriver")

# Configuração do navegador para Raspberry Pi
options = webdriver.ChromeOptions()
options.binary_location = CHROMIUM_BINARY  # Definir caminho explícito do navegador
options.add_argument("--no-sandbox")
options.add_argument("--disable-dev-shm-usage")
options.add_argument("--disable-gpu")
options.add_argument("--window-size=1920,1080")
options.add_argument("--disable-software-rasterizer")
options.add_argument("--remote-debugging-port=9222")
options.add_argument("--disable-extensions")
options.add_argument("--disable-infobars")
options.add_argument("--disable-notifications")
options.add_argument("--mute-audio")

# Definir o idioma do navegador para PT-BR
options.add_argument("--lang=pt-BR")

#Definir User-Agent para PT-BR (ajuda em alguns casos)
options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0.0.0 Safari/537.36")

# Inicializa o driver do Chrome corretamente para Selenium 4+
service = Service(CHROMEDRIVER_BINARY)
driver = webdriver.Chrome(service=service, options=options)

def login_monday_google(driver, email, password):
    """
    Realiza login via Google na página inicial do Monday.com.
    Aguarda corretamente cada etapa e só prossegue após o login ser bem-sucedido.
    """
    wait = WebDriverWait(driver, 20)

    try:
        # Verifica se a tela de login apareceu
        google_button = wait.until(
            EC.element_to_be_clickable((By.XPATH, '//button[@class="social-login-provider"]'))
        )
        print("Botão 'Fazer login com Google' encontrado, clicando...")
        google_button.click()

        # Preencher o campo de e-mail
        email_input = wait.until(EC.presence_of_element_located((By.NAME, "identifier")))
        email_input.clear()
        email_input.send_keys(email)

        # Clicar no botão "Próxima" (PT-BR ou EN)
        next_btn = wait.until(EC.element_to_be_clickable(
            (By.XPATH, '//span[text()="Próxima"]/ancestor::button | //span[text()="Next"]/ancestor::button')
        ))
        next_btn.click()
        print("E-mail preenchido e avançado.")

        time.sleep(2)

        # Preencher a senha
        password_input = wait.until(EC.presence_of_element_located((By.NAME, "Passwd")))
        password_input.clear()
        password_input.send_keys(password)

        # Clicar no botão "Próxima" (PT-BR ou EN)
        next_btn = wait.until(EC.element_to_be_clickable(
            (By.XPATH, '//span[text()="Próxima"]/ancestor::button | //span[text()="Next"]/ancestor::button')
        ))
        next_btn.click()
        print("Senha preenchida e avançado.")

        # Aguarda a página carregar completamente
        time.sleep(5)
        print("Login via Google concluído!")

        #**Validação do login na Monday**
        login_success = verificar_login(driver)
        if not login_success:
            print("ERRO: Login não foi concluído corretamente! Encerrando...")
            driver.quit()
            return False

        return True

    except Exception as e:
        print(f"Erro durante o login: {e}")
        driver.quit()
        return False


def verificar_login(driver):
    """
    Verifica se o login foi realmente bem-sucedido, esperando um elemento específico da Monday.
    Retorna True se o login foi confirmado, False caso contrário.
    """
    wait = WebDriverWait(driver, 20)
    try:
        wait.until(EC.presence_of_element_located((By.XPATH, '//div[contains(@class, "board-header")]')))
        print("Login confirmado na Monday.com!")
        return True
    except Exception:
        print("Falha ao verificar login. Pode ser que as credenciais estejam incorretas.")
        return False


# URLs dos dashboards do Monday.com
dashboards = [
    "https://saudeblue.monday.com/overviews/28996325",
    "https://saudeblue.monday.com/overviews/29024003",
    "https://saudeblue.monday.com/overviews/29011931"
]

# URL da página inicial do Monday.com
monday_home = "https://saudeblue.monday.com"

# Suas credenciais do Google
EMAIL = "henrique.barreto@saudeblue.com"
PASSWORD = "gd1d@yfh."

# 1️Abre a página inicial da Monday e faz login
print("Acessando página inicial da Monday para login...")
driver.get(monday_home)
time.sleep(5)  # Aguarda carregamento inicial

if login_monday_google(driver, EMAIL, PASSWORD):
    # 2Aguarda confirmação do login antes de abrir os dashboards
    print("✅ Login realizado com sucesso! Abrindo dashboards...")

    for url in dashboards:
        try:
            driver.execute_script(f"window.open('{url}', '_blank');")
            time.sleep(5)  # Pequeno delay entre cada abertura
        except Exception as e:
            print(f"Erro ao abrir {url}: {e}")

    #Fecha a primeira aba (página inicial da Monday)
    abas = driver.window_handles  # Obtém todas as abas abertas
    if len(abas) > 1:
        driver.switch_to.window(abas[0])  # Muda para a primeira aba
        driver.close()  # Fecha a primeira aba
        print("Aba da página inicial fechada.")

    # Atualiza a lista de abas restantes
    driver.switch_to.window(driver.window_handles[0])
    abas = driver.window_handles

    # 4️Loop infinito para alternar entre as abas a cada 5 minutos
    print("Iniciando loop para alternar entre dashboards...")
    while True:
        for aba in abas:
            driver.switch_to.window(aba)
            print(f"Exibindo a aba: {aba}")
            time.sleep(300)  # Aguarda 5 minutos antes de trocar para a próxima aba

else:
    print("O login falhou! O script foi encerrado.")
    driver.quit()
