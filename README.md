

## Sistema de Gestión y Acceso para Gimnasios

## Descripción

Este proyecto es un sistema de gestión para gimnasios que integra el control de acceso de personas con la administración de socios, pagos y actividades.
La idea principal es centralizar toda la lógica del gimnasio en una sola aplicación y permitir, en una segunda etapa, la conexión con dispositivos físicos como puertas con cerradura magnética, lectores RFID y lectores de huella digital.

El sistema está pensado para funcionar incluso en contextos de bajo presupuesto y poder crecer de forma progresiva sin necesidad de rehacer el software.

---

## Objetivo del proyecto

El objetivo es crear una aplicación que permita:

* Controlar el ingreso al gimnasio de forma automática o manual
* Administrar socios y sus pagos mensuales
* Gestionar actividades, profesores y horarios
* Crear promociones y combos de actividades con precios editables
* Evitar el acceso cuando la membresía está vencida
* Registrar todos los ingresos para control interno

---

## Cómo funciona a nivel general

Cada persona registrada en el sistema tiene un perfil con sus datos básicos.
El acceso puede realizarse de distintas maneras:

* Mediante llavero RFID
* Mediante huella digital
* De forma manual por nombre y apellido (modo respaldo)

Antes de permitir el ingreso, el sistema verifica que el socio esté activo y tenga la cuota correspondiente al día.
Si la validación es correcta, se autoriza la apertura de la puerta.

---

## Acceso manual y tolerancia a fallos

El sistema contempla que los dispositivos físicos pueden fallar.
Por ese motivo, siempre existe la opción de permitir el acceso de manera manual desde el panel administrativo, quedando el evento registrado.

Esto garantiza que el gimnasio pueda seguir funcionando sin interrupciones.

---

## Promociones y actividades

El sistema permite crear actividades individuales y también promociones o combos, por ejemplo:

* Una sola disciplina
* Dos o más disciplinas con un precio especial

El administrador puede modificar precios, actividades incluidas y vigencia sin necesidad de cambiar el código.

---

## Enfoque del desarrollo

El proyecto se desarrolla por etapas:

1. Desarrollo completo del sistema de gestión (software).
2. Pruebas con hardware simulado.
3. Integración con dispositivos físicos reales.

Este enfoque permite avanzar sin depender del hardware desde el primer momento.

---

## Estado del proyecto

El proyecto se encuentra en desarrollo activo.
La primera etapa está enfocada en la lógica del sistema y la gestión administrativa.

---

## Futuras mejoras

* Integración con lectores RFID y huella digital
* Apertura de puerta con cerradura magnética
* Estadísticas de asistencia
* Notificaciones por vencimiento de cuota
* Aplicación o panel para socios

---

## Licencia

Este proyecto es de uso libre para fines educativos o de desarrollo.
El uso comercial queda a criterio del autor.
