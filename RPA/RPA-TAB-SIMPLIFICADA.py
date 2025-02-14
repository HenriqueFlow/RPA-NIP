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

    # Se precisar rodar sem interface gráfica (headless)
    # options.add_argument("--headless=new")

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
    "https://saudeblue.monday.com/overviews/28996325",
    "https://saudeblue.monday.com/overviews/29024003",
    "https://saudeblue.monday.com/overviews/29011931"
]

# Inicializa o WebDriver no modo Kiosk
driver = iniciar_driver()

# Suas credenciais do Monday.com
EMAIL = "henrique.barreto@saudeblue.com"
PASSWORD = "SUA_SENHA"

# 1️⃣ **Abre todas as abas dos dashboards de uma vez**
print("Abrindo dashboards diretamente...")
for url in dashboards:
    try:
        driver.execute_script(f"window.open('{url}', '_blank');")
        time.sleep(5)
    except Exception as e:
        print(f"Erro ao abrir {url}: {e}")

# 2️⃣ **Alterna para a primeira aba e realiza o login**
print("Alternando para a primeira aba para realizar o login...")
abas = driver.window_handles
driver.switch_to.window(abas[0])
login_monday(driver, EMAIL, PASSWORD)

# 3️⃣ **Loop infinito para alternar entre os dashboards**
print("Iniciando loop de alternância entre dashboards...")
while True:
    for aba in abas:
        driver.switch_to.window(aba)
        print(f"Exibindo dashboard: {aba}")
        time.sleep(300)  # Espera 5 minutos antes de alternar
