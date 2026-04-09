"""
========================================================
  Calculadora de Propinas y División de Cuentas
  Autor: Generado con Claude
  Python 3.8+ | Sin librerías externas (solo datetime)
========================================================
"""

from datetime import datetime

# ──────────────────────────────────────────────
# CONSTANTES
# ──────────────────────────────────────────────
MAX_HISTORIAL = 5          # Máximo de registros en el historial
SEPARADOR = "─" * 45       # Línea decorativa para la UI


# ──────────────────────────────────────────────
# FUNCIÓN DE VALIDACIÓN REUTILIZABLE
# ──────────────────────────────────────────────
def validar_entrada(prompt: str, tipo: type, minimo: float = 0) -> float | int:
    """
    Solicita y valida un valor numérico al usuario.

    Parámetros:
        prompt  -- Texto que se muestra al usuario.
        tipo    -- Tipo esperado: float o int.
        minimo  -- Valor mínimo aceptable (por defecto 0).

    Retorna el valor validado o lanza una excepción controlada.

    Manejo de excepciones:
        - ValueError: entrada no numérica o tipo incorrecto.
        - ValueError: valor por debajo del mínimo permitido.
    """
    while True:
        try:
            # Intentamos convertir la entrada al tipo requerido
            valor = tipo(input(prompt).strip().replace(",", "."))

            # Validamos que no sea negativo (o menor al mínimo indicado)
            if valor < minimo:
                print(f"  ⚠  El valor no puede ser menor a {minimo}. Intenta de nuevo.")
                continue

            return valor

        except ValueError:
            # Capturamos entradas no numéricas o conversiones fallidas
            tipo_str = "número entero" if tipo == int else "número decimal"
            print(f"  ✖  Entrada inválida. Por favor ingresa un {tipo_str} válido.")


# ──────────────────────────────────────────────
# FUNCIÓN DE CÁLCULO
# ──────────────────────────────────────────────
def calcular_cuenta(
    total: float, propina_porcentaje: float, personas: int
) -> tuple[float, float]:
    """
    Calcula el total con propina y el monto por persona.

    Parámetros:
        total              -- Monto de la cuenta sin propina.
        propina_porcentaje -- Porcentaje de propina (ej. 15 para 15%).
        personas           -- Número de personas que dividen la cuenta.

    Retorna:
        (total_con_propina, total_por_persona)

    Manejo de excepciones:
        - ZeroDivisionError: si personas es 0 (no debería llegar aquí
          gracias a validar_entrada con minimo=1, pero se protege igual).
    """
    monto_propina = total * (propina_porcentaje / 100)
    total_con_propina = total + monto_propina

    # Protección explícita contra división entre cero
    if personas == 0:
        raise ZeroDivisionError("El número de personas no puede ser cero.")

    total_por_persona = total_con_propina / personas
    return total_con_propina, total_por_persona


# ──────────────────────────────────────────────
# FUNCIÓN PARA MOSTRAR HISTORIAL
# ──────────────────────────────────────────────
def mostrar_historial(historial: list) -> None:
    """
    Imprime en consola los últimos cálculos guardados.

    Parámetro:
        historial -- Lista de diccionarios con los resultados previos.
    """
    print(f"\n{SEPARADOR}")
    print("  📋  HISTORIAL DE CÁLCULOS")
    print(SEPARADOR)

    if not historial:
        print("  (Aún no hay cálculos registrados)")
    else:
        for i, registro in enumerate(historial, start=1):
            print(f"\n  [{i}] {registro['fecha']}")
            print(f"      Cuenta: S/ {registro['total_original']:.2f}  |  "
                  f"Propina: {registro['propina_pct']:.1f}%  |  "
                  f"Personas: {registro['personas']}")
            print(f"      Total c/propina : S/ {registro['total_con_propina']:.2f}")
            print(f"      Por persona      : S/ {registro['total_por_persona']:.2f}")

    print(f"{SEPARADOR}\n")


