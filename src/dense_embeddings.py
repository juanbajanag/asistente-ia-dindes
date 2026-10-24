"""
dense_embeddings.py
-------------------
Cliente local para embeddings usando Ollama.

Modelo esperado:
    qwen3-embedding:0.6b

Endpoint:
    http://localhost:11434/api/embed

No requiere librerías externas adicionales: utiliza urllib de la biblioteca estándar.
"""

from __future__ import annotations

import json
import urllib.request
import urllib.error

import numpy as np


class OllamaEmbeddingClient:
    def __init__(
        self,
        model: str = "qwen3-embedding:0.6b",
        base_url: str = "http://localhost:11434",
        timeout: int = 120,
    ):
        self.model = model
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout

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
                "No se pudo conectar con Ollama. Verifique que Ollama esté "
                "ejecutándose y que el modelo de embeddings esté instalado."
            ) from exc

    def embed(self, texts: list[str] | str) -> np.ndarray:
        """
        Genera embeddings para uno o varios textos.

        Returns
        -------
        np.ndarray
            Matriz shape (n_textos, dimension).
        """
        if isinstance(texts, str):
            texts = [texts]

        if not texts:
            raise ValueError("No se recibieron textos para generar embeddings.")

        response = self._post_json(
            "/api/embed",
            {
                "model": self.model,
                "input": texts,
            },
        )

        embeddings = response.get("embeddings")
        if embeddings is None:
            raise RuntimeError(
                f"Ollama no devolvió 'embeddings'. Respuesta recibida: {response}"
            )

        matrix = np.asarray(embeddings, dtype=np.float32)

        # Normalización L2 para usar producto punto como similitud coseno.
        norms = np.linalg.norm(matrix, axis=1, keepdims=True)
        norms = np.where(norms == 0.0, 1.0, norms)
        return matrix / norms

    def health_check(self) -> bool:
        """
        Comprueba que el endpoint de embeddings responde.
        """
        try:
            vector = self.embed(["prueba"])
            return bool(vector.shape[0] == 1 and vector.shape[1] > 0)
        except Exception:
            return False
