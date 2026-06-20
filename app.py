from flask import Flask, request, jsonify
from agent_runtime.runtime import ComposedAgentRuntime, AgentRuntimeError
from security.guardrails import GuardrailError

app = Flask(__name__, static_folder='static', static_url_path='')

@app.route('/')
def index():
    return app.send_static_file('index.html')

@app.route('/api/breakdown', methods=['POST'])
def api_breakdown():
    data = request.get_json() or {}
    goal = data.get('goal', '')
    deadline = data.get('deadline', '')
    availability = data.get('availability', '')
    sessions_pref = data.get('sessions', '')  # sessions_pref parameter mapping
    
    try:
        runtime = ComposedAgentRuntime()
        # Execute the agent planning & scheduling pipeline
        result = runtime.run(
            goal=goal,
            deadline=deadline,
            availability=availability,
            sessions_pref=sessions_pref
        )
        return jsonify({
            "status": "success",
            "data": result
        }), 200
    except GuardrailError as e:
        return jsonify({
            "status": "error",
            "message": f"Security Guardrail Blocked: {str(e)}"
        }), 400
    except AgentRuntimeError as e:
        return jsonify({
            "status": "error",
            "message": f"Agent Runtime Error: {str(e)}"
        }), 500
    except Exception as e:
        return jsonify({
            "status": "error",
            "message": f"An unexpected error occurred: {str(e)}"
        }), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True, threaded=False)