# ──────────────────────────────────────────────
# FUNCIÓN PARA GUARDAR EN HISTORIAL
# ──────────────────────────────────────────────
def guardar_en_historial(
    historial: list,
    total: float,
    propina_pct: float,
    personas: int,
    total_con_propina: float,
    total_por_persona: float,
) -> None:
    """
    Agrega un nuevo registro al historial, manteniendo solo los últimos MAX_HISTORIAL.
    """
    registro = {
        "fecha": datetime.now().strftime("%d/%m/%Y %H:%M:%S"),
        "total_original": total,
        "propina_pct": propina_pct,
        "personas": personas,
        "total_con_propina": total_con_propina,
        "total_por_persona": total_por_persona,
    }
    historial.append(registro)

    # Descartamos el más antiguo si superamos el límite
    if len(historial) > MAX_HISTORIAL:
        historial.pop(0)


# ──────────────────────────────────────────────
# FUNCIÓN PARA MOSTRAR MENÚ
# ──────────────────────────────────────────────
def mostrar_menu() -> None:
    print(f"\n{SEPARADOR}")
    print("  💰  CALCULADORA DE PROPINAS")
    print(SEPARADOR)
    print("  [1] Nuevo cálculo")
    print("  [2] Ver historial")
    print("  [3] Salir")
    print(SEPARADOR)


# ──────────────────────────────────────────────
# FUNCIÓN PRINCIPAL
# ──────────────────────────────────────────────
def main() -> None:
    """
    Punto de entrada del programa.
    Ejecuta el bucle principal hasta que el usuario elige salir.
    """
    historial: list = []  # Historial en memoria (no persistente)

    print("\n  Bienvenido/a a la Calculadora de Propinas 🎉")

    while True:
        mostrar_menu()

        opcion = input("  Elige una opción [1/2/3]: ").strip()

        # ── Opción 1: Nuevo cálculo ──
        if opcion == "1":
            print(f"\n{SEPARADOR}")
            print("  Ingresa los datos de la cuenta:")
            print(SEPARADOR)

            # Validación con la función reutilizable
            # minimo=0.01 para evitar cuentas de $0
            total = validar_entrada(
                "  Total de la cuenta (ej. 120.50): S/ ",
                float,
                minimo=0.01,
            )

            # minimo=0 permite propinas del 0%
            propina_pct = validar_entrada(
                "  Porcentaje de propina (ej. 15): ",
                float,
                minimo=0,
            )

            # minimo=1 previene división entre cero de forma proactiva
            personas = validar_entrada(
                "  Número de personas: ",
                int,
                minimo=1,
            )

            try:
                # Cálculo principal
                total_con_propina, total_por_persona = calcular_cuenta(
                    total, propina_pct, personas
                )

                # Mostramos resultados con 2 decimales
                print(f"\n{SEPARADOR}")
                print("  ✅  RESULTADOS")
                print(SEPARADOR)
                print(f"  Subtotal               : S/ {total:.2f}")
                print(f"  Propina ({propina_pct:.1f}%)         : S/ {total * propina_pct / 100:.2f}")
                print(f"  Total con propina      : S/ {total_con_propina:.2f}")
                print(f"  Total por persona      : S/ {total_por_persona:.2f}")
                print(SEPARADOR)

                # Guardamos en historial
                guardar_en_historial(
                    historial, total, propina_pct, personas,
                    total_con_propina, total_por_persona
                )

            except ZeroDivisionError as e:
                # Este bloque es una red de seguridad adicional
                print(f"\n  ✖  Error de cálculo: {e}")

        # ── Opción 2: Ver historial ──
        elif opcion == "2":
            mostrar_historial(historial)

        # ── Opción 3: Salir ──
        elif opcion == "3":
            print(f"\n{SEPARADOR}")
            print("  ¡Hasta luego! 👋")
            print(SEPARADOR)
            break

        # ── Opción inválida ──
        else:
            print("  ⚠  Opción no válida. Por favor elige 1, 2 o 3.")


# ──────────────────────────────────────────────
# PUNTO DE ENTRADA
# ──────────────────────────────────────────────
if __name__ == "__main__":
    main()
