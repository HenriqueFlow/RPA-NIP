from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time

def login_monday_google(driver, email, password):
    """
    Realiza login via Google na página inicial do Monday.com.
    Aguarda corretamente cada etapa e só prossegue após o login ser bem-sucedido.
    """
    wait = WebDriverWait(driver, 15)

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

        # Clicar no botão "Próxima"
        next_btn = wait.until(EC.element_to_be_clickable((By.XPATH, '//span[text()="Próxima"]/ancestor::button')))
        next_btn.click()
        print("E-mail preenchido e avançado.")

        time.sleep(2)

        # Preencher a senha
        password_input = wait.until(EC.presence_of_element_located((By.NAME, "Passwd")))
        password_input.clear()
        password_input.send_keys(password)

        # Clicar no botão "Próxima"
        next_btn = wait.until(EC.element_to_be_clickable((By.XPATH, '//span[text()="Próxima"]/ancestor::button')))
        next_btn.click()
        print("Senha preenchida e avançado.")

        # Aguarda a página carregar completamente
        time.sleep(5)
        print("Login via Google concluído!")

    except Exception:
        print("Usuário já está logado! Prosseguindo...")

# URLs dos dashboards do Monday.com
dashboards = [
    "https://saudeblue.monday.com/overviews/28996325",
    "https://saudeblue.monday.com/overviews/29024003",
    "https://saudeblue.monday.com/overviews/29011931"
]

# URL da página inicial do Monday.com (onde será feito o login)
monday_home = "https://saudeblue.monday.com"

# Configurações do navegador para Raspberry Pi
options = webdriver.ChromeOptions()
options.add_argument('--no-sandbox')
options.add_argument('--disable-dev-shm-usage')
# options.add_argument('--headless')  # Descomente se quiser rodar sem interface gráfica

driver = webdriver.Chrome(options=options)  # Certifique-se de ter o chromedriver instalado

# Suas credenciais do Google
EMAIL = "henrique.barreto@saudeblue.com"
PASSWORD = "GD1D@yFh.g"

# Abre a página inicial da Monday e faz login
print("Abrindo página inicial da Monday para login...")
driver.get(monday_home)
time.sleep(5)  # Aguarda carregamento inicial
login_monday_google(driver, EMAIL, PASSWORD)

# Aguarda 1 minuto para garantir que o login foi feito corretamente
print("Aguardando 1 minuto para garantir o login...")
time.sleep(60)

# Abre os 3 dashboards em novas abas
print("Abrindo dashboards...")
for url in dashboards:
    driver.execute_script(f"window.open('{url}', '_blank');")
    time.sleep(5)  # Pequeno delay entre cada abertura

# Fecha a primeira aba (página inicial da Monday)
abas = driver.window_handles  # Obtém todas as abas abertas
if len(abas) > 1:
    driver.switch_to.window(abas[0])  # Muda para a primeira aba
    driver.close()  # Fecha a primeira aba
    print("Aba da página inicial fechada.")

# Atualiza a lista de abas restantes
driver.switch_to.window(driver.window_handles[0])  # Garante que estamos na primeira aba útil
abas = driver.window_handles

# Loop infinito para alternar entre as abas a cada 5 minutos
print("Iniciando loop infinito para alternar entre dashboards...")
while True:
    for aba in abas:
        driver.switch_to.window(aba)
        print(f"Exibindo a aba: {aba}")
        time.sleep(300)  # Aguarda 5 minutos antes de trocar para a próxima aba
