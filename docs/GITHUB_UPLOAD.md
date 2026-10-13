# Как грамотно залить проект на GitHub

Полная инструкция от локальной папки до релиза с `.deb`, `.rpm`, `.pkg.tar.zst`,
`AppImage` и `.exe`. Сделано так, чтобы можно было повторять на каждом новом
релизе.

---

## 0. Что уже подготовлено

В репозитории лежит всё, что нужно для публикации:

| Файл/папка | Зачем |
|---|---|
| `README.md` | главная страница на русском |
| `README.en.md` | английская версия |
| `LICENSE` | MIT |
| `CHANGELOG.md` | история изменений |
| `CONTRIBUTING.md`, `CODE_OF_CONDUCT.md`, `SECURITY.md` | стандартные файлы для открытого проекта |
| `.gitignore` | отсекает `.venv`, `build/`, `dist/`, `*.deb` и прочее |
| `.github/workflows/build.yml` | автосборка всех форматов |
| `.github/ISSUE_TEMPLATE/*.yml` | формы для багов и предложений |
| `docs/images/*.png` | скриншоты для README |
| `packaging/`, `scripts/` | .desktop, spec для RPM, PKGBUILD, NSIS, PyInstaller |

---

## 1. Подготовка перед первым коммитом

### 1.1 Проверьте, что мусор не попадёт в репозиторий

```bash
git status --ignored --short | head -50
```

В списке должны быть только `!!` (игнорируемые) для `.venv/`, `build/`, `dist/`.

### 1.2 Обновите версию и changelog

Версия берётся из одного места — `pastypw/__init__.py`:

```bash
sed -i 's/__version__ = "1.0.0"/__version__ = "1.1.0"/' pastypw/__init__.py
```

Добавьте раздел в `CHANGELOG.md` и опишите изменения в `README.md`.

### 1.3 Проверьте, что всё работает

```bash
make venv
make test          # 26 тестов
make all           # тесты + иконки + бинарник + .deb + AppImage
```

### 1.4 Убедитесь, что нет секретов и личных данных

```bash
grep -RInE "(password|token|secret|api[_-]?key)\s*=\s*['\"][^'\"]{6,}" --include='*.py' . || echo "чисто"
```

В `history.json` паролей быть не должно: он лежит в
`~/.local/share/pastypw/history.json` и в репозиторий не попадает.

---

## 2. Первый коммит

```bash
cd /путь/к/проекту

git init -b main                      # ветка main сразу
git add .
git status                            # посмотрите, что попадает в коммит
git commit -m "PastyNew Password Generator 1.0.0

- offline password generator with a Qt/PySide6 dark interface
- .deb/.rpm/.pkg.tar.zst/AppImage/.exe packaging
- GitHub Actions pipeline, bilingual README"
```

### Что должно быть в коммите

```
pastypw/      scripts/      tests/      docs/      packaging/
.github/      Makefile      pyproject.toml  requirements.txt
README.md     README.en.md  LICENSE      CHANGELOG.md
CONTRIBUTING.md  CODE_OF_CONDUCT.md  SECURITY.md
.gitignore    .editorconfig
```

### Чего быть НЕ должно

`.venv/`, `build/`, `dist/`, `*.deb`, `*.rpm`, `*.AppImage`, `__pycache__`,
`.pytest_cache`, `build/screenshot-sandbox/`.

---

## 3. Создание репозитория на GitHub

### Вариант A. Через сайт

1. Откройте <https://github.com/new>.
2. **Repository name**: `pastypw`
3. **Description**: `Offline password generator with a modern dark interface (by PastyNew)`
4. **Public** (проект открытый).
5. ⚠️ **НЕ** ставьте галочки «Add a README file», `.gitignore`, License —
   они уже есть локально, иначе будет конфликт при первом пуше.
6. **Create repository**.

### Вариант B. Через консоль GitHub CLI

```bash
gh auth login                                    # один раз
gh repo create pastypw --public --description "Offline password generator (by PastyNew)" --source=. --remote=origin --push
```

---

## 4. Связывание и первый пуш

Если репозиторий создан через сайт:

```bash
git remote add origin https://github.com/PastyNew/pastypw.git
git remote -v                                    # проверка
git push -u origin main
```

