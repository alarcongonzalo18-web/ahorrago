# Fase 5D Analisis - Clasificacion de Hallazgos

Analisis read-only basado en `reports/auditoria_categorias.csv`. No modifica la base de datos.

## Resumen

- Hallazgos clasificados: 95
- alimento_en_limpieza: 31
- mascota_en_higiene: 53
- bebida_en_mascotas: 11

## Categorias Sugeridas

| Tipo | Categoria sugerida | Confianza | Cantidad |
|---|---|---:|---:|
| alimento_en_limpieza | Despensa | Alta | 15 |
| alimento_en_limpieza | Higiene Personal | Alta | 5 |
| alimento_en_limpieza | Limpieza | Alta | 11 |
| bebida_en_mascotas | Mascotas | Alta | 11 |
| mascota_en_higiene | Higiene Personal | Alta | 9 |
| mascota_en_higiene | Mascotas | Alta | 44 |

## alimento_en_limpieza

| ID | Producto | Categoria actual | Categoria sugerida | Confianza | Motivo |
|---:|---|---|---|---|---|
| 389 | Fideo Pasta Al Huevo Nidos De Fetuccini Bolsa 400 g Talliani | Limpieza > Blanqueadores | Despensa | Alta | Producto alimenticio tipo fideo/pasta; corresponde a Despensa, idealmente subcategoria Fideos. |
| 3478 | Fideo Pasta Espirales Bolsa 400 g Lider | Limpieza > Blanqueadores | Despensa | Alta | Producto alimenticio tipo fideo/pasta; corresponde a Despensa, idealmente subcategoria Fideos. |
| 3489 | Pasta Fideos Instantáneos Sabor Pollo 69 g Nissin | Limpieza > Blanqueadores | Despensa | Alta | Producto alimenticio tipo fideo/pasta; corresponde a Despensa, idealmente subcategoria Fideos. |
| 3492 | Pasta Fideos Instantáneos Ramen Sabor Pollo Bolsa 85 g Nissin | Limpieza > Blanqueadores | Despensa | Alta | Producto alimenticio tipo fideo/pasta; corresponde a Despensa, idealmente subcategoria Fideos. |
| 3504 | Fideo Pasta Caracoquesos 4 Quesos Caja 296 g Carozzi | Limpieza > Blanqueadores | Despensa | Alta | Producto alimenticio tipo fideo/pasta; corresponde a Despensa, idealmente subcategoria Fideos. |
| 3505 | Fideo Pasta Espiral N°49 1 kg Carozzi | Limpieza > Blanqueadores | Despensa | Alta | Producto alimenticio tipo fideo/pasta; corresponde a Despensa, idealmente subcategoria Fideos. |
| 3509 | Fideo Pasta Spaghettini N°3 Bolsa 500 g Barilla | Limpieza > Blanqueadores | Despensa | Alta | Producto alimenticio tipo fideo/pasta; corresponde a Despensa, idealmente subcategoria Fideos. |
| 3510 | Fideo Pasta Spaghetti N°5 Bolsa 500 g Barilla | Limpieza > Blanqueadores | Despensa | Alta | Producto alimenticio tipo fideo/pasta; corresponde a Despensa, idealmente subcategoria Fideos. |
| 3511 | Fideo Pasta Bavette N°13 Caja 500 g Barilla | Limpieza > Blanqueadores | Despensa | Alta | Producto alimenticio tipo fideo/pasta; corresponde a Despensa, idealmente subcategoria Fideos. |
| 3512 | Fideo Pasta Fusilli N°98 Caja 500 g Barilla | Limpieza > Blanqueadores | Despensa | Alta | Producto alimenticio tipo fideo/pasta; corresponde a Despensa, idealmente subcategoria Fideos. |
| 3513 | Fideo Pasta Spaghetti N°7 Bolsa 500 g Barilla | Limpieza > Blanqueadores | Despensa | Alta | Producto alimenticio tipo fideo/pasta; corresponde a Despensa, idealmente subcategoria Fideos. |
| 3515 | Fideo Pasta Penne Rigate N°73 Caja 500 g Barilla | Limpieza > Blanqueadores | Despensa | Alta | Producto alimenticio tipo fideo/pasta; corresponde a Despensa, idealmente subcategoria Fideos. |
| 3517 | Fideo Pasta Macaroni & Cheese Caja 296 g Lucchetti | Limpieza > Blanqueadores | Despensa | Alta | Producto alimenticio tipo fideo/pasta; corresponde a Despensa, idealmente subcategoria Fideos. |
| 3528 | Fideo Pasta Macaroni & Cheese Original Caja 225 g Great Value | Limpieza > Blanqueadores | Despensa | Alta | Producto alimenticio tipo fideo/pasta; corresponde a Despensa, idealmente subcategoria Fideos. |
| 3786 | Pasta Para Uno Caracoquesos Cup 70 g Carozzi | Limpieza > Blanqueadores | Despensa | Alta | Producto alimenticio tipo fideo/pasta; corresponde a Despensa, idealmente subcategoria Fideos. |
| 25316 | Pasta Limpiadora The Pink Stuff Multiuso 850 g | Limpieza > Limpiadores | Limpieza | Alta | Falso positivo de auditoria: pasta/kit de limpieza multiuso, categoria actual consistente. |
| 25326 | Pasta de Limpieza Fibro Glow 500 g | Limpieza > Limpiadores | Limpieza | Alta | Falso positivo de auditoria: pasta/kit de limpieza multiuso, categoria actual consistente. |
| 25390 | Pasta de Limpieza Fibro Glow 200 g | Limpieza > Limpiadores | Limpieza | Alta | Falso positivo de auditoria: pasta/kit de limpieza multiuso, categoria actual consistente. |
| 25599 | Leche Limpiadora Petrizzio 200 ml + Loción Tonic 200 ml | Limpieza > Limpiadores | Higiene Personal | Alta | Producto de limpieza facial/cosmetica; no es limpieza del hogar. |
| 25601 | Leche Nivea Facial Limpiador Suave 200 ml | Limpieza > Limpiadores | Higiene Personal | Alta | Producto de limpieza facial/cosmetica; no es limpieza del hogar. |
| 25685 | Betún Pasta Calzado Virginia Bio Café 80 ml | Limpieza > Limpiadores | Limpieza | Alta | Falso positivo de auditoria: betun/pasta para calzado, categoria actual razonable. |
| 25717 | Betún Pasta Calzado Nugget Café 65 g | Limpieza > Limpiadores | Limpieza | Alta | Falso positivo de auditoria: betun/pasta para calzado, categoria actual razonable. |
| 25723 | Betún Pasta Calzado Nugget Negra 65 g | Limpieza > Limpiadores | Limpieza | Alta | Falso positivo de auditoria: betun/pasta para calzado, categoria actual razonable. |
| 25736 | Kit Pasta + Esponja The Pink Stuff | Limpieza > Limpiadores | Limpieza | Alta | Falso positivo de auditoria: pasta/kit de limpieza multiuso, categoria actual consistente. |
| 25749 | Leche & Tónico Micelar Nivea Rose Care 2en1 - 200 ml | Limpieza > Limpiadores | Higiene Personal | Alta | Producto de limpieza facial/cosmetica; no es limpieza del hogar. |
| 25770 | Leche Limpieza Facial La Roche Posay Toleriane 200 ml | Limpieza > Limpiadores | Higiene Personal | Alta | Producto de limpieza facial/cosmetica; no es limpieza del hogar. |
| 25787 | Leche Limpiadora Nivea Piel Seca 200 ml | Limpieza > Limpiadores | Higiene Personal | Alta | Producto de limpieza facial/cosmetica; no es limpieza del hogar. |
| 25853 | Betún Pasta Calzado Virginia Bio Negro 50 ml | Limpieza > Limpiadores | Limpieza | Alta | Falso positivo de auditoria: betun/pasta para calzado, categoria actual razonable. |
| 25854 | Betún Pasta Calzado Virginia Bio Café 50 ml | Limpieza > Limpiadores | Limpieza | Alta | Falso positivo de auditoria: betun/pasta para calzado, categoria actual razonable. |
| 25892 | Betún Pasta Calzado Virginia Bio Negro 80 ml | Limpieza > Limpiadores | Limpieza | Alta | Falso positivo de auditoria: betun/pasta para calzado, categoria actual razonable. |
| 25908 | Pasta Limpiadora Multiuso The Pink Stuff 500 g | Limpieza > Limpiadores | Limpieza | Alta | Falso positivo de auditoria: pasta/kit de limpieza multiuso, categoria actual consistente. |

