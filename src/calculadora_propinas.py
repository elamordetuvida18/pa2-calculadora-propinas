"""
Calculadora de Propinas — versión 2.0
Producción-ready: validación robusta, dataclasses, persistencia atómica, tests-friendly.
"""

from __future__ import annotations

import csv
import json
import os
from dataclasses import asdict, dataclass, field
from datetime import datetime
from pathlib import Path
from typing import List, Optional

from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, HRFlowable
from reportlab.lib.enums import TA_CENTER, TA_RIGHT

# ─── Configuración ────────────────────────────────────────────────────────────

VERSION = "2.0"
MONEDA_SIMBOLO = "S/"
MAX_HISTORIAL = 50
ARCHIVO_HISTORIAL = Path("historial_tip_calculator.json")
SEPARADOR = "─" * 42

PROPINAS_RAPIDAS = [10, 15, 18, 20, 25]
EQUIPO = ["Edgar Romario Sebastian Carhuachin Sanchez"] 


# ─── Estilos de consola (ANSI) ────────────────────────────────────────────────

class Estilo:
    RESET    = "\033[0m"
    NEGRITA  = "\033[1m"
    AZUL     = "\033[94m"
    VERDE    = "\033[92m"
    AMARILLO = "\033[93m"
    ROJO     = "\033[91m"
    GRIS     = "\033[90m"


# ─── Modelo de datos ──────────────────────────────────────────────────────────

@dataclass
class Calculo:
    """Representa un cálculo de propina completo."""
    fecha: str
    total_original: float
    propina_pct: float
    personas: int
    total_con_propina: float
    total_por_persona: float

    @classmethod
    def desde_dict(cls, d: dict) -> Optional["Calculo"]:
        """Construye un Calculo desde un dict, retorna None si el schema es inválido."""
        campos = {"fecha", "total_original", "propina_pct", "personas",
                  "total_con_propina", "total_por_persona"}
        if not campos.issubset(d.keys()):
            return None
        try:
            return cls(
                fecha=str(d["fecha"]),
                total_original=float(d["total_original"]),
                propina_pct=float(d["propina_pct"]),
                personas=int(d["personas"]),
                total_con_propina=float(d["total_con_propina"]),
                total_por_persona=float(d["total_por_persona"]),
            )
        except (ValueError, TypeError):
            return None


# ─── Lógica de negocio (pura, sin prints, testeable) ──────────────────────────

def calcular_propina(monto: float, propina_pct: float, personas: int) -> Calculo:
    """
    Calcula propina y división. Función pura sin efectos secundarios.

    Args:
        monto: Total de la cuenta (> 0).
        propina_pct: Porcentaje de propina (0–100).
        personas: Número de personas (>= 1).

    Returns:
        Calculo con todos los valores calculados.

    Raises:
        ValueError: Si algún argumento está fuera de rango.
    """
    if monto <= 0:
        raise ValueError("El monto debe ser mayor a 0.")
    if not (0 <= propina_pct <= 100):
        raise ValueError("La propina debe estar entre 0% y 100%.")
    if personas < 1:
        raise ValueError("Debe haber al menos 1 persona.")

    total_con_propina = monto * (1 + propina_pct / 100)
    total_por_persona = total_con_propina / personas

    return Calculo(
        fecha=datetime.now().strftime("%Y-%m-%d %H:%M"),
        total_original=round(monto, 2),
        propina_pct=round(propina_pct, 2),
        personas=personas,
        total_con_propina=round(total_con_propina, 2),
        total_por_persona=round(total_por_persona, 2),
    )


def fmt_moneda(valor: float) -> str:
    """Formatea un valor como moneda con separadores de miles."""
    return f"{MONEDA_SIMBOLO} {valor:,.2f}"


# ─── Persistencia ─────────────────────────────────────────────────────────────

