"""
ollama_llm.py
-------------
Cliente local para generación con Ollama usando qwen3.5:9b.

Fase 4.1:
- Desactiva explícitamente el modo thinking con `"think": false`.
- Esto evita que Qwen3.5 consuma la salida en `message.thinking`
  y deje `message.content` vacío.
- El cliente solo utiliza la respuesta final contenida en `message.content`.
"""

from __future__ import annotations

import json
import urllib.request
import urllib.error


class OllamaChatClient:
    def __init__(
        self,
        model: str = "qwen3.5:9b",
        base_url: str = "http://localhost:11434",
        timeout: int = 180,
        temperature: float = 0.2,
        think: bool = False,
    ):
        self.model = model
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout
        self.temperature = temperature
        self.think = think

    def _post_json(self, endpoint: str, payload: dict) -> dict:
        url = f"{self.base_url}{endpoint}"
        data = json.dumps(payload).encode("utf-8")

        request = urllib.request.Request(
            url,
            data=data,
            headers={"Content-Type": "application/json"},
            method="POST",
        )

        try:
            with urllib.request.urlopen(request, timeout=self.timeout) as response:
                return json.loads(response.read().decode("utf-8"))

        except urllib.error.URLError as exc:
            raise RuntimeError(
                "No se pudo conectar con Ollama. "
                "Verifique que Ollama esté ejecutándose y que "
                f"el modelo {self.model} esté instalado."
            ) from exc

    def chat(
        self,
        system_prompt: str,
        user_prompt: str,
        temperature: float | None = None,
    ) -> str:

        payload = {
            "model": self.model,
            "stream": False,

            # Importante para Qwen3 / Qwen3.5:
            # fuerza respuesta directa en message.content.
            "think": self.think,

            "messages": [
                {
                    "role": "system",
                    "content": system_prompt,
                },
                {
                    "role": "user",
                    "content": user_prompt,
                },
            ],

            "options": {
                "temperature": (
                    self.temperature
                    if temperature is None
                    else temperature
                )
            },
        }

        response = self._post_json(
            "/api/chat",
            payload,
        )

        message = response.get(
            "message",
            {},
        )

        content = (
            message.get("content", "")
            or ""
        ).strip()

        if not content:
            raise RuntimeError(
                "Ollama no devolvió una respuesta final en message.content. "
                "Revise la versión de Ollama y confirme que el modelo soporte "
                "el parámetro think=false."
            )

        return content

    def health_check(self) -> bool:
        try:
            reply = self.chat(
                system_prompt=(
                    "Responde únicamente con la palabra OK."
                ),
                user_prompt="Prueba de conectividad.",
                temperature=0.0,
            )

            return bool(reply)

        except Exception:
            return False
