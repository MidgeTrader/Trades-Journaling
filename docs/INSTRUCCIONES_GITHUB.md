# Cómo subir tu herramienta a GitHub

Sigue estos pasos para subir este código a un nuevo repositorio en GitHub:

### 1. Crear el repositorio en GitHub
1. Ve a [github.com](https://github.com) e inicia sesión.
2. Haz clic en el botón **"New"** (o el icono **+**) para crear un nuevo repositorio.
3. Ponle un nombre (ejemplo: `trading-report-tool`).
4. Déjalo como **Public** o **Private**, según prefieras.
5. **IMPORTANTE**: No marques las casillas de "Add a README", "Add .gitignore" o "Choose a license" (ya hemos creado esos archivos).
6. Haz clic en **"Create repository"**.

### 2. Configurar Git en tu computadora
Abre una terminal (PowerShell o CMD) y navega hasta esta carpeta:
```powershell
cd "C:\Users\TU_USUARIO\Desktop\Reportes Brokers (Version Compartible)"
```

Luego ejecuta los siguientes comandos uno por uno:

1. **Inicializar Git**:
   ```bash
   git init
   ```

2. **Añadir los archivos**:
   ```bash
   git add .
   ```

3. **Primer commit**:
   ```bash
   git commit -m "Initial commit: Shareable trading report tool"
   ```

4. **Configurar la rama principal**:
   ```bash
   git branch -M main
   ```

5. **Conectar con GitHub**:
   *(Copia la línea que dice "git remote add origin ..." de la página de GitHub que acabas de crear)*
   ```bash
   git remote add origin https://github.com/TU_USUARIO/TU_REPOSITORIO.git
   ```

6. **Subir el código**:
   ```bash
   git push -u origin main
   ```

---
**Nota**: Si es la primera vez que usas Git, es posible que te pida configurar tu nombre y correo:
```bash
git config --global user.name "Tu Nombre"
git config --global user.email "tu@email.com"
```

---

### 7. Activar la barrera de datos personales

Este repositorio es público. Todo lo que entra en un commit se queda en el
historial y viaja con cualquier copia, clon o fork que alguien haga después:
borrarlo más tarde no recupera esas copias.

El hook `.githooks/pre-commit` bloquea commits que metan correos, rutas locales
del sistema o ids de carpeta de Drive. Hay que activarlo una vez por clon:

```bash
git config core.hooksPath .githooks
```

Ese tipo de datos va en `.env`, que está en `.gitignore` y nunca se sube.
