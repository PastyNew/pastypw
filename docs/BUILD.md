# Сборка PastyNew Password Generator из исходников

Инструкция для каждого формата: `.deb`, `.rpm`, `.pkg.tar.zst`, `AppImage`
и `.exe`. Всё собирается из одного и того же кода — меняется только упаковка.

---

## 0. Подготовка окружения

```bash
git clone https://github.com/PastyNew/pastypw.git
cd pastypw

python3 -m venv .venv
. .venv/bin/activate
pip install -r requirements.txt        # PySide6, PyInstaller, pytest

python -m pytest tests -q              # 26 тестов, всё должно быть зелёным
python -m pastypw                      # запуск из исходников
```

### Системные библиотеки Qt (Linux)

```bash
# Debian / Ubuntu / Kali / Mint
sudo apt install libgl1 libegl1 libxkbcommon0 libxkbcommon-x11-0 \
                 libdbus-1-3 libfontconfig1 libxcb-cursor0 libxcb-icccm4 \
                 libxcb-keysyms1 libxcb-shape0 libxcb-render-util0 \
                 libxcb-xinerama0 libxkbcommon0

# Fedora
sudo dnf install mesa-libGL mesa-libEGL libxkbcommon libxkbcommon-x11 \
                 dbus-libs fontconfig libxcb-cursor libxcb-icccm

# Arch
sudo pacman -S mesa libxkbcommon libxkbcommon-x11 dbus fontconfig libxcb-util
```

---

## 1. Замороженное приложение (нужно для всех пакетов)

```bash
python scripts/make_icons.py          # иконки в build/icons
python -m PyInstaller packaging/pyinstaller/pastypw-linux.spec \
    --noconfirm --clean --distpath dist --workpath build/pyinstaller
python scripts/slim_bundle.py         # выкидываем ненужные плагины Qt
```

Результат: `dist/pastypw/pastypw` (запускаемый бинарник) и
`dist/pastypw/_internal/` (Qt-библиотеки).

Проверка:

```bash
./dist/pastypw/pastypw                 # должно открыться окно
```

Или без графики:

```bash
QT_QPA_PLATFORM=offscreen timeout 10 ./dist/pastypw/pastypw; echo "код: $?"
# 124 = приложение живо и было убито таймаутом (это нормально)
```

---

## 2. Debian / Ubuntu / Mint / Kali — `.deb`

Нужен `dpkg-deb` (есть в системе по умолчанию).

```bash
python scripts/build_deb.py
# -> dist/pastypw_1.0.0_amd64.deb
```

Проверка без установки:

```bash
dpkg-deb -I  dist/pastypw_1.0.0_amd64.deb       # метаданные
dpkg-deb -c  dist/pastypw_1.0.0_amd64.deb | head # состав
```

Установка:

```bash
sudo dpkg -i dist/pastypw_1.0.0_amd64.deb
pastypw                                            # запуск
sudo apt remove pastypw                            # удаление
```

Сборка под другую архитектуру (arm64 через кросс-сборку или CI):

```bash
python scripts/build_deb.py --arch arm64 --binary-dir dist-arm64/pastypw
```

---

## 3. Fedora / RHEL / openSUSE — `.rpm`

Нужен `rpmbuild`:

```bash
sudo dnf install rpm-build      # Fedora/RHEL/CentOS
sudo apt install rpm            # Debian/Ubuntu
```

```bash
./scripts/build_rpm.sh
# -> dist/pastypw-1.0.0-1.x86_64.rpm (+ .src.rpm)
```

Установка:

```bash
sudo dnf install ./dist/pastypw-1.0.0-1.x86_64.rpm
```

> Скрипт берёт версию из `pastypw/__init__.py` и подставляет её в
> `packaging/rpm/pastypw.spec`, поэтому руками ничего править не нужно.

---

## 4. Arch Linux / Manjaro / Kali — `.pkg.tar.zst`

Нужны `makepkg`, `libarchive` и `zstd`:

```bash
sudo pacman -S --needed base-devel libarchive zstd
```

```bash
./scripts/build_arch_pkg.sh
# -> dist/pastypw-1.0.0-1-x86_64.pkg.tar.zst
```

