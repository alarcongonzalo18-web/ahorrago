# Roadmap de producto — AhorraGo

> Features definidas por Gonzalo el 17-07-2026. Marcan un giro: de comparador abierto a
> **producto con cuentas y monetización freemium**. Ninguna está implementada todavía.
> Relacionado: [auditoria-2026-07-17.md](auditoria-2026-07-17.md) · [ahorrago-contexto.md](ahorrago-contexto.md)

## 1. Cuentas y monetización (freemium)

La base de todo lo demás: sin usuarios no hay alertas, plan de compra ni membresía.

- **Registro de usuarios**: cuenta propia (email/clave y/o login social). Hoy todo es
  localStorage y se pierde entre dispositivos — las listas, el historial y las alertas pasan a
  vivir en la cuenta.
- **Membresía para uso completo**: plan de pago que habilita todas las funciones.
- **Prueba de 15 días con todas las funciones**: al registrarse, acceso full por 15 días.
- **Versión acotada al terminar la prueba**: si no contrata, queda con un set reducido
  (definir qué entra en el free vs el pago — ej: N comparaciones/día, sin alertas, sin historial).

**Implica**: modelo `Usuario`, autenticación (JWT/sesión), estados de suscripción y trial,
gating de features en backend y frontend, y una pasarela de pago chilena (Webpay/MercadoPago/Flow).
Decisión pendiente: qué queda gratis (el gancho) y qué se paga.

## 2. Geolocalización — supermercados cercanos

Saber **qué supermercados hay cerca del usuario** para que la comparación sea accionable: no
sirve mandarlo al Jumbo más barato si no tiene uno cerca.

- Pedir ubicación (o comuna) al usuario.
- Catálogo de locales por cadena con coordenadas.
- Filtrar/priorizar la comparación por las cadenas que tiene a mano y mostrar distancia.
- Alimenta directo la recomendación de "dividir la compra": dividir solo tiene sentido si las
  dos tiendas están cerca.

**Implica**: fuente de datos de locales (cada cadena publica su listado de sucursales),
geocoding, y sumar la variable distancia al motor de compra óptima.

## 3. Plan de compra

Convertir el carrito en un **plan accionable**: qué comprar, en qué tienda, en qué orden,
con el ahorro estimado. Es la evolución del banner de recomendación actual (que ya dice
"conviene dividir" o "compra todo en X") hacia un plan concreto y guardable.

**Implica**: persistir el plan en la cuenta del usuario, y cruzarlo con geolocalización
(tiendas cercanas) para que el plan sea realista.

## 4. Alertas de precio inteligentes (por media histórica)

Alertas basadas en la **media de precios de los productos que el usuario compra o tiene en el
carro**, no en un umbral que el usuario tenga que adivinar.

- Calcular la media histórica de cada producto.
- Avisar cuando el precio actual cae bajo esa media (buen momento para comprar).
- Priorizar los productos que el usuario efectivamente compra/agrega al carro.

**Implica** (dependencia dura): **historial de precios**. Hoy `Precio` no tiene fecha ni se
guarda el histórico, así que no existe la media. Ver Fase D de la auditoría: agregar timestamp
a `Precio` + tabla de historial poblada en cada corrida del pipeline. Sin eso, esta feature
no se puede construir.

---

## Orden sugerido (por dependencias)

1. **Historial de precios** (timestamp + tabla histórica) — desbloquea las alertas por media.
2. **Cuentas de usuario** — desbloquea membresía, plan guardado y alertas personalizadas.
3. **Membresía + trial 15 días + versión acotada** — encima de cuentas.
4. **Alertas por media histórica** — encima de historial + cuentas.
5. **Geolocalización** — se puede hacer en paralelo; mejora la recomendación de dividir.
6. **Plan de compra** — encima de cuentas + geolocalización.

> Nota: nada de esto sirve si la comparabilidad sigue baja. La prioridad de datos
> (backfill de EAN, cobertura) sigue siendo previa a monetizar — ver la auditoría.
