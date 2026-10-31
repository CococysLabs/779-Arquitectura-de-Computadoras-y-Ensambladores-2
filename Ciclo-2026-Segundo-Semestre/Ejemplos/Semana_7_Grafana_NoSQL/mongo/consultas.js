// Responsable del material: Wendy Mazariegos.
// Ejecutar dentro de mongosh: load('/ejemplos/consultas.js')
const laboratorio = db.getSiblingDB('temperaturas');
print('1. Documento más reciente:');
printjson(laboratorio.lecturas.find().sort({fecha:-1}).limit(1).toArray());
print('2. Cantidad de lecturas almacenadas:');
printjson(laboratorio.lecturas.countDocuments({}));
print('3. Lecturas desde el umbral didáctico de 30 °C:');
printjson(laboratorio.lecturas.find({valor:{$gte:30}}).sort({fecha:-1}).limit(5).toArray());
print('4. Promedio, mínimo y máximo por dispositivo:');
printjson(laboratorio.lecturas.aggregate([
  {$group:{_id:'$dispositivo', promedio:{$avg:'$valor'}, minimo:{$min:'$valor'},
           maximo:{$max:'$valor'}, lecturas:{$sum:1}}}
]).toArray());