Скрипт сам подкладывает `dist/pastypw`, иконки и `.desktop` рядом с
`PKGBUILD` и запускает `makepkg -sf`.

Установка:

```bash
sudo pacman -U dist/pastypw-1.0.0-1-x86_64.pkg.tar.zst
```

Сборка в контейнере (если на машине нет makepkg):

```bash
podman run --rm -v "$PWD:/pkg" -w /pkg docker.io/library/archlinux:base-devel \
    bash -lc "pacman -Syu --noconfirm --needed base-devel libarchive zstd >/dev/null && ./scripts/build_arch_pkg.sh"
```

---

## 5. AppImage (любой Linux)

```bash
./scripts/build_appimage.sh
# -> dist/pastypw-1.0.0-x86_64.AppImage
```

Скрипт сам скачивает `linuxdeploy` (если его нет) и собирает AppDir.
Если FUSE недоступен в системе, `linuxdeploy` запускается с
`APPIMAGE_EXTRACT_AND_RUN=1` — скрипт это уже учитывает.

```bash
chmod +x dist/*.AppImage
./dist/pastypw-1.0.0-x86_64.AppImage
```

---

## 6. Windows — `.exe`

PyInstaller не умеет собирать Windows-приложение на Linux, поэтому нужен
Windows (или GitHub Actions, который делает это сам).

На Windows:

```powershell
git clone https://github.com/PastyNew/pastypw.git
cd pastypw
powershell .\scripts\build_windows.ps1
```

Результат:

* `dist\pastypw.exe` — портативная версия;
* `dist\PastyNew-PasswordGenerator-Setup-1.0.0.exe` — установщик NSIS
  (нужен [NSIS](https://nsis.sourceforge.io/Download), ставится через
  `choco install nsis`).

Без NSIS можно раздавать портативный `pastypw.exe`.

---

## 7. Всё сразу

```bash
./scripts/build_all.sh
```

Скрипт прогонит тесты, соберёт иконки, бинарник, `.deb` и AppImage и
покажет список готовых файлов. RPM и Arch собираются там, где есть
`rpmbuild` / `makepkg` (или в CI).

`make all` — то же самое коротко.

---

## 8. Скриншоты для README (без графики)

```bash
QT_QPA_PLATFORM=offscreen python scripts/render_screenshots.py
# -> docs/images/main-ru.png, main-en.png, batch-and-history-ru.png, compact.png
```

Используется и в CI, чтобы скриншоты в README всегда соответствовали коду.

---

## 9. Полезные проверки

```bash
# метаданные пакета
dpkg-deb -I dist/*.deb
rpm -qip dist/*.rpm                    # внутри среды с rpm
pacman -Qip dist/*.pkg.tar.zst         # внутри Arch

# зависимости бинарника
ldd dist/pastypw/pastypw | grep 'not found' || echo "все библиотеки на месте"

# размеры
du -sh dist/pastypw
```

---

## 10. Частые проблемы при сборке

| Проблема | Что делать |
|---|---|
| `dpkg-deb: ошибка: ... Depends` | проверьте, что в `RUNTIME_DEPS` нет пакетов, которых нет в вашей системе |
| `error: rpmbuild not found` | `sudo dnf install rpm-build` |
| `makepkg: fatal error` | `sudo pacman -S base-devel libarchive` |
| `ModuleNotFoundError: PySide6` | `pip install PySide6` в активном venv |
| Бинарник не запускается: `libxcb-xinerama.so.0 not found` | доустановите системные библиотеки Qt из раздела 0 |
| PyInstaller: `script not found` | запускайте из корня репозитория |
| Окно белое на Wayland | проверьте `echo $XDG_SESSION_TYPE`; при необходимости запустите через `QT_QPA_PLATFORM=xcb` |

---

## 11. Автоматическая сборка

`.github/workflows/build.yml` делает всё то же самое на трёх системах
(Ubuntu для Linux-пакетов, Windows для `.exe`) и складывает результат в
Artifacts, а по тегу `v*` — в Releases. Локальная сборка нужна только если
вы хотите проверить изменения до пуша.