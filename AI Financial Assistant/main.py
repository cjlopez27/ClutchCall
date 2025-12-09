from flask import Flask, render_template_string, request, jsonify
import re

app = Flask(__name__)

# Default financial data
user_data = {
    "income": 3000,
    "expenses": 1500,
    "savings": 200,
    "categories": {
        "food": 300,
        "entertainment": 200,
        "bills": 1000
    }
}

# HTML for the chat interface
HTML_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <title>AI Financial Assistant 💬</title>
    <style>
        body { font-family: Arial; background: #f5f7fa; display: flex; justify-content: center; margin-top: 50px; }
        #chatbox { width: 420px; background: #fff; border-radius: 10px; box-shadow: 0 0 10px rgba(0,0,0,0.1); }
        #header { background: #007bff; color: white; padding: 12px; border-radius: 10px 10px 0 0; font-size: 18px; font-weight: bold; text-align: center; }
        #chatlog { height: 450px; overflow-y: auto; padding: 12px; border-bottom: 1px solid #ddd; }
        .user { text-align: right; margin: 8px 0; }
        .user span { background: #007bff; color: white; padding: 8px 12px; border-radius: 15px; display: inline-block; }
        .bot { text-align: left; margin: 8px 0; }
        .bot span { background: #f1f1f1; padding: 8px 12px; border-radius: 15px; display: inline-block; }
        #inputArea { display: flex; }
        #message { flex: 1; padding: 10px; border: none; border-radius: 0 0 0 10px; outline: none; }
        #send { background: #007bff; color: white; border: none; padding: 10px 20px; border-radius: 0 0 10px 0; cursor: pointer; }
        #send:hover { background: #0056b3; }
    </style>
</head>
<body>
    <div id="chatbox">
        <div id="header">AI Financial Assistant 💬</div>
        <div id="chatlog"></div>
        <div id="inputArea">
            <input type="text" id="message" placeholder="Type your message..." />
            <button id="send">Send</button>
        </div>
    </div>

    <script>
        async function sendMessage() {
            const input = document.getElementById("message");
            const msg = input.value.trim();
            if (!msg) return;
            const chatlog = document.getElementById("chatlog");

            chatlog.innerHTML += `<div class='user'><span>${msg}</span></div>`;
            input.value = "";
            chatlog.scrollTop = chatlog.scrollHeight;

            const response = await fetch("/chat", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ message: msg })
            });
            const data = await response.json();
            chatlog.innerHTML += `<div class='bot'><span>${data.reply}</span></div>`;
            chatlog.scrollTop = chatlog.scrollHeight;
        }

        document.getElementById("send").addEventListener("click", sendMessage);
        document.getElementById("message").addEventListener("keypress", e => {
            if (e.key === "Enter") sendMessage();
        });

        // Initial greeting message on load
        window.onload = () => {
            const chatlog = document.getElementById("chatlog");
            chatlog.innerHTML += `<div class='bot'><span>👋 Welcome to your AI Financial Assistant!<br>
            You can say things like:<br>
            • "Update my income to 4000"<br>
            • "Add 200 to entertainment"<br>
            • "Show my budget"<br>
            • "Help" to see all commands</span></div>`;
        };
    </script>
