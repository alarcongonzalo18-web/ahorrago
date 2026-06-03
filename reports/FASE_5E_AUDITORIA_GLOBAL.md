# Fase 5E Auditoria Global - AhorraGo

Modo: READ ONLY. No se modificaron datos, producto_base, categorias, usuarios ni frontend.

# Estado General

- total_productos: 31124
- total_precios: 31139
- total_producto_base: 27299
- total_equivalencias_productos: 6451
- total_equivalencias_grupos: 2626
- total_conflictos_grupos: 1891
- total_conflictos_pares_muestreados: 4014
- productos_sin_equivalencia: 24673

# Calidad de Datos

- Auditoria de categorias: 0 hallazgos.
- La base mantiene trazabilidad de Fases 5B, 5B-FIX, 5D-FIX y 5C.
- Los principales riesgos restantes estan en producto_base conflictivos y categorias de baja equivalencia.

# Matching

- Productos con equivalencia: 6451.
- Productos sin equivalencia: 24673.
- Grupos con equivalencia: 2626.
- Grupos conflictivos restantes: 1891.

# Cobertura

## Productos por Supermercado

| Supermercado | Productos con precio | Precios | Cobertura productos |
|---|---:|---:|---:|
| Jumbo | 23299 | 23299 | 74.86% |
| Líder | 6027 | 6027 | 19.36% |
| Unimarc | 1813 | 1813 | 5.83% |

## Cobertura por Categoria

| Categoria | Productos | Equivalencias | Conflictos | % equivalencia | % conflicto |
|---|---:|---:|---:|---:|---:|
| Bebe | 1471 | 384 | 320 | 26.1% | 21.75% |
| Bebidas | 4274 | 1231 | 910 | 28.8% | 21.29% |
| Carnes y Pescados | 2060 | 331 | 274 | 16.07% | 13.3% |
| Congelados | 1960 | 189 | 110 | 9.64% | 5.61% |
| Desayuno y Snacks | 4802 | 718 | 648 | 14.95% | 13.49% |
| Despensa | 4038 | 666 | 516 | 16.49% | 12.78% |
| Frutas y Verduras | 998 | 83 | 57 | 8.32% | 5.71% |
| Higiene Personal | 2800 | 674 | 536 | 24.07% | 19.14% |
| Lacteos, Huevos y Congelados | 5658 | 1078 | 750 | 19.05% | 13.26% |
| Limpieza | 1595 | 607 | 386 | 38.06% | 24.2% |
| Lácteos, Huevos y Congelados | 184 | 83 | 37 | 45.11% | 20.11% |
| Mascotas | 476 | 300 | 77 | 63.03% | 16.18% |
| Panaderia | 808 | 107 | 84 | 13.24% | 10.4% |

## Top Categorias con Mas Equivalencias

| Categoria | % equivalencia | Productos equivalentes |
|---|---:|---:|
| Mascotas | 63.03% | 300 |
| Lácteos, Huevos y Congelados | 45.11% | 83 |
| Limpieza | 38.06% | 607 |
| Bebidas | 28.8% | 1231 |
| Bebe | 26.1% | 384 |
| Higiene Personal | 24.07% | 674 |
| Lacteos, Huevos y Congelados | 19.05% | 1078 |
| Despensa | 16.49% | 666 |
| Carnes y Pescados | 16.07% | 331 |
| Desayuno y Snacks | 14.95% | 718 |

## Top Categorias con Menos Equivalencias

| Categoria | % equivalencia | Productos |
|---|---:|---:|
| Frutas y Verduras | 8.32% | 998 |
| Congelados | 9.64% | 1960 |
| Panaderia | 13.24% | 808 |
| Desayuno y Snacks | 14.95% | 4802 |
| Carnes y Pescados | 16.07% | 2060 |
| Despensa | 16.49% | 4038 |
| Lacteos, Huevos y Congelados | 19.05% | 5658 |
| Higiene Personal | 24.07% | 2800 |
| Bebe | 26.1% | 1471 |
| Bebidas | 28.8% | 4274 |

## Top Categorias con Mas Conflictos

| Categoria | Conflictos | % conflicto |
|---|---:|---:|
| Bebidas | 910 | 21.29% |
| Lacteos, Huevos y Congelados | 750 | 13.26% |
| Desayuno y Snacks | 648 | 13.49% |
| Higiene Personal | 536 | 19.14% |
| Despensa | 516 | 12.78% |
| Limpieza | 386 | 24.2% |
| Bebe | 320 | 21.75% |
| Carnes y Pescados | 274 | 13.3% |
| Congelados | 110 | 5.61% |
| Panaderia | 84 | 10.4% |

## Top Categorias con Menos Conflictos

| Categoria | Conflictos | % conflicto |
|---|---:|---:|
| Lácteos, Huevos y Congelados | 37 | 20.11% |
| Frutas y Verduras | 57 | 5.71% |
| Mascotas | 77 | 16.18% |
| Panaderia | 84 | 10.4% |
| Congelados | 110 | 5.61% |
| Carnes y Pescados | 274 | 13.3% |
| Bebe | 320 | 21.75% |
| Limpieza | 386 | 24.2% |
| Despensa | 516 | 12.78% |
| Higiene Personal | 536 | 19.14% |

# Conflictos

Top 100 conflictos restantes. Export completo: `reports/fase5e_top_conflictos.csv`.

