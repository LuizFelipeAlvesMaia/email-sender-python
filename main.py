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


# Função para consultar a API e obter a data de criação do changelog mais recente
def get_latest_changelog_update(api_key, doc_url, title):
    url = "https://dash.readme.com/api/v1/changelogs"
    headers = {"Authorization": f"Basic {api_key}"}
    response = requests.get(url, headers=headers)
    changelogs = response.json()

    if not changelogs:
        print("Nenhum changelog encontrado.")
        return None

    # Procura pelo changelog com o título especificado
    latest_changelog = None
    for changelog in changelogs:
        if changelog.get("title") == title:
            latest_changelog = changelog
            break

    if not latest_changelog:
        print(f"Documentação '{doc_url}' não encontrada.")
        return None

    # Tenta obter updatedAt da resposta da API
    updated_at = latest_changelog.get("updatedAt")

    # Se updatedAt não estiver presente, retorna mensagem personalizada
    if not updated_at:
        return f"Documentação '{doc_url}' está desatualizada."

    updated_at = datetime.strptime(updated_at, "%Y-%m-%dT%H:%M:%S.%fZ")
    return updated_at


# Função para atualizar o banco de dados com o novo changelog
def update_changelog_in_db(changelog_id, update_at):
    try:
        connection = psycopg2.connect(
            user=os.getenv("DB_USER"),
            password=os.getenv("DB_PASSWORD"),
            host=os.getenv("DB_HOST"),
            port=os.getenv("DB_PORT"),
            database=os.getenv("DB_NAME"),
        )
        cursor = connection.cursor()

        if isinstance(update_at, str):
            print(update_at)
            return None

        # Consultar o URL da documentação no banco de dados
        cursor.execute("SELECT doc_url FROM changelogs WHERE id = %s;", (changelog_id,))
        doc_url = cursor.fetchone()[0]

        # Consultar a data mais recente no banco de dados
        cursor.execute(
            "SELECT updated_at FROM changelogs WHERE id = %s;", (changelog_id,)
        )
        record = cursor.fetchone()

        if record:
            last_updated = record[0]

            if update_at > last_updated:
                # Atualizar o banco de dados com o novo changelog
                cursor.execute(
                    "UPDATE changelogs SET updated_at = %s WHERE id = %s;",
                    (update_at, changelog_id),
                )
                connection.commit()
                print(
                    f"Tabela de changelogs atualizada com sucesso para Documentação: {doc_url}."
                )
                return doc_url
            else:
                print(f"A documentação: {doc_url} não teve alterações recentes.")
                return None
        else:
            # Inserir o primeiro registro se não houver nenhum
            cursor.execute(
                "UPDATE changelogs SET updated_at = %s WHERE id = %s;",
                (update_at, changelog_id),
            )
            connection.commit()
            print(
                f"Tabela de changelogs criada com sucesso para Documentação: {doc_url}."
            )
            return doc_url

    except (Exception, Error) as error:
        print("Erro ao conectar ao PostgreSQL:", error)
        return None

    finally:
        if connection:
            cursor.close()
            connection.close()
            print("Conexão ao PostgreSQL encerrada.")


# Função para enviar email aos usuários
def send_email(user_email, documentation_link):
    sender_email = os.getenv("EMAIL_USER")
    password = os.getenv("EMAIL_PASSWORD")

    message = MIMEMultipart()
    message["From"] = sender_email
    message["To"] = user_email
    message["Subject"] = "Atualização de Documentação"
    context = ssl.create_default_context()
    # Construir o conteúdo HTML do e-mail
    html_content = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        <meta http-equiv="X-UA-Compatible" content="IE=edge">
        <title>Atualização de Documentação</title>
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <style>
            body {{
                font-family: Arial, sans-serif;
                background-color: #f4f4f4;
                margin: 0;
                padding: 0;
            }}
            .container {{
        width: 100%;
        max-width: 600px;
        margin: 0 auto;
        padding: 20px;
        background-color: #ffffff;
        border-radius: 10px;
        box-shadow: 0 0 10px rgba(0, 0, 0, 0.1);
            }}
            .header {{
        background-color: #007bff;
        color: #ffffff;
        text-align: center;
        padding: 10px;
        border-top-left-radius: 10px;
        border-top-right-radius: 10px;
            }}
            .content {{
                padding: 20px;
            }}
            .footer {{
                text-align: center;
                padding-top: 10px;
                color: #777777;
                font-size: 12px;
            }}
            .button-container {{
                text-align: center;
                margin-top: 15px;
            }}
            .button {{
                display: inline-block;
                background-color: #007bff;
                color: #ffffff;
                text-decoration: none;
                padding: 10px 20px;
                border-radius: 5px;
                font-weight: bold;
            }}
            .button:hover {{
                background-color: #0056b3;
            }}
            .button a {{
                color: #ffffff;
                text-decoration: none;
            }}

        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h1>Atualização de Documentação</h1>
            </div>
            <div class="content">
                <p>Olá,</p>
                <p>A documentação da nossa aplicação foi atualizada. Confira os detalhes abaixo:</p>
                <p><a href="{documentation_link}" class="button">Ver Documentação</a></p>
                <p>Atenciosamente,<br>QESH</br></p>
            </div>
            <div class="footer">
                <p>Este é um e-mail automático. Por favor, não responda.</p>
            </div>
        </div>
    </body>
    </html>
    """

    message.attach(MIMEText(html_content, "html"))

    try:
        with smtplib.SMTP_SSL("smtp.gmail.com", 465, context=context) as server:
            server.login(sender_email, password)
            server.sendmail(sender_email, user_email, message.as_string())
        print(f"Email enviado para {user_email}")
    except Exception as e:
        print(f"Erro ao enviar email para {user_email}: {e}")


# Função principal para coordenar o processo
def main():
    try:
        connection = psycopg2.connect(
            user=os.getenv("DB_USER"),
            password=os.getenv("DB_PASSWORD"),
            host=os.getenv("DB_HOST"),
            port=os.getenv("DB_PORT"),
            database=os.getenv("DB_NAME"),
        )
        cursor = connection.cursor()

        # Consultar todas as chaves de API e URLs de documentação
        cursor.execute("SELECT id, api_keys, doc_url, title FROM changelogs;")
        changelogs = cursor.fetchall()

        for changelog_id, api_key, doc_url, title in changelogs:
            # Obter a data de atualização mais recente do changelog
            update_at = get_latest_changelog_update(api_key, doc_url, title)

            if update_at:
                # Atualizar o banco de dados se houver um changelog mais recente
                if update_changelog_in_db(changelog_id, update_at):
                    # Consultar usuários no banco de dados e enviar email de notificação
                    cursor.execute("SELECT email FROM users;")
                    users = cursor.fetchall()

                    for user in users:
                        user_email = user[0]
                        send_email(user_email, doc_url)

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