def cargar_historial(archivo: Path = ARCHIVO_HISTORIAL) -> List[Calculo]:
    """Carga el historial desde JSON. Ignora registros con schema inválido."""
    if not archivo.exists():
        return []
    try:
        datos = json.loads(archivo.read_text(encoding="utf-8"))
        if not isinstance(datos, list):
            return []
        calculos = []
        for item in datos:
            c = Calculo.desde_dict(item)
            if c is not None:
                calculos.append(c)
        return calculos
    except (json.JSONDecodeError, OSError):
        return []


def guardar_historial(historial: List[Calculo], archivo: Path = ARCHIVO_HISTORIAL) -> None:
    """
    Guarda el historial en JSON de forma atómica.
    Escribe en .tmp y renombra para evitar corrupción ante crashes.
    """
    tmp = archivo.with_suffix(".tmp")
    try:
        datos = [asdict(c) for c in historial]
        tmp.write_text(json.dumps(datos, ensure_ascii=False, indent=2), encoding="utf-8")
        tmp.replace(archivo)
    except OSError as e:
        print(f"  ✖  Error guardando historial: {e}")
    finally:
        if tmp.exists():
            tmp.unlink(missing_ok=True)


# ─── Helpers de input validado ────────────────────────────────────────────────

def _pedir_float(prompt: str, minimo: float = 0, maximo: float = float("inf")) -> float:
    """Solicita un float validado en rango (minimo, maximo]."""
    while True:
        raw = input(prompt).strip().replace(",", ".")
        try:
            valor = float(raw)
            if not (minimo < valor <= maximo):
                raise ValueError
            return valor
        except ValueError:
            print(f"  ⚠  Ingresa un número entre {minimo} y {maximo}.")


def _pedir_int(prompt: str, minimo: int = 1, maximo: int = 9999) -> int:
    """Solicita un entero validado en rango [minimo, maximo]."""
    while True:
        raw = input(prompt).strip()
        try:
            valor = int(raw)
            if not (minimo <= valor <= maximo):
                raise ValueError
            return valor
        except ValueError:
            print(f"  ⚠  Ingresa un número entero entre {minimo} y {maximo}.")


def _pedir_propina() -> float:
    """Solicita el porcentaje de propina con opciones rápidas."""
    opciones = "  ".join(f"[{p}%]" for p in PROPINAS_RAPIDAS)
    print(f"\n  Propinas rápidas: {opciones}")
    print("  O escribe cualquier porcentaje (0–100).")
    return _pedir_float("  ➤ Propina (%): ", minimo=-1, maximo=100)


# ─── Aplicación ───────────────────────────────────────────────────────────────