| # | Producto | Categoria | Supermercado | Score | Motivo estimado |
|---:|---|---|---|---:|---|
| 1 | Fideo Pasta Spaghetti N°5 Bolsa 1 Kg Carozzi / Fideo Pasta Proteína Spaghetti N°5 Bolsa 400 g Lucchetti | Despensa | Líder / Líder | 49 | formato distinto; marca distinta; peso distinto; score bajo |
| 2 | Fideo Pasta Spaghetti N°5 Bolsa 1 Kg Carozzi / Fideo Pasta Spaghetti N°5 Bolsa 400 g Lider | Despensa | Líder / Líder | 52 | formato distinto; marca distinta; peso distinto; score bajo |
| 3 | Fideo Pasta Spaghetti N°5 Bolsa 1 Kg Carozzi / Fideo Pasta Spaghetti N°5 Bolsa 400 g Lucchetti | Despensa | Líder / Líder | 52 | formato distinto; marca distinta; peso distinto; score bajo |
| 4 | Desodorante Ambiental Air Wick Eléctrico Repuesto Lirios de Luna y Seda 21 ml 3 un. / Desodorante Ambiental Air Wick Eléctrico Repuesto Flores Desiert | Higiene Personal | Jumbo / Jumbo | 52 | cantidad distinta; formato distinto; score bajo; volumen distinto |
| 5 | Desodorante Ambiental Air Wick Eléctrico Repuesto Country Berry 21 ml 3 un. / Desodorante Ambiental Air Wick Eléctrico Repuesto Flores Desierto Atacam | Higiene Personal | Jumbo / Jumbo | 53 | cantidad distinta; formato distinto; score bajo; volumen distinto |
| 6 | Desodorante Ambiental Air Wick Eléctrico Repuesto Flores Desierto Atacama 20 ml 2 un. / Desodorante Ambiental Air Wick Eléctrico Repuesto Manzana & Ca | Higiene Personal | Jumbo / Jumbo | 53 | cantidad distinta; formato distinto; score bajo; volumen distinto |
| 7 | Snack Perro Pet's Fun Fémur de Vacuno 1.75 kg / Snack Perro Pet's Fun Fémur de Cerdo 2 un. | Carnes y Pescados | Jumbo / Jumbo | 54 | categoria distinta; formato distinto; score bajo |
| 8 | Desodorante Ambiental Air Wick Eléctrico Repuesto Vainilla 21 ml 3 un. / Desodorante Ambiental Air Wick Eléctrico Repuesto Flores Desierto Atacama 20  | Higiene Personal | Jumbo / Jumbo | 54 | cantidad distinta; formato distinto; score bajo; volumen distinto |
| 9 | Desodorante Spray Dove Men Invisible Dry y Cuidado Total 89 g 2 un. / Desodorante Spray Dove Men Invisible Dry 150 ml | Higiene Personal | Jumbo / Jumbo | 54 | formato distinto; score bajo |
| 10 | Yoghurt Protein Con Trozos Sabor Mango Maracuyá Pote 140 g Loncoleche / Yoghurt Protein Con Trozos Sabor Mango Maracuyá Pote 155 gr Soprole | Lacteos, Huevos y Congelados | Líder / Líder | 54 | marca distinta; peso distinto; score bajo |
| 11 | Desodorante Ambiental Air Wick Eléctrico Manzana Canela 21 ml 5 un. / Desodorante Ambiental Air Wick Eléctrico Manzana Navidad 3 un. | Higiene Personal | Jumbo / Jumbo | 55 | cantidad distinta; formato distinto; score bajo |
| 12 | Desodorante Ambiental Air Wick Freshmatic Manzana Navidad Full 1 Un / Desodorante Ambiental Air Wick Freshmatic Manzana Recarga 250 ml 2 Un | Higiene Personal | Jumbo / Jumbo | 55 | cantidad distinta; formato distinto; score bajo |
| 13 | Duraznos En Mitades Tarro Drenado 340 g - Neto 580 g Aconcagua / Duraznos En Mitades Tarro Drenado 480 g- Neto 820 g Lider | Despensa | Líder / Líder | 56 | formato distinto; peso distinto; score bajo |
| 14 | Duraznos En Mitades Tarro Drenado 340 g - Neto 590 g Wasil / Duraznos En Mitades Tarro Drenado 480 g- Neto 820 g Lider | Despensa | Líder / Líder | 56 | formato distinto; peso distinto; score bajo |
| 15 | Té Verde Chino Caja 20 Un Green / Té Verde Chino Caja 200 g Green | Despensa | Líder / Líder | 56 | formato distinto; score bajo |
| 16 | Desodorante Ambiental Air Wick Eléctrico Aparato + Repuesto Manzana Canela 21 ml / Desodorante Ambiental Air Wick Eléctrico Aparato + Recarga Manzana  | Higiene Personal | Jumbo / Jumbo | 56 | formato distinto; score bajo |
| 17 | Desodorante Ambiental Air Wick Eléctrico Repuesto 21 ml 3 un. / Desodorante Ambiental Air Wick Eléctrico Repuesto Flores Desierto Atacama 20 ml 2 un. | Higiene Personal | Jumbo / Jumbo | 56 | cantidad distinta; formato distinto; score bajo; volumen distinto |
| 18 | Bebida Energética Sin Azúcar Lata 473 ml Red Bull / Bebida Energética Zero Azúcar Lata 250 ml Red Bull | Bebe | Líder / Líder | 57 | formato distinto; score bajo; volumen distinto |
| 19 | Bebida Energética Zero Azúcar Lata 250 ml Red Bull / Bebida Energética Sin Azúcar Lata 355 ml Red Bull | Bebe | Líder / Líder | 57 | formato distinto; score bajo; volumen distinto |
| 20 | Jugo Natural Prensado Bless 07 Maracuyá, Naranja, Piña, Manzana y Limón 1 L / Jugo Prensado Bless 07 Maracuyá, Naranja, Piña y Manzana 300 ml | Bebidas | Jumbo / Jumbo | 57 | formato distinto; score bajo; volumen distinto |
| 21 | Jugo Natural Prensado Bless 45 Pepino, Espirulina, Manzana, Piña, Jengibre y Limón 1 L / Jugo Prensado Bless 45 Pepino, Espirulina, Manzana, Piña y Je | Bebidas | Jumbo / Jumbo | 57 | formato distinto; score bajo; volumen distinto |
| 22 | Hamburguesa De Vacuno Y Cerdo Con Carne Angus 100 g La Preferida / Hamburguesa De Vacuno Y Cerdo Con Carne De Angus Pack 10 Un 1 kg La Preferida | Congelados | Líder / Líder | 57 | formato distinto; peso distinto; score bajo |
| 23 | Galletas Oreo Selena Gomez Sabor Canela 108 g / Galletas Oreo Selena Gomez Sabor Canela 216 g 6 un. | Desayuno y Snacks | Jumbo / Jumbo | 57 | formato distinto; peso distinto; score bajo |
| 24 | Snack Perro Gran Cani Esófago de Bovino 250 g / Snack Perro Gran Cani Esófago de Bovino 4 un. | Desayuno y Snacks | Jumbo / Jumbo | 57 | formato distinto; score bajo |
| 25 | Crema Para Peinar Pantene Pro-v Rizos Definidos / Crema para Peinar Pantene Pro-V Bambú Nutre & Crece 300 ml | Despensa | Líder / Jumbo | 57 | categoria distinta; score bajo |
| 26 | Desodorante Barra Dove Men Cuidado Total 45 g / Desodorante Barra Dove Men Cuidado Total 50 g 2 un. | Higiene Personal | Jumbo / Jumbo | 57 | formato distinto; peso distinto; score bajo |
| 27 | Desodorante Spray Garnier Bí-O Protection 5 150 ml / Desodorante Spray Garnier Bí-O Protection 5 450 ml 3 un. | Higiene Personal | Jumbo / Jumbo | 57 | formato distinto; score bajo; volumen distinto |
| 28 | Desodorante Spray Garnier Bí-O Protection 5 Hombre 150 ml 2 un. / Desodorante Spray Garnier Bí-O Protection 5 450 ml 3 un. | Higiene Personal | Jumbo / Jumbo | 57 | cantidad distinta; formato distinto; score bajo; volumen distinto |
| 29 | Jabón Barra Le Sancy Frutos Rojos 3 un. 90 g / Jabón Barra Le Sancy Frutos Rojos 150 g 2 un. | Higiene Personal | Jumbo / Jumbo | 57 | cantidad distinta; formato distinto; peso distinto; score bajo |
| 30 | Jabón Barra Le Sancy Karité & Verbena 90 g 3 un. / Jabón Barra Le Sancy Karite & Verbena 2 un. de 150 g | Higiene Personal | Jumbo / Jumbo | 57 | cantidad distinta; formato distinto; peso distinto; score bajo |
| 31 | Crema Facial Día L’Oréal Revitalift Antiarrugas Láser 50 ml / Crema Facial Día L’Oréal Revitalift Ácido Hialurónico FPS 20 - 25 ml | Lacteos, Huevos y Congelados | Jumbo / Jumbo | 57 | formato distinto; score bajo; volumen distinto |
| 32 | Alimento Húmedo Perro Pet's Fun Paté Carne y Vegetales 170 g / Alimento Húmedo Perro Pet's Fun Trocitos Pollo Cordero y Pescado 100 g | Carnes y Pescados | Jumbo / Jumbo | 58 | categoria distinta; formato distinto; peso distinto; score bajo |
| 33 | Alimento Seco Cachorro Raza Mediana/grande Carne Bolsa 3 Kg Champion Dog / Alimento Seco Cachorro Raza Mediana/grande Sabor Pollo Bolsa 2,5 Kg Animal  | Carnes y Pescados | Líder / Líder | 58 | formato distinto; peso distinto; score bajo |
| 34 | Alimento Seco Cachorro Raza Mediana/grande Sabor Carne Y Leche Bolsa 3 Kg Master Dog / Alimento Seco Cachorro Raza Mediana/grande Sabor Pollo Bolsa 2, | Carnes y Pescados | Líder / Líder | 58 | formato distinto; peso distinto; score bajo |
| 35 | Alimento Seco Perro Adulto Raza Mediana/grande Carne Y Cereales Bolsa 3 Kg Champion Dog / Alimento Seco Perro Adulto Raza Mediana/grande Sabor Pollo B | Carnes y Pescados | Líder / Líder | 58 | categoria distinta; formato distinto; peso distinto; score bajo |
| 36 | Base Para Carne Mongoliana (5 Porciones) Sobre 30 g Lider / Base Para Carne Mongoliana (5 Porciones) Sobre 26 g Maggi | Carnes y Pescados | Líder / Líder | 58 | formato distinto; peso distinto; score bajo |
| 37 | Café En Cápsulas Single-origin Colombia Espresso 10 Un 57 g Starbucks by Nespresso / Café En Cápsulas Single-origin Colombia Espresso 12 Tazas 66 g St | Despensa | Líder / Líder | 58 | formato distinto; peso distinto; score bajo |
| 38 | Fideo Pasta Spaghetti N°5 Bolsa 500 g Barilla / Fideo Pasta Proteína Spaghetti N°5 Bolsa 400 g Lucchetti | Despensa | Líder / Líder | 58 | formato distinto; peso distinto; score bajo |
| 39 | Orégano Entero Bolsa 50 g Gourmet / Orégano Entero Natural Bolsa 20 g Gourmet | Despensa | Líder / Líder | 58 | formato distinto; peso distinto; score bajo |
| 40 | Pack 2 un. Antitranspirante Spray Nivea Tono Natural 50 ml / Pack 2 un. Antitranspirante Spray Nivea Men Fresh Active 91 g | Higiene Personal | Jumbo / Jumbo | 58 | formato distinto; score bajo |
| 41 | Pasta Dental Colgate Triple Acción Extra Frescura 90 g 3 un. / Pasta Dental Colgate Triple Acción Extra Blancura 125 ml | Higiene Personal | Jumbo / Jumbo | 58 | formato distinto; score bajo |
| 42 | Pasta Dental Oral-B 3D White Brilliant Fresh 53 ml / Pasta Dental Oral-B 3D White Glamorous 3 un. | Higiene Personal | Jumbo / Jumbo | 58 | formato distinto; score bajo |
| 43 | Pasta Dental Oral-B 3D White Brilliant Fresh 53 ml / Pasta Dental Oral-B 3D White Perfection 2 un. | Higiene Personal | Jumbo / Jumbo | 58 | formato distinto; score bajo |
| 44 | Pasta Dental Oral-B 3D White Mineral Clean 75 ml / Pasta Dental Oral-B 3D White Glamorous 3 un. | Higiene Personal | Jumbo / Jumbo | 58 | formato distinto; score bajo |
| 45 | Pasta Dental Oral-B 3D White Perfection 102 g / Pasta Dental Oral-B 3D White Glamorous 3 un. | Higiene Personal | Jumbo / Jumbo | 58 | formato distinto; score bajo |
| 46 | Pasta Dental Oral-B 3D White Perfection 2 un. / Pasta Dental Oral-B 3D White Mineral Clean 75 ml | Higiene Personal | Jumbo / Jumbo | 58 | formato distinto; score bajo |
| 47 | Shampoo Ballerina Natural Manzanilla Doypack / Shampoo Ballerina Manzanilla Doypack 750 ml | Higiene Personal | Líder / Jumbo | 58 | score bajo |
| 48 | Crema Facial Día L’Oréal Revitalift Láser Triple Acción Antiedad FPS 25 50 ml / Crema Facial Día L’Oréal Revitalift Ácido Hialurónico FPS 20 - 25 ml | Lacteos, Huevos y Congelados | Jumbo / Jumbo | 58 | formato distinto; score bajo; volumen distinto |
| 49 | Pack St. Ives: Crema Elastina 532 ml + Scrub Pink Lemon 170 g / Pack St. Ives: Crema Elastina + Scrub Apricot + Body Wash Karité | Lacteos, Huevos y Congelados | Jumbo / Jumbo | 58 | score bajo |
| 50 | Agua Mineral Cachantun Sin Gas 1.6 L / Agua Mineral Cachantun Light Gas 500 ml | Bebidas | Jumbo / Jumbo | 59 | formato distinto; score bajo; volumen distinto |
| 51 | Agua Mineral Cachantun Sin Gas 2.25 L / Agua Mineral Cachantun Light Gas 500 ml | Bebidas | Jumbo / Jumbo | 59 | formato distinto; score bajo; volumen distinto |
| 52 | Alimento Seco Perro Adulto Raza Mediana/grande Carne Y Cereales Bolsa 3 Kg Champion Dog / Alimento Seco Perro Adulto Raza Mediana/grande Pollo Y Carne | Carnes y Pescados | Líder / Líder | 59 | categoria distinta; formato distinto; peso distinto; score bajo |
| 53 | Hamburguesa Vegetal Receta del Abuelo Vegan Crispy Nugget 400 g / Hamburguesa Vegetal Receta del Abuelo Vegan Burger Queso Azul 100 g | Carnes y Pescados | Jumbo / Jumbo | 59 | categoria distinta; formato distinto; peso distinto; score bajo |
| 54 | Néctar Watt's Naranja Light 200 cc / Néctar Watt's Naranja 1.5 L | Desayuno y Snacks | Jumbo / Jumbo | 59 | categoria distinta; formato distinto; score bajo; volumen distinto |
| 55 | Néctar Watt's Naranja Light 200 cc / Néctar Watt's Naranja 300 ml | Desayuno y Snacks | Jumbo / Jumbo | 59 | categoria distinta; formato distinto; score bajo; volumen distinto |
| 56 | Néctar Watt's Piña Light 200 ml / Néctar Watt's Piña 1.5 L | Desayuno y Snacks | Jumbo / Jumbo | 59 | categoria distinta; formato distinto; score bajo; volumen distinto |
| 57 | Crema Para Peinar Pantene Pro-v Rizos Definidos / Crema para Peinar Pantene Pro-V Hidratación 300 ml | Despensa | Líder / Jumbo | 59 | categoria distinta; score bajo |
| 58 | Crema Para Peinar Pantene Pro-v Rizos Definidos / Crema para Peinar Pantene Pro-V Restauración 300 ml | Despensa | Líder / Jumbo | 59 | categoria distinta; score bajo |
| 59 | Jabón Líquido Ballerina Coco Jazmín 1.3 L / Jabón Ballerina Coco Jazmín 950 ml | Higiene Personal | Jumbo / Jumbo | 59 | formato distinto; score bajo; volumen distinto |
| 60 | Shampoo Herbal Essences Bio Renew Argan Oil 865 ml / Shampoo Herbal Essences Bio:Renew Argan Oil Of Morocco 400 ml | Higiene Personal | Jumbo / Jumbo | 59 | formato distinto; score bajo; volumen distinto |
| 61 | Crema Facial Día L’Oréal Revitalift Retinol FPS 17 - 50 ml / Crema Facial Día L’Oréal Revitalift Ácido Hialurónico FPS 20 - 25 ml | Lacteos, Huevos y Congelados | Jumbo / Jumbo | 59 | formato distinto; score bajo; volumen distinto |
| 62 | Crema Facial Día L’Oréal Revitalift Ácido Hialurónico FPS 20 - 25 ml / Crema Facial Día L’Oréal Revitalift Antiarrugas 50 ml | Lacteos, Huevos y Congelados | Jumbo / Jumbo | 59 | formato distinto; score bajo; volumen distinto |
| 63 | Quitamanchas Líquido Ropa Color Doypack 800 ml Vanish / Quitamanchas Polvo Ropa Color Doypack 450 g Vanish | Limpieza | Líder / Líder | 59 | formato distinto; score bajo |
| 64 | Quitamanchas Polvo Ropa Blanca Doypack 100 g Vanish / Quitamanchas Líquido Ropa Blanca Doypack 1.8 L Vanish | Limpieza | Líder / Líder | 59 | formato distinto; score bajo |
| 65 | Quitamanchas Polvo Ropa Blanca Doypack 100 g Vanish / Quitamanchas Líquido Ropa Blanca Doypack 800 ml Vanish | Limpieza | Líder / Líder | 59 | formato distinto; score bajo |
| 66 | Quitamanchas Polvo Ropa Color Doypack 450 g Vanish / Quitamanchas Líquido Ropa Color Doypack 1.8 L Vanish | Limpieza | Líder / Líder | 59 | formato distinto; score bajo |
| 67 | Agua Mineral Light Gas Botella 600 ml Cachantun / Agua Mineral Sin Gas Botella 1 L Cachantun | Bebe | Líder / Líder | 60 | formato distinto; score bajo; volumen distinto |
| 68 | Agua Mineral Light Gas Botella 600 ml Cachantun / Agua Mineral Sin Gas Botella 1,6 L Cachantun | Bebe | Líder / Líder | 60 | formato distinto; score bajo; volumen distinto |
| 69 | Agua Mineral Light Gas Botella 600 ml Cachantun / Agua Mineral Sin Gas Botella 2,5 L Cachantun | Bebe | Líder / Líder | 60 | formato distinto; score bajo; volumen distinto |
| 70 | Agua Mineral Sin Gas Botella 600 ml Cachantun / Agua Mineral Light Gas Botella 1,6 L Cachantun | Bebe | Líder / Líder | 60 | formato distinto; score bajo; volumen distinto |
| 71 | Jugo En Polvo Libre De Azúcar Pera De Agua 7g Sobre 1 Un Livean / Jugo En Polvo Libre De Azúcar Pera De Agua Sobre 8 g Vivo | Bebe | Líder / Líder | 60 | formato distinto; peso distinto; score bajo |
| 72 | Agua Mineral Cachantun Light Gas 1.6 L / Agua Mineral Cachantun Sin Gas 1 L | Bebidas | Jumbo / Jumbo | 60 | formato distinto; score bajo; volumen distinto |
| 73 | Agua Mineral Cachantun Light Gas 1.6 L / Agua Mineral Cachantun Sin Gas 500 ml | Bebidas | Jumbo / Jumbo | 60 | formato distinto; score bajo; volumen distinto |
| 74 | Agua Mineral Cachantun Light Gas 1.6 L / Agua Mineral Cachantun Sin Gas 6 L | Bebidas | Jumbo / Jumbo | 60 | formato distinto; score bajo; volumen distinto |
| 75 | Agua Mineral Cachantun Sin Gas 1 L / Agua Mineral Cachantun Light Gas 500 ml | Bebidas | Jumbo / Jumbo | 60 | formato distinto; score bajo; volumen distinto |
| 76 | Agua Mineral Cachantun Sin Gas 2.25 L / Agua Mineral Cachantun Light Gas 1.6 L | Bebidas | Jumbo / Jumbo | 60 | formato distinto; score bajo; volumen distinto |
| 77 | Agua Mineral Cachantun Sin Gas 6 L / Agua Mineral Cachantun Light Gas 500 ml | Bebidas | Jumbo / Jumbo | 60 | formato distinto; score bajo; volumen distinto |
| 78 | Agua Mineral Puyehue Gasificada 500 ml / Agua Mineral Puyehue Light Gasificada 1.5 L | Bebidas | Jumbo / Jumbo | 60 | formato distinto; score bajo; volumen distinto |
| 79 | Néctar del Valle Durazno 400 cc / Néctar del Valle Durazno Light 1 L | Bebidas | Jumbo / Jumbo | 60 | formato distinto; score bajo; volumen distinto |
| 80 | Néctar del Valle Naranja 400 cc / Néctar del Valle Naranja Light 1 L | Bebidas | Jumbo / Jumbo | 60 | formato distinto; score bajo; volumen distinto |
| 81 | Vino Miguel Torres Santa Digna Reserva Chardonnay 750 cc / Vino Miguel Torres Santa Digna Reserva Sauvignon Blanc 375 cc | Bebidas | Jumbo / Jumbo | 60 | formato distinto; score bajo; volumen distinto |
| 82 | Vino Santa Ema Select Terroir Reserva Cabernet Sauvignon 375 cc / Vino Santa Ema Select Terroir Reserva Carmenere 750 cc | Bebidas | Jumbo / Jumbo | 60 | formato distinto; score bajo; volumen distinto |
| 83 | Vino Santa Ema Select Terroir Reserva Cabernet Sauvignon 375 cc / Vino Santa Ema Select Terroir Reserva Chardonnay 750 cc | Bebidas | Jumbo / Jumbo | 60 | formato distinto; score bajo; volumen distinto |
| 84 | Vino Santa Ema Select Terroir Reserva Carmenere 375 cc / Vino Santa Ema Select Terroir Reserva Cabernet Sauvignon 750 cc | Bebidas | Jumbo / Jumbo | 60 | formato distinto; score bajo; volumen distinto |
| 85 | Vino Santa Ema Select Terroir Reserva Carmenere 375 cc / Vino Santa Ema Select Terroir Reserva Sauvignon Blanc 750 cc | Bebidas | Jumbo / Jumbo | 60 | formato distinto; score bajo; volumen distinto |
| 86 | Vino Santa Ema Select Terroir Reserva Carmenere 750 cc / Vino Santa Ema Select Terroir Reserva Sauvignon Blanc 375 cc | Bebidas | Jumbo / Jumbo | 60 | formato distinto; score bajo; volumen distinto |
| 87 | Vino Santa Ema Select Terroir Reserva Sauvignon Blanc 375 cc / Vino Santa Ema Select Terroir Reserva Chardonnay 750 cc | Bebidas | Jumbo / Jumbo | 60 | formato distinto; score bajo; volumen distinto |
| 88 | Vino Santa Rita 120 3 Medallas Cabernet Sauvignon 187 cc / Vino Santa Rita 120 3 Medallas Carmenere 700 cc | Bebidas | Jumbo / Jumbo | 60 | formato distinto; score bajo; volumen distinto |
| 89 | Vino Santa Rita 120 3 Medallas Cabernet Sauvignon 187 cc / Vino Santa Rita 120 3 Medallas Chardonnay 750 cc | Bebidas | Jumbo / Jumbo | 60 | formato distinto; score bajo; volumen distinto |
| 90 | Vino Santa Rita 120 3 Medallas Cabernet Sauvignon 700 cc / Vino Santa Rita 120 3 Medallas Chardonnay 750 cc | Bebidas | Jumbo / Jumbo | 60 | formato distinto; score bajo; volumen distinto |
| 91 | Vino Santa Rita 120 3 Medallas Carmenere 700 cc / Vino Santa Rita 120 3 Medallas Sauvignon Blanc 187 cc | Bebidas | Jumbo / Jumbo | 60 | formato distinto; score bajo; volumen distinto |
| 92 | Vino Santa Rita 120 3 Medallas Chardonnay 750 cc / Vino Santa Rita 120 3 Medallas Sauvignon Blanc 700 cc | Bebidas | Jumbo / Jumbo | 60 | formato distinto; score bajo; volumen distinto |
| 93 | Vino Santa Rita 120 3 Medallas Sauvignon Blanc 187 cc / Vino Santa Rita 120 3 Medallas Chardonnay 750 cc | Bebidas | Jumbo / Jumbo | 60 | formato distinto; score bajo; volumen distinto |
| 94 | Vino Santa Rita Medalla Real Reserva Cabernet Sauvignon 187 cc / Vino Santa Rita Medalla Real Reserva Chardonnay 750 cc | Bebidas | Jumbo / Jumbo | 60 | formato distinto; score bajo; volumen distinto |
| 95 | Vino Santa Rita Medalla Real Reserva Cabernet Sauvignon 187 cc / Vino Santa Rita Medalla Real Reserva Ensamblaje 750 cc | Bebidas | Jumbo / Jumbo | 60 | formato distinto; score bajo; volumen distinto |
| 96 | Vino Santa Rita Medalla Real Reserva Cabernet Sauvignon 375 cc / Vino Santa Rita Medalla Real Reserva Chardonnay 750 cc | Bebidas | Jumbo / Jumbo | 60 | formato distinto; score bajo; volumen distinto |
| 97 | Vino Santa Rita Medalla Real Reserva Cabernet Sauvignon 375 cc / Vino Santa Rita Medalla Real Reserva Ensamblaje 750 cc | Bebidas | Jumbo / Jumbo | 60 | formato distinto; score bajo; volumen distinto |
| 98 | Vino Santa Rita Medalla Real Reserva Carmenere 750 cc / Vino Santa Rita Medalla Real Reserva Cabernet Sauvignon 187 cc | Bebidas | Jumbo / Jumbo | 60 | formato distinto; score bajo; volumen distinto |
| 99 | Vino Santa Rita Medalla Real Reserva Carmenere 750 cc / Vino Santa Rita Medalla Real Reserva Cabernet Sauvignon 375 cc | Bebidas | Jumbo / Jumbo | 60 | formato distinto; score bajo; volumen distinto |
| 100 | Hamburguesa Vegetal Receta del Abuelo Vegan Crispy Nugget 400 g / Hamburguesa Vegetal Receta del Abuelo Vegan Burger Pepinillos 100 g | Carnes y Pescados | Jumbo / Jumbo | 60 | categoria distinta; formato distinto; peso distinto; score bajo |