Если пуш требует пароль и ругается на аутентификацию — используйте
[Personal Access Token](https://github.com/settings/tokens) (scope `repo`)
вместо пароля, либо включите 2FA и SSH-ключ:

```bash
ssh-keygen -t ed25519 -C "pastypew@gmail.com"
cat ~/.ssh/id_ed25519.pub                        # добавить в GitHub → Settings → SSH keys
ssh -T git@github.com                            # проверка: "Hi PastyNew!"
git remote set-url origin git@github.com:PastyNew/pastypw.git
```

---

## 5. Автоматическая сборка (Actions)

Каждый `push` в `main` и каждый тег `v*` запускают
`.github/workflows/build.yml`:

| Job | Что собирает |
|---|---|
| `test` | юнит-тесты |
| `linux` | `.deb`, `.rpm`, `.pkg.tar.zst`, `AppImage` |
| `windows` | портативный `pastypw.exe` + установщик NSIS |
| `release` | публикует файлы в Releases (только для тегов) |

Как скачать:

1. Откройте **Actions** → выберите зелёный запуск.
2. Внизу **Artifacts** → `pastypw-linux-packages` или `pastypw-windows`.
3. GitHub отдаёт zip-архив.

> Первый запуск занимает 8-15 минут: собирается Qt.

---

## 6. Релиз с готовыми файлами

```bash
git tag -a v1.0.0 -m "PastyNew Password Generator 1.0.0"
git push origin v1.0.0
```

После этого:

* соберутся все форматы;
* job `release` создаст релиз на <https://github.com/PastyNew/pastypw/releases>
  с прикреплёнными `.deb`, `.rpm`, `.pkg.tar.zst`, `AppImage`, `.exe`;
* текст релиза создастся автоматически, дополните его списком изменений из
  `CHANGELOG.md`.

Проверить, что тег ушёл:

```bash
git ls-remote --tags origin
```

### Релиз следующей версии

```bash
# 1. правим версию
sed -i 's/__version__ = "1.0.0"/__version__ = "1.1.0"/' pastypw/__init__.py
# 2. дописываем CHANGELOG.md
# 3. коммит и тег
git add -A && git commit -m "Release 1.1.0"
git tag -a v1.1.0 -m "PastyNew Password Generator 1.1.0"
git push origin main --follow-tags
```

---

## 7. Оформление страницы репозитория

* **About → Description**: `Offline password generator with a modern dark interface`
* **About → Topics**: `password-generator`, `password`, `security`, `pyside6`,
  `qt6`, `linux`, `windows`, `kali-linux`, `arch-linux`, `offline`
* **About → Website**: ссылка на Releases
* **Settings → General → Features**: включите *Issues*, *Discussions*,
  *Projects* (по желанию), *Wiki* (опционально)
* **Settings → Pages**: можно включить, если захотите страницу с документацией

Бейджи в README уже добавлены (`Build`, `License`, `Creator`). Бейдж сборки
подхватится автоматически после первого успешного прогона Actions.

---

## 8. Проверка перед публикацией

```bash
# код компилируется и тесты зелёные
python -m pytest tests -q

# пакеты собираются
ls -lh dist/

# в README есть реальные картинки
ls docs/images/

# нет хвостов от других систем
git status --short

# история коммитов читаемая
git log --oneline --graph --decorate -10
```

---

## 9. Частые проблемы

| Симптом | Причина и решение |
|---|---|
| `remote origin already exists` | `git remote set-url origin <адрес>` |
| `Permission denied (publickey)` | настроить SSH-ключ или PAT |
| `rejected ... non-fast-forward` | сначала `git pull --rebase origin main`, потом push |
| `fatal: not a git repository` | забыли `git init` |
| В коммит попал `.venv/` | проверьте, что `.gitignore` на месте: `git rm -r --cached .venv` |
| Бейдж Actions красный | откройте лог job, чаще всего нужны системные библиотеки Qt |
| Большой репозиторий (>100 МБ) | в `.gitignore` добавьте `dist/`, `build/`; переисторию через `git filter-repo` |
| Releases пустой | тег не начинается с `v` или job `release` не запустился — проверьте условие `if:` |

---

## 10. Что НЕ надо делать

* Публиковать `.venv/`, `dist/`, `build/` — они в `.gitignore`.
* Загружать на GitHub свой `history.json` с реальными паролями.
* Коммитить чужие библиотеки Qt в исходники (Qt ставится через `pip`).
* Хранить токены в коде или в workflows — используйте GitHub Secrets.
* Публиковать `.exe` в Releases вручную из Windows-машины, если уже работает
  Actions: файлы будут одинаковыми и проверенными.

---

## 11. Итоговый чек-лист релиза

- [ ] версия обновлена в `pastypw/__init__.py`
- [ ] `CHANGELOG.md` содержит новый раздел
- [ ] `python -m pytest tests -q` — все тесты зелёные
- [ ] `make all` — пакеты собраны, скриншоты обновлены
- [ ] README показывает актуальные скриншоты
- [ ] `git add -A && git commit`
- [ ] `git push origin main`
- [ ] Actions завершился успешно, артефакты скачались
- [ ] создан и отправлен тег `vX.Y.Z`
- [ ] релиз появился на странице Releases со всеми файлами