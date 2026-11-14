
import os
from flask import Flask, render_template, request, jsonify
from dotenv import load_dotenv
from google import genai

load_dotenv()

app = Flask(__name__)

api_key = os.getenv("GEMINI_API_KEY")
client = genai.Client(api_key=api_key) if api_key else None


@app.route("/")
def home():
    return render_template("index.html")


@app.route("/generate", methods=["POST"])
def generate():
    if client is None:
        return jsonify({
            "error": "API-ключ Gemini не знайдено у файлі .env"
        }), 500

    data = request.get_json(silent=True) or {}
    tasks = data.get("tasks", [])

    if not isinstance(tasks, list) or not tasks:
        return jsonify({
            "error": "Спочатку додайте завдання."
        }), 400

    task_lines = []

    for task in tasks:
        if not isinstance(task, dict):
            continue

        name = str(task.get("name", "")).strip()
        priority = str(task.get("priority", "Середній"))
        done = task.get("done", False)

        if name and not done:
            task_lines.append(
                f"- {name} (пріоритет: {priority})"
            )

    if not task_lines:
        return jsonify({
            "error": "Немає невиконаних завдань."
        }), 400

    prompt = f"""
Ти — AI-помічник для планування дня.

Склади оптимальний розклад українською мовою
для таких завдань:

{chr(10).join(task_lines)}

Правила:
1. Починай планування о 09:00.
2. Враховуй пріоритет кожного завдання.
3. Оцінюй приблизну тривалість справ.
4. Додавай перерви між складними завданнями.
5. Не допускай накладання завдань у часі.
6. Вказуй час початку та завершення.
7. Наприкінці дай коротку пораду.

Формат:

📅 МІЙ РОЗКЛАД

09:00–10:00 — Завдання
10:00–10:15 — Перерва

💡 ПОРАДА:
Коротка рекомендація.
"""

    try:
        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=prompt
        )

        if not response.text:
            return jsonify({
                "error": "Gemini не повернув відповідь."
            }), 502

        return jsonify({
            "schedule": response.text
        })

    except Exception as error:
        print("Помилка Gemini:", repr(error))
        return jsonify({
            "error": "Помилка Gemini API. Перевірте "
                     "ключ, доступ до моделі та термінал."
        }), 502


if __name__ == "__main__":
    app.run(debug=True)