class CalculadoraPropinas:
    """Controlador principal de la aplicación."""

    def __init__(self) -> None:
        self.historial: List[Calculo] = cargar_historial()

    # ── Menú ──────────────────────────────────────────────────────────────────

    def mostrar_menu(self) -> None:
        """Muestra el menú principal."""
        print(f"\n{SEPARADOR}")
        print(f"  💰  CALCULADORA DE PROPINAS v{VERSION}")
        print(SEPARADOR)
        print("  [1] ➕ Nuevo cálculo")
        print("  [2] 📋 Ver historial")
        print("  [3] 🗑️  Limpiar historial")
        print("  [4] 📤 Exportar CSV")
        print("  [5] 📄 Exportar PDF")
        print("  [6] 📊 Estadísticas")
        print("  [7] ❌ Salir")
        print(SEPARADOR)

    # ── Nuevo cálculo ─────────────────────────────────────────────────────────

    def _procesar_nuevo_calculo(self) -> None:
        """Solicita datos, calcula y guarda el resultado."""
        print(f"\n{SEPARADOR}")
        print("  NUEVO CÁLCULO")
        print(SEPARADOR)

        monto = _pedir_float("  ➤ Total de la cuenta: ", minimo=0)
        propina_pct = _pedir_propina()
        personas = _pedir_int("  ➤ Número de personas: ", minimo=1)

        try:
            resultado = calcular_propina(monto, propina_pct, personas)
        except ValueError as e:
            print(f"  ✖  {e}")
            return

        self._mostrar_resultado(resultado)
        self._agregar_al_historial(resultado)
        input("\n  ⏎ Presiona Enter para continuar...")

    def _mostrar_resultado(self, c: Calculo) -> None:
        """Muestra el resultado formateado en pantalla."""
        propina_monto = c.total_con_propina - c.total_original
        print(f"\n{SEPARADOR}")
        print("  RESULTADO")
        print(SEPARADOR)
        print(f"  {'Subtotal:':<22} {fmt_moneda(c.total_original):>12}")
        print(f"  {'Propina ({:.0f}%):'.format(c.propina_pct):<22} {fmt_moneda(propina_monto):>12}")
        print(f"  {'Total con propina:':<22} {fmt_moneda(c.total_con_propina):>12}")
        if c.personas > 1:
            print(SEPARADOR)
            print(f"  {'Por persona ({} pers.):'.format(c.personas):<22} {fmt_moneda(c.total_por_persona):>12}")
        print(SEPARADOR)

    def _agregar_al_historial(self, calculo: Calculo) -> None:
        """Agrega un cálculo al historial respetando el límite máximo."""
        self.historial.append(calculo)
        if len(self.historial) > MAX_HISTORIAL:
            self.historial = self.historial[-MAX_HISTORIAL:]
        guardar_historial(self.historial)

    # ── Historial ─────────────────────────────────────────────────────────────

    def mostrar_historial(self) -> None:
        """Muestra el historial completo como tabla."""
        if not self.historial:
            print("  ℹ  El historial está vacío.")
            return

        print(f"\n{SEPARADOR}")
        print(f"  HISTORIAL ({len(self.historial)} registros)")
        print(SEPARADOR)

        # Encabezado
        print(f"  {'Fecha':<17} {'Total':>10} {'Prop':>6} {'Pers':>5} {'Por persona':>12}")
        print(f"  {'─'*17} {'─'*10} {'─'*6} {'─'*5} {'─'*12}")

        for c in reversed(self.historial):
            print(
                f"  {c.fecha:<17} "
                f"{fmt_moneda(c.total_con_propina):>10} "
                f"{c.propina_pct:>5.0f}% "
                f"{c.personas:>5} "
                f"{fmt_moneda(c.total_por_persona):>12}"
            )
        print(SEPARADOR)
        input("\n  ⏎ Presiona Enter para continuar...")

    # ── Limpiar historial ─────────────────────────────────────────────────────

    def limpiar_historial(self) -> None:
        """Limpia el historial local y el archivo persistente."""
        if not self.historial:
            print("  ℹ  El historial ya está vacío.")
            return

        confirm = input(
            f"  🗑️  Confirmar limpieza de {len(self.historial)} registro(s)? [s/N]: "
        ).strip().lower()

        if confirm == "s":
            self.historial.clear()
            guardar_historial(self.historial)
            print("  ✅ Historial limpiado correctamente.")
        else:
            print("  ℹ  Operación cancelada.")

    # ── Exportar CSV ──────────────────────────────────────────────────────────

    def exportar_csv(self) -> None:
        """Exporta el historial completo a CSV ordenado por fecha (más reciente primero)."""
        if not self.historial:
            print("  ⚠  No hay datos para exportar.")
            return

        archivo_csv = Path("historial_tip_calculator.csv")
        historial_ordenado = sorted(self.historial, key=lambda c: c.fecha, reverse=True)

        try:
            with archivo_csv.open("w", newline="", encoding="utf-8") as f:
                fieldnames = [
                    "fecha", "total_original", "propina_pct",
                    "personas", "total_con_propina", "total_por_persona",
                ]
                writer = csv.DictWriter(f, fieldnames=fieldnames)
                writer.writeheader()
                writer.writerows(asdict(c) for c in historial_ordenado)

            print(f"  ✅ Exportado: {archivo_csv.resolve()}")
            print(f"  📊 {len(historial_ordenado)} registros | UTF-8 | más reciente primero")
        except OSError as e:
            print(f"  ✖  Error exportando CSV: {e}")

    # ── Exportar PDF ──────────────────────────────────────────────────────────

    def exportar_pdf(self) -> None:
        """Genera un reporte PDF con historial y estadísticas."""
        if not self.historial:
            print("  ⚠  No hay datos para exportar.")
            return

        archivo_pdf = Path("historial_tip_calculator.pdf")

        try:
            doc = SimpleDocTemplate(
                str(archivo_pdf),
                pagesize=A4,
                leftMargin=2*cm, rightMargin=2*cm,
                topMargin=2*cm, bottomMargin=2*cm,
            )

            styles = getSampleStyleSheet()
            titulo_style = ParagraphStyle(
                "titulo", parent=styles["Title"],
                fontSize=18, spaceAfter=4, textColor=colors.HexColor("#1a1a1a"),
            )
            subtitulo_style = ParagraphStyle(
                "subtitulo", parent=styles["Normal"],
                fontSize=10, textColor=colors.HexColor("#666666"),
                spaceAfter=16, alignment=TA_CENTER,
            )
            seccion_style = ParagraphStyle(
                "seccion", parent=styles["Heading2"],
                fontSize=12, textColor=colors.HexColor("#1a1a1a"),
                spaceBefore=16, spaceAfter=8,
            )

            story = []

            # ── Encabezado ────────────────────────────────────────────────────
            story.append(Paragraph(f"Calculadora de Propinas v{VERSION}", titulo_style))
            story.append(Paragraph(
                f"Reporte generado el {datetime.now().strftime('%d/%m/%Y %H:%M')} "
                f"| {len(self.historial)} registro(s)",
                subtitulo_style,
            ))
            story.append(HRFlowable(width="100%", thickness=0.5, color=colors.HexColor("#dddddd")))

            # ── Estadísticas ──────────────────────────────────────────────────
            story.append(Paragraph("Resumen", seccion_style))

            total_gastado = sum(c.total_con_propina for c in self.historial)
            propina_prom  = sum(c.propina_pct for c in self.historial) / len(self.historial)
            gasto_prom    = total_gastado / len(self.historial)
            gasto_max     = max(self.historial, key=lambda c: c.total_con_propina)

            stats_data = [
                ["Métrica", "Valor"],
                ["Total gastado",              fmt_moneda(total_gastado)],
                ["Gasto promedio por cálculo", fmt_moneda(gasto_prom)],
                ["Mayor gasto registrado",     fmt_moneda(gasto_max.total_con_propina)],
                ["Propina promedio",           f"{propina_prom:.1f}%"],
                ["Número de cálculos",         str(len(self.historial))],
            ]

            stats_table = Table(stats_data, colWidths=[10*cm, 6*cm])
            stats_table.setStyle(TableStyle([
                ("BACKGROUND",   (0, 0), (-1, 0),  colors.HexColor("#1a1a1a")),
                ("TEXTCOLOR",    (0, 0), (-1, 0),  colors.white),
                ("FONTNAME",     (0, 0), (-1, 0),  "Helvetica-Bold"),
                ("FONTSIZE",     (0, 0), (-1, 0),  10),
                ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.HexColor("#f9f9f9"), colors.white]),
                ("FONTSIZE",     (0, 1), (-1, -1),  9),
                ("ALIGN",        (1, 0), (1, -1),  "RIGHT"),
                ("TOPPADDING",   (0, 0), (-1, -1),  6),
                ("BOTTOMPADDING",(0, 0), (-1, -1),  6),
                ("LEFTPADDING",  (0, 0), (-1, -1),  10),
                ("RIGHTPADDING", (0, 0), (-1, -1),  10),
                ("GRID",         (0, 0), (-1, -1),  0.4, colors.HexColor("#e0e0e0")),
                ("ROUNDEDCORNERS", (0, 0), (-1, -1), [4, 4, 4, 4]),
            ]))
            story.append(stats_table)

            # ── Historial ─────────────────────────────────────────────────────
            story.append(Paragraph("Historial completo", seccion_style))

            historial_ordenado = sorted(self.historial, key=lambda c: c.fecha, reverse=True)

            encabezado = ["Fecha", "Total original", "Propina", "Personas", "Total", "Por persona"]
            filas = [encabezado] + [
                [
                    c.fecha,
                    fmt_moneda(c.total_original),
                    f"{c.propina_pct:.0f}%",
                    str(c.personas),
                    fmt_moneda(c.total_con_propina),
                    fmt_moneda(c.total_por_persona),
                ]
                for c in historial_ordenado
            ]

            col_widths = [3.8*cm, 3*cm, 1.8*cm, 2*cm, 3*cm, 3*cm]
            hist_table = Table(filas, colWidths=col_widths, repeatRows=1)
            hist_table.setStyle(TableStyle([
                ("BACKGROUND",     (0, 0), (-1, 0),  colors.HexColor("#1a1a1a")),
                ("TEXTCOLOR",      (0, 0), (-1, 0),  colors.white),
                ("FONTNAME",       (0, 0), (-1, 0),  "Helvetica-Bold"),
                ("FONTSIZE",       (0, 0), (-1, 0),  8),
                ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.HexColor("#f9f9f9"), colors.white]),
                ("FONTSIZE",       (0, 1), (-1, -1),  8),
                ("ALIGN",          (1, 0), (-1, -1),  "RIGHT"),
                ("ALIGN",          (0, 0), (0, -1),   "LEFT"),
                ("TOPPADDING",     (0, 0), (-1, -1),  5),
                ("BOTTOMPADDING",  (0, 0), (-1, -1),  5),
                ("LEFTPADDING",    (0, 0), (-1, -1),  8),
                ("RIGHTPADDING",   (0, 0), (-1, -1),  8),
                ("GRID",           (0, 0), (-1, -1),  0.4, colors.HexColor("#e0e0e0")),
            ]))
            story.append(hist_table)

            doc.build(story)
            print(f"  ✅ PDF exportado: {archivo_pdf.resolve()}")
            print(f"  📄 {len(historial_ordenado)} registros | A4 | UTF-8")

        except Exception as e:
            print(f"  ✖  Error exportando PDF: {e}")

    # ── Estadísticas ──────────────────────────────────────────────────────────

    def mostrar_estadisticas(self) -> None:
        """Muestra estadísticas agregadas del historial."""
        if not self.historial:
            print("  ℹ  Sin datos para estadísticas.")
            return

        total_gastado = sum(c.total_con_propina for c in self.historial)
        propina_promedio = sum(c.propina_pct for c in self.historial) / len(self.historial)
        gasto_promedio = total_gastado / len(self.historial)
        propina_max = max(self.historial, key=lambda c: c.propina_pct)
        gasto_max = max(self.historial, key=lambda c: c.total_con_propina)

        print(f"\n{SEPARADOR}")
        print("  ESTADÍSTICAS")
        print(SEPARADOR)
        print(f"  {'Total gastado:':<26} {fmt_moneda(total_gastado):>12}")
        print(f"  {'Gasto promedio por cálculo:':<26} {fmt_moneda(gasto_promedio):>12}")
        print(f"  {'Propina promedio:':<26} {propina_promedio:>11.1f}%")
        print(f"  {'Propina más alta:':<26} {propina_max.propina_pct:>11.0f}%")
        print(f"  {'Mayor gasto registrado:':<26} {fmt_moneda(gasto_max.total_con_propina):>12}")
        print(f"  {'Nº de cálculos:':<26} {len(self.historial):>12}")
        print(SEPARADOR)
        input("\n  ⏎ Presiona Enter para continuar...")

    # ── Bucle principal ───────────────────────────────────────────────────────

    def ejecutar(self) -> None:
        """Bucle principal de la aplicación con manejo de Ctrl+C."""
        equipo_str = " | ".join(EQUIPO)
        print(f"\n  {Estilo.AZUL}{Estilo.NEGRITA}💰 BIENVENIDO A CALCULADORA DE PROPINAS v{VERSION}{Estilo.RESET}")
        print(f"  💱 Moneda: {MONEDA_SIMBOLO} | Límite: {MAX_HISTORIAL} registros")
        print(f"  {Estilo.GRIS}👥 Equipo: {equipo_str}{Estilo.RESET}")
        print(f"  {Estilo.GRIS}💾 {len(self.historial)} registro(s) cargado(s) desde disco.{Estilo.RESET}")

        try:
            while True:
                self.mostrar_menu()
                opcion = input("  ➤ Elige una opción [1-7]: ").strip()

                if opcion == "1":
                    self._procesar_nuevo_calculo()
                elif opcion == "2":
                    self.mostrar_historial()
                elif opcion == "3":
                    self.limpiar_historial()
                elif opcion == "4":
                    self.exportar_csv()
                    input("\n  ⏎ Presiona Enter para continuar...")
                elif opcion == "5":
                    self.exportar_pdf()
                    input("\n  ⏎ Presiona Enter para continuar...")
                elif opcion == "6":
                    self.mostrar_estadisticas()
                elif opcion == "7":
                    print(f"\n{SEPARADOR}")
                    print("  ¡Hasta luego! 👋")
                    print(SEPARADOR)
                    break
                else:
                    print("  ⚠  Opción inválida. Usa 1–7.")
        except KeyboardInterrupt:
            print(f"\n\n{SEPARADOR}")
            print("  Salida forzada. ¡Hasta luego! 👋")
            print(SEPARADOR)


