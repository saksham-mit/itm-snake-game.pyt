# ITM Snake Game (Python / pygame)

A polished Snakes & Ladders game: 1 human + 3 smart bots, smooth animations, music/SFX, and packaging guide for desktop, web, and Android.

## How to run (desktop)

```bash
python -m venv .venv
# Activate the venv (Windows)
.venv\Scripts\activate
# or (macOS/Linux)
source .venv/bin/activate

pip install -r requirements.txt
python main.py
```

## Controls
- **SPACE / Click**: Roll dice (your turn)
- **N**: New game
- **F**: Fast mode (speeds up animations)
- **G**: Toggle board numbers
- **P**: Pause/Resume music
- **ESC / Window X**: Quit

## Bot Difficulty
- Bot A: *Chill*
- Bot B: *Balanced*
- Bot C: *Spicy* (tries to aim for ladders / avoid snakes more often)

You can tweak difficulty in `players` inside `main.py`.

---

## Build a Windows/macOS/Linux executable (PyInstaller)

```bash
pip install pyinstaller
pyinstaller --noconfirm --windowed --name "ITM Snake Game" --add-data "assets{}assets" main.py
```
> Replace `{sep}` below with `;` on Windows, `:` on macOS/Linux.

On Windows:
```bash
pyinstaller --noconfirm --windowed --name "ITM Snake Game" --add-data "assets;assets" main.py
```
On macOS/Linux:
```bash
pyinstaller --noconfirm --windowed --name "ITM Snake Game" --add-data "assets:assets" main.py
```

Your executable will be in `dist/ITM Snake Game/`.

---

## Build a Web version (shareable link) with **pygbag**

Pygbag compiles pygame to WebAssembly so your game runs in the browser.

```bash
pip install pygbag
pygbag --build main.py
```
Open the generated `build/web/index.html` in a browser, or host the `build/web` folder anywhere (GitHub Pages, Netlify, etc.). You can also zip this folder and send it via WhatsApp; users can unzip and open `index.html` to play.

---

## Build an Android APK (share via WhatsApp)

Use **Buildozer** (Linux or WSL recommended) which wraps python-for-android.

1. Install prerequisites (Ubuntu 22.04 example):
   ```bash
   sudo apt update
   sudo apt install -y python3-venv build-essential git zip unzip openjdk-17-jdk
   pip install --upgrade cython virtualenv
   pip install buildozer
   ```
2. Initialize project:
   ```bash
   buildozer init
   ```
3. Edit `buildozer.spec`:
   - Set `title = ITM Snake Game`
   - Set `package.name = itm_snake_game`
   - Set `requirements = python3, pygame`
   - Set `source.include_exts = py,wav`
   - Set `presplash.filename = assets/bg_music.wav` (optional, or remove)
   - Set `orientation = landscape`
   - Under `android.permissions`, add `WRITE_EXTERNAL_STORAGE` if you need save files (not required here).
   - Ensure `android.minapi = 21`.
4. Build debug APK:
   ```bash
   buildozer -v android debug
   ```
   The APK will be in `bin/`. Send the APK over WhatsApp.
5. (Optional) Sign/release:
   ```bash
   buildozer android release
   ```

> Tip: If you see missing SDL/pygame requirements, add `sdl2, sdl2_image, sdl2_mixer, sdl2_ttf` to `requirements` in `buildozer.spec`:
> `requirements = python3, pygame, sdl2, sdl2_image, sdl2_mixer, sdl2_ttf`

---

## Tweak visuals / music / difficulty

- Colors & sizes: edit the color constants and `CELL`, `BOARD_SIZE` in `main.py`.
- SFX/Music are in `assets/*.wav`. Replace with your own files (same names).
- Bot difficulty: change `difficulty` for Bot A/B/C to `Chill`, `Balanced`, or `Spicy`.
- Title/branding: change `TITLE` at the top.

---

## Known limits
- Pygame UI is for desktop/mobile (via APK). For websites, use the **pygbag** build flow.
- Touch input works through taps (treated like mouse click) in the APK build.

Enjoy! ✨

## Automatic Web Build & Deployment (GitHub Pages)

Included is a GitHub Actions workflow that will build the pygbag web build and deploy it to the `gh-pages` branch automatically when you push to `main`/`master`:

1. Create a new GitHub repository (empty) and push this project to it:
   ```bash
   git init
   git add .
   git commit -m "Initial commit - ITM Snake Game"
   git branch -M main
   git remote add origin https://github.com/<your-username>/itm-snake-game.git
   git push -u origin main
   ```
2. The GitHub Actions workflow `.github/workflows/pygbag_build.yml` will run on push, install `pygbag`, run `pygbag --build main.py`, and deploy `build/web` to the `gh-pages` branch using `peaceiris/actions-gh-pages`.
3. After the workflow completes, go to `https://<your-username>.github.io/itm-snake-game/` (GitHub Pages) — your game should load and be playable in Chrome (desktop & mobile).

Notes & troubleshooting:
- If the Actions runner fails due to missing system libs, you may need to add apt packages in the workflow (e.g., build-essential, libasound2) — open an issue and I’ll help tailor the workflow.
- Alternatively, use Netlify by connecting your repo and Netlify will run the build command `pygbag --build main.py` and publish the `build/web` directory automatically (there's also a `netlify.toml` in the repo).

If you'd like, I can also:
- Create the GitHub repository for you (I can't push to your account; you'll need to give me a repo name and push the ZIP or I can give exact commands).
- Generate a `gh-pages` deployment PR or show you how to enable Pages in one click.
