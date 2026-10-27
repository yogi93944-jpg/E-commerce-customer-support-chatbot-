# ShopBot — E-Commerce Customer Support Chatbot

A beginner-friendly Flask + SQLite demo shop with product browsing, search, category filters, cart, registration/sign-in, demo checkout, order history, admin product/order management, and a simple rule-based NLP chatbot.

## 1. Requirements
- Python 3.10 or newer
- Internet connection for remote Unsplash product photos (optional)

## 2. Install and run (Windows)
Open PowerShell inside the extracted `ShopBot` folder:

```powershell
py -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
python app.py
```

If PowerShell blocks activation, run `python -m pip install -r requirements.txt` without activating the environment.

Open `http://127.0.0.1:5000` in your browser. The `ecommerce.db` database is created automatically the first time the app runs.

## 3. Demo admin
- Email: `admin@shopbot.local`
- Password: `Admin123!`

Sign in, then open **Admin** from the sidebar. Change the demo password and `SECRET_KEY` before any real deployment. This is a learning demo, not a production-ready payment system.

## 4. Features
- Product search and category filtering
- Product detail page
- Add/update/remove cart items
- Register/sign in with password hashing
- Demo checkout and order history
- Admin: add/delete products and update order status
- Chatbot endpoint at `/api/chat`

## 5. Common fixes
- **ModuleNotFoundError: flask** — run `python -m pip install -r requirements.txt`.
- **Port 5000 already in use** — stop the other Flask app or change `app.run(port=5001)`.
- **Photos don't load** — check your internet connection; the app still works without them.
- **Reset demo database** — stop the server, delete `ecommerce.db`, then run `python app.py` again. This removes local demo accounts and orders too.


## Open ShopBot on your phone (same Wi-Fi)
1. Start the app on your Windows laptop with `python app.py`.
2. Connect your phone and laptop to the same Wi-Fi network.
3. On Windows, open PowerShell and run `ipconfig`.
4. Find the active Wi-Fi adapter's `IPv4 Address` (for example `192.168.1.8`).
5. On your phone browser, open `http://YOUR-LAPTOP-IP:5000` (example: `http://192.168.1.8:5000`).
6. If Windows Firewall asks, allow Python on your private network only.

The app must remain running on the laptop while you use it on your phone. This is for local Wi-Fi testing, not public internet deployment.
