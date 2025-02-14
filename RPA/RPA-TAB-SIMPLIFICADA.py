from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time

def iniciar_driver():
    """Configura e inicia o Chrome no modo Kiosk para Raspberry Pi 3 (Legacy 32-bit)."""
    options = webdriver.ChromeOptions()
    options.binary_location = "/usr/bin/chromium-browser"

    # Modo Kiosk (Tela cheia sem barras de navegação)
    options.add_argument("--kiosk")

    # Ajustes para Raspberry Pi 3 (Legacy 32-bit)
    options.add_argument("--disable-gpu")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-background-timer-throttling")
    options.add_argument("--disable-renderer-backgrounding")
    options.add_argument("--disable-sync-preferences")
    options.add_argument("--disable-sync")
    options.add_argument("--disable-infobars")
    options.add_argument("--disable-extensions")
    options.add_argument("--disable-notifications")
    options.add_argument("--mute-audio")
    options.add_argument("--start-maximized")
    options.add_argument("--disable-features=VizDisplayCompositor")

    chromedriver_path = "/usr/bin/chromedriver"
    return webdriver.Chrome(executable_path=chromedriver_path, options=options)

def login_monday(driver, email, password):
    """Realiza login manualmente preenchendo os campos de e-mail e senha."""
    wait = WebDriverWait(driver, 20)

    try:
        email_input = wait.until(EC.presence_of_element_located((By.XPATH, '//input[@id="user_email"]')))
        email_input.clear()
        email_input.send_keys(email)
        print("E-mail preenchido.")

        password_input = wait.until(EC.presence_of_element_located((By.XPATH, '//input[@id="user_password"]')))
        password_input.clear()
        password_input.send_keys(password)
        print("Senha preenchida.")

        login_button = wait.until(EC.element_to_be_clickable((By.XPATH, '//button[contains(@class, "next-button submit_button")]')))
        login_button.click()
        print("Botão de login clicado.")

        time.sleep(5)
        print("Login concluído!")

    except Exception as e:
        print(f"Erro ao fazer login: {e}")

# URLs dos dashboards do Monday.com
dashboards = [
    "https://saudeblue.monday.com/overviews/28996325",  # Primeiro link (onde será feito login)
    "https://saudeblue.monday.com/overviews/29024003",  # Segundo link (sem login)
    "https://saudeblue.monday.com/overviews/29011931"   # Terceiro link (sem login)
]

# Inicializa o WebDriver no modo Kiosk
driver = iniciar_driver()

# Suas credenciais do Monday.com
EMAIL = "henrique.barreto@saudeblue.com"
PASSWORD = "SUA_SENHA"

# 1️⃣ **Abre o primeiro link e realiza o login**
print(f"Abrindo primeiro link para login: {dashboards[0]}")
driver.get(dashboards[0])
time.sleep(5)  # Aguarda carregamento inicial
login_monday(driver, EMAIL, PASSWORD)

# 2️⃣ **Aguarda 1 minuto antes de abrir o segundo link**
print("Aguardando 1 minuto para estabilizar o login...")
time.sleep(60)

# 3️⃣ **Abre o segundo link (sem necessidade de login)**
print(f"Abrindo segundo link: {dashboards[1]}")
driver.execute_script(f"window.open('{dashboards[1]}', '_blank');")
time.sleep(60)  # Aguarda 1 minuto antes de abrir o próximo

# 4️⃣ **Abre o terceiro link**
print(f"Abrindo terceiro link: {dashboards[2]}")
driver.execute_script(f"window.open('{dashboards[2]}', '_blank');")
time.sleep(60)  # Aguarda 1 minuto antes de iniciar a rotação

# 5️⃣ **Loop infinito para alternar entre os dashboards**
print("Iniciando loop de alternância entre dashboards...")
abas = driver.window_handles  # Obtém todas as abas abertas

while True:
    for aba in abas:
        driver.switch_to.window(aba)
        print(f"Exibindo dashboard: {aba}")
        time.sleep(300)  # Espera 5 minutos antes de alternar
