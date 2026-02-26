"""
Example: Integrating ThreatVision into your existing Flask app
Run:  python app.py
"""

from flask import Flask, render_template, send_from_directory
import os

app = Flask(__name__)

# ── ThreatVision config ───────────────────────────────────────────────────────
app.config["THREAT_MODEL_SIZE"] = "n"    # 'n'=fast, 's'/'m'/'l'=accurate
app.config["THREAT_DEVICE"]     = "cpu"  # 'cuda' if GPU available

# Register the blueprint  ← THIS IS ALL YOU ADD TO YOUR EXISTING APP
from app.threat_detection.routes import threat_bp
app.register_blueprint(threat_bp, url_prefix="/threat")

# ── your existing routes ──────────────────────────────────────────────────────
@app.route("/")
def index():
    return render_template("index.html")

@app.route("/static/<path:filename>")
def static_files(filename):
    return send_from_directory("threat_detection/static", filename)


if __name__ == "__main__":
    os.makedirs("data", exist_ok=True)
    app.run(debug=True, port=5000)