</body>
</html>
"""

def calculate_remaining_budget():
    total_spent = sum(user_data["categories"].values()) + user_data["savings"]
    return user_data["income"] - total_spent

def handle_input(user_input):
    text = user_input.lower().strip()

    # Help and greeting
    if text in ["hi", "hello", "hey"]:
        return ("👋 Hi there! I'm your AI Financial Assistant.<br>"
                "You can ask me to:<br>"
                "- Update your income or expenses<br>"
                "- Add to food, bills, or entertainment<br>"
                "- Type 'help' for a list of all commands!")

    if "help" in text:
        return ("🧭 Here’s what you can say:<br>"
                "• 'Show my budget'<br>"
                "• 'Add 200 to food'<br>"
                "• 'Update entertainment to 400'<br>"
                "• 'Set income to 5000'<br>"
                "• 'Update savings to 300'<br>"
                "• 'Reset data'")

    # Reset
    if "reset" in text:
        user_data.update({
            "income": 3000,
            "expenses": 1500,
            "savings": 200,
            "categories": {"food": 300, "entertainment": 200, "bills": 1000}
        })
        return "🔄 All data reset to default values."

    # Income updates
    if "income" in text:
        try:
            amount = float("".join([c for c in text if c.isdigit() or c == "."]))
            if any(word in text for word in ["update", "set", "change", "make"]):
                user_data["income"] = amount
                return f"💰 Income updated to ${amount:,.2f}."
            else:
                user_data["income"] += amount
                return f"💰 Added ${amount:,.2f} to income. Total: ${user_data['income']:,.2f}."
        except:
            return "⚠️ Couldn't process income update."

    # Expenses updates
    if "expense" in text or "expenses" in text:
        try:
            amount = float("".join([c for c in text if c.isdigit() or c == "."]))
            if any(word in text for word in ["update", "set", "change"]):
                user_data["expenses"] = amount
                return f"💳 Expenses updated to ${amount:,.2f}."
            else:
                user_data["expenses"] += amount
                return f"💳 Added ${amount:,.2f} to expenses. Total: ${user_data['expenses']:,.2f}."
        except:
            return "⚠️ Couldn't process expenses update."

    # Savings updates
    if "saving" in text or "savings" in text:
        try:
            amount = float("".join([c for c in text if c.isdigit() or c == "."]))
            if any(word in text for word in ["update", "set", "change"]):
                user_data["savings"] = amount
                return f"🏦 Savings updated to ${amount:,.2f}."
            else:
                user_data["savings"] += amount
                return f"🏦 Added ${amount:,.2f} to savings. Total: ${user_data['savings']:,.2f}."
        except:
            return "⚠️ Couldn't process savings update."

    # Category updates
    for category in user_data["categories"]:
        if category in text:
            try:
                amount = float("".join([c for c in text if c.isdigit() or c == "."]))
                if any(word in text for word in ["update", "set", "change", "make"]):
                    user_data["categories"][category] = amount
                    return f"🔄 {category.capitalize()} updated to ${amount:,.2f}."
                else:
                    user_data["categories"][category] += amount
                    return f"✅ Added ${amount:,.2f} to {category}. Total: ${user_data['categories'][category]:,.2f}."
            except:
                return f"⚠️ Please specify a valid amount for {category}."

    # Show budget breakdown
    if "budget" in text or "show" in text:
        remaining = calculate_remaining_budget()
        category_breakdown = "<br>".join([f"• {k.capitalize()}: ${v:,.2f}" for k, v in user_data["categories"].items()])
        return (f"💰 Here's your budget breakdown:<br>"
                f"Income: ${user_data['income']:,.2f}<br>"
                f"Expenses: ${user_data['expenses']:,.2f}<br>"
                f"Savings: ${user_data['savings']:,.2f}<br>"
                f"{category_breakdown}<br>"
                f"Remaining: ${remaining:,.2f}")

    # Default fallback summary
    remaining = calculate_remaining_budget()
    return (f"Here’s your quick financial summary:<br>"
            f"• Income: ${user_data['income']:,.2f}<br>"
            f"• Expenses: ${user_data['expenses']:,.2f}<br>"
            f"• Savings: ${user_data['savings']:,.2f}<br>"
            f"• Remaining budget: ${remaining:,.2f}<br><br>"
            "Need help? Type 'help' to see what else I can do.")

@app.route("/")
def index():
    return render_template_string(HTML_TEMPLATE)

@app.route("/chat", methods=["POST"])
def chat():
    user_message = request.json.get("message", "")
    reply = handle_input(user_message)
    return jsonify({"reply": reply})

if __name__ == "__main__":
    app.run(debug=True)
