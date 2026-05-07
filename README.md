# Modelado-Y-Simulacion-rover-pick-and-place
This repository holds an university assigment where it is asked to develop a gazebo simulation parting from a blender model from a previous assigment.


## Plots
<img width="1040" height="871" alt="image" src="https://github.com/user-attachments/assets/ca393577-8a8f-420e-95eb-8030f28e3005" />

La primera grafica representa la posicion de las ruedas del robot a lo largo del tiempo:

**0-110s**:
Esta primera fraccion de tiempo representa el proceso del pick and place, donde el robot se mantiene estatico mientras utiliza el brazo para recoger el cubo que se encuentra en el suelo. Por ello las ruedas no cambian de posicion.
**110-225**
Una vez depositadso el cubo verde, empezamos a girar el robot usando teleop de ros para orientarlo hacia el cubo azul. Al girar hacia la izquierda, las ruedas de la derecha giran hacia delante y las de la izquierda hacia atras. Principalmente se aprecia el movimiento negativo de las ruedas de la izquierda, ya que la grafica refleja las rotaciones acumuladas, como al girar el robot era necesario hacer pequeños ajustes  para que no se pasase de largo o se quedase muy atras, las ruedas de la derecha que avanzaban para girar pero retrocedian para alejar un poco el robot del cubo se mantien cercano a 0. En cambio las ruedas de la izquierda practicamente solo giran hacia atras, de ahi el valor negativo de la grafica.
**225-290**
En este segmento, una vez recogido el cubo azul, se realizan multiples maniobras para orientar el robot hacia el cubo rojo. Un movimiento similar al anterior pero girando hacia la derecha y a la vez moviendose hacia atras, de esta manera las ruedas de la derecha hacen multiples rotaciones hacia atras y su valor baja mas notablemente, de la misma manera el valor de las ruedas de la izquierda tambien baja, similarmente por la misma razon que el segmento temporal anterior.De todas maneras hay que tener en cuenta que los ejes de los lados estan invertidos.
**290-end**
En el ultimo segmento subimos la velocidad maxima del teleop para hacer que el rover se mueva hacia adelante a mayor velocidad, la razon por la que un lado sube y otro baja es porque las TF de el lado izquierdo, apuntan su  hacia adelante, y las del lado derecho hacia atras.
