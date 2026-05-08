# Git Workflow — HotelSys

Este documento define el flujo oficial de trabajo con Git para el proyecto HotelSys.

Todos los integrantes del equipo deben seguir estas reglas para evitar:
- conflictos,
- pérdida de código,
- migraciones rotas,
- problemas de integración,
- y errores en producción.

---

# 1. Estructura de Branches

El proyecto utiliza una estrategia basada en:

```text
main
develop
feature/*
```

---

# 2. Branches Oficiales

| Branch | Propósito |
|---|---|
| `main` | Rama estable de producción |
| `develop` | Rama principal de integración |
| `feature/*` | Desarrollo individual por funcionalidad |

---

# 3. Reglas Generales

## Prohibido

❌ Trabajar directamente sobre:

- `main`
- `develop`

---

## Obligatorio

✅ Todo desarrollo debe hacerse en una branch `feature/*`.

---

# 4. Flujo Oficial de Trabajo

```text
feature/* → develop → main
```

---

# 5. Flujo Paso a Paso

## 5.1 Actualizar proyecto

Antes de empezar:

```bash
git checkout develop
git pull origin develop
```

---

## 5.2 Crear branch feature

Formato:

```text
feature/nombre-modulo
```

### Ejemplos

```bash
git checkout -b feature/reservations
```

```bash
git checkout -b feature/billing
```

```bash
git checkout -b feature/dashboard
```

---

## 5.3 Trabajar normalmente

Agregar cambios:

```bash
git add .
```

Crear commit:

```bash
git commit -m "feat: add reservation validation"
```

---

## 5.4 Subir branch

```bash
git push origin feature/reservations
```

---

## 5.5 Crear Pull Request

El Pull Request debe dirigirse hacia:

```text
develop
```

Nunca directamente hacia:

```text
main
```

---

## 5.6 Revisión

El líder técnico debe:

- revisar código,
- validar funcionamiento,
- verificar estándares,
- aprobar PR.

---

## 5.7 Merge

Una vez aprobado:

```text
feature/* → develop
```

---

# 6. Flujo hacia Producción

Cuando `develop` sea estable:

```text
develop → main
```

Esto solo debe hacerlo el líder técnico.

---

# 7. Convención de Nombres de Branches

## Formato

```text
feature/nombre
```

---

## Ejemplos válidos

```text
feature/reservations
feature/rooms
feature/billing
feature/reports
feature/checkin-checkout
```

---

## Evitar

❌

```text
feature1
trabajo-jose
rama-nueva
```

---

# 8. Convención de Commits

## Formato

```text
tipo: descripcion
```

---

# 9. Tipos de Commits Permitidos

| Tipo | Uso |
|---|---|
| feat | Nueva funcionalidad |
| fix | Corrección de errores |
| refactor | Refactorización |
| docs | Documentación |
| style | Formato/estilos |
| test | Testing |
| chore | Tareas generales |

---

# 10. Ejemplos de Commits

## Correctos

```bash
git commit -m "feat: add reservation overlap validation"
```

```bash
git commit -m "fix: solve folio total calculation"
```

```bash
git commit -m "docs: update README"
```

---

## Incorrectos

❌

```bash
git commit -m "cambios"
```

```bash
git commit -m "avance"
```

```bash
git commit -m "update"
```

---

# 11. Reglas de Pull Requests

## Todo Pull Request debe:

- tener descripción clara,
- explicar cambios realizados,
- indicar archivos modificados,
- indicar si existen migraciones.

---

## Nunca hacer merge si:

- el proyecto no compila,
- Docker falla,
- existen conflictos,
- hay migraciones rotas.

---

# 12. Reglas de Migraciones

## Muy importante

Las migraciones son sensibles en proyectos grupales.

---

## Reglas

### Solo el líder técnico puede:

- modificar modelos críticos,
- eliminar campos,
- renombrar columnas,
- reorganizar relaciones.

---

## Antes de subir migraciones:

Ejecutar:

```bash
docker compose exec web python manage.py makemigrations
```

```bash
docker compose exec web python manage.py migrate
```

---

## Nunca:

❌ borrar migraciones ya ejecutadas.

❌ modificar migraciones subidas al repositorio.

---

# 13. Reglas de Integración

Antes de crear un Pull Request:

## Obligatorio

Actualizar `develop`:

```bash
git checkout develop
git pull origin develop
```

Luego:

```bash
git checkout feature/mi-rama
git merge develop
```

Resolver conflictos localmente.

---

# 14. Reglas de Calidad

Antes de subir código:

✅ Verificar:
- Docker funciona
- Proyecto levanta
- No hay errores
- Migraciones funcionan
- Código sigue estándares
- No existen archivos basura

---

# 15. Archivos que NO deben subirse

Nunca subir:

```text
.env
venv/
__pycache__/
*.pyc
db.sqlite3
.idea/
.vscode/
```

---

# 16. Responsabilidades del Líder Técnico

El líder técnico debe:

- aprobar Pull Requests,
- controlar migraciones,
- resolver conflictos,
- integrar módulos,
- validar estándares,
- mantener estable `develop`,
- realizar merge final a `main`.

---

# 17. Reglas Finales

Todo desarrollador debe:

- trabajar únicamente en su módulo,
- respetar estándares,
- documentar cambios importantes,
- mantener commits limpios,
- evitar modificar código ajeno sin coordinación.

---

# 18. Flujo Resumido

```text
1. Actualizar develop
2. Crear feature branch
3. Programar
4. Commit
5. Push
6. Pull Request a develop
7. Revisión líder
8. Merge
9. Integración final
```