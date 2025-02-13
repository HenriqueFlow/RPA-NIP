from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time

def login_monday(driver, email, password):
    """
    Realiza login manualmente preenchendo os campos de e-mail e senha.
    """
    wait = WebDriverWait(driver, 15)

    try:
        # Preencher o campo de e-mail
        email_input = wait.until(EC.presence_of_element_located((By.XPATH, '//input[@id="user_email"]')))
        email_input.clear()
        email_input.send_keys(email)
        print("E-mail preenchido.")

        # Preencher a senha
        password_input = wait.until(EC.presence_of_element_located((By.XPATH, '//input[@id="user_password"]')))
        password_input.clear()
        password_input.send_keys(password)
        print("Senha preenchida.")

        # Clicar no botão "Login"
        login_button = wait.until(EC.element_to_be_clickable((By.XPATH, '//button[contains(@class, "next-button submit_button")]')))
        login_button.click()
        print("Botão de login clicado.")

        # Aguarda o carregamento da página inicial
        time.sleep(5)
        print("Login concluído, página inicial carregada!")

    except Exception as e:
        print(f"Erro ao realizar login: {e}")
        print("Usuário já pode estar logado. Prosseguindo...")

def acessar_dashboard(driver, dashboard_url):
    """
    Acessa o dashboard através da página inicial.
    """
    try:
        # Aguarda a página carregar completamente antes de clicar no link do dashboard
        time.sleep(5)
        print(f"Acessando o dashboard: {dashboard_url}")
        driver.get(dashboard_url)
        time.sleep(5)
    except Exception as e:
        print(f"Erro ao acessar o dashboard: {e}")

# URLs dos dashboards do Monday.com
dashboards = [
    "https://saudeblue.monday.com/overviews/28996325",
    "https://saudeblue.monday.com/overviews/29024003",
    "https://saudeblue.monday.com/overviews/29011931"
]

# URL da página inicial do Monday.com
monday_login = "https://saudeblue.monday.com"

# Configurações do navegador para Raspberry Pi
options = webdriver.ChromeOptions()
options.binary_location = "/usr/bin/chromium-browser"
options.add_argument("--no-sandbox")
options.add_argument("--disable-dev-shm-usage")
options.add_argument("--disable-gpu")
options.add_argument("--headless")  # Modo sem interface gráfica para otimizar recursos
options.add_argument("--window-size=1920,1080")

# Caminho do ChromeDriver no Raspberry Pi
chromedriver_path = "/usr/bin/chromedriver"

# Inicializa o driver do Chrome
driver = webdriver.Chrome(executable_path=chromedriver_path, options=options)

# Suas credenciais do Monday.com
EMAIL = "henrique.barreto@saudeblue.com"
PASSWORD = "SUA_SENHA"

# Acessa a página inicial de login e faz login
print("Abrindo página de login do Monday...")
driver.get(monday_login)
time.sleep(5)  # Aguarda carregamento inicial
login_monday(driver, EMAIL, PASSWORD)

# Aguarda 1 minuto para garantir que o login foi feito corretamente
print("Aguardando 1 minuto para garantir o login...")
time.sleep(60)

# Abre os 3 dashboards em novas abas
print("Abrindo dashboards...")
for url in dashboards:
    try:
        driver.execute_script(f"window.open('{url}', '_blank');")
        time.sleep(5)
    except Exception as e:
        print(f"Erro ao abrir {url}: {e}")

# Fecha a primeira aba (página de login)
abas = driver.window_handles  # Obtém todas as abas abertas
if len(abas) > 1:
    driver.switch_to.window(abas[0])
    driver.close()
    print("Aba da página de login fechada.")

# Atualiza a lista de abas restantes
driver.switch_to.window(driver.window_handles[0])
abas = driver.window_handles

# Loop infinito para alternar entre as abas a cada 5 minutos
print("Iniciando loop infinito para alternar entre dashboards...")
while True:
    for aba in abas:
        driver.switch_to.window(aba)
        print(f"Exibindo a aba: {aba}")
        time.sleep(300)  # Aguarda 5 minutos antes de trocar para a próxima aba
