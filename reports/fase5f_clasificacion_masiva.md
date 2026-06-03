# Fase 5F - Clasificacion Masiva de Categorias

Modo: READ ONLY. No modifica base de datos, producto_base ni categorias.

## Resumen

- Hallazgos totales: 1986
- Alta confianza: 1639
- Media confianza: 347
- Baja confianza: 0
- Falso positivo probable: 0

## Categorias Mas Afectadas

- Bebe: 627
- Desayuno y Snacks: 407
- Lacteos, Huevos y Congelados: 391
- Carnes y Pescados: 213
- Congelados: 104
- Despensa: 99
- Bebidas: 75
- Mascotas: 44
- Frutas y Verduras: 17
- Limpieza: 3

## Motivos Principales

- Producto de mascotas fuera de Mascotas: 657
- Producto de higiene personal fuera de Higiene Personal: 457
- Bebida detectada dentro de categoria Bebe: 416
- Bebida fuera de Bebidas: 298
- Snack/fruto seco detectado dentro de categoria Bebe: 126
- Producto de limpieza fuera de Limpieza: 27
- Producto de limpieza detectado dentro de categoria Bebe: 5

## Productos Criticos Alta Confianza

| ID | Producto | Actual | Sugerida | Motivo |
|---:|---|---|---|---|
| 56 | Bebida Leche Láctea Yogu Yogu Chirimoya Caja | Bebe > Alimentos Bebe | Bebidas > Bebidas | Bebida detectada dentro de categoria Bebe |
| 132 | Bebida Leche Láctea Yogu Yogu Mora Caja | Bebe > Alimentos Bebe | Bebidas > Bebidas | Bebida detectada dentro de categoria Bebe |
| 148 | Bebida Leche Láctea Yogu Yogu Damasco Caja | Bebe > Alimentos Bebe | Bebidas > Bebidas | Bebida detectada dentro de categoria Bebe |
| 149 | Bebida Leche Láctea Yogu Yogu Frutilla Caja | Bebe > Alimentos Bebe | Bebidas > Bebidas | Bebida detectada dentro de categoria Bebe |
| 150 | Bebida Leche Láctea Yogu Yogu Piña Caja | Bebe > Alimentos Bebe | Bebidas > Bebidas | Bebida detectada dentro de categoria Bebe |
| 151 | Bebida Leche Láctea Trencito Chocolate Caja | Bebe > Alimentos Bebe | Bebidas > Bebidas | Bebida detectada dentro de categoria Bebe |
| 199 | Bebida Vegetal Notmilk Protein Con 7gr Proteína 750 ml NotCo | Bebe > Alimentos Bebe | Bebidas > Bebidas | Bebida detectada dentro de categoria Bebe |
| 213 | Bebida Láctea Sin Lactosa Chocolate 200 ml Milo | Bebe > Alimentos Bebe | Bebidas > Bebidas | Bebida detectada dentro de categoria Bebe |
| 217 | Bebida Vegetal Notmilk Chocolate Tetra Pak 200 ml NotCo | Bebe > Alimentos Bebe | Bebidas > Bebidas | Bebida detectada dentro de categoria Bebe |
| 218 | Bebida Vegetal Notmilk Original 1 L NotCo | Bebe > Alimentos Bebe | Bebidas > Bebidas | Bebida detectada dentro de categoria Bebe |
| 220 | Bebida Láctea Sabor Frutilla 200 ml Surlat | Bebe > Alimentos Bebe | Bebidas > Bebidas | Bebida detectada dentro de categoria Bebe |
| 221 | Bebida Láctea Sabor Chocolate 200 ml Surlat | Bebe > Alimentos Bebe | Bebidas > Bebidas | Bebida detectada dentro de categoria Bebe |
| 222 | Bebida Láctea Sabor Vainilla 200 ml Surlat | Bebe > Alimentos Bebe | Bebidas > Bebidas | Bebida detectada dentro de categoria Bebe |
| 225 | Bebida Vegetal Notmilk Zero 1 L NotCo | Bebe > Alimentos Bebe | Bebidas > Bebidas | Bebida detectada dentro de categoria Bebe |
| 226 | Bebida Vegetal Notmilk Low Fat 1 L NotCo | Bebe > Alimentos Bebe | Bebidas > Bebidas | Bebida detectada dentro de categoria Bebe |
| 228 | Bebida Vegetal Original 1 L Nature's Heart | Bebe > Alimentos Bebe | Bebidas > Bebidas | Bebida detectada dentro de categoria Bebe |
| 246 | Chocolate Lenguas De Gato Leche 120 g Costa | Lacteos, Huevos y Congelados > Leche | Mascotas > Alimento Gatos | Producto de mascotas fuera de Mascotas |
| 286 | Galletas Cachorro Raza Grande Sabor Leche Bolsa 500 g Master Dog | Desayuno y Snacks > Snacks | Mascotas > Alimento Perros | Producto de mascotas fuera de Mascotas |
| 300 | Alimento Seco Cachorro Raza Pequeña Carne Y Leche Bolsa 3 Kg Master Dog | Carnes y Pescados > Carnes | Mascotas > Alimento Perros | Producto de mascotas fuera de Mascotas |
| 306 | Alimento Seco Cachorro Raza Mediana/grande Sabor Carne Y Leche Bolsa 3 Kg Master Dog | Carnes y Pescados > Carnes | Mascotas > Alimento Perros | Producto de mascotas fuera de Mascotas |
| 310 | Galleta Perro Cachoro Leche g g Pet Food | Desayuno y Snacks > Snacks | Mascotas > Alimento Perros | Producto de mascotas fuera de Mascotas |
| 339 | Tónico Rose Care Leche & Tonico Micelar 2 En 1 200 ml Nivea | Lacteos, Huevos y Congelados > Leche | Higiene Personal > Cuidado Facial | Producto de higiene personal fuera de Higiene Personal |
| 429 | Bebida Vegetal Notmilk Chocolate 1 L NotCo | Bebe > Alimentos Bebe | Bebidas > Bebidas | Bebida detectada dentro de categoria Bebe |
| 444 | Bebida Vegetal De Avellana Sabor Chocolate Caja 1 L Vivicosí | Bebe > Alimentos Bebe | Bebidas > Bebidas | Bebida detectada dentro de categoria Bebe |
| 509 | Desodorante Spray Nivea Black&white Original Masculino Xl Hombre | Lacteos, Huevos y Congelados > Huevos | Higiene Personal > Desodorantes | Producto de higiene personal fuera de Higiene Personal |
| 553 | Bebida Vegetal Almendras Sabor Original 1 L Vilay | Bebe > Alimentos Bebe | Bebidas > Bebidas | Bebida detectada dentro de categoria Bebe |
| 554 | Bebida Vegetal Sabor Té Chai 330 ml Vilay | Bebe > Alimentos Bebe | Bebidas > Bebidas | Bebida detectada dentro de categoria Bebe |
| 571 | Bebida Láctea Probiótico Original Multipack Botella 6 Un x 80 ml Chamyto | Bebe > Alimentos Bebe | Bebidas > Bebidas | Bebida detectada dentro de categoria Bebe |
| 600 | Bebida Vegetal Café Caramelo Protein Sin Azúcar 250 ml Notco | Bebe > Alimentos Bebe | Bebidas > Bebidas | Bebida detectada dentro de categoria Bebe |
| 602 | Bebida Vegetal Proteína 1 L Nature's Heart | Bebe > Alimentos Bebe | Bebidas > Bebidas | Bebida detectada dentro de categoria Bebe |
| 669 | Bebida Láctea Probiótico Sabor Frambuesa Multipack Botella 80ml Chamyto | Bebe > Alimentos Bebe | Bebidas > Bebidas | Bebida detectada dentro de categoria Bebe |
| 760 | Bebida Vegetal Soya Natural Caja 1 L Loncoleche | Bebe > Alimentos Bebe | Bebidas > Bebidas | Bebida detectada dentro de categoria Bebe |
| 846 | Bebida De Coco Original 1 L Vilay | Bebe > Alimentos Bebe | Bebidas > Bebidas | Bebida detectada dentro de categoria Bebe |
| 847 | Bebida Vegetal Chocolate 1 L Vilay | Bebe > Alimentos Bebe | Bebidas > Bebidas | Bebida detectada dentro de categoria Bebe |
| 850 | Bebida Barista Almendra 1 L Orasi | Bebe > Alimentos Bebe | Bebidas > Bebidas | Bebida detectada dentro de categoria Bebe |
| 912 | Bebida De Almendras Sabor Chocolate 1 L Vilay | Bebe > Alimentos Bebe | Bebidas > Bebidas | Bebida detectada dentro de categoria Bebe |
| 913 | Bebida De Almendras Sabor Vainilla 1 L Vilay | Bebe > Alimentos Bebe | Bebidas > Bebidas | Bebida detectada dentro de categoria Bebe |
| 914 | Bebida Vegetal Arroz Chocolate 1 L Vilay | Bebe > Alimentos Bebe | Bebidas > Bebidas | Bebida detectada dentro de categoria Bebe |
| 915 | Bebida Vegetal Sin Azúcar Coco 1 L Vilay | Bebe > Alimentos Bebe | Bebidas > Bebidas | Bebida detectada dentro de categoria Bebe |
| 916 | Bebida De Almendras Sabor Vainilla 200 ml Vilay | Bebe > Alimentos Bebe | Bebidas > Bebidas | Bebida detectada dentro de categoria Bebe |
| 917 | Bebida Vegetal Barista Almendra 1 L Vilay | Bebe > Alimentos Bebe | Bebidas > Bebidas | Bebida detectada dentro de categoria Bebe |
| 922 | Bebida Vegetal Notshake Protein Chocolate 250 ml Notco | Bebe > Alimentos Bebe | Bebidas > Bebidas | Bebida detectada dentro de categoria Bebe |
| 925 | Bebida Vegetal Barista Soya 1 L Orasi | Bebe > Alimentos Bebe | Bebidas > Bebidas | Bebida detectada dentro de categoria Bebe |
| 926 | Bebida Vegetal Almendra Sin Azucar 1 L Orasi | Bebe > Alimentos Bebe | Bebidas > Bebidas | Bebida detectada dentro de categoria Bebe |
| 946 | Bebida Vegetal Almendras 6x1 1 L Loncoleche | Bebe > Alimentos Bebe | Bebidas > Bebidas | Bebida detectada dentro de categoria Bebe |
| 960 | Bebida Vegetal Almendras Sabor Original Sin Azúcar 1 L Vilay | Bebe > Alimentos Bebe | Bebidas > Bebidas | Bebida detectada dentro de categoria Bebe |
| 966 | Bebida Vegetal Almendras Sin Azúcar 946 ml Great Value | Bebe > Alimentos Bebe | Bebidas > Bebidas | Bebida detectada dentro de categoria Bebe |
| 984 | Bebida Láctea Probiótico Sabor Manzana Multipack Botella 80ml Chamyto | Bebe > Alimentos Bebe | Bebidas > Bebidas | Bebida detectada dentro de categoria Bebe |
| 997 | Bebida Láctea Probiótico Sabor Frutilla Pack Botella 6 Botellas 90 cc c/u Calán | Bebe > Alimentos Bebe | Bebidas > Bebidas | Bebida detectada dentro de categoria Bebe |
| 1043 | Bebida Vegetal Soya 1 L Orasí | Bebe > Alimentos Bebe | Bebidas > Bebidas | Bebida detectada dentro de categoria Bebe |
| 1044 | Bebida Vegetal Arroz 1 l Orasí | Bebe > Alimentos Bebe | Bebidas > Bebidas | Bebida detectada dentro de categoria Bebe |
| 1046 | Bebida Láctea Probiótico Sabor Frutilla Multipack Botella 80ml Chamyto | Bebe > Alimentos Bebe | Bebidas > Bebidas | Bebida detectada dentro de categoria Bebe |
| 1052 | Bebida Láctea Probiótico Uno Sabor Frutilla Pack 12 Botella 80 ml c/u Soprole | Bebe > Alimentos Bebe | Bebidas > Bebidas | Bebida detectada dentro de categoria Bebe |
| 1065 | Bebida Láctea Probiótico Uno Multifruta Pack 12 Botella 80 ml c/u Soprole | Bebe > Alimentos Bebe | Bebidas > Bebidas | Bebida detectada dentro de categoria Bebe |
| 1105 | Jabón Crema Ballerina Triple Humectación Piel Sensible Hipoalergénico | Lacteos, Huevos y Congelados > Quesos | Higiene Personal > Jabon | Producto de higiene personal fuera de Higiene Personal |
| 1110 | Acondicionador Ballerina Detox Carbón Activado Y Menta | Lacteos, Huevos y Congelados > Quesos | Higiene Personal > Acondicionador | Producto de higiene personal fuera de Higiene Personal |
| 1113 | Jabón Líquido Hipoalergénico Doypack 650 ml Ballerina | Bebe > Alimentos Bebe | Higiene Personal > Jabon | Producto de higiene personal fuera de Higiene Personal |
| 1119 | Jabón Líquido Ballerina Violetas Silvestres | Lacteos, Huevos y Congelados > Quesos | Higiene Personal > Jabon | Producto de higiene personal fuera de Higiene Personal |
| 1120 | Jabón Líquido Ballerina Yoghurt Y Berries Vainilla | Lacteos, Huevos y Congelados > Quesos | Higiene Personal > Jabon | Producto de higiene personal fuera de Higiene Personal |
| 1122 | Acondicionador Ballerina Largo Increible | Lacteos, Huevos y Congelados > Quesos | Higiene Personal > Acondicionador | Producto de higiene personal fuera de Higiene Personal |
| 1123 | Acondicionador Ballerina Natural Manzanilla | Lacteos, Huevos y Congelados > Quesos | Higiene Personal > Acondicionador | Producto de higiene personal fuera de Higiene Personal |
| 1124 | Acondicionador Ballerina Sin Sal Palta Y Almendra | Despensa > Salsas | Higiene Personal > Acondicionador | Producto de higiene personal fuera de Higiene Personal |
| 1126 | Acondicionador Ballerina Ondas Y Rizos Controlados | Lacteos, Huevos y Congelados > Quesos | Higiene Personal > Acondicionador | Producto de higiene personal fuera de Higiene Personal |
| 1127 | Acondicionador Ballerina Micelar Botella - Bajo Poo | Lacteos, Huevos y Congelados > Quesos | Higiene Personal > Acondicionador | Producto de higiene personal fuera de Higiene Personal |
| 1133 | Jabón Líquido Extra Suave Baby Line Doy Pack 750 ml Ballerina | Bebe > Alimentos Bebe | Higiene Personal > Jabon | Producto de higiene personal fuera de Higiene Personal |
| 1134 | Jabón Ballerina Energy | Lacteos, Huevos y Congelados > Quesos | Higiene Personal > Jabon | Producto de higiene personal fuera de Higiene Personal |
| 1136 | Jabón Crema Ballerina Triple Humectación Aceite De Karité | Despensa > Aceite | Higiene Personal > Jabon | Producto de higiene personal fuera de Higiene Personal |
| 1158 | Crema Facial Pack Hidratante + Luminosidad 1 Un Petrizzio | Lacteos, Huevos y Congelados > Crema | Higiene Personal > Cuidado Facial | Producto de higiene personal fuera de Higiene Personal |
| 1159 | Crema Facial Aclaradora 400 g Teatrical | Lacteos, Huevos y Congelados > Crema | Higiene Personal > Cuidado Facial | Producto de higiene personal fuera de Higiene Personal |
| 1160 | Crema Facial Antiarrugas 400 g Teatrical | Lacteos, Huevos y Congelados > Crema | Higiene Personal > Cuidado Facial | Producto de higiene personal fuera de Higiene Personal |
| 1279 | Mix Frutos Secos Mix Gourmet: Avellanas, Almendras, Maravilla Y Maní 300 gr Sembrasol | Bebe > Alimentos Bebe | Desayuno y Snacks > Snacks | Snack/fruto seco detectado dentro de categoria Bebe |
| 1291 | Frutos Secos Mix Cajuna 700 g Tribu | Bebe > Alimentos Bebe | Desayuno y Snacks > Snacks | Snack/fruto seco detectado dentro de categoria Bebe |
| 1293 | Mix Frutos Secos Mix De Almendras, Pasas Rubias Y Maní Tostado, Sin Sal 700 g Lider | Bebe > Alimentos Bebe | Desayuno y Snacks > Snacks | Snack/fruto seco detectado dentro de categoria Bebe |
| 1307 | Mix Frutos Secos Mix De Maní Confitado, Pasas Morenas, Almendras Y Pistacho, Sin Sal 700 g Lider | Bebe > Alimentos Bebe | Desayuno y Snacks > Snacks | Snack/fruto seco detectado dentro de categoria Bebe |
| 1336 | Mix Frutos Secos Mix Nuts Cajú, Almendras Y Maní 300 gr Sembrasol | Bebe > Alimentos Bebe | Desayuno y Snacks > Snacks | Snack/fruto seco detectado dentro de categoria Bebe |
| 1539 | Desinfectante Líquido Concentrado Para Frutas, Verduras Y Utensilios Botella 250 ml Germalimp | Frutas y Verduras > Frutas | Limpieza > Limpiadores | Producto de limpieza fuera de Limpieza |
| 1562 | Bebida Isotónica Frutas Tropicales Botella 500 ml Gatorade | Bebe > Alimentos Bebe | Bebidas > Bebidas | Bebida detectada dentro de categoria Bebe |
| 1567 | Néctar Durazno Frutas+vitamin Lata 340 ml Del Valle | Bebe > Alimentos Bebe | Bebidas > Jugos | Bebida detectada dentro de categoria Bebe |
| 1577 | Bebida Isotónica Frutas Tropicales Botella 1 L Gatorade | Bebe > Alimentos Bebe | Bebidas > Bebidas | Bebida detectada dentro de categoria Bebe |
| 1580 | Bebida Isotónica Frutas Tropicales Botella 750 ml Gatorade | Bebe > Alimentos Bebe | Bebidas > Bebidas | Bebida detectada dentro de categoria Bebe |
| 1655 | Bebida Hidratante Frutos Tropicales Botella 1 L Ironade | Bebe > Alimentos Bebe | Bebidas > Bebidas | Bebida detectada dentro de categoria Bebe |
| 1676 | Desodorante Ambiental Aerosol Placer Floral Y Frutos Rojos Lata 360 cc Glade | Frutas y Verduras > Frutas | Higiene Personal > Desodorantes | Producto de higiene personal fuera de Higiene Personal |
| 1678 | Desinfectante Aerosol Frutos Del Bosque Lata 360 ml Lysoform | Frutas y Verduras > Frutas | Limpieza > Limpiadores | Producto de limpieza fuera de Limpieza |
| 1680 | Kombucha Fruta Prensada En Frío Manzana Y Jengibre 475 ml Dr Kombu | Bebe > Alimentos Bebe | Bebidas > Jugos | Bebida detectada dentro de categoria Bebe |
| 1681 | Agua Saborizada Frutos Rojos Botella 1.5 L Benedictino | Bebe > Alimentos Bebe | Bebidas > Aguas | Bebida detectada dentro de categoria Bebe |
| 1683 | Bebida Hidratante Frutos Rojos Botella 630 ml Suerox | Bebe > Alimentos Bebe | Bebidas > Bebidas | Bebida detectada dentro de categoria Bebe |
| 1685 | Desodorante Ambiental Aerosol Frutos Del Sur Gatillo Frasco 250 ml Arom | Frutas y Verduras > Frutas | Higiene Personal > Desodorantes | Producto de higiene personal fuera de Higiene Personal |
| 1693 | Bebida Energética Sabor Fruta Del Dragón Lata 250 ml Red Bull | Bebe > Alimentos Bebe | Bebidas > Bebidas Energeticas | Bebida detectada dentro de categoria Bebe |
| 1695 | Agua Saborizada Power-c Fruta De Dragón Botella 500 ml Vitamin Water | Bebe > Alimentos Bebe | Bebidas > Aguas | Bebida detectada dentro de categoria Bebe |
| 1697 | Desodorante Ambiental Gel En Lata Frutos Silvestres Y Flor De Durazno 70 g Air Wick | Frutas y Verduras > Frutas | Higiene Personal > Desodorantes | Producto de higiene personal fuera de Higiene Personal |
| 1698 | Maní Japones Clásico 80 g Kazai | Bebe > Alimentos Bebe | Desayuno y Snacks > Snacks | Snack/fruto seco detectado dentro de categoria Bebe |
| 1700 | Desodorante Ambiental Aerosol Placer Floral Y Frutos Rojos Lata 255 ml Glade | Frutas y Verduras > Frutas | Higiene Personal > Desodorantes | Producto de higiene personal fuera de Higiene Personal |
| 1703 | Kombucha Fruta Prensada En Frío Mix Berries 475 ml Dr Kombu | Bebe > Alimentos Bebe | Bebidas > Jugos | Bebida detectada dentro de categoria Bebe |
| 1711 | Mani Cáscara Sembrasol 350 Grs | Bebe > Alimentos Bebe | Desayuno y Snacks > Snacks | Snack/fruto seco detectado dentro de categoria Bebe |
| 1713 | Maní Tostado Sin Sal 700 g Lider | Bebe > Alimentos Bebe | Desayuno y Snacks > Snacks | Snack/fruto seco detectado dentro de categoria Bebe |
| 1714 | Mani Con Sal De Mar 150 g Frutisa | Bebe > Alimentos Bebe | Desayuno y Snacks > Snacks | Snack/fruto seco detectado dentro de categoria Bebe |
| 1715 | Maní Tostado Sin Sal 400 g Sembrasol | Bebe > Alimentos Bebe | Desayuno y Snacks > Snacks | Snack/fruto seco detectado dentro de categoria Bebe |
| 1716 | Maní Tostado Sin Sal 150 g Sembrasol | Bebe > Alimentos Bebe | Desayuno y Snacks > Snacks | Snack/fruto seco detectado dentro de categoria Bebe |
| 1719 | Maní Japonés 350 g De La Rosa | Bebe > Alimentos Bebe | Desayuno y Snacks > Snacks | Snack/fruto seco detectado dentro de categoria Bebe |
| 1721 | Maní Sin Sal 150 g Marco Polo | Bebe > Alimentos Bebe | Desayuno y Snacks > Snacks | Snack/fruto seco detectado dentro de categoria Bebe |

## Recomendacion Fase 5F-FIX

- Aplicar solo hallazgos de Alta confianza en una fase separada con backup y rollback especifico.
- Revisar manualmente hallazgos de Media confianza antes de mover datos.
- Mantener sin cambios los falsos positivos probables.
- No recalcular producto_base hasta completar la correccion de categorias.
