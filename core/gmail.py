from google.auth.transport.requests import Request
from google.auth.exceptions import RefreshError
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

from email.mime.text import MIMEText

from bs4 import BeautifulSoup

import base64
import quopri
import re
import os


SCOPES = [
    "https://www.googleapis.com/auth/gmail.modify"
]


BASE_DIR = os.path.dirname(
    os.path.dirname(
        os.path.abspath(__file__)
    )
)

CREDENTIALS = os.path.join(
    BASE_DIR,
    "credentials.json"
)

TOKEN = os.path.join(
    BASE_DIR,
    "token.json"
)


# ======================================
# LOGIN
# ======================================

def login_gmail():

    creds = None

    if os.path.exists(TOKEN):

        creds = Credentials.from_authorized_user_file(
            TOKEN,
            SCOPES
        )

    if not creds or not creds.valid:

        necesita_login_nuevo = True

        if creds and creds.expired and creds.refresh_token:

            try:

                creds.refresh(Request())

                necesita_login_nuevo = False

            except RefreshError:

                # El refresh token quedó inválido/revocado
                # (por ejemplo, expiró por estar la app en modo
                # "Testing" en Google Cloud, o fue revocado a mano).
                # Borramos el token viejo y forzamos re-autenticación
                # en vez de quedar reintentando un token muerto en
                # cada request.

                if os.path.exists(TOKEN):

                    os.remove(TOKEN)

                creds = None

        if necesita_login_nuevo:

            flow = InstalledAppFlow.from_client_secrets_file(
                CREDENTIALS,
                SCOPES
            )

            creds = flow.run_local_server(port=0)

        with open(TOKEN, "w") as token:

            token.write(creds.to_json())

    return creds


# ======================================
# SERVICIO
# ======================================

def obtener_servicio():

    creds = login_gmail()

    return build(
        "gmail",
        "v1",
        credentials=creds
    )


# ======================================
# LISTAR
# ======================================

def listar_correos(cantidad=10):

    service = obtener_servicio()

    respuesta = service.users().messages().list(
        userId="me",
        maxResults=cantidad
    ).execute()

    return respuesta.get(
        "messages",
        []
    )


# ======================================
# ENVIAR
# ======================================
def enviar_correo(
    destinatario,
    asunto,
    mensaje,
    thread_id=None,
    message_id=None
):

    service = obtener_servicio()

    mime = MIMEText(
        mensaje,
        "plain",
        "utf-8"
    )

    mime["To"] = destinatario
    mime["Subject"] = asunto


    if message_id:

        mime["In-Reply-To"] = message_id
        mime["References"] = message_id


    raw = base64.urlsafe_b64encode(
        mime.as_bytes()
    ).decode()


    body = {
        "raw": raw
    }


    if thread_id:

        body["threadId"] = thread_id


    respuesta = service.users().messages().send(
        userId="me",
        body=body
    ).execute()


    return {
        "message_id": respuesta.get("id"),
        "thread_id": respuesta.get("threadId")
    }
# ======================================
# OBTENER MENSAJE
# ======================================

def obtener_correo(id_mensaje):

    service = obtener_servicio()

    return service.users().messages().get(
        userId="me",
        id=id_mensaje,
        format="full"
    ).execute()


# ======================================
# OBTENER HEADER
# ======================================

def obtener_encabezado(
    mensaje,
    nombre
):

    headers = mensaje["payload"].get(
        "headers",
        []
    )

    for header in headers:

        if header["name"] == nombre:

            return header["value"]

    return ""
# ======================================
# OBTENER TEXTO DEL MENSAJE
# ======================================

def obtener_texto(mensaje):

    payload = mensaje.get(
        "payload",
        {}
    )


    def extraer(parte):

        mime = parte.get(
            "mimeType",
            ""
        )


        # ==========================
        # multipart/*
        # ==========================

        if "parts" in parte:

            for subparte in parte["parts"]:

                resultado = extraer(
                    subparte
                )

                if resultado:

                    return resultado


        # ==========================
        # text/plain
        # ==========================

        if mime == "text/plain":

            data = parte.get(
                "body",
                {}
            ).get("data")

            if data:

                return base64.urlsafe_b64decode(
                    data
                ).decode(
                    "utf-8",
                    errors="ignore"
                )


        # ==========================
        # text/html
        # ==========================

        if mime == "text/html":

            data = parte.get(
                "body",
                {}
            ).get("data")

            if data:

                html = base64.urlsafe_b64decode(
                    data
                ).decode(
                    "utf-8",
                    errors="ignore"
                )

                return BeautifulSoup(
                    html,
                    "html.parser"
                ).get_text("\n")


        return ""


    if "parts" in payload:

        texto = extraer(
            payload
        )

    else:

        data = payload.get(
            "body",
            {}
        ).get("data")

        texto = ""

        if data:

            texto = base64.urlsafe_b64decode(
                data
            ).decode(
                "utf-8",
                errors="ignore"
            )


    # ==========================
    # Quoted Printable
    # ==========================

    try:

        texto = quopri.decodestring(
            texto
        ).decode(
            "utf-8",
            errors="ignore"
        )

    except Exception:

        pass


    # ==========================
    # Caracteres especiales
    # ==========================

    texto = texto.replace(
        "\\u000A",
        "\n"
    )

    texto = texto.replace(
        "\\u000D",
        ""
    )

    texto = texto.replace(
        "\r",
        ""
    )

    texto = texto.replace(
        "\xa0",
        " "
    )


    # Intentar corregir acentos dañados

    try:

        texto = texto.encode(
            "latin1"
        ).decode(
            "utf-8"
        )

    except Exception:

        pass


    # ==========================
    # Eliminar líneas citadas
    # ==========================

    texto = re.sub(
        r"^>.*$",
        "",
        texto,
        flags=re.MULTILINE
    )


    # ==========================
    # Cortar historial Gmail
    # ==========================

    patrones = [

        r"\nEl .* escribió:",

        r"\nOn .* wrote:",

        r"\nDe: .*",

        r"\nFrom: .*",

        r"\nEnviado desde .*",

        r"\n---------- Forwarded message ----------",

    ]


    for patron in patrones:

        partes = re.split(

            patron,

            texto,

            maxsplit=1,

            flags=re.IGNORECASE | re.DOTALL

        )

        texto = partes[0]


    # ==========================
    # Limpiar saltos
    # ==========================

    texto = re.sub(

        r"\n{3,}",

        "\n\n",

        texto

    )


    return texto.strip()
def obtener_hilo(thread_id):

    service = obtener_servicio()

    hilo = service.users().threads().get(
        userId="me",
        id=thread_id,
        format="full"
    ).execute()

    return hilo