# Productos Sin Matching

Top 100 productos sin equivalencia. Export completo: `reports/fase5e_top_sin_matching.csv`.

| # | Producto | Categoria | Supermercado | Clasificacion |
|---:|---|---|---|---|
| 1 | Agua Botella Purificada Con Gas 500 ml Benedictino | Bebe > Alimentos Bebe | Líder | posible error de matching |
| 2 | Agua Botella Purificada Sin Gas 500 ml Benedictino | Bebe > Alimentos Bebe | Líder | posible error de matching |
| 3 | Agua Botella Saborizada Manzana 2 L Benedictino | Bebe > Alimentos Bebe | Líder | posible error de matching |
| 4 | Agua Mineral Con Gas Botella 1,6 L Vital | Bebe > Alimentos Bebe | Líder | posible error de matching |
| 5 | Agua Mineral Sin Gas Botella 1,6 L Vital | Bebe > Alimentos Bebe | Líder | posible error de matching |
| 6 | Agua Saborizada Manzana Botella 500 ml Benedictino | Bebe > Alimentos Bebe | Líder | posible error de matching |
| 7 | Bebida Botella Sabor Original 591 ml Coca-Cola | Bebe > Alimentos Bebe | Líder | posible error de matching |
| 8 | Bebida Botella Sabor Original Limón 591 ml Sprite | Bebe > Alimentos Bebe | Líder | posible error de matching |
| 9 | Bebida Botella Sin Azúcar 591 ml Coca-Cola | Bebe > Alimentos Bebe | Líder | posible error de matching |
| 10 | Bebida Frambuesa Sin Azúcar Añadida Botella 500 Kombuchacha | Bebe > Alimentos Bebe | Líder | posible error de matching |
| 11 | Bebida Frambuesa Sin Azúcar Añadida Lata 355 Kombuchacha | Bebe > Alimentos Bebe | Líder | posible error de matching |
| 12 | Bebida Frutal Pack Lata 6 Un Bilz | Bebe > Alimentos Bebe | Líder | posible error de matching |
| 13 | Bebida Ginger Ale Pack Lata 6 Un Canada Dry | Bebe > Alimentos Bebe | Líder | posible error de matching |
| 14 | Bebida Light Botella 2 L Coca-Cola | Bebe > Alimentos Bebe | Líder | posible error de matching |
| 15 | Bebida Light Pack Lata 6 Un Coca-Cola | Bebe > Alimentos Bebe | Líder | posible error de matching |
| 16 | Bebida Limón Pack Lata 6 Un Sprite | Bebe > Alimentos Bebe | Líder | posible error de matching |
| 17 | Bebida Naranja Pack Lata 6 Un Fanta | Bebe > Alimentos Bebe | Líder | posible error de matching |
| 18 | Bebida Original Botella 1500 ml Pepsi | Bebe > Alimentos Bebe | Líder | posible error de matching |
| 19 | Bebida Original Botella 3 L Pepsi | Bebe > Alimentos Bebe | Líder | posible error de matching |
| 20 | Bebida Original Botella 600 ml Pepsi | Bebe > Alimentos Bebe | Líder | posible error de matching |
| 21 | Bebida Original Botella Retornable 2 L Inca Kola | Bebe > Alimentos Bebe | Líder | posible error de matching |
| 22 | Bebida Original Limón Botella 600 ml Limón Soda | Bebe > Alimentos Bebe | Líder | posible error de matching |
| 23 | Bebida Original Pack Lata 6 Un Coca-Cola | Bebe > Alimentos Bebe | Líder | posible error de matching |
| 24 | Bebida Original Pack Lata 6 Un Limón Soda | Bebe > Alimentos Bebe | Líder | posible error de matching |
| 25 | Bebida Papaya Botella | Bebe > Alimentos Bebe | Líder | posible error de matching |
| 26 | Bebida Papaya Original Botella | Bebe > Alimentos Bebe | Líder | posible error de matching |
| 27 | Bebida Papaya Pack Lata | Bebe > Alimentos Bebe | Líder | posible error de matching |
| 28 | Bebida Sabor Papaya Botella | Bebe > Alimentos Bebe | Líder | posible error de matching |
| 29 | Bebida Sabor Piña Botella 2500 ml Kem | Bebe > Alimentos Bebe | Líder | posible error de matching |
| 30 | Bebida Sin Azúcar Pack Lata 6 Un Coca-Cola | Bebe > Alimentos Bebe | Líder | posible error de matching |
| 31 | Bebida Zero Botella 3 L Pepsi | Bebe > Alimentos Bebe | Líder | posible error de matching |
| 32 | Bebida Zero Botella 600 ml Pepsi | Bebe > Alimentos Bebe | Líder | posible error de matching |
| 33 | Bebida Zero Pack Lata 6 Un Pepsi Zero | Bebe > Alimentos Bebe | Líder | posible error de matching |
| 34 | Caja de Toallas Húmedas Aqua Baby Bio 360 un. | Bebe > Panales | Jumbo | posible error de matching |
| 35 | Castañas De Caju 80 g Lider | Bebe > Alimentos Bebe | Líder | posible error de matching |
| 36 | Castañas De Cajú 400 g Lider | Bebe > Alimentos Bebe | Líder | posible error de matching |
| 37 | Detergente Líquido Hipoalergénico Bebé Botella 3 l Popeye | Bebe > Alimentos Bebe | Líder | posible error de matching |
| 38 | Emulsionado Neutro 700 ml Babyland | Bebe > Alimentos Bebe | Líder | posible error de matching |
| 39 | Emulsionado Neutro Botella 410 ml Babyland | Bebe > Alimentos Bebe | Líder | posible error de matching |
| 40 | Galletas Saladas 90 g Cracker | Bebe > Alimentos Bebe | Líder | posible error de matching |
| 41 | Galletas Saladas Pack 3 Un 270 g Cracker | Bebe > Alimentos Bebe | Líder | posible error de matching |
| 42 | Maní Con Pasas Bolsa 180 g Marco Polo | Bebe > Alimentos Bebe | Líder | posible error de matching |
| 43 | Maní Japonés 200 g Lider | Bebe > Alimentos Bebe | Líder | posible error de matching |
| 44 | Maní Japonés 400 g Lider | Bebe > Alimentos Bebe | Líder | posible error de matching |
| 45 | Maní Japonés Bolsa 200 g De La Rosa | Bebe > Alimentos Bebe | Líder | posible error de matching |
| 46 | Mix Nut Mix 2 350 g Marco Polo | Bebe > Alimentos Bebe | Líder | posible error de matching |
| 47 | Mix Nut Mix 350 g Marco Polo | Bebe > Alimentos Bebe | Líder | posible error de matching |
| 48 | Pañales Pampers Premium Care 14-18 kg Talla XXG 60 un. | Bebe > Panales | Jumbo | posible error de matching |
| 49 | Toallas Húmedas Aqua Baby Bio 60 un. | Bebe > Panales | Jumbo | posible error de matching |
| 50 | Agua Score Water Sin Gas 500 ml | Bebidas > Aguas | Jumbo | posible error de matching |
| 51 | Agua Score Water con Gas 500 ml | Bebidas > Aguas | Jumbo | posible error de matching |
| 52 | Agua Sin Gas Cachantún 2.5 L | Bebidas > Aguas | Jumbo | posible error de matching |
| 53 | Agua con Gas Cachantún 2.5 L | Bebidas > Aguas | Jumbo | posible error de matching |
| 54 | Aireador de Vino | Bebidas > Vinos | Jumbo | posible error de matching |
| 55 | Aireador para vino | Bebidas > Vinos | Jumbo | posible error de matching |
| 56 | Bebida 310 ml | Bebidas > Bebidas | Jumbo | posible error de matching |
| 57 | Bebida 7Up 3 L | Bebidas > Bebidas | Jumbo | posible error de matching |
| 58 | Bebida 7Up 500 ml | Bebidas > Bebidas | Jumbo | posible error de matching |
| 59 | Bebida Bilz 1.5 L | Bebidas > Bebidas | Jumbo | posible error de matching |
| 60 | Bebida Bilz 3 L | Bebidas > Bebidas | Jumbo | posible error de matching |
| 61 | Bebida Bilz 310 ml | Bebidas > Bebidas | Jumbo | posible error de matching |
| 62 | Bebida Bilz 350 cc | Bebidas > Bebidas | Jumbo | posible error de matching |
| 63 | Bebida Bilz 500 cc | Bebidas > Bebidas | Jumbo | posible error de matching |
| 64 | Bebida Bilz Zero 3 L | Bebidas > Bebidas | Jumbo | posible error de matching |
| 65 | Bebida Bilz Zero 500 cc | Bebidas > Bebidas | Jumbo | posible error de matching |
| 66 | Bebida Bilz Zero 600 ml | Bebidas > Bebidas | Jumbo | posible error de matching |
| 67 | Bebida Coca-Cola | Bebidas > Bebidas | Jumbo | posible error de matching |
| 68 | Bebida Coca-Cola Lata 350 cc | Bebidas > Bebidas | Jumbo | posible error de matching |
| 69 | Bebida Coca-Cola Lata Zero 350 ml | Bebidas > Bebidas | Jumbo | posible error de matching |
| 70 | Bebida Coca-Cola Light 2 L | Bebidas > Bebidas | Jumbo | posible error de matching |
| 71 | Bebida Coca-Cola Light 220 ml | Bebidas > Bebidas | Jumbo | posible error de matching |
| 72 | Bebida Coca-Cola Light 3 L | Bebidas > Bebidas | Jumbo | posible error de matching |
| 73 | Bebida Coca-Cola Light 591 ml | Bebidas > Bebidas | Jumbo | posible error de matching |
| 74 | Bebida Coca-Cola Light Lata 350 cc | Bebidas > Bebidas | Jumbo | posible error de matching |
| 75 | Bebida Coca-Cola Light Lata 350 ml | Bebidas > Bebidas | Jumbo | posible error de matching |
| 76 | Bebida Coca-Cola Original 2 L | Bebidas > Bebidas | Jumbo | posible error de matching |
| 77 | Bebida Coca-Cola Original 220 ml | Bebidas > Bebidas | Jumbo | posible error de matching |
| 78 | Bebida Coca-Cola Original 3 L | Bebidas > Bebidas | Jumbo | posible error de matching |
| 79 | Bebida Coca-Cola Original 591 ml | Bebidas > Bebidas | Jumbo | posible error de matching |
| 80 | Bebida Coca-Cola Zero 2 L | Bebidas > Bebidas | Jumbo | posible error de matching |
| 81 | Bebida Coca-Cola Zero 220 ml | Bebidas > Bebidas | Jumbo | posible error de matching |
| 82 | Bebida Coca-Cola Zero 3 L | Bebidas > Bebidas | Jumbo | posible error de matching |
| 83 | Bebida Coca-Cola Zero Lata 350 cc | Bebidas > Bebidas | Jumbo | posible error de matching |
| 84 | Bebida Coca-Cola Zero Lata 473 cc | Bebidas > Bebidas | Jumbo | posible error de matching |
| 85 | Bebida Crush 3 L | Bebidas > Bebidas | Jumbo | posible error de matching |
| 86 | Bebida Crush 350 ml | Bebidas > Bebidas | Jumbo | posible error de matching |
| 87 | Bebida Crush 500 ml | Bebidas > Bebidas | Jumbo | posible error de matching |
| 88 | Bebida Crush Light 500 ml | Bebidas > Bebidas | Jumbo | posible error de matching |
| 89 | Bebida Crush Light Lata 350 cc | Bebidas > Bebidas | Jumbo | posible error de matching |
| 90 | Bebida Crush Zero 3 L | Bebidas > Bebidas | Jumbo | posible error de matching |
| 91 | Bebida Crush Zero 350 ml | Bebidas > Bebidas | Jumbo | posible error de matching |
| 92 | Bebida Crush Zero 600 ml | Bebidas > Bebidas | Jumbo | posible error de matching |
| 93 | Bebida Energética Monster Mango Loco 473 cc | Bebidas > Bebidas | Jumbo | posible error de matching |
| 94 | Bebida Energética Monster Pipeline Punch 473 cc | Bebidas > Bebidas | Jumbo | posible error de matching |
| 95 | Bebida Energética Mr. Big Lata 473 cc | Bebidas > Bebidas | Jumbo | posible error de matching |
| 96 | Bebida Energética Mr. Big Panther 500 ml | Bebidas > Bebidas | Jumbo | posible error de matching |
| 97 | Bebida Energética Mr. Big Panther Botella 2 L | Bebidas > Bebidas | Jumbo | posible error de matching |
| 98 | Bebida Energética Mr. Big Panther Lata 473 cc | Bebidas > Bebidas | Jumbo | posible error de matching |
| 99 | Bebida Energética Red Bull Fruta del Dragón 250 ml | Bebidas > Bebidas | Jumbo | posible error de matching |
| 100 | Bebida Energética Rockstar 500 ml | Bebidas > Bebidas | Jumbo | posible error de matching |

