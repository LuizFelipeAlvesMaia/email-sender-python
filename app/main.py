import os
import requests
import psycopg2
import smtplib, ssl
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from psycopg2 import Error
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

# Função para consultar a API e obter o updatedAt do changelog mais recente
def get_latest_changelog_update():
    url = "https://dash.readme.com/api/v1/changelogs"
    headers = {
        "Authorization": "Basic cmRtZV94bjhzOWhkOTJmZmM0OTNlODI2ODEwNGQ1MWU4MTYyYzFkODRhNzJiY2JkODE0OTRlNjdhYTg5N2JkMGFiZmI4ZTEyOGI5Og=="
    }
    response = requests.get(url, headers=headers)
    changelogs = response.json()

    if not changelogs:
        print("Nenhum changelog encontrado.")
        return None

    latest_changelog = changelogs[0]
    update_at = latest_changelog.get("updatedAt")
    update_at = datetime.strptime(update_at, "%Y-%m-%dT%H:%M:%S.%fZ")
    return update_at

# Função para atualizar o banco de dados com o novo changelog
def update_changelog_in_db(update_at):
    try:
        connection = psycopg2.connect(
            user=os.getenv("DB_USER"),
            password=os.getenv("DB_PASSWORD"),
            host=os.getenv("DB_HOST"),
            port=os.getenv("DB_PORT"),
            database=os.getenv("DB_NAME"),
        )
        cursor = connection.cursor()

        # Consultar a data mais recente no banco de dados
        cursor.execute(
            "SELECT updated_at FROM changelogs ORDER BY updated_at DESC LIMIT 1;"
        )
        record = cursor.fetchone()

        if record:
            last_updated = record[0]

            if update_at > last_updated:
                # Atualizar o banco de dados com o novo changelog
                cursor.execute(
                    "UPDATE changelogs SET updated_at = %s WHERE id = %s;",
                    (update_at, 1),
                )
                connection.commit()
                print("Tabela de changelogs atualizada com sucesso.")
                return True
            else:
                print("A documentação ainda não foi atualizada.")
                return False
        else:
            # Inserir o primeiro registro se não houver nenhum
            cursor.execute(
                "INSERT INTO changelogs (id, updated_at) VALUES (%s, %s);",
                (1, update_at),
            )
            connection.commit()
            print("Tabela de changelogs criada com sucesso.")
            return True

    except (Exception, Error) as error:
        print("Erro ao conectar ao PostgreSQL:", error)
        return False

    finally:
        if connection:
            cursor.close()
            connection.close()
            print("Conexão ao PostgreSQL encerrada.")

# Função para enviar email aos usuários
def send_email(user_email, documentation_link):
    sender_email = os.getenv("EMAIL_USER"
    password = os.getenv("EMAIL_PASSWORD")

    message = MIMEMultipart()
    message["From"] = sender_email
    message["To"] = user_email
    message["Subject"] = "Atualização de Documentação"
    context = ssl.create_default_context()
    body = f"""
    Olá,

    A documentação foi atualizada. Confira os detalhes aqui: {documentation_link}

    Atenciosamente,
    Sua Aplicação
    """

    message.attach(MIMEText(body, "plain"))

    try:
        with smtplib.SMTP_SSL("smtp.gmail.com", 465, context=context) as server:
            server.login(sender_email, password)
            server.sendmail(sender_email, user_email, message.as_string())
        print(f"Email enviado para {user_email}")
    except Exception as e:
        print(f"Erro ao enviar email para {user_email}: {e}")

# Função principal para coordenar o processo
def main():
    # Obter a data de atualização mais recente do changelog
    update_at = get_latest_changelog_update()

    if update_at:
        # Atualizar o banco de dados se houver um changelog mais recente
        if update_changelog_in_db(update_at):
            # Consultar usuários no banco de dados e enviar email de notificação
            try:
                connection = psycopg2.connect(
                    user=os.getenv("DB_USER"),
                    password=os.getenv("DB_PASSWORD"),
                    host=os.getenv("DB_HOST"),
                    port=os.getenv("DB_PORT"),
                    database=os.getenv("DB_NAME"),
                )
                cursor = connection.cursor()

                cursor.execute("SELECT email FROM users;")
                users = cursor.fetchall()

                for user in users:
                    user_email = user[0]
                    documentation_link = "https://link_da_documentacao.com"  # Substituir pelo link real da documentação
                    send_email(user_email, documentation_link)

            except (Exception, Error) as error:
                print("Erro ao conectar ao PostgreSQL:", error)

            finally:
                if connection:
                    cursor.close()
                    connection.close()
                    print("Conexão ao PostgreSQL encerrada.")

# Executar o programa principal
if __name__ == "__main__":
    main()
