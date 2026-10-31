"""Lecturas de temperatura: documentos MongoDB y JSON para Grafana."""
import os
from contextlib import asynccontextmanager
from datetime import datetime, timedelta, timezone
from typing import Any

from fastapi import FastAPI, HTTPException, Query, Request
from pydantic import BaseModel, Field, field_validator
from pymongo import MongoClient, ASCENDING
from pymongo.errors import PyMongoError

UTC = timezone.utc
UMBRAL = 30.0  # Umbral didáctico, no una especificación de seguridad industrial.


class Lectura(BaseModel):
    dispositivo: str = Field(default="sensor-01", pattern=r"^[a-zA-Z0-9_-]{1,40}$")
    valor: float = Field(ge=-40, le=125, allow_inf_nan=False)
    fecha: datetime | None = None
    ubicacion: str = Field(default="Laboratorio", max_length=80)
    origen: str = Field(default="manual", max_length=40)
    atributos: dict[str, Any] = Field(default_factory=dict)

    @field_validator("fecha")
    @classmethod
    def validar_fecha(cls, fecha):
        if fecha is not None and fecha.tzinfo is None:
            raise ValueError("Indica la zona horaria: usa Z o -06:00 al final de la fecha")
        return fecha


def serializar(doc):
    fecha = doc["fecha"].replace(tzinfo=UTC) if doc["fecha"].tzinfo is None else doc["fecha"]
    return {**doc, "_id": str(doc["_id"]),
            "fecha": fecha.astimezone(UTC).isoformat().replace("+00:00", "Z"),
            "estado": "REVISAR" if doc["valor"] >= UMBRAL else "NORMAL"}


def sembrar(coleccion):
    """Solo agrega historial inicial si la colección está vacía."""
    if coleccion.count_documents({}) == 0:
        ahora = datetime.now(UTC)
        coleccion.insert_many([
            {"dispositivo": "sensor-01", "fecha": ahora-timedelta(seconds=(30-i)*10),
             "valor": round(24+(i % 12)*0.7, 1), "unidad": "°C",
             "ubicacion": "Laboratorio", "origen": "historial-simulado", "atributos": {}}
            for i in range(30)
        ])


def create_app(coleccion=None, sembrar_datos=True):
    @asynccontextmanager
    async def lifespan(app):
        cliente = None
        if coleccion is None:
            cliente = MongoClient(
                host=os.getenv("MONGO_HOST", "localhost"), port=27017,
                username=os.getenv("MONGO_USER", "laboratorio"),
                password=os.getenv("MONGO_PASSWORD", "TemperaturaDemo2026"),
                authSource="admin", tz_aware=True, serverSelectionTimeoutMS=5000)
            cliente.admin.command("ping")
            app.state.lecturas = cliente.temperaturas.lecturas
        else:
            app.state.lecturas = coleccion
        app.state.lecturas.create_index([("dispositivo", ASCENDING), ("fecha", ASCENDING)])
        if sembrar_datos:
            sembrar(app.state.lecturas)
        try:
            yield
        finally:
            if cliente is not None:
                cliente.close()

    app = FastAPI(title="Semana 7 · Temperaturas", version="1.0.0",
                  description="Responsable del material: Wendy Mazariegos. Datos simulados.",
                  lifespan=lifespan)

    @app.get("/health")
    def health(request: Request):
        try:
            request.app.state.lecturas.database.client.admin.command("ping")
        except PyMongoError:
            raise HTTPException(503, "MongoDB no está disponible")
        return {"estado": "ok", "almacenamiento": "MongoDB"}

    @app.post("/lecturas", status_code=201)
    def registrar(lectura: Lectura, request: Request):
        doc = lectura.model_dump(exclude={"fecha"})
        doc["fecha"] = (lectura.fecha or datetime.now(UTC)).astimezone(UTC)
        doc["unidad"] = "°C"
        resultado = request.app.state.lecturas.insert_one(doc)
        # Leer otra vez demuestra que la respuesta corresponde al documento guardado.
        return serializar(request.app.state.lecturas.find_one({"_id": resultado.inserted_id}))

    @app.get("/lecturas")
    def consultar(request: Request, dispositivo: str = "sensor-01",
                  desde: datetime | None = None, hasta: datetime | None = None,
                  limite: int = Query(default=2000, ge=1, le=10000)):
        for fecha in (desde, hasta):
            if fecha is not None and fecha.tzinfo is None:
                raise HTTPException(422, "Las fechas deben incluir zona horaria")
        if desde and hasta and desde > hasta:
            raise HTTPException(422, "desde debe ser anterior o igual a hasta")
        filtro = {"dispositivo": dispositivo}
        rango = {}
        if desde: rango["$gte"] = desde.astimezone(UTC)
        if hasta: rango["$lte"] = hasta.astimezone(UTC)
        if rango: filtro["fecha"] = rango
        docs = list(request.app.state.lecturas.find(filtro).sort(
            [("fecha", -1), ("_id", -1)]).limit(limite))
        return [serializar(doc) for doc in reversed(docs)]

    return app


app = create_app()
