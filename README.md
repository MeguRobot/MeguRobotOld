![MeguBot](https://telegra.ph/file/4645f09a45e70298624d7.jpg)
# Megu Bot 
[![GPLv3 license](https://img.shields.io/badge/License-GPLv3-blue.svg)](https://perso.crans.org/besson/LICENSE.html) [![Open Source Love svg2](https://badges.frapsoft.com/os/v2/open-source.svg?v=103)](https://github.com/ellerbrock/open-source-badges/) [![PRs Welcome](https://img.shields.io/badge/PRs-welcome-brightgreen.svg?style=flat-square)](https://makeapullrequest.com)


Un bot modular de Telegram Python en español que se ejecuta en python3 con una base de datos sqlalchemy.

Originalmente un fork de SaitamaRobot.

Se puede encontrar en telegram como [Megu](https://t.me/CrimsonMeguBot).

Puede comunicarse con el grupo de soporte en [Megu Support](https://t.me/MeguSupport), donde puede solicitar ayuda sobre [Megu](https://t.me/CrimsonMeguBot), descubrir/solicitar nuevas funciones, informar errores y mantenerse informado cuando sea hay una nueva actualización disponible.

## Cómo configurar/implementar.

### Lea estas notas detenidamente antes de continuar
 - Edite cualquier mención de @MeguSupport en su propio chat de soporte.
 - No admitimos bifurcaciones, una vez que bifurque el bot y despliegue el dolor de cabeza de los errores y el soporte sea suyo, no venga a nuestro chat de soporte pidiendo ayuda técnica.
 - Su código debe ser de código abierto y debe haber un enlace al repositorio de su bifurcación en la respuesta de inicio del bot. [Ver esto](https://github.com/NachABR/MeguBot/blob/f3c76b1c84e14b88a93f3f5a57b4ee748a83c551/MeguBot/__main__.py#L24)
 - Si viene a nuestro chat de soporte en Telegram pidiendo ayuda sobre una "bifurcación" o un problema técnico con un módulo, terminará siendo ignorado o prohibido.
 - Por último, si se encuentra que ejecuta este repositorio sin que el código sea de código abierto o el enlace del repositorio no se menciona en el bot, le enviaremos una gban en nuestra red debido a una violación de la licencia, puede hacerlo sea un idiota y no respete el código fuente abierto (no nos importa), pero no lo tendremos en nuestros chats.
<details>
<summary>Pasos para implementar en Heroku!!</summary>

```
Complete todos los detalles, ¡Implemente!
Ahora vaya a https://dashboard.heroku.com/apps/(app-name)/resources (Reemplace (app-name) con el nombre de su aplicación)
Encienda el dinamómetro del trabajador (no se preocupe, es gratis :D) y Webhook
Ahora envíe el bot /start. Si no responde, vaya a https://dashboard.heroku.com/apps/(app-name)/settings y elimine el webhook y el puerto.
```
[![Deploy](https://www.herokucdn.com/deploy/button.svg)](https://heroku.com/deploy?template=https://github.com/NachABR/MeguBot.git)

</details>
<details>
 <summary>Pasos para hostearlo!!</summary>

  ## Configuración del bot (¡lea esto antes de intentar usarlo!):
¡Asegúrese de usar python 3.6, ya que no puedo garantizar que todo funcione como se esperaba en versiones anteriores de Python!
Esto se debe a que el análisis de markdown se realiza iterando a través de un dictado, que está ordenado por defecto en 3.6.

  ### Configuración

Hay dos formas posibles de configurar su bot: un archivo config.py o variables ENV.

La versión preferida es usar un archivo `config.py`, ya que facilita ver todas las configuraciones agrupadas.
Este archivo debe colocarse en su carpeta `MeguBot`, junto con el archivo `__main__.py`.
Aquí es donde se cargará su token de bot, así como el URI de su base de datos (si está usando una base de datos), y la mayoría de
sus otras configuraciones.

Se recomienda importar sample_config y extender la clase Config, ya que esto asegurará que su configuración contenga todos
valores predeterminados establecidos en sample_config, lo que facilita la actualización.

Un ejemplo de archivo `config.py` podría ser:
```
from MeguBot.sample_config import Config

class Development(Config):
    OWNER_ID = 254318997 # Su ID de telegram.
    OWNER_USERNAME = "SonOfLars" # Su nombre de usuario de telegram.
    API_KEY = "your bot api key" # Su clave api, tal como la proporciona @botfather.
    SQLALCHEMY_DATABASE_URI = 'postgresql://nombredeusuario:contraseña@localhost:5432/database' # Credenciales de base de datos de muestra.
    MESSAGE_DUMP = '-1234567890' # Algún chat grupal donde su bot este ahí.
    USE_MESSAGE_DUMP = True
    SUDO_USERS = [18673980, 83489514] # Lista de identificadores de usuarios que tienen acceso superusuario al bot.
    LOAD = []
    NO_LOAD = ['translation']
```

Si no puede tener un archivo config.py (EG en Heroku), también es posible usar variables de entorno.
Se admiten las siguientes variables de entorno:
 - `ENV`: Establecer esto en CUALQUIER COSA habilitará las variables env

 - `TOKEN`: Su token de bot, como una cadena.
 - `OWNER_ID`: un número entero que consiste en su ID de propietario
 - `OWNER_USERNAME`: Su nombre de usuario

 - `DATABASE_URL`: URL de su base de datos
 - `MESSAGE_DUMP`: Opcional: Un chat donde se almacenan los registros de entrada del bot.
 - `LOAD`: Lista de módulos separados por espacios que le gustaría cargar
 - `NO_LOAD`: Lista de módulos separados por espacios que le gustaría NO cargar
 - `WEBHOOK`: Configurar esto en CUALQUIER COSA habilitará webhooks cuando esté en modo env
 mensajes
 - `URL`: La URL a la que debe conectarse su webhook (solo se necesita para el modo webhook)

 - `SUDO_USERS`: Una lista separada por espacios de user_ids que deben considerarse usuarios sudo
 - `SUPPORT_USERS`: una lista separada por espacios de user_ids que deben considerarse usuarios de soporte (pueden usar gban/ungban, nada más)
 - `WHITELIST_USERS`: Una lista separada por espacios de user_ids que deben considerarse en la lista blanca; no se pueden prohibir.
 - `DONATION_LINK`: Opcional: enlace donde te gustaría recibir donaciones.
 - `CERT_PATH`: Ruta a su certificado de webhook
 - `PORT`: Puerto que se utilizará para sus webhooks
 - `DEL_CMDS`: si eliminar comandos de usuarios que no tienen derechos para usar ese comando
 - `STRICT_GBAN`: Aplicar gbans en grupos nuevos y antiguos. Cuando un usuario de gbanned hable, será expulsado.
 - `WORKERS`: Número de subprocesos a utilizar. 8 es la cantidad recomendada (y predeterminada), pero su experiencia puede variar.
 __Nota__ que volverse loco con más subprocesos no necesariamente acelerará su bot, dada la gran cantidad de datos SQL
 accesos, y la forma en que funcionan las llamadas asincrónicas de Python.
 - `BAN_STICKER`: Qué etiqueta usar al prohibir personas.
 - `ALLOW_EXCL`: Si se permite el uso de signos de exclamación ! para comandos y /.

  ### Dependencias de Python

Instale las dependencias de Python necesarias moviéndose al directorio del proyecto y ejecutando:

`pip3 install -r requirements.txt`.

Esto instalará todos los paquetes de Python necesarios.

  ### Base de datos

Si desea utilizar un módulo dependiente de la base de datos (por ejemplo: bloqueos, notas, información de usuario, usuarios, filtros, bienvenidos),
necesitará tener una base de datos instalada en su sistema. Yo uso Postgres, por lo que recomiendo usarlo para una compatibilidad óptima.

En el caso de Postgres, así es como configuraría una base de datos en un sistema Debian/Ubuntu. Otras distribuciones pueden variar.

- Instalar postgresql:

`sudo apt-get update && sudo apt-get install postgresql`

- Cambiar al usuario de Postgres:

`sudo su - postgres`

- Cree un nuevo usuario de base de datos (cambie YOUR_USER apropiadamente):

`createuser -P -s -e YOUR_USER`

A continuación, deberá introducir su contraseña.

- Crea una nueva tabla de base de datos:

`createdb -O YOUR_USER YOUR_DB_NAME`

Cambie YOUR_USER y YOUR_DB_NAME de forma adecuada.

- Finalmente:

`psql YOUR_DB_NAME -h YOUR_HOST YOUR_USER`

Esto le permitirá conectarse a su base de datos a través de su terminal.
Por defecto, YOUR_HOST debería ser 0.0.0.0:5432.

Ahora debería poder crear el URI de su base de datos. Esto será:

`sqldbtype://nombredeusuario:pw@hostname:puerto/db_name`

Reemplace sqldbtype con la base de datos que esté utilizando (por ejemplo, Postgres, MySQL, SQLite, etc.)
repita para su nombre de usuario, contraseña, nombre de host (localhost?), puerto (5432?) y nombre de base de datos.

  ## Módulos
   ### Configuración del orden de carga.

El orden de carga del módulo se puede cambiar a través de los ajustes de configuración `LOAD` y `NO_LOAD`.
Ambos deben representar listas.

Si `LOAD` es una lista vacía, todos los módulos en `modules/`se seleccionarán para cargar de forma predeterminada.

Si "NO_LOAD" no está presente o es una lista vacía, se cargarán todos los módulos seleccionados para cargar.

Si un módulo está tanto en `LOAD` como en `NO_LOAD`, el módulo no se cargará; `NO_LOAD` tiene prioridad.

   ### Creando tus propios módulos.

La creación de un módulo se ha simplificado tanto como ha sido posible, pero no dude en sugerir una simplificación adicional.

Todo lo que se necesita es que su archivo .py esté en la carpeta de módulos.

Para agregar comandos, asegúrese de importar el despachador a través de

`from MeguBot import dispatcher`.

Luego puede agregar comandos usando el habitual

`dispatcher.add_handler()`.

Asignar la variable `__help__` a una cadena que describe los módulos disponibles
Los comandos permitirán al bot cargarlo y agregar la documentación para
su módulo al comando `/help`. Establecer la variable `__mod_name__` también le permitirá usar un nombre más agradable y fácil de usar para un módulo.

La función `__migrate__()` se usa para migrar chats: cuando un chat se actualiza a un supergrupo, la ID cambia, por lo que
es necesario migrarlo en la base de datos.

La función `__stats__()` es para recuperar estadísticas del módulo, por ejemplo, número de usuarios, número de chats. Esto se accede
a través del comando `/stats`, que solo está disponible para el propietario del bot.

## Iniciando el bot.

Una vez que haya configurado su base de datos y su configuración esté completa, simplemente ejecute el archivo bat (si está en Windows) o ejecute (Linux):

`python3 -m MeguBot`

Puede usar [nssm](https://nssm.cc/usage) para instalar el bot como servicio en Windows y configurarlo para que se reinicie en /gitpull
Asegúrese de editar el inicio y reiniciar los murciélagos según sus necesidades.
Nota: el bate de reinicio requiere que el control de la cuenta de usuario esté deshabilitado.

Para consultas o cualquier problema relacionado con el bot, abra un ticket de problema o visítenos en [Megu Support](https://t.me/MeguSupport)
## Cómo configurar Heroku
Para empezar, haga clic en este botón

[![Deploy](https://www.herokucdn.com/deploy/button.svg)](https://heroku.com/deploy?template=https://github.com/NachABR/MeguBot.git)


## Créditos
El bot se basa en el trabajo original realizado por [PaulSonOfLars](https://github.com/PaulSonOfLars)
Este repositorio acaba de renovarse para adaptarse a una comunidad centrada en el anime. Todos los créditos originales son para Paul y su dedicación. Sin sus esfuerzos, esta bifurcación no habría sido posible!


Cualquier otra autoría/créditos se puede ver a través de las confirmaciones.

Si falta alguno, háganoslo saber en [Megu Support](https://t.me/OnePunchSupport) o simplemente envíe una solicitud de extracción en el archivo README.

