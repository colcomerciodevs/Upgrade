#!/usr/bin/env python3

import argparse
import io
import json
import os
import re
import sys
from urllib.parse import quote

import requests
from openpyxl import load_workbook


# ============================================================
# CONFIGURACIÓN DEL INVENTARIO SLES15 GEOPOS
# ============================================================

TENANT_ID = os.getenv("TENANT_ID")
CLIENT_ID = os.getenv("CLIENT_ID")
CLIENT_SECRET = os.getenv("CLIENT_SECRET")

SHAREPOINT_HOST = "colcomerciocom.sharepoint.com"
SHAREPOINT_SITE_PATH = "/sites/AreaInfraestructura"

# La biblioteca "Documentos compartidos" es el drive principal del sitio.
# Por eso la ruta comienza después de "Documentos compartidos".
EXCEL_PATH = (
    "General/Inventario Infraestructura/"
    "Inventario_SLES15_GeoPOS_Upgrade.xlsx"
)

SHEET_NAME = "SLES15 GeoPOS"

HOSTNAME_COLUMN = "HostName"


# Columnas Excel -> variables Ansible
COMPOSE = {
    "ambiente": "Ambiente",
    "ansible_host": "IPv4Address",
    "crq": "CRQ",
    "hostname": "HostName",
    "ip": "IPv4Address",
    "location": "UBICACIÓN",
    "lote": "Lote",
    "os": "SISTEMA OPERATIVO",
    "type_os": "TIPO SO",
}


# ============================================================
# UTILIDADES
# ============================================================

def fail(message):
    print(f"ERROR: {message}", file=sys.stderr)
    sys.exit(1)


def normalize_value(value):
    """Convierte valores de Excel a tipos seguros para JSON."""
    if value is None:
        return ""

    if isinstance(value, str):
        return value.strip()

    return value


def safe_group_name(value):
    """
    Convierte el valor de Lote en nombre válido para grupo Ansible.

    Ejemplo:
        Lote 1 -> lote_1
        Lote-02 -> lote_02
    """
    value = str(value).strip().lower()
    value = re.sub(r"[^a-zA-Z0-9_]+", "_", value)
    value = value.strip("_")

    if not value:
        return None

    return f"lote_{value}"


# ============================================================
# AUTENTICACIÓN MICROSOFT GRAPH
# ============================================================

def get_access_token():
    if not TENANT_ID:
        fail("Variable de entorno TENANT_ID no definida")

    if not CLIENT_ID:
        fail("Variable de entorno CLIENT_ID no definida")

    if not CLIENT_SECRET:
        fail("Variable de entorno CLIENT_SECRET no definida")

    token_url = (
        f"https://login.microsoftonline.com/"
        f"{TENANT_ID}/oauth2/v2.0/token"
    )

    data = {
        "client_id": CLIENT_ID,
        "client_secret": CLIENT_SECRET,
        "scope": "https://graph.microsoft.com/.default",
        "grant_type": "client_credentials",
    }

    try:
        response = requests.post(
            token_url,
            data=data,
            timeout=30,
        )

        response.raise_for_status()

    except requests.RequestException as exc:
        fail(f"No fue posible autenticarse contra Microsoft Graph: {exc}")

    token = response.json().get("access_token")

    if not token:
        fail("Microsoft Graph no devolvió access_token")

    return token


# ============================================================
# SHAREPOINT
# ============================================================

def get_site_id(token):
    """
    Obtiene el ID del sitio:
    https://colcomerciocom.sharepoint.com/sites/AreaInfraestructura
    """

    site_url = (
        "https://graph.microsoft.com/v1.0/sites/"
        f"{SHAREPOINT_HOST}:{SHAREPOINT_SITE_PATH}"
    )

    headers = {
        "Authorization": f"Bearer {token}",
    }

    try:
        response = requests.get(
            site_url,
            headers=headers,
            timeout=30,
        )

        response.raise_for_status()

    except requests.RequestException as exc:
        fail(f"No fue posible obtener el sitio de SharePoint: {exc}")

    site_id = response.json().get("id")

    if not site_id:
        fail("No se recibió el ID del sitio de SharePoint")

    return site_id


