# 🎯 Gift Sniper — Telegram Gift Hunter 🎁

A fast and lightweight tool that automatically detects and redeems Telegram gift links — and instantly purchases any gift that drops in price by **40% or more**.

---

## 📦 Requirements

- Python 3.10+ (better with `pyenv`)
- `nodejs` & `npm` for `pm2` installing
- `pm2` for process management ([Install Guide](https://pm2.keymetrics.io/))
- A working `.env` file with proper configuration
    - You can exclude gifts by adding their names in `EXCLUDE`
- Telegram session strings saved in `sessions.txt`

---

## 🏃 Run the Sniper with PM2
- Clone the repo
```bash
git clone https://github.com/z44d/TgGiftsSniper && cd TgGiftsSniper
```
- Install dependencies
```bash
pip install -r requirements.txt
```
- Use the provided `gen.py` to generate the `ecosystem.config.js` file dynamically:
```bash
python gen.py
```
- This script will:
    - Split your sessions into chunks (default: 50 per process)
    - Create multiple sessions_X.txt files
    - Generate a valid ecosystem.config.js file for PM2

- Then launch everything with:
```bash
pm2 start ecosystem.config.js
```
- To make sure that buying process is working:
```bash
curl http://127.0.0.1:8000/
```
- To monitor logs:
```bash
pm2 logs
```
- To stop all processes:
```bash
pm2 kill
```

## 💙 Made with love by [Zaid](https://t.me/DevZaid)