## mascota_en_higiene

| ID | Producto | Categoria actual | Categoria sugerida | Confianza | Motivo |
|---:|---|---|---|---|---|
| 3718 | Shampoo Herbal Essences Sin Sal Nutre E Hidrata Pequi & Aguacate | Higiene Personal > Shampoo | Higiene Personal | Alta | Falso positivo de auditoria por substring como cat en aguacate o food en Hair Food; producto humano. |
| 5455 | Shampoo Garnier Fructis Hair Food Aguacate | Higiene Personal > Shampoo | Higiene Personal | Alta | Falso positivo de auditoria por substring como cat en aguacate o food en Hair Food; producto humano. |
| 5624 | Shampoo Para Perro Antiparasitario Botella 300 ml Sinpul | Higiene Personal > Shampoo | Mascotas | Alta | Producto de higiene para perro/gato; corresponde a Mascotas, no Higiene Personal humana. |
| 5638 | Shampoo Para Perro Balsamico Uso Frecuente Botella 390 ml Canish | Higiene Personal > Shampoo | Mascotas | Alta | Producto de higiene para perro/gato; corresponde a Mascotas, no Higiene Personal humana. |
| 5640 | Shampoo Para Perro Balsámico Aroma Vainilla Botella 1000 ml Buddy Pet | Higiene Personal > Shampoo | Mascotas | Alta | Producto de higiene para perro/gato; corresponde a Mascotas, no Higiene Personal humana. |
| 5643 | Shampoo Para Perro Repelente Pulgas Aroma Eucalipto Botella 1000 ml Buddy Pet | Higiene Personal > Shampoo | Mascotas | Alta | Producto de higiene para perro/gato; corresponde a Mascotas, no Higiene Personal humana. |
| 5644 | Shampoo Para Perro Espuma Seca Aroma Granada Lata 230 ml Buddy Pet | Higiene Personal > Shampoo | Mascotas | Alta | Producto de higiene para perro/gato; corresponde a Mascotas, no Higiene Personal humana. |
| 5647 | Shampoo Para Gato Seco Repelente Pulgas Aroma Eucaliptus Lata 100 g Buddy Pet | Higiene Personal > Shampoo | Mascotas | Alta | Producto de higiene para perro/gato; corresponde a Mascotas, no Higiene Personal humana. |
| 5649 | Shampoo Para Perro Pelaje Claro Con Aloe Vera Aroma Frambuesa Y Papaya Botella 300 ml Buddy Pet | Higiene Personal > Shampoo | Mascotas | Alta | Producto de higiene para perro/gato; corresponde a Mascotas, no Higiene Personal humana. |
| 5650 | Shampoo Para Perro 2 En 1 Con Balsamo Aroma Vainilla Botella 300 ml Buddy Pet | Higiene Personal > Shampoo | Mascotas | Alta | Producto de higiene para perro/gato; corresponde a Mascotas, no Higiene Personal humana. |
| 5651 | Shampoo Para Perro Hipoalergenico Uso Frecuente Botella 390 ml Canish | Higiene Personal > Shampoo | Mascotas | Alta | Producto de higiene para perro/gato; corresponde a Mascotas, no Higiene Personal humana. |
| 5655 | Shampoo Para Perro Seco Aroma Eucaliptus Lata 100 g Buddy Pet | Higiene Personal > Shampoo | Mascotas | Alta | Producto de higiene para perro/gato; corresponde a Mascotas, no Higiene Personal humana. |
| 5656 | Shampoo Para Perro Repelente Con Aloe Vera Aroma Eucaliptus Botella 300 ml Buddy Pet | Higiene Personal > Shampoo | Mascotas | Alta | Producto de higiene para perro/gato; corresponde a Mascotas, no Higiene Personal humana. |
| 26165 | Shampoo Fructis Hair Food Aguacate 300 ml | Higiene Personal > Shampoo | Higiene Personal | Alta | Falso positivo de auditoria por substring como cat en aguacate o food en Hair Food; producto humano. |
| 26303 | Shampoo Cantu Aguacate 400 ml | Higiene Personal > Shampoo | Higiene Personal | Alta | Falso positivo de auditoria por substring como cat en aguacate o food en Hair Food; producto humano. |
| 26362 | Shampoo Perro Pet's Fun en Seco 100 g | Higiene Personal > Shampoo | Mascotas | Alta | Producto de higiene para perro/gato; corresponde a Mascotas, no Higiene Personal humana. |
| 26393 | Shampoo Perro Pet's Fun Pelaje Blanco 290 cc | Higiene Personal > Shampoo | Mascotas | Alta | Producto de higiene para perro/gato; corresponde a Mascotas, no Higiene Personal humana. |
| 26400 | Shampoo Perro Pet's Fun Desenredante 290 cc | Higiene Personal > Shampoo | Mascotas | Alta | Producto de higiene para perro/gato; corresponde a Mascotas, no Higiene Personal humana. |
| 26408 | Shampoo Perro Pet's Fun Hipoalergénico 290 cc | Higiene Personal > Shampoo | Mascotas | Alta | Producto de higiene para perro/gato; corresponde a Mascotas, no Higiene Personal humana. |
| 26514 | Shampoo Perro Canish en Seco 160 g | Higiene Personal > Shampoo | Mascotas | Alta | Producto de higiene para perro/gato; corresponde a Mascotas, no Higiene Personal humana. |
| 26516 | Shampoo Gato Tidy En Seco Perfumado 200 g | Higiene Personal > Shampoo | Mascotas | Alta | Producto de higiene para perro/gato; corresponde a Mascotas, no Higiene Personal humana. |
| 26521 | Shampoo Gato Traper Espuma En Seco 170 ml | Higiene Personal > Shampoo | Mascotas | Alta | Producto de higiene para perro/gato; corresponde a Mascotas, no Higiene Personal humana. |
| 26528 | Shampoo Perro Tidy En Seco Perfumado 100 g | Higiene Personal > Shampoo | Mascotas | Alta | Producto de higiene para perro/gato; corresponde a Mascotas, no Higiene Personal humana. |
| 26531 | Shampoo Perro Traper Espuma En Seco 170 ml | Higiene Personal > Shampoo | Mascotas | Alta | Producto de higiene para perro/gato; corresponde a Mascotas, no Higiene Personal humana. |
| 26535 | Shampoo Perro Canish Hipoalergénico 300 ml | Higiene Personal > Shampoo | Mascotas | Alta | Producto de higiene para perro/gato; corresponde a Mascotas, no Higiene Personal humana. |
| 26536 | Shampoo Perro Drag Pharma Antiparasitario 100 ml | Higiene Personal > Shampoo | Mascotas | Alta | Producto de higiene para perro/gato; corresponde a Mascotas, no Higiene Personal humana. |
| 26537 | Shampoo Gato Traper Neutro 260 cc | Higiene Personal > Shampoo | Mascotas | Alta | Producto de higiene para perro/gato; corresponde a Mascotas, no Higiene Personal humana. |
| 26559 | Shampoo Perro Adulto Traper Neutro Hipóalergénico 260 cc | Higiene Personal > Shampoo | Mascotas | Alta | Producto de higiene para perro/gato; corresponde a Mascotas, no Higiene Personal humana. |
| 26562 | Shampoo y Acondicionador Perro Canish 300 ml | Higiene Personal > Shampoo | Mascotas | Alta | Producto de higiene para perro/gato; corresponde a Mascotas, no Higiene Personal humana. |
| 26564 | Shampoo Perros Eco Traper Pieles Sensibles 250 ml | Higiene Personal > Shampoo | Mascotas | Alta | Producto de higiene para perro/gato; corresponde a Mascotas, no Higiene Personal humana. |
| 26565 | Shampoo Perro Canish 390 ml | Higiene Personal > Shampoo | Mascotas | Alta | Producto de higiene para perro/gato; corresponde a Mascotas, no Higiene Personal humana. |
| 26568 | Shampoo Perro Adulto Traper Aloe Piel Sensible 260 cc | Higiene Personal > Shampoo | Mascotas | Alta | Producto de higiene para perro/gato; corresponde a Mascotas, no Higiene Personal humana. |
| 26569 | Shampoo Perro Traper Extra Brillo y Suavidad 260 ml | Higiene Personal > Shampoo | Mascotas | Alta | Producto de higiene para perro/gato; corresponde a Mascotas, no Higiene Personal humana. |
| 26571 | Shampoo Perro Adulto Traper Manzanilla 260 cc | Higiene Personal > Shampoo | Mascotas | Alta | Producto de higiene para perro/gato; corresponde a Mascotas, no Higiene Personal humana. |
| 26572 | Shampoo Perro Cachorro Traper Neutro Cereza 260 cc | Higiene Personal > Shampoo | Mascotas | Alta | Producto de higiene para perro/gato; corresponde a Mascotas, no Higiene Personal humana. |
| 26573 | Shampoo Perro Sinpul Antiparasitario 300 cc | Higiene Personal > Shampoo | Mascotas | Alta | Producto de higiene para perro/gato; corresponde a Mascotas, no Higiene Personal humana. |
| 26574 | Shampoo Perro Pets & Friends Pelaje Blanco 250 cc | Higiene Personal > Shampoo | Mascotas | Alta | Producto de higiene para perro/gato; corresponde a Mascotas, no Higiene Personal humana. |
| 26575 | Shampoo Perro Drag Pharma 360 cc | Higiene Personal > Shampoo | Mascotas | Alta | Producto de higiene para perro/gato; corresponde a Mascotas, no Higiene Personal humana. |
| 26578 | Acondicionador Perro Adulto Traper Desenredante 260 cc | Higiene Personal > Shampoo | Mascotas | Alta | Producto de higiene para perro/gato; corresponde a Mascotas, no Higiene Personal humana. |
| 26579 | Acondicionador Perros Traper Cachorro 260 cc | Higiene Personal > Shampoo | Mascotas | Alta | Producto de higiene para perro/gato; corresponde a Mascotas, no Higiene Personal humana. |
| 26580 | Shampoo Perro Pets & Friends 250 cc | Higiene Personal > Shampoo | Mascotas | Alta | Producto de higiene para perro/gato; corresponde a Mascotas, no Higiene Personal humana. |
| 26599 | Shampoo Gato Pet's Fun en Seco 100 g | Higiene Personal > Shampoo | Mascotas | Alta | Producto de higiene para perro/gato; corresponde a Mascotas, no Higiene Personal humana. |
| 26600 | Shampoo Perro Pet's Fun en Seco 160 g | Higiene Personal > Shampoo | Mascotas | Alta | Producto de higiene para perro/gato; corresponde a Mascotas, no Higiene Personal humana. |
| 26608 | Shampoo Perro Pets & Friends Matico 320 cc | Higiene Personal > Shampoo | Mascotas | Alta | Producto de higiene para perro/gato; corresponde a Mascotas, no Higiene Personal humana. |
| 26609 | Shampoo Perro Pets & Friends Cobre 320 cc | Higiene Personal > Shampoo | Mascotas | Alta | Producto de higiene para perro/gato; corresponde a Mascotas, no Higiene Personal humana. |
| 26669 | Shampoo Original Remedies Délicatesse de Avena 300 ml | Higiene Personal > Shampoo | Higiene Personal | Alta | Falso positivo de auditoria por substring como cat en aguacate o food en Hair Food; producto humano. |
| 26677 | Shampoo Perro Pets & Friends Cachorros 250 cc | Higiene Personal > Shampoo | Mascotas | Alta | Producto de higiene para perro/gato; corresponde a Mascotas, no Higiene Personal humana. |
| 26678 | Shampoo Fructis Hair Food Aguacate 300 ml + Bálsamo 300 ml | Higiene Personal > Shampoo | Higiene Personal | Alta | Falso positivo de auditoria por substring como cat en aguacate o food en Hair Food; producto humano. |
| 26737 | Shampoo Perro Pets & Friends Hipoalergénico 250 ml | Higiene Personal > Shampoo | Mascotas | Alta | Producto de higiene para perro/gato; corresponde a Mascotas, no Higiene Personal humana. |
| 26741 | Shampoo Perro Pets & Friends Balsámico 250 ml | Higiene Personal > Shampoo | Mascotas | Alta | Producto de higiene para perro/gato; corresponde a Mascotas, no Higiene Personal humana. |
| 26896 | Acondicionador Fructis Hair Food Aguacate 300 ml | Higiene Personal > Acondicionador | Higiene Personal | Alta | Falso positivo de auditoria por substring como cat en aguacate o food en Hair Food; producto humano. |
| 27004 | Acondicionador Cantu Aguacate 400 ml | Higiene Personal > Acondicionador | Higiene Personal | Alta | Falso positivo de auditoria por substring como cat en aguacate o food en Hair Food; producto humano. |
| 27217 | Acondicionador Original Remedies Délicatesse de Avena 250 ml | Higiene Personal > Acondicionador | Higiene Personal | Alta | Falso positivo de auditoria por substring como cat en aguacate o food en Hair Food; producto humano. |

