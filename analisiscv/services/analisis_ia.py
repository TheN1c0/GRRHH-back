import requests
import os
import json  
from dotenv import load_dotenv

load_dotenv(dotenv_path=os.getenv("ENV_PATH", ".env")) 


def analizar_curriculum_con_ia(texto: str) -> list:
    try:
        endpoint = "https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash-latest:generateContent"
        api_key = os.getenv("GEMINI_API_KEY")
        headers = {"Content-Type": "application/json"}
        data = {
            "contents": [
                {
                    "parts": [
                        {
                            "text": "Extrae habilidades, certificaciones y áreas del siguiente texto y devuelve solo un JSON plano con claves: habilidades, certificaciones, areas." + texto
                        }
                    ]
                }
            ]
        }
        response = requests.post(f"{endpoint}?key={api_key}", headers=headers, json=data, timeout=10)
        result = response.json()

        raw_text = result['candidates'][0]['content']['parts'][0]['text']
        cleaned = raw_text.strip().removeprefix("```json").removesuffix("```").strip()
        parsed = json.loads(cleaned)
        return parsed.get("habilidades", []) + parsed.get("certificaciones", []) + parsed.get("areas", [])
    except Exception as e:
        print("Error al llamar a Gemini:", e)
        return []

def generar_etiquetas_para_cargo(nombre: str, descripcion: str = "") -> list:
    try:
        endpoint = "https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash-latest:generateContent"
        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            raise ValueError("API key 'GEMINI_API_KEY' no encontrada. Revisa tu archivo .env")

        prompt = (
            f"Eres un asistente de reclutamiento. Dado el nombre y descripción de un cargo interno en una organización, "
            f"devuelve en JSON las habilidades técnicas, certificaciones y áreas esperadas para ese cargo. "
            f"Usa este formato:\n\n"
            f"{{\"habilidades\": [...], \"certificaciones\": [...], \"areas\": [...]}}\n\n"
            f"Cargo: {nombre}\n"
            f"Descripción: {descripcion}"
        )

        headers = {"Content-Type": "application/json"}
        data = {
            "contents": [
                {
                    "parts": [
                        {"text": prompt}
                    ]
                }
            ]
        }

        response = requests.post(f"{endpoint}?key={api_key}", headers=headers, json=data, timeout=10)
        result = response.json()

        raw_text = result['candidates'][0]['content']['parts'][0]['text']
        try:
            cleaned = raw_text.strip().removeprefix("```json").removesuffix("```").strip()
            parsed = json.loads(cleaned)
        except json.JSONDecodeError as err:
            print("Error al decodificar JSON de Gemini:", err)
            print("Texto recibido:", raw_text)
            return []


        return {
    "habilidades": parsed.get("habilidades", []),
    "certificaciones": parsed.get("certificaciones", []),
    "areas": parsed.get("areas", [])
}

    except Exception as e:
        print("Error al generar etiquetas desde IA:", e)
        return []
