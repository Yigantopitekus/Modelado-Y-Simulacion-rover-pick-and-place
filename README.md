# Modelado-Y-Simulacion-rover-pick-and-place
This repository holds an university assigment where it is asked to develop a gazebo simulation parting from a blender model from a previous assigment.


## Plots
<img width="1040" height="871" alt="image" src="https://github.com/user-attachments/assets/ca393577-8a8f-420e-95eb-8030f28e3005" />
### Posicion Ruedas vs Tiempo
**0-110s**:
Esta primera fraccion de tiempo representa el proceso del pick and place, donde el robot se mantiene estatico mientras utiliza el brazo para recoger el cubo que se encuentra en el suelo. Por ello las ruedas no cambian de posicion.
**110-225**
Una vez depositadso el cubo verde, empezamos a girar el robot usando teleop de ros para orientarlo hacia el cubo azul. Al girar hacia la izquierda, las ruedas de la derecha giran hacia delante y las de la izquierda hacia atras. Principalmente se aprecia el movimiento negativo de las ruedas de la izquierda, ya que la grafica refleja las rotaciones acumuladas, como al girar el robot era necesario hacer pequeños ajustes  para que no se pasase de largo o se quedase muy atras, las ruedas de la derecha que avanzaban para girar pero retrocedian para alejar un poco el robot del cubo se mantien cercano a 0. En cambio las ruedas de la izquierda practicamente solo giran hacia atras, de ahi el valor negativo de la grafica.
**225-290**
En este segmento, una vez recogido el cubo azul, se realizan multiples maniobras para orientar el robot hacia el cubo rojo. Un movimiento similar al anterior pero girando hacia la derecha y a la vez moviendose hacia atras, de esta manera las ruedas de la derecha hacen multiples rotaciones hacia atras y su valor baja mas notablemente, de la misma manera el valor de las ruedas de la izquierda tambien baja, similarmente por la misma razon que el segmento temporal anterior.De todas maneras hay que tener en cuenta que los ejes de los lados estan invertidos.
**290-end**
En el ultimo segmento subimos la velocidad maxima del teleop para hacer que el rover se mueva hacia adelante a mayor velocidad, la razon por la que un lado sube y otro baja es porque las TF de el lado izquierdo, apuntan su  hacia adelante, y las del lado derecho hacia atras.

### Aceleracion vs Tiempo
Primeramente hay que notar que la aceleracion del eje z empieza en +9.8 debido a la gravedad
**0-110s**:
Esta primera fraccion de tiempo representa el proceso del pick and place, donde el robot se mantiene estatico mientras utiliza el brazo para recoger el cubo que se encuentra en el suelo.Por ello el Imu que se encuentra en la base del robot se mantiene constante salvo algo de ruio producido por el movimiento.
**110-225**
En esta seccion, se gira el robot para ir a recoger el cubo azul, aqui se empieza a notar vibraciones en el IMU, debido al terreno irregular, y a la falta de amortiguacion en el rover.A pesar de eso es dificil interpretar que significan las vibraciones invididualmente mas alla de eso.
**225-290**
En este segmento de tiempo, se recoge el cubo azul, y una vez se sube el cubo arriba, se empieza a girar de nuevo el robot para orientarlo hacia el cubo rojo. Es por eso que las vibraciones no empiezan hasta el **250**, porque hay q esperar a subir el cubo antes de mover el robot.
**290-end**
En este ultimo segmento se registran un valor de vibraciones en el imu debido a la velocidad que se toma en el avance de los 10 metros. Aunque el color de esta parte de la grafica predomina el verde (Z) el valor de X deberia ser muy alto ya que el robot esta avanzando a lo largo de su eje x, generando mayor aceleracion en el eje x, que en el eje y, lamentablemente se solapa al representarlo. La aceleracion del eje Z es provocada por los baches en el terreno

### Gasto Energetico vs Tiempo
EL modelo de mi robot tiene la posicion de reposo de la pinza a ras de suelo por ende no se visualiza un gasto para acercar la pinza al cubo.
**15-50**