## bebida_en_mascotas

| ID | Producto | Categoria actual | Categoria sugerida | Confianza | Motivo |
|---:|---|---|---|---|---|
| 1988 | Alimento Húmedo Gato Adulto Sabor Pechuga De Pollo Con Salmón Al Jugo Pouch 85 g Animal Planet | Mascotas > Alimento Gatos | Mascotas | Alta | Falso positivo de auditoria: alimento humedo/trocitos jugosos para perro/gato; no corresponde mover a Bebidas. |
| 1990 | Alimento Húmedo Perro Adulto Y Cachorro Sabor Pechuga De Pollo Con Salmón Al Jugo Pouch 100 g Animal Planet | Mascotas > Alimento Perros | Mascotas | Alta | Falso positivo de auditoria: alimento humedo/trocitos jugosos para perro/gato; no corresponde mover a Bebidas. |
| 29019 | Alimento Perro Adulto Master Dog Trocitos Jugosos Razas Pequeñas 85 g | Mascotas > Alimento Perros | Mascotas | Alta | Falso positivo de auditoria: alimento humedo/trocitos jugosos para perro/gato; no corresponde mover a Bebidas. |
| 29027 | Alimento Húmedo Perro Cachorro Master Dog Trocitos Jugosos 85 g | Mascotas > Alimento Perros | Mascotas | Alta | Falso positivo de auditoria: alimento humedo/trocitos jugosos para perro/gato; no corresponde mover a Bebidas. |
| 29039 | Trocitos Jugosos Master Dog Senior 100 g | Mascotas > Alimento Perros | Mascotas | Alta | Falso positivo de auditoria: alimento humedo/trocitos jugosos para perro/gato; no corresponde mover a Bebidas. |
| 29073 | Alimento Húmedo Perro Adulto Cannes Trocitos Jugosos Pollo 375 g | Mascotas > Alimento Perros | Mascotas | Alta | Falso positivo de auditoria: alimento humedo/trocitos jugosos para perro/gato; no corresponde mover a Bebidas. |
| 29075 | Alimento Húmedo Perro Adulto Cannes Trocitos Jugosos Pollo 100 g | Mascotas > Alimento Perros | Mascotas | Alta | Falso positivo de auditoria: alimento humedo/trocitos jugosos para perro/gato; no corresponde mover a Bebidas. |
| 29164 | Alimento Húmedo Gatito Master Cat Trocitos Jugosos 85 g | Mascotas > Alimento Gatos | Mascotas | Alta | Falso positivo de auditoria: alimento humedo/trocitos jugosos para perro/gato; no corresponde mover a Bebidas. |
| 29232 | Trocitos Jugosos Master Cat Sabor Atún 85 g | Mascotas > Alimento Gatos | Mascotas | Alta | Falso positivo de auditoria: alimento humedo/trocitos jugosos para perro/gato; no corresponde mover a Bebidas. |
| 29269 | Trocitos Jugosos Master Cat Senior Sabor Pollo 85 g | Mascotas > Alimento Gatos | Mascotas | Alta | Falso positivo de auditoria: alimento humedo/trocitos jugosos para perro/gato; no corresponde mover a Bebidas. |
| 29310 | Pack 5 un. Alimento Húmedo Gato Master Cat Trocitos Jugosos | Mascotas > Alimento Gatos | Mascotas | Alta | Falso positivo de auditoria: alimento humedo/trocitos jugosos para perro/gato; no corresponde mover a Bebidas. |

## Recomendacion

- No aplicar correcciones automaticamente todavia.
- Priorizar correcciones con confianza Alta y categoria sugerida distinta de la actual.
- Revisar falsos positivos para ajustar la auditoria: `cat` no debe matchear dentro de `aguacate`, y `jugo/jugosos` no debe marcar alimentos humedos de mascotas como bebidas.
- Preparar una fase de datos separada para los 15 fideos/pastas residuales en Limpieza y los productos de higiene animal en Higiene Personal.