# ─── Tests unitarios (pytest) ─────────────────────────────────────────────────

def _tests() -> None:
    """Suite mínima de tests. Ejecutar con: python tip_calculator.py --test"""
    errores = []

    def check(nombre: str, condicion: bool) -> None:
        estado = "✅" if condicion else "✖ "
        print(f"  {estado} {nombre}")
        if not condicion:
            errores.append(nombre)

    print(f"\n{SEPARADOR}")
    print("  TESTS UNITARIOS")
    print(SEPARADOR)

    # calcular_propina — casos válidos
    r = calcular_propina(100, 15, 2)
    check("Propina 15% sobre 100 = total 115", r.total_con_propina == 115.0)
    check("División entre 2 personas = 57.50", r.total_por_persona == 57.50)

    r2 = calcular_propina(200, 0, 1)
    check("Propina 0% — sin propina", r2.total_con_propina == 200.0)

    r3 = calcular_propina(100, 100, 1)
    check("Propina 100% — total doble", r3.total_con_propina == 200.0)

    # calcular_propina — casos límite (deben lanzar ValueError)
    for nombre, args in [
        ("Monto 0 lanza ValueError", (0, 15, 2)),
        ("Monto negativo lanza ValueError", (-50, 15, 2)),
        ("Propina >100 lanza ValueError", (100, 101, 2)),
        ("0 personas lanza ValueError", (100, 15, 0)),
    ]:
        try:
            calcular_propina(*args)
            check(nombre, False)
        except ValueError:
            check(nombre, True)

    # fmt_moneda
    check("fmt_moneda 1000.5 → 'S/ 1,000.50'", fmt_moneda(1000.5) == "S/ 1,000.50")

    # Calculo.desde_dict — schema inválido
    check("desde_dict schema inválido → None", Calculo.desde_dict({"x": 1}) is None)

    # Persistencia — guardar y recargar
    import tempfile
    with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as tf:
        tmp_path = Path(tf.name)
    try:
        c = calcular_propina(80, 10, 4)
        guardar_historial([c], tmp_path)
        recargado = cargar_historial(tmp_path)
        check("Guardar y recargar historial", len(recargado) == 1)
        check("Datos preservados tras persistencia",
              recargado[0].total_con_propina == c.total_con_propina)
    finally:
        tmp_path.unlink(missing_ok=True)

    # Resumen
    print(SEPARADOR)
    total = 12
    pasados = total - len(errores)
    print(f"  Resultado: {pasados}/{total} tests pasados.")
    if errores:
        print(f"  Fallidos: {', '.join(errores)}")
    print(SEPARADOR)


# ─── Punto de entrada ─────────────────────────────────────────────────────────

if __name__ == "__main__":
    import sys
    if "--test" in sys.argv:
        _tests()
    else:
        CalculadoraPropinas().ejecutar()