# Riesgos

- Existen grupos de producto_base que aun mezclan formatos, volumenes o pesos.
- Algunas categorias de alto volumen mantienen baja equivalencia y requieren reglas especificas.
- Los productos exclusivos por supermercado pueden inflar el porcentaje sin equivalencia sin ser error real.
- Antes de usuarios, conviene mantener dashboard de calidad y auditoria automatica.

# Oportunidades

## Categorias prioritarias

| Categoria | Productos | % equivalencia | Conflictos |
|---|---:|---:|---:|
| Frutas y Verduras | 998 | 8.32% | 57 |
| Congelados | 1960 | 9.64% | 110 |
| Panaderia | 808 | 13.24% | 84 |
| Desayuno y Snacks | 4802 | 14.95% | 648 |
| Carnes y Pescados | 2060 | 16.07% | 274 |
| Despensa | 4038 | 16.49% | 516 |
| Lacteos, Huevos y Congelados | 5658 | 19.05% | 750 |
| Higiene Personal | 2800 | 24.07% | 536 |
| Bebe | 1471 | 26.1% | 320 |
| Bebidas | 4274 | 28.8% | 910 |

## Categorias maduras

| Categoria | Productos | % equivalencia | Conflictos |
|---|---:|---:|---:|

# Recomendaciones

- Fase 6 deberia construir dashboard operativo usando `reports/dashboard_dataset.csv`.
- Priorizar reglas por categoria con alto volumen y baja equivalencia.
- Separar productos exclusivos de errores reales de matching para no perseguir falsos problemas.
- No ampliar matching automatico sin lista blanca o reglas de categoria especificas.
- Mantener rollback por fase y reportes PDF/CSV como requisito permanente.

# Preparacion para Usuarios

- La auditoria de categorias esta en 0 hallazgos, buen requisito previo.
- El matching ya tiene trazabilidad por fase y endpoint diagnostico actualizado.
- Antes de usuarios reales, conviene exponer alertas internas de baja cobertura y conflictos altos.
- Fase 6 puede enfocarse en dashboard, observabilidad y decision de reglas futuras, no en login todavia.
