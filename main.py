from flask import Flask, request, jsonify, abort
import os, hmac, hashlib, requests

app = Flask(__name__)

BOT_TOKEN = os.environ.get("BOT_TOKEN")
CWALLET_SECRET = os.environ.get("CWALLET_SECRET")
ADMIN_ID = os.environ.get("ADMIN_ID")

def verify_signature(raw, header_sig):
    if not CWALLET_SECRET:
        return True
    computed = hmac.new(CWALLET_SECRET.encode(), raw, hashlib.sha256).hexdigest()
    return hmac.compare_digest(computed, header_sig or "")

@app.route("/cwallet-webhook", methods=["POST"])
def webhook():
    raw = request.get_data()
    if not verify_signature(raw, request.headers.get("X-Cwallet-Signature")):
        abort(400, "Bad signature")

    data = request.json
    status = data.get("status", "").lower()
    metadata = data.get("metadata", {})
    user_id = metadata.get("telegram_user_id")
    amount = data.get("amount")
    currency = data.get("currency", "USDT")

    if status != "completed":
        return jsonify({"ok": True, "note": "Not completed"}), 200

    message = f"✅ تم إيداع {amount} {currency} بنجاح من المستخدم {user_id}"
    requests.get(f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage",
                 params={"chat_id": ADMIN_ID, "text": message})

    requests.get(f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage",
                 params={"chat_id": user_id,
                         "text": f"💰 تم استلام إيداعك بقيمة {amount} {currency}. شكراً!"})

    return jsonify({"ok": True}), 200

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