def download_excel(token, site_id):
    """
    Descarga el Excel desde SharePoint usando Microsoft Graph.
    """

    encoded_path = quote(EXCEL_PATH, safe="/")

    url = (
        "https://graph.microsoft.com/v1.0/"
        f"sites/{site_id}/drive/root:/{encoded_path}:/content"
    )

    headers = {
        "Authorization": f"Bearer {token}",
    }

    try:
        response = requests.get(
            url,
            headers=headers,
            timeout=60,
        )

        response.raise_for_status()

    except requests.RequestException as exc:
        fail(
            "No fue posible descargar el Excel desde SharePoint: "
            f"{exc}"
        )

    return response.content


# ============================================================
# EXCEL
# ============================================================

def read_excel(excel_content):
    try:
        workbook = load_workbook(
            filename=io.BytesIO(excel_content),
            read_only=True,
            data_only=True,
        )
    except Exception as exc:
        fail(f"No fue posible abrir el archivo Excel: {exc}")

    if SHEET_NAME not in workbook.sheetnames:
        fail(
            f"No existe la hoja '{SHEET_NAME}'. "
            f"Hojas disponibles: {', '.join(workbook.sheetnames)}"
        )

    sheet = workbook[SHEET_NAME]

    rows = sheet.iter_rows(values_only=True)

    try:
        header_row = next(rows)
    except StopIteration:
        fail("La hoja Excel está vacía")

    headers = {}

    for index, value in enumerate(header_row):
        if value is not None:
            headers[str(value).strip()] = index

    required_columns = {
        HOSTNAME_COLUMN,
        "IPv4Address",
    }

    missing = required_columns - set(headers.keys())

    if missing:
        fail(
            "Faltan columnas obligatorias en Excel: "
            + ", ".join(sorted(missing))
        )

    hosts = []

    for row in rows:

        hostname_index = headers[HOSTNAME_COLUMN]

        if hostname_index >= len(row):
            continue

        hostname = normalize_value(row[hostname_index])

        if not hostname:
            continue

        hostvars = {}

        for variable_name, excel_column in COMPOSE.items():

            if excel_column not in headers:
                continue

            index = headers[excel_column]

            if index >= len(row):
                continue

            value = normalize_value(row[index])

            if value != "":
                hostvars[variable_name] = value

        hosts.append(
            {
                "hostname": str(hostname),
                "vars": hostvars,
            }
        )

    return hosts


# ============================================================
# INVENTARIO ANSIBLE
# ============================================================

def build_inventory(hosts):

    inventory = {
        "_meta": {
            "hostvars": {}
        },
        "all": {
            "hosts": [],
            "children": []
        }
    }

    lote_groups = {}

    for host in hosts:

        hostname = host["hostname"]
        hostvars = host["vars"]

        inventory["_meta"]["hostvars"][hostname] = hostvars
        inventory["all"]["hosts"].append(hostname)

        # ----------------------------------------------------
        # keyed_groups equivalente al YAML anterior:
        # keyed_groups:
        #   - key: Lote
        # ----------------------------------------------------

        lote = hostvars.get("lote")

        if lote:

            group_name = safe_group_name(lote)

            if group_name:

                lote_groups.setdefault(group_name, [])
                lote_groups[group_name].append(hostname)

    for group_name, group_hosts in lote_groups.items():

        inventory[group_name] = {
            "hosts": group_hosts
        }

        inventory["all"]["children"].append(group_name)

    return inventory


def generate_inventory():

    token = get_access_token()

    site_id = get_site_id(token)

    excel_content = download_excel(
        token,
        site_id,
    )

    hosts = read_excel(excel_content)

    if not hosts:
        fail(
            f"No se encontraron hosts en la hoja '{SHEET_NAME}'"
        )

    return build_inventory(hosts)


# ============================================================
# MAIN
# ============================================================

def main():

    parser = argparse.ArgumentParser(
        description="Inventario dinámico SLES15 GeoPOS"
    )

    parser.add_argument(
        "--list",
        action="store_true",
        help="Mostrar inventario completo",
    )

    parser.add_argument(
        "--host",
        help="Mostrar variables de un host",
    )

    args = parser.parse_args()

    inventory = generate_inventory()

    if args.host:

        hostvars = inventory.get(
            "_meta",
            {}
        ).get(
            "hostvars",
            {}
        ).get(
            args.host,
            {}
        )

        print(
            json.dumps(
                hostvars,
                indent=2,
                ensure_ascii=False,
                default=str,
            )
        )

        return

    print(
        json.dumps(
            inventory,
            indent=2,
            ensure_ascii=False,
            default=str,
        )
    )


if __name__ == "__main__":
    main()