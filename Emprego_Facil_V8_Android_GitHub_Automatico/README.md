# Emprego Fácil V8 — Android

V8 Android baseada no V7, com cliente Kivy preparado para APK:
- login/cadastro
- busca e detalhes de vagas
- favoritos e candidaturas
- recomendações/notificações
- currículo e análise IA
- perfil
- URL da API configurável no próprio app
- sessão persistente
- Buildozer configurado para Android arm64

## APK
O APK não pode ser compilado neste ambiente porque Buildozer/Android SDK precisam ser baixados em um ambiente Linux/WSL2.

No Ubuntu/WSL2:
```bash
sudo apt update
sudo apt install -y python3-pip git zip unzip openjdk-17-jdk
cd android
python3 -m pip install --user buildozer cython
buildozer -v android debug
```
Resultado: `android/bin/*.apk`

No Windows, execute `android/build_apk.bat` com WSL2 instalado.

## Backend
```bash
cd backend
pip install -r requirements.txt
uvicorn app.main:app --host 0.0.0.0 --port 8000
```
No celular físico, configure no app `http://IP_DO_PC:8000/api/v1`.
No emulador Android use `http://10.0.2.2:8000/api/v1`.

## Gerar APK automaticamente pelo GitHub Actions

A V8 já contém o workflow `.github/workflows/android-apk.yml`.

### Como usar

1. Crie um repositório no GitHub.
2. Envie **todo o conteúdo desta pasta** para o repositório (incluindo `.github`).
3. No GitHub, abra **Actions**.
4. Selecione **Emprego Fácil V8 - Android APK**.
5. Clique em **Run workflow**.
6. Aguarde a compilação terminar.
7. Abra a execução concluída e, em **Artifacts**, baixe `Emprego-Facil-V8-Android-APK`.
8. Dentro do ZIP estará o arquivo `.apk` para instalar no Android.

### Gerar Release automaticamente

Também é possível criar uma tag, por exemplo `v8.0.0`. Quando a tag for enviada ao GitHub, o workflow compila o APK e anexa o arquivo automaticamente à Release.

Exemplo no terminal:

```bash
git add .
git commit -m "Emprego Fácil V8 Android"
git tag v8.0.0
git push origin main --tags
```

> O primeiro build pode demorar bastante porque o GitHub precisa preparar o Android SDK/NDK e o ambiente do Buildozer. Os builds seguintes tendem a ser mais rápidos graças ao